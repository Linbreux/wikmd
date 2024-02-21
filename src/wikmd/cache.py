import os
from shutil import rmtree
from typing import Optional

import cachelib


class Cache:
    cache: cachelib.FileSystemCache

    def __init__(self, path: str):
        if os.path.exists(path):
            rmtree(path)  # delete an existing cache on start/restart
        os.makedirs(path)
        self.cache = cachelib.FileSystemCache(path)

    def get(self, key: str) -> Optional[str]:
        if self.cache.has(key):
            if os.path.getmtime(key) > os.path.getmtime(self.cache._get_filename(key)):
                self.cache.delete(key)
                return None
            return self.cache.get(key)
        return None

    def set(self, key: str, content: str):
        self.cache.set(key, content, timeout=0)
