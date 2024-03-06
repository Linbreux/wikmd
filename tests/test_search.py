import os
import tempfile
import time
from pathlib import Path
import pytest

from wikmd.search import Search, Watchdog


@pytest.fixture(scope="module")
def search_dir():
    return tempfile.mkdtemp()


@pytest.fixture()
def search_file():
    file_name = "test_index.md"
    title = "test index"
    content = "index\nsearch\ntest"
    return file_name, title, content


@pytest.fixture()
def search_engine(search_dir):
    return Search(search_dir, create=True)


@pytest.fixture()
def search_engine_with_content(search_engine, search_dir, search_file):
    file_name, title, content = search_file

    search_engine.index(search_dir, file_name, title, content)
    return search_engine


def test_textify():
    tmp = tempfile.mkdtemp()
    s = Search(tmp, create=True)
    md = "# h1\n## h2\ntest"
    assert s.textify(md) == "h1\nh2\ntest"


def test_search(search_engine_with_content, search_dir, search_file):
    res, total, pages, _ = search_engine_with_content.search("index", 1)
    assert total == 1
    assert pages == 1
    assert res[0].path == search_dir
    assert res[0].filename == search_file[0]

    _, _, _, sug = search_engine_with_content.search("ndex", 1)
    assert "index" in sug


def test_pagination(search_engine, search_dir):
    for i in range(25):
        fname, title = f"test_index_{i}.md", f"test index {i}"
        content = "index\nsearch\ntest"
        search_engine.index(search_dir, fname, title, content)

    res, total, pages, _ = search_engine.search("index", 1)
    assert total == 25
    assert pages == 3


def test_index_and_delete(search_engine_with_content, search_dir, search_file ):
    search_engine_with_content.delete(search_dir, search_file[0])
    res, total, pages, _ = search_engine_with_content.search("index", 1)
    assert total == 0
    assert pages == 0
    assert len(res) == 0


def test_index_all(search_engine, search_dir):
    nf = []
    content = "index\nsearch\ntest"
    for n in ("a", "b"):
        file_name = f"{n}.md"
        p = Path(search_dir) / file_name
        with p.open("w") as f:
            f.write(content)
        nf.append((file_name, n, "."))

    # Add a file to a sub folder
    p_dir = Path(search_dir)
    (p_dir / "z").mkdir()
    file_name = p_dir / "z" / "y.md"
    with file_name.open("w") as f:
        f.write(content)
    nf.append(("y.md", "y", "z"))

    search_engine.index_all(search_dir, nf)
    res, total, pages, _ = search_engine.search("index", 1)
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
