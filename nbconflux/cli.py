import argparse
import getpass
import os
import sys

from .api import notebook_to_page


def main(argv=None):
    """Command line interface."""
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
        description='Converts Jupyter Notebooks to Atlassian Confluence pages using nbconvert',
        epilog="Collects credentials from the following locations:\n"
        "1. CONFLUENCE_USERNAME and CONFLUENCE_PASSWORD environment variables\n"
        "2. ~/.nbconflux file in the format username:password\n"
        "3. User prompts")
    parser.add_argument('notebook', type=str, help='Path to local notebook (ipynb)')
    parser.add_argument('url', type=str, help='URL of Confluence page to update')
    parser.add_argument('--exclude-toc', action='store_true', help='Do not generate a table of contents')
    parser.add_argument('--exclude-ipynb', action='store_true', help='Do not attach the notebook to the page')
    parser.add_argument('--exclude-style', action='store_true', help='Do not include the Jupyter base stylesheet')
    parser.add_argument('--include-mathjax', action='store_true', help='Enable MathJax on the page')
    parser.add_argument('--extra-labels', nargs='+', type=str, help='Additional labels to add to the page')

    args = parser.parse_args(argv or sys.argv[1:])

    username = os.getenv('CONFLUENCE_USERNAME')
    password = os.getenv('CONFLUENCE_PASSWORD')
    cfg = os.path.expanduser('~/.nbconflux')

    # Prefer credentials in environment variables
    if username and password:
        print('Using credentials for {} from environment variables'.format(username))
    elif os.path.isfile(cfg):
        # Fallback on credentials in a well known file location
        with open(cfg) as f:
            segs = f.read().strip().split(':', 1)
            if len(segs) == 2:
                username = segs[0]
                password = segs[1]
                print('Using credentials for {} from configuration file'.format(username))

    # Prompt the user for missing credentials
    if username is None:
        current = getpass.getuser()
        current = current[2:] if current.startswith('p-') else current
        username = input('Confluence username ({}): '.format(current))
        # Use the current username if the user doesn't enter anything
        if not username.strip():
            username = current
    if password is None:
        password = getpass.getpass('Confluence password: ')

    notebook_to_page(args.notebook, args.url, username, password,
                     generate_toc=not args.exclude_toc, attach_ipynb=not args.exclude_ipynb,
                     enable_style=not args.exclude_style, enable_mathjax=args.include_mathjax,
                     extra_labels=args.extra_labels)

if __name__ == '__main__':
    main()