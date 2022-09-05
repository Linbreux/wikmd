import os
import time
from collections import namedtuple
from multiprocessing import Process
from typing import List, NamedTuple, Tuple, Union

from bs4 import BeautifulSoup
from markdown import Markdown
from watchdog.events import (
    FileSystemEventHandler,
    FileCreatedEvent,
    FileDeletedEvent,
    FileModifiedEvent,
)
from watchdog.observers import Observer
from whoosh import index
from whoosh.fields import SchemaClass, DATETIME, TEXT, ID
from whoosh.highlight import SentenceFragmenter
from whoosh.qparser import MultifieldParser


class SearchSchema(SchemaClass):
    path: ID = ID(stored=True, unique=True)
    title: TEXT = TEXT(stored=True)
    content: TEXT = TEXT(stored=True)


SearchResult = namedtuple("Result", "path title score highlights")


class Search:
    _index: index
    _schema: SearchSchema

    def __init__(self, index_path: str, create: bool = False):
        self._schema = SearchSchema()
        if create:
            if not os.path.exists(index_path):
                os.mkdir(index_path)
            self._index = index.create_in(index_path, self._schema)
        else:
            self._index = index.open_dir(index_path)

    def textify(self, text: str) -> str:
        md = Markdown(extensions=["meta", "extra"])
        html = md.convert(text)
        soup = BeautifulSoup(html, "html.parser")
        return soup.get_text()

    def search(self, term: str) -> Tuple[List[NamedTuple], List[str]]:
        query = MultifieldParser(["title", "content"], schema=self._schema).parse(term)
        frag = SentenceFragmenter(maxchars=2000)
        with self._index.searcher() as searcher:
            res = searcher.search(query)
            res.fragmenter = frag
            results = [
                SearchResult(
                    r.get("path"),
                    r.get("title"),
                    r.score,
                    r.highlights("content"),
                )
                for r in res
            ]
            corrector = searcher.corrector("content")
            suggestions = corrector.suggest(term)
        return results, suggestions

    def index(self, path: str, title: str, content: str):
        writer = self._index.writer()
        content = self.textify(content)
        writer.add_document(path=path, title=title, content=content)
        writer.commit()

    def delete(self, path: str):
        writer = self._index.writer()
        writer.delete_by_term("path", path)
        writer.commit()

    def index_all(self, wiki_directory: str, files: List[Tuple[str, str]]):
        writer = self._index.writer()
        for path, title in files:
            fpath = os.path.join(wiki_directory, path)
            with open(fpath) as f:
                content = f.read()
            content = self.textify(content)
            writer.add_document(path=path, title=title, content=content)
        writer.commit()

    def close(self):
        self._index.close()


def watchdog(base_dir: str, search_path: str):
    class WatchdogHandler(FileSystemEventHandler):
        def __init__(self):
            self.base_dir = base_dir
            self.search = Search(search_path)
            super().__init__()

        def on_created(self, event: Union[FileCreatedEvent, FileDeletedEvent]):
            if os.path.splitext(event.src_path)[1].lower() == ".md":
                filename = event.src_path.replace(f"{base_dir}/", "")
                title, _ = os.path.splitext(filename)
                with open(event.src_path) as f:
                    content = f.read()
                self.search.index(filename, title, content)

        def on_deleted(self, event: Union[FileCreatedEvent, FileDeletedEvent]):
            if os.path.splitext(event.src_path)[1].lower() == ".md":
                filename = event.src_path.replace(f"{base_dir}/", "")
                self.search.delete(filename)

        def on_modified(self, event: FileModifiedEvent):
            self.on_deleted(event)
            self.on_created(event)

    def _watchdog():
        event_handler = WatchdogHandler()
        observer = Observer()
        observer.schedule(event_handler, base_dir, recursive=True)
        observer.start()
        try:
            while observer.is_alive():
                observer.join(1)
                time.sleep(1)
        finally:
            observer.stop()
            observer.join()

    try:
        p = Process(target=_watchdog)
        p.daemon = True
        p.start()
    except KeyboardInterrupt:
        p.terminate()
