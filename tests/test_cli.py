import pytest

from nbconflux import cli


@pytest.fixture(scope='module')
def argv():
    return [
        'fake-notebook.ipynb',
        'https://confluence.localhost/some/page',
        '--exclude-toc',
        '--exclude-ipynb',
        '--exclude-style',
        '--include-mathjax',
        '--extra-labels', 'extra-label-1', 'extra-label-2'
    ]


def mock_notebook_to_page(notebook, url, username, password, generate_toc, attach_ipynb,
                          enable_style, enable_mathjax, extra_labels, notebook_css):
    assert notebook == 'fake-notebook.ipynb'
    assert url == 'https://confluence.localhost/some/page'
    assert username == 'fake-username'
    assert password == 'fake-password'
    assert not generate_toc
    assert not attach_ipynb
    assert not enable_style
    assert enable_mathjax
    assert extra_labels == ['extra-label-1', 'extra-label-2']
    assert notebook_css is None


def test_cli_args(argv, monkeypatch):
    """Should respect command line arguments."""
    monkeypatch.setattr('os.path.isfile', lambda x: False)
    monkeypatch.setattr(cli, 'notebook_to_page', mock_notebook_to_page)
    monkeypatch.setitem(__builtins__, 'input', lambda x: 'fake-username')
    monkeypatch.setattr('getpass.getpass', lambda x: 'fake-password')
    cli.main(argv)


def test_blank_username(argv, monkeypatch):
    """Should default to the current username."""
    monkeypatch.setattr('os.path.isfile', lambda x: False)
    monkeypatch.setattr(cli, 'notebook_to_page', mock_notebook_to_page)
    monkeypatch.setitem(__builtins__, 'input', lambda x: '')
    monkeypatch.setattr('getpass.getpass', lambda x: 'fake-password')
    monkeypatch.setattr('getpass.getuser', lambda: 'fake-username')
    cli.main(argv)


def test_cli_env_vars(argv, monkeypatch):
    """Should use credentials from the environment."""
    monkeypatch.setattr('os.path.isfile', lambda x: False)
    monkeypatch.setattr(cli, 'notebook_to_page', mock_notebook_to_page)
    monkeypatch.setenv('CONFLUENCE_USERNAME', 'fake-username')
    monkeypatch.setenv('CONFLUENCE_PASSWORD', 'fake-password')
    cli.main(argv)


def test_cli_creds_file(argv, tmpdir, monkeypatch):
    """Should use credentials from the user's home directory."""
    monkeypatch.setattr(cli, 'notebook_to_page', mock_notebook_to_page)
    monkeypatch.setattr('os.path.isfile', lambda x: True)

    cfg = tmpdir.mkdir('nbconflux_test').join('.nbconflux')
    cfg.write('fake-username:fake-password')

    monkeypatch.setattr('os.path.expanduser', lambda x: str(cfg))
    cli.main(argv)
