"""Confluence page preprocessor that handles image and notebook
attachment versioning.
"""
import os

from collections import namedtuple

import requests

from nbconvert.preprocessors import Preprocessor
from traitlets import Instance, Any


Attachment = namedtuple('Attachment', 'id version download_url upload_url')


class ConfluencePreprocessor(Preprocessor):
    """Builds absolute URLs to versioned page attachments for use
    by HTMLExporter when rendering Confluence XHTML storage format.

    Attributes
    ----------
    exporter: ConfluenceExporter
        Exporter with information about the Confluence server and the page
        to be updated
    """
    exporter = Instance(klass='nbconflux.exporter.ConfluenceExporter', config=True)

    def preprocess(self, nb, resources):
        """Adds Attachment instances under resources['attachments']
        for every notebook output extracted by ExtractOutputPreprocessor
        and to be attached to the Confluence page.

        Also adds the filename of the notebook to be converted to a
        Confluence page under resources['notebook_filename'] and an associated
        Attachment for the notebook under resources['attachments'].

        Parameters
        ----------
        nb: nbformat.notebooknode.NotebookNode
            Root of a notebook
        resources: dict
            Additional nbconvert resources

        Returns
        -------
        2-tuple
            Modified nb and resources per the nbconvert Preprocessor API
            contract

        Note
        ----
        Uses the Confluence API to page through all attachments on the page in
        order to fetch their names and versions. This information is necessary
        to retain stable page-to-attachment version links in the page history.
        """
        # Get the attachments on the page, following ._links.next URLs until we know all attachment
        # names and versions.
        path = ('/rest/api/content/{page_id}/child/attachment?expand=version'
                .format(page_id=self.exporter.page_id))
        resources['attachments'] = {}
        while path:
            url = '{server}{path}'.format(server=self.exporter.server, path=path)
            resp = requests.get(url, auth=(self.exporter.username, self.exporter.password))
            resp.raise_for_status()
            attachments = resp.json()
            # Build a map from attachment filename to attachment ID and attachment version
            resources['attachments'].update(
                {result['title']: Attachment(result['id'], result['version']['number'], None, None)
                 for result in attachments['results']}
            )
            # Try to fetch the path (unfortunately, not full URL) of the next page of links
            path = attachments.get('_links', {}).get('next')

        # Notebook extreacted files to be attached to the page
        to_be_attached = dict(resources.get('outputs', {}))

        # consider the notebook itself an attachment that needs to be versioned
        if self.exporter.attach_ipynb:
            notebook_filename = os.path.basename(self.exporter.notebook_filename)
            to_be_attached[notebook_filename] = None
            resources['notebook_filename'] = notebook_filename

        for filename in to_be_attached:
            try:
                attachment_id, attachment_version, _, _ = resources['attachments'][filename]
            except KeyError:
                # The given filename is not yet an attachment in the page history so start at
                # version 0
                attachment_id = None
                attachment_version = 0
                upload_url = ('{server}/rest/api/content/{page_id}/child/attachment'
                              .format(server=self.exporter.server, page_id=self.exporter.page_id))
            else:
                upload_url = ('{server}/rest/api/content/{page_id}/child/attachment/{attachment_id}/data'
                              .format(server=self.exporter.server, page_id=self.exporter.page_id,
                                      attachment_id=attachment_id))

            # Populate the download url template
            download_url = ('{server}/download/attachments/{page_id}/{filename}?version={version}'
                            .format(server=self.exporter.server, page_id=self.exporter.page_id,
                                    filename=filename, version=attachment_version+1))

            # Keep the URL in the resources for later lookup in the page template
            resources['attachments'][filename] = Attachment(attachment_id, attachment_version, download_url, upload_url)

        return nb, resources