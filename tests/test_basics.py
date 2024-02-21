from wikmd import wiki
import pytest
import os

from wikmd.wiki import app

@pytest.fixture
def client():
    return app.test_client

# test if homepage responses
def test_homepage():
    rv = app.test_client().get("/")
    
    # see if hompage responses
    assert rv.status_code == 200

    # Check if homepage loads
    assert b'What is it?' in rv.data

# check if list returns all files (tests only 2 defaults)
def test_list():
    rv = app.test_client().get("/list/")

    assert rv.status_code == 200
    #assert b'homepage.md' in rv.data
    assert b'Features.md' in rv.data

# creates a file and check if the content of the file is visible in the wiki
def test_create_file_in_folder():
    # create dir if it does not exist
    if not os.path.exists("wiki/testing_folder_0123"):
        os.makedirs("wiki/testing_folder_0123")

    # write content in the test.md file
    f = open("wiki/testing_folder_0123/test.md","w+")
    f.write("# this is the header\n extra content")
    f.close()

    rv = app.test_client().get("/testing_folder_0123/test")

    assert rv.status_code == 200
    assert b'this is the header' in rv.data 
    assert b'extra content' in rv.data 

    # remove created folders
    os.remove("wiki/testing_folder_0123/test.md")
    os.removedirs("wiki/testing_folder_0123/")
    
# checks if the search response with searchterm = Features    
def test_search():
     wiki.setup_search()
     rv = app.test_client().get("/?q=Features")
     assert rv.status_code == 200
     assert b'Found' in rv.data
     assert b'result(s)' in rv.data
     assert b'Features' in rv.data

# create a new file using the wiki and check if it is visible in the wiki
def test_new_file():
    rv = app.test_client().get("/add_new")
    assert rv.status_code == 200
    assert b'content' in rv.data

    # create new file
    rv = app.test_client().post("/add_new", data=dict(
        PN="testing01234filenotexisting",
        CT="#testing file\n this is a test"
    ))

    # look at file
    rv = app.test_client().get("/testing01234filenotexisting")
    assert b'testing file' in rv.data
    assert b'this is a test' in rv.data

    os.remove("wiki/testing01234filenotexisting.md")

# create a new file in a folder using the wiki and check if it is visible in the wiki
def test_new_file_folder():
    rv = app.test_client().get("/add_new")
    assert rv.status_code == 200
    assert b'content' in rv.data

    # create new file
    rv = app.test_client().post("/add_new", data=dict(
        PN="testingfolder01234/testing01234filenotexisting",
        CT="#testing file\n this is a test"
    ))
    
    # look at file
    rv = app.test_client().get("/testingfolder01234/testing01234filenotexisting")
    assert b'testing file' in rv.data
    assert b'this is a test' in rv.data

    os.remove("wiki/testingfolder01234/testing01234filenotexisting.md")
    os.removedirs("wiki/testingfolder01234")

# edits file using the wiki and check if it is visible in the wiki
def test_edit_file():
    f = open("wiki/testing01234filenotexisting.md","w+")
    f.write("# this is the header\n extra content")
    f.close()

    rv = app.test_client().get("/edit/testing01234filenotexisting")
    assert rv.status_code == 200
    assert b'this is the header' in rv.data

    # create new file
    rv = app.test_client().post("/edit/testing01234filenotexisting", data=dict(
        PN="testing01234filenotexisting",
        CT="#testing file\n this is a test"
    ))
    
    # look at file
    rv = app.test_client().get("/testing01234filenotexisting")
    assert b'testing file' in rv.data
    assert b'this is a test' in rv.data

    os.remove("wiki/testing01234filenotexisting.md")

# edits file in folder using the wiki and check if it is visible in the wiki
def test_edit_file_folder():
    if not os.path.exists("wiki/testingfolder01234"):
        os.makedirs("wiki/testingfolder01234")

    f = open("wiki/testingfolder01234/testing01234filenotexisting.md","w+")
    f.write("# this is the header\n extra content")
    f.close()

    rv = app.test_client().get("/edit/testingfolder01234/testing01234filenotexisting")
    assert rv.status_code == 200
    assert b'this is the header' in rv.data

    # create new file
    rv = app.test_client().post("/edit/testingfolder01234/testing01234filenotexisting", data=dict(
        PN="testingfolder01234/testing01234filenotexisting",
        CT="#testing file\n this is a test"
    ))
    
    # look at file
    rv = app.test_client().get("/testingfolder01234/testing01234filenotexisting")
    assert b'testing file' in rv.data
    assert b'this is a test' in rv.data

    os.remove("wiki/testingfolder01234/testing01234filenotexisting.md")
    os.removedirs("wiki/testingfolder01234")
