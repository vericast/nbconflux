import os
import pathlib

from nbconflux import exporter
import traitlets.config

import pytest


def test_init():
    c = traitlets.config.Config()
    c.ConfluenceExporter.url = "https://confluence.test.com/pages/viewpage.action?pageId=314159"
    exp = exporter.ConfluenceExporter(config=c)
    assert exp.server == "https://confluence.test.com"
    assert exp.page_id == 314159


@pytest.fixture
def config():
    """
    This is a full integration test, against a confluence you have access to.

    This should be populated for CI runs
    """
    c = traitlets.config.Config()

    cpage = os.getenv("CONFLUENCE_TEST")
    if not cpage:
        pytest.skip("Requires $CONFLUENCE_TEST to be defined")
    c.ConfluenceExporter.url = cpage

    c.ConfluenceExporter.username = os.getenv("CONFLUENCE_USERNAME")
    c.ConfluenceExporter.password = os.getenv("CONFLUENCE_PASSWORD")
    return c


def test_upload(config):
    exp = exporter.ConfluenceExporter(config=config)
    exp.from_filename(pathlib.Path(__file__).parent / "notebooks/nbconflux-test.ipynb")
