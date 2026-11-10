import os
import tempfile
import time

from wikmd.search import Search, Watchdog


def test_start_returns_after_watcher_is_ready():
    tmps, tmpd = tempfile.mkdtemp(), tempfile.mkdtemp()
    s = Search(tmps, create=True)
    w = Watchdog(tmpd, tmps)
    w.start()
    try:
        # No sleep: a file created immediately after start() returns
        # must still be picked up (previously lost in the startup gap).
        with open(os.path.join(tmpd, "a.md"), "w") as f:
            f.write("index\nsearch\ntest")
        deadline = time.monotonic() + 20
        total = 0
        while time.monotonic() < deadline:
            _, total, _, _ = s.search("index", 1)
            if total == 1:
                break
            time.sleep(0.5)
        assert total == 1
    finally:
        w.stop()
