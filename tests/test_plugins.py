import pytest
from wikmd import wiki
from wikmd.wiki import app


@pytest.fixture()
def client():
    return app.test_client


def test_plugin_loading():
    assert wiki.plugins


def test_process_md():
    before = "#test this is test\n text should still be available after plugin"
    md = before
    for plugin in wiki.plugins:
        if "process_md" in dir(plugin):
            md = plugin.process_md(md)
    assert md == before


def test_draw_md():
    before = "#test this is test\n[[draw]] \n next line"
    md = before
    for plugin in wiki.plugins:
        if "process_md" in dir(plugin):
            md = plugin.process_md(md)
    assert md != before
    assert md != ""


def test_process_html():
    before = "<html><h1>this is a test</h1></html>"
    html = before
    for plugin in wiki.plugins:
        if "process_html" in dir(plugin):
            html = plugin.process_html(html)
    assert html == before