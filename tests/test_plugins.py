import pytest
from wikmd import wiki
from wikmd.wiki import app


@pytest.fixture()
def client():
    return app.test_client


@pytest.fixture()
def plugin_manager():
    return wiki.plugin_manager


def test_plugin_loading(plugin_manager):
    assert plugin_manager.plugins


def test_process_md(plugin_manager):
    before = "#test this is test\n text should still be available after plugin"
    md = before
    md = plugin_manager.broadcast("process_md", md)
    assert md == before


def test_draw_md(plugin_manager):
    before = "#test this is test\n[[draw]] \n next line"
    md = before
    md = plugin_manager.broadcast("process_md", md)
    assert md != before
    assert md != ""


def test_process_html(plugin_manager):
    before = "<html><h1>this is a test</h1></html>"
    html = before
    html = plugin_manager.broadcast("process_html", html)
    assert html == before
