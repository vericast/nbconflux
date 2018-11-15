"""Confluence page exporter that transforms notebook content into Confluence
XML storage format and posts it to an existing page.
"""
import os
import urllib.parse as urlparse

import requests

from .filter import sanitize_html
from .markdown import ConfluenceMarkdownRenderer
from .preprocessor import ConfluencePreprocessor
from nbconvert import HTMLExporter
from nbconvert.filters.markdown_mistune import MarkdownWithMath
from traitlets import Bool, List, Unicode
from traitlets.config import Config


class ConfluenceExporter(HTMLExporter):
    """Converts a notebook into Confluence storage format XHTML and the
    notebook binary output cell assets into page attachments, and updates
    a given Confluence page with both.

    Attributes
    ----------
    server: str
        Base URL of the confluence server
    page_id: int
        Page ID to update
    notebook_filename: str
        Local filename of the notebook to be attached to the page

    url: traitlets.Unicode
        Human-readable Confluence page URL to convert to lookup page_id
    username: traitlets.Unicode
        Basic auth username
    password: traitlets.Unicode
        Basic auth password
    generate_toc: bool, optional
        Insert a Confluence table of contents macro at the top of the page (default: True)
    attach_ipynb: traitlets.Bool
        Attach the notebook ipynb to the page and link to it from the page footer (default: True)
    enable_style: traitlets.Bool
        Add the Jupyter base stylesheet to the page (default: True)
    enable_mathjax: traitlets.Bool
        Add MathJax to the page to render equations (default: False)
    """
    url = Unicode(config=True, help='Confluence URL to update with notebook content')
    username = Unicode(config=True, help='Confluence username')
    password = Unicode(config=True, help='Confluence password')
    generate_toc = Bool(config=True, default_value=True, help='Show a table of contents at the top of the page?')
    attach_ipynb = Bool(config=True, default_value=True, help='Attach the notebook ipynb to the page?')
    enable_style = Bool(config=True, default_value=True, help='Add basic Jupyter stylesheet?')
    enable_mathjax = Bool(config=True, default_value=False, help='Add MathJax to the page to render equations?')
    extra_labels = List(config=True, trait=Unicode(), help='List of additional labels to add to the page')

    @property
    def default_config(self):
        overrides = Config({
            'CSSHTMLHeaderPreprocessor': {
                'enabled': False
            },
            'HighlightMagicsPreprocessor': {
                'enabled': False
            },
            'TemplateExporter': {
                'exclude_input_prompt': True,
                'exclude_output_prompt': True
            },
            'TagRemovePreprocessor': {
                'remove_cell_tags': {'nocell', 'no-cell', 'no_cell'},
                'remove_input_tags': {'noinput', 'no-input', 'no_input'},
                'remove_all_outputs_tags': {'nooutput', 'no-output', 'no_output'},
                'enabled': True
            },
            'ExtractOutputPreprocessor': {
                'enabled': True
            },
        })

        c = super(ConfluenceExporter, self).default_config.copy()
        c.merge(overrides)
        return c

    def __init__(self, config, **kwargs):
        config.HTMLExporter.preprocessors = [ConfluencePreprocessor]
        config.HTMLExporter.filters = {
            'sanitize_html': sanitize_html,
        }

        super(ConfluenceExporter, self).__init__(config=config, **kwargs)
        self._preprocessors[-1].exporter = self

        self.template_path = [os.path.abspath(os.path.dirname(__file__))]
        self.template_file = 'confluence'
        # Must be at least a single character, or the header generator produces
        # an (invalid?) empty anchor tag that trips up bleach during
        # sanitization
        self.anchor_link_text = ' '

        self.server, self.page_id = self.get_server_info(self.url)
        self.notebook_filename = None

    def get_server_info(self, url):
        """Given a human visitable Confluence URL copy/pasted from the browser
        address bar, attempts to look up the programmatic page ID for use in
        working with the Confluence REST API.

        Parameters
        ----------
        url: str
            Human readable URL

        Returns
        -------
        2-tuple of str, int
            Confluence server base URL and programmatic page ID

        Raises
        ------
        Exception
            When the URL format is unknown, the Confluence API returns an error,
            or the Confluence API returns an unexpected result
        """
        pr = urlparse.urlparse(url)

        # Figure out the base URL of the server
        segs = pr.path.split('/')
        for i, seg in enumerate(segs):
            if seg in ('display', 'spaces'):
                server = pr.scheme + '://' + pr.netloc + '/'.join(segs[:i])
                break
        else:
            server = pr.scheme + '://' + pr.netloc

        # URL contains the pageId as a query arg
        # https://somewhere.com/pages/viewpage.action?pageId=123456
        query = urlparse.parse_qs(pr.query)
        if 'pageId' in query:
            # page ID is a query param
            return (server, int(query['pageId'][0]))

        # NOTE: Maybe these need to loop and find keys in the path, but I
        # don't have enough info yet on how these URLs can vary. Right now, just
        # using the path positions that I know about.

        # URL on Confluence Cloud contains the page ID in the path under a space
        # https://somewhere.atlassian.net/wiki/spaces/ASPACE/pages/123456/Page+Title
        if len(segs) > 5 and segs[4] == 'pages':
            page_id = int(segs[5])
            return (server, page_id)

        # URL on Confluence Server contains a space and page title requiring lookup
        # https://confluence.somewhere.com/display/ASPACE/Page+Title
        if len(segs) > 2 and segs[1] == 'display':
            # use space and page title to lookup the page ID
            space = segs[2]
            title = segs[3]

            resp = requests.get('{server}/rest/api/content?title={title}&spaceKey={space}'.format(server=server,
                                                                                                  title=title,
                                                                                                  space=space),
                                auth=(self.username, self.password)
                               )
            resp.raise_for_status()
            results = resp.json()['results']
            if not results:
                raise ValueError(
                    'Could not locate {} in {}. Ensure the page exists: '
                    'nbconflux will not create it for you.'.format(title, space)
                )
            return (server, int(resp.json()['results'][0]['id']))

        raise RuntimeError('Unknown URL format: ' + url)

    def update_page(self, page_id, body):
        """Updates the body of the page with new content.

        Parameters
        ----------
        page_id: int
            Confluence page ID
        body: str
            Confluence storage format content
            https://confluence.atlassian.com/doc/confluence-storage-format-790796544.html

        Raises
        ------
        Exception
            When Confluence API returns an error
        """
        # Fetch version number from the existing page so that we can increment it by 1.
        resp = requests.get('{server}/rest/api/content/{page_id}'.format(server=self.server,
                                                                         page_id=page_id),
                            auth=(self.username, self.password))
        resp.raise_for_status()
        content = resp.json()
        version = content['version']['number']
        # Newer Confluence requires title when posting the page back
        title = content['title']

        # Update the page with the new content.
        resp = requests.put('{server}/rest/api/content/{page_id}'.format(server=self.server,
                                                                         page_id=page_id),
                            json={
                               'version': {"number":version + 1},
                               'title': title,
                               'type': 'page',
                               'body': {
                                   'storage': {
                                       'representation': 'storage',
                                       'value': body
                                   }
                               }
                            },
                            auth=(self.username, self.password)
                           )
        resp.raise_for_status()

    def add_label(self, page_id, label):
        """Adds a label with global prefix to the page.

        Parameters
        ----------
        page_id: int
            Confluence page ID
        label: str
            Label to add

        Raises
        ------
        Exception
            When Confluence API returns an error
        """
        # Add the nbconflux label to the set of labels. OK if it already exists.
        resp = requests.post('{server}/rest/api/content/{page_id}/label'.format(server=self.server,
                                                                                page_id=page_id),
                             json=[dict(prefix='global', name=label)],
                             auth=(self.username, self.password))
        resp.raise_for_status()

    def add_or_update_attachment(self, filename, data, resources):
        """Creates or updates page attachments.

        Parameters
        ----------
        filename: str
            Local filename
        data: bytes
            Data to post
        resources: dict
            Additional nbconvert resources

        Returns
        -------
        request.Response
            Response from the Confluence server
        """
        basename = os.path.basename(filename)
        attachment = resources.get('attachments', {}).get(basename)
        if attachment is None:
            return
        files = {
            'file': (basename, data)
        }
        resp = requests.post(attachment.upload_url,
                             headers={
                                 'X-Atlassian-Token': 'nocheck'
                             },
                             files=files,
                             auth=(self.username, self.password))
        resp.raise_for_status()
        return resp

    def markdown2html(self, source):
        """Override the base class implementation to force empty tags to be
        XHTML compliant for compatibility with Confluence storage format.
        """
        renderer = ConfluenceMarkdownRenderer(escape=False,
                                              use_xhtml=True,
                                              anchor_link_text=self.anchor_link_text)
        return MarkdownWithMath(renderer=renderer).render(source)

    def from_notebook_node(self, nb, resources=None, **kw):
        """Publishes a notebook to Confluence given a notebook object
        from nbformat.

        Parameters
        ----------
        nb: nbformat.notebooknode.NotebookNode
            Root of a notebook
        resources: dict
            Additional nbconvert resources

        Returns
        -------
        2-tuple
            Published Confluence storage format HTML and nbconvert resources
        """
        if self.notebook_filename is None:
            raise ValueError('only from_filename is supported')

        # Seed resources with option flags
        resources = resources if resources is not None else {}
        resources['generate_toc'] = self.generate_toc
        resources['enable_mathjax'] = self.enable_mathjax
        resources['enable_style'] = self.enable_style

        # Convert the notebook to Confluence storage format, which is XHTML-like
        html, resources = super(ConfluenceExporter, self).from_notebook_node(nb, resources, **kw)

        # Update the page with the new content
        self.update_page(self.page_id, html)
        # Add the nbconflux label to the page for tracking
        self.add_label(self.page_id, 'nbconflux')
        # If requested, add any extra labels to the page
        if self.extra_labels:
            for label in self.extra_labels:
                self.add_label(self.page_id, label)

        # Create or update all attachments on the page
        for filename, data in resources.get('outputs', {}).items():
            self.add_or_update_attachment(filename, data, resources)

        # Create or update the notebook document attachment on the page
        if self.attach_ipynb:
            with open(self.notebook_filename, encoding='utf-8') as f:
                self.add_or_update_attachment(self.notebook_filename, f.read(), resources)

        return html, resources

    def from_filename(self, filename, *args, **kwargs):
        """Publishes a notebook to Confluence given a local notebook filename.

        Parameters
        ----------
        filename: str
            Path to a local ipynb

        Returns
        -------
        2-tuple
            Published Confluence storage format HTML and nbconvert resources
        """
        # Preprocessor needs the filename to attach the notebook source file properly
        # so stash it here for later lookup
        self.notebook_filename = filename
        return super(ConfluenceExporter, self).from_filename(filename, *args, **kwargs)
