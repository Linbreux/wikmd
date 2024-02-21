import os
import tempfile
import time

from wikmd.search import Search, Watchdog


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
    res, total, pages, _ = s.search("index", 1)
    assert total == 1
    assert pages == 1
    assert res[0].path == tmp
    assert res[0].filename == fname

    _, _, _, sug = s.search("ndex", 1)
    assert "index" in sug


def test_pagination():
    tmp = tempfile.mkdtemp()
    s = Search(tmp, create=True)

    for i in range(25):
        fname, title = f"test_index_{i}.md", f"test index {i}"
        content = "\n".join(("index", "search" "test"))
        s.index(tmp, fname, title, content)

    res, total, pages, _ = s.search("index", 1)
    assert total == 25
    assert pages == 3


def test_index_and_delete():
    tmp = tempfile.mkdtemp()
    s = Search(tmp, create=True)
    fname, title = "test_index.md", "test index"
    content = "\n".join(("index", "search" "test"))

    s.index(tmp, fname, title, content)
    res, total, pages, _ = s.search("index", 1)
    assert total == 1
    assert pages == 1
    assert res[0].filename == fname

    s.delete(tmp, fname)
    res, total, pages, _ = s.search("index", 1)
    assert total == 0
    assert pages == 0
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
    res, total, pages, _ = s.search("index", 1)
    assert total == 3
    assert pages == 1
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

    assert s.search("index", 1) == ([], 0, 0, [])

    # test index
    content = "\n".join(("index", "search" "test"))
    fpath = os.path.join(tmpd, "a.md")
    with open(fpath, "w") as f:
        f.write(content)

    time.sleep(2)
    res, total, pages, _ = s.search("index", 1)
    assert total == 1
    assert pages == 1
    assert len(res) == 1
    assert res[0].path == "."
    assert "index" in res[0].highlights

    # test update
    with open(fpath, "w") as f:
        content2 = "\n".join(("something", "else", "entirely"))
        f.write(content2)

    time.sleep(2)
    res, total, pages, _ = s.search("index", 1)
    assert total == 0
    assert pages == 0
    assert len(res) == 0

    res, total, pages, _ = s.search("something", 1)
    assert total == 1
    assert pages == 1
    assert len(res) == 1
    assert res[0].path == "."
    assert "something" in res[0].highlights

    # test move
    os.rename(os.path.join(tmpd, "a.md"), os.path.join(tmpd, "b.md"))
    time.sleep(2)
    res, total, pages, _ = s.search("something", 1)
    assert total == 1
    assert pages == 1
    assert len(res) == 1
    assert res[0].path == "."
    assert res[0].filename == "b.md"
    assert "something" in res[0].highlights

    # test remove
    os.remove(os.path.join(tmpd, "b.md"))
    time.sleep(2)
    res, total, pages, _ = s.search("index", 1)
    assert total == 0
    assert pages == 0
    assert len(res) == 0

    res, total, pages, _ = s.search("something", 1)
    assert total == 0
    assert pages == 0
    assert len(res) == 0


def test_watchdog_subdirectory():
    tmps, tmpd = tempfile.mkdtemp(), tempfile.mkdtemp()
    s = Search(tmps, create=True)
    w = Watchdog(tmpd, tmps)
    w.start()

    assert s.search("index", 1) == ([], 0, 0, [])
    # test index subdir
    sub_dir = os.path.join(tmpd, "subdir")
    os.makedirs(sub_dir)
    fpath = os.path.join(sub_dir, "t.md")
    with open(fpath, "w") as f:
        content2 = "\n".join(("something", "else", "entirely"))
        f.write(content2)

    time.sleep(2)
    res, total, pages, _ = s.search("something", 1)
    assert total == 1
    assert pages == 1
    assert len(res) == 1
    assert res[0].path == "subdir"

    # test move subdir
    os.rename(os.path.join(sub_dir, "t.md"), os.path.join(tmpd, "z.md"))
    time.sleep(2)
    res, total, pages, _ = s.search("something", 1)
    assert total == 1
    assert pages == 1
    assert len(res) == 1
    assert res[0].path == "."
    assert res[0].filename == "z.md"
    assert "something" in res[0].highlights

    # test remove subdir
    os.rename(os.path.join(tmpd, "z.md"), os.path.join(sub_dir, "t.md"))
    os.remove(fpath)
    time.sleep(2)
    res, total, pages, _ = s.search("something", 1)
    assert total == 0
    assert pages == 0
    assert len(res) == 0

    w.stop()
