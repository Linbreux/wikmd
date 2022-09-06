import os
import tempfile
import time
from unittest import mock

from search import Search, Watchdog
from wiki import app


def test_textify():
    tmp = tempfile.mkdtemp()
    s = Search(tmp, create=True)
    md = "\n".join(("# h1", "## h2", "test"))
    assert s.textify(md) == "h1\nh2\ntest"


def test_index_and_search():
    tmp = tempfile.mkdtemp()
    s = Search(tmp, create=True)
    fname, title = "test_index.md", "test index"
    content = "\n".join(("index", "search" "test"))

    s.index(tmp, fname, title, content)
    res, _ = s.search("index")
    assert res[0].path == tmp
    assert res[0].filename == fname

    _, sug = s.search("ndex")
    assert "index" in sug


def test_index_and_delete():
    tmp = tempfile.mkdtemp()
    s = Search(tmp, create=True)
    fname, title = "test_index.md", "test index"
    content = "\n".join(("index", "search" "test"))

    s.index(tmp, fname, title, content)
    res, _ = s.search("index")
    assert res[0].filename == fname

    s.delete(tmp, fname)
    res, _ = s.search("index")
    assert len(res) == 0


def test_index_all():
    tmps, tmpd = tempfile.mkdtemp(), tempfile.mkdtemp()
    s = Search(tmps, create=True)
    nf = []
    content = "\n".join(("index", "search" "test"))
    for n in ("a", "b"):
        fname = f"{n}.md"
        with open(os.path.join(tmpd, fname), "w") as f:
            f.write(content)
        nf.append((fname, n, "."))

    os.mkdir(os.path.join(tmpd, "z"))
    with open(os.path.join(tmpd, "z", "y.md"), "w") as f:
        f.write(content)
    nf.append(("y.md", "y", "z"))

    s.index_all(tmpd, nf)
    res, _ = s.search("index")
    assert len(res) == 3
    a, b, z = res
    assert a.path == "."
    assert a.filename == "a.md"
    assert b.path == "."
    assert b.filename == "b.md"
    assert z.path == "z"
    assert z.filename == "y.md"


def test_watchdog():
    tmps, tmpd = tempfile.mkdtemp(), tempfile.mkdtemp()
    s = Search(tmps, create=True)
    w = Watchdog(tmpd, tmps)
    w.start()

    assert s.search("index") == ([], [])

    # test index
    content = "\n".join(("index", "search" "test"))
    fpath = os.path.join(tmpd, "a.md")
    with open(fpath, "w") as f:
        f.write(content)

    time.sleep(1)
    res, _ = s.search("index")
    assert len(res) == 1
    assert "index" in res[0].highlights

    # test update
    with open(fpath, "w") as f:
        content2 = "\n".join(("something", "else", "entirely"))
        f.write(content2)

    time.sleep(1)
    res, _ = s.search("index")
    assert len(res) == 0

    res, _ = s.search("something")
    assert len(res) == 1
    assert "something" in res[0].highlights

    # test remove
    os.remove(fpath)
    time.sleep(1)
    res, _ = s.search("index")
    assert len(res) == 0

    res, _ = s.search("something")
    assert len(res) == 0

    w.stop()
