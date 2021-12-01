import pytest
from wiki import app

@pytest.fixture
def client():
    return app.test_client


def test_homepage():
    rv = client.get("/")
    assert b'nope' in rv.data

    
