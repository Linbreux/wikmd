import os
from pathlib import Path
import shutil

import pytest
from wikmd import wiki
from wikmd.wiki import app, cfg

cfg.wiki_directory = (Path(__file__).parent.parent / "src" / "wikmd" / "wiki_template").as_posix()

@pytest.fixture()
def client():
    return app.test_client


@pytest.fixture(scope="module")
def test_file_content():
    return b"this is the header", b"extra content"


@pytest.fixture()
def project_file(test_file_content):
    testing_folder = Path(cfg.wiki_directory) / "testing_folder"
    testing_folder.mkdir()

    test_file = testing_folder / "test.md"
    with test_file.open("wb") as fp:
        fp.writelines(test_file_content)

    yield test_file

    shutil.rmtree(str(testing_folder))


@pytest.fixture()
def wiki_file(project_file):
    return f"/{project_file.parent.name}/{project_file.stem}"


def test_homepage():
    """Homepage renders."""
    rv = app.test_client().get("/")

    assert rv.status_code == 200

    # Check if homepage loads
    assert b"What is it?" in rv.data


def test_list():
    """List functionality returns one of the standard files."""
    rv = app.test_client().get("/list/")

    assert rv.status_code == 200
    assert b"Features.md" in rv.data


def test_create_file_in_folder(wiki_file, test_file_content):
    """Make sure the created file is accessible."""
    rv = app.test_client().get(wiki_file)

    assert rv.status_code == 200
    assert test_file_content[0] in rv.data
    assert test_file_content[1] in rv.data


def test_search():
    """Search functionality returns result."""
    wiki.setup_search()
    rv = app.test_client().get("/search?q=Features")
    assert rv.status_code == 200
    assert b"Found" in rv.data
    assert b"result(s)" in rv.data
    assert b"Features" in rv.data


def test_new_file():
    """App can create files."""
    rv = app.test_client().get("/add_new")
    assert rv.status_code == 200
    assert b"content" in rv.data

    # create new file
    app.test_client().post("/add_new", data={
        "PN": "testing01234filenotexisting",
        "CT": "#testing file\n this is a test",
    })

    # look at file
    rv = app.test_client().get("/testing01234filenotexisting")
    assert b"testing file" in rv.data
    assert b"this is a test" in rv.data

    f = Path(cfg.wiki_directory) / "testing01234filenotexisting.md"
    f.unlink()


# create a new file in a folder using the wiki and check if it is visible in the wiki
def test_new_file_folder():
    """App can create folders."""
    rv = app.test_client().get("/add_new")
    assert rv.status_code == 200
    assert b"content" in rv.data

    # create new file in a folder
    app.test_client().post("/add_new", data={
        "PN": "testingfolder01234/testing01234filenotexisting",
        "CT": "#testing file\n this is a test",
    })

    # look at file
    rv = app.test_client().get("/testingfolder01234/testing01234filenotexisting")
    assert b"testing file" in rv.data
    assert b"this is a test" in rv.data

    f = Path(cfg.wiki_directory) / "testingfolder01234"
    shutil.rmtree(f)


# edits file using the wiki and check if it is visible in the wiki
def test_get_file_after_file_edit(project_file, wiki_file):
    with project_file.open("w+") as fp:
        fp.write("our new content")

    rv = app.test_client().get(wiki_file)
    assert rv.status_code == 200
    assert b"our new content" in rv.data


def test_get_file_after_api_edit(wiki_file):
    # Edit the file through API
    app.test_client().post(f"/edit{wiki_file}", data={
        "PN": wiki_file[1:],
        "CT": "#testing file\n this is a test",
    })

    rv = app.test_client().get(wiki_file)
    assert b"testing file" in rv.data
    assert b"this is a test" in rv.data


# edits file in folder using the wiki and check if it is visible in the wiki
def test_get_edit_page_content(project_file, wiki_file):
    with project_file.open("w+") as fp:
        fp.write("# this is the header\n extra content")

    rv = app.test_client().get(f"/edit{wiki_file}")
    assert rv.status_code == 200
    assert b"this is the header" in rv.data
