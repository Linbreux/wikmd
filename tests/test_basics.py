import os
from pathlib import Path
import shutil

import pytest
from wikmd import wiki
from wikmd.wiki import app, cfg, setup_wiki_template


@pytest.fixture(scope="function", autouse=True)
def wiki_path(tmp_path: Path):
    """Sets up the temporary wiki path.
     autouse=True is needed as this behaves as a setup for the tests.
    """
    wiki_path = tmp_path / "wiki"
    wiki_path.mkdir()
    cfg.wiki_directory = wiki_path.as_posix()
    setup_wiki_template()
    return wiki_path


@pytest.fixture()
def client():
    return app.test_client


@pytest.fixture(scope="module")
def test_file_content():
    return b"this is the header", b"extra content"


@pytest.fixture()
def project_file(wiki_path, test_file_content):
    testing_folder = wiki_path / "testing_folder"
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
    """Test for accessing file that exists, GET '/{file_name}'."""
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


def test_add_new_file(wiki_path):
    """App can create files."""
    wiki.setup_wiki_template()
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

    f = wiki_path / "testing01234filenotexisting.md"
    f.unlink()


def test_bad_file_names():
    """Test for creating files with odd character in names."""
    # Disallowed
    bad_name = "file*with*star"
    bad_all_bad = r'<>:"/\|?*'

    r = app.test_client().post("/add_new", data={
        "PN": bad_all_bad,
        "CT": "#testing file\n this is a test",
    })
    assert r.status_code == 200
    assert b"Page name not accepted." in r.data

    r = app.test_client().post("/add_new", data={
        "PN": bad_name,
        "CT": "#testing file\n this is a test",
    })
    assert r.status_code == 200
    assert bad_name.replace("*", "").encode() in r.data


def test_ok_file_names(wiki_path):
    """Test for creating files with odd character in names."""
    # Disallowed
    ok_name1 = "file with space"
    ok_name2 = 'file with slash/is a folder'
    r = app.test_client().post("/add_new", data={
        "PN": ok_name1,
        "CT": "#testing file\n this is a test",
    })
    assert r.status_code == 302
    assert (wiki_path / ok_name1).with_suffix(".md").exists()

    r = app.test_client().post("/add_new", data={
        "PN": ok_name2,
        "CT": "#testing file\n this is a test",
    })
    assert r.status_code == 302
    assert (wiki_path / ok_name2).with_suffix(".md").exists()


# create a new file in a folder using the wiki and check if it is visible in the wiki
def test_new_file_folder(wiki_path):
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

    f = wiki_path / "testingfolder01234"
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
