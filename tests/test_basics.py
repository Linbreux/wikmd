import pytest
import pypandoc
import os

from wiki import app

@pytest.fixture
def client():
    return app.test_client


def test_homepage():
    rv = app.test_client().get("/")
    
    # see if hompage responses
    assert rv.status_code == 200

    # Check if homepage loads
    assert b'What is it?' in rv.data


def test_list():
    rv = app.test_client().get("/list/")

    assert rv.status_code == 200
    assert b'homepage.md' in rv.data
    assert b'Features.md' in rv.data

def test_create_file_in_folder():
    if not os.path.exists("wiki/testing"):
        os.makedirs("wiki/testing")

    f = open("wiki/testing/test.md","w+")
    f.write("# this is the header\n extra content")
    f.close()

    rv = app.test_client().get("/testing/test")

    assert rv.status_code == 200
    assert b'this is the header' in rv.data 
    assert b'extra content' in rv.data 

    # remove created folders
    os.remove("wiki/testing/test.md")
    os.removedirs("wiki/testing/")
    