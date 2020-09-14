import os
import re

import responses
import nbconflux
import pytest


@pytest.fixture(scope='module')
def notebook_path(request):
    return os.path.join(os.path.abspath(os.path.dirname(request.module.__file__)), 'notebooks', 'nbconflux-test.ipynb')


@pytest.fixture(scope='module')
def page_url(request):
    return 'http://confluence.localhost/display/SPACE/Some+Page+Name'


@pytest.fixture(scope='module')
def bad_page_url(request):
    return 'http://confluence.localhost/display/SPACE/Does+Not+Exist'


@pytest.fixture(scope='module')
def server():
    with responses.RequestsMock(assert_all_requests_are_fired=False) as mock:
        yield mock


def test_version():
    """Package should have a version defined."""
    version = getattr(nbconflux, '__version__', None)
    assert version is not None


def test_post_to_confluence(notebook_path, page_url, server):
    """Notebook should post to a mock Confluence server."""
    # Mock page space/name translation to page ID
    server.add('GET', 'http://confluence.localhost/rest/api/content?title=Some+Page+Name&spaceKey=SPACE',
        match_querystring=True,
        json={
            'results': [
                {
                    'id': 12345
                }
            ]
        })
    # Mock current page attachment lookup
    server.add('GET', 'http://confluence.localhost/rest/api/content/12345/child/attachment?expand=version',
        match_querystring=True,
        json={
            'results': [
                {
                    'id': 1,
                    'title': 'output_6_0.png',
                    'version': {
                        'number': 5
                    }
                },
                {
                    'id': 5,
                    'title': 'fake-image-2.jpg',
                    'version': {
                        'number': 10
                    }
                }
            ]
        })
    # Mock current page version lookup
    server.add('GET', 'http://confluence.localhost/rest/api/content/12345',
        json={
            'title': 'fake-title',
            'version': {
                'number': 100
            }
        })
    # Mock updating the page content
    server.add('PUT', 'http://confluence.localhost/rest/api/content/12345')
    # Mock adding the page label (we expect this to be invoked three times, once for each label)
    server.add('POST', 'http://confluence.localhost/rest/api/content/12345/label')
    server.add('POST', 'http://confluence.localhost/rest/api/content/12345/label')
    server.add('POST', 'http://confluence.localhost/rest/api/content/12345/label')
    # Mock updating attachments
    server.add('POST', 'http://confluence.localhost/rest/api/content/12345/child/attachment/1/data')
    server.add('POST', 'http://confluence.localhost/rest/api/content/12345/child/attachment')

    html, resources = nbconflux.notebook_to_page(notebook_path, page_url, 'fake-username', 'fake-pass',
                                                 extra_labels=['extra-label-1', 'extra-label-2'])

    # Includes a table of contents macro
    assert 'ac:name="toc"' in html
    # Markdown is HTML
    assert re.search('<h1[^>]*>Notebook for Testing', html) is not None
    # Makrdown image is <ac:image>
    assert '<ac:image ac:alt="Juputer Logo"><ri:url ri:value="http://jupyter.org/assets/nav_logo.svg"></ri:url></ac:image>' in html
    # Image is a properly versioned attachment
    assert '<ac:image><ri:url ri:value="http://confluence.localhost/download/attachments/12345/output_6_0.png?version=6" /></ac:image>' in html
    # Input hidden, output shown
    assert 'sns.violinplot' not in html
    # Output hidden, input shown
    assert "&quot;This cell output is hidden.&quot;" in html
    assert "<pre>This cell output is hidden" not in html
    # Cell completely hidden
    assert 'This cell is completely hidden.' not in html
    # Notebook linked in footer
    assert '<a href="http://confluence.localhost/download/attachments/12345/nbconflux-test.ipynb?version=1">nbconflux-test.ipynb</a>' in html
    # MathJax not included
    assert 'MathJax' not in html

    # Default label added to page
    req = server.calls[4].request
    assert req.method == 'POST'
    assert b'nbconflux' in req.body
    assert 'Authorization' in req.headers

    # Additional labels added to page
    req = server.calls[5].request
    assert req.method == 'POST'
    assert b'extra-label-1' in req.body
    assert 'Authorization' in req.headers

    req = server.calls[6].request
    assert req.method == 'POST'
    assert b'extra-label-2' in req.body
    assert 'Authorization' in req.headers

    # Existing image attachment updated
    req = server.calls[7].request
    assert req.method == 'POST'
    assert b'PNG' in req.body
    assert b'filename="output_6_0.png"' in req.body
    assert 'Authorization' in req.headers

    # New notebook attachment created
    req = server.calls[8].request
    assert req.method == 'POST'
    assert b'filename="nbconflux-test.ipynb"' in req.body
    assert b'"nbformat": 4' in req.body
    assert 'Authorization' in req.headers


def test_optional_components(notebook_path, page_url, server):
    """Page should not include a table of contents or notebook attachment,
    and include MathJax.
    """
    # Mock page space/name translation to page ID
    server.add('GET', 'http://confluence.localhost/rest/api/content?title=Some+Page+Name&spaceKey=SPACE',
        match_querystring=True,
        json={
            'results': [
                {
                    'id': 12345
                }
            ]
        })
    # Mock current page attachment lookup
    server.add('GET', 'http://confluence.localhost/rest/api/content/12345/child/attachment?expand=version',
        match_querystring=True,
        json={
            'results': [
                {
                    'id': 1,
                    'title': 'output_6_0.png',
                    'version': {
                        'number': 5
                    }
                }
            ]
        })
    # Mock current page version lookup
    server.add('GET', 'http://confluence.localhost/rest/api/content/12345',
        json={
            'version': {
                'number': 100
            }
        })
    # Mock updating the page content
    server.add('PUT', 'http://confluence.localhost/rest/api/content/12345')
    # Mock adding the page label
    server.add('POST', 'http://confluence.localhost/rest/api/content/12345/label')
    # Mock updating image attachment, but not the notebook attachment
    server.add('POST', 'http://confluence.localhost/rest/api/content/12345/child/attachment/1/data')

    html, resources = nbconflux.notebook_to_page(notebook_path, page_url, 'fake-username', 'fake-pass', False, False, False, True)

    # Excludes a table of contents macro
    assert 'ac:name="toc"' not in html
    # Excludes the Jupyter stylesheet
    assert 'ipython.min.css' not in html
    # Includes MathJax
    assert 'MathJax' in html


def test_post_to_unknown(notebook_path, bad_page_url, server):
    """Should raise an exception that the page URL is unknown."""
    # Mock page space/name translation to page ID
    server.add('GET', 'http://confluence.localhost/rest/api/content?title=Does+Not+Exist&spaceKey=SPACE',
        match_querystring=True,
        json={
            'results': []
        })
    with pytest.raises(ValueError) as ex:
        nbconflux.notebook_to_page(notebook_path, bad_page_url, 'fake-username', 'fake-pass')

    assert 'Could not locate' in str(ex.value)
