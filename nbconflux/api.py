import getpass

from .exporter import ConfluenceExporter
from traitlets.config import Config


def notebook_to_page(notebook_file, confluence_url, username=None, password=None,
    generate_toc=True, attach_ipynb=True, include_style=True, include_mathjax=False):
    """Transforms the given notebook file into Confluence storage format and
    updates the given Confluence URL with its content.

    Attaches images to the page and links to pinned versions to preserve
    a complete page snapshot in the history. Also attaches a copy of the source
    notebook to the page and links to that version in the page footer.

    Parameters
    ----------
    notebook_file: str
        Relative or absolute path to the notebook to transform and post
    confluence_url: str
        Page URL to update with the notebook content. The page must
        already exist.
    username: str, optional
        Confluence username. Uses the current username if not specified.
    password: str, optional
        Confluence password. Prompts for the password if not given.
    generate_toc: bool, optional
        Insert a Confluence table of contents macro at the top of the page (default: True)
    attach_ipynb: bool, optional
        Attach the notebook ipynb to the page and link to it from the page footer (default: True)
    include_style: bool, optional
        Include the Jupyter base stylesheet (default: True)
    include_mathjax: bool, optional
        Include the MathJax script and configuration (default: False)
    """
    if username is None:
        username = getpass.getuser()
    if password is None:
        password = getpass.getpass('Confluence password for {}:'.format(username))

    c = Config()
    c.ConfluenceExporter.url = confluence_url
    c.ConfluenceExporter.username = username
    c.ConfluenceExporter.password = password
    c.ConfluenceExporter.generate_toc = generate_toc
    c.ConfluenceExporter.attach_ipynb = attach_ipynb
    c.ConfluenceExporter.include_style = include_style
    c.ConfluenceExporter.include_mathjax = include_mathjax

    exporter = ConfluenceExporter(c)
    result = exporter.from_filename(notebook_file)
    print('Updated', confluence_url)
    return result