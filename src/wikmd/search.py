import os
import time
from collections import namedtuple
from multiprocessing import Process
from pathlib import Path
from typing import List, NamedTuple, Tuple

from bs4 import BeautifulSoup
from markdown import Markdown
from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer
from whoosh import index, query
from whoosh.fields import ID, TEXT, SchemaClass
from whoosh.highlight import SentenceFragmenter
from whoosh.qparser import MultifieldParser
from whoosh.writing import AsyncWriter


class SearchSchema(SchemaClass):
    path: ID = ID(stored=True, unique=True)
    filename: ID = ID(stored=True)
    title: TEXT = TEXT(stored=True)
    content: TEXT = TEXT(stored=True)


SearchResult = namedtuple("Result", "path filename title score highlights")


class Search:
    _index: index
    _schema: SearchSchema

    def __init__(self, index_path: str, create: bool = False):
        self._schema = SearchSchema()
        if create:
            if not os.path.exists(index_path):
                os.makedirs(index_path)
            self._index = index.create_in(index_path, self._schema)
        else:
            self._index = index.open_dir(index_path)

    def textify(self, text: str) -> str:
        md = Markdown(extensions=["meta", "extra"])
        html = md.convert(text)
        soup = BeautifulSoup(html, "html.parser")
        return soup.get_text()

    def search(
        self, term: str, page: int
    ) -> Tuple[List[NamedTuple], int, int, List[str]]:
        query = MultifieldParser(["title", "content"], schema=self._schema).parse(term)
        frag = SentenceFragmenter(maxchars=2000)
        with self._index.searcher() as searcher:
            res = searcher.search_page(query, page)
            res.fragmenter = frag
            results = [
                SearchResult(
                    r.get("path"),
                    r.get("filename"),
                    r.get("title"),
                    r.score,
                    r.highlights("content"),
                )
                for r in res
            ]
            corrector = searcher.corrector("content")
            suggestions = corrector.suggest(term)
        return results, res.total, res.pagecount, suggestions

    def index(self, path: str, filename: str, title: str, content: str):
        writer = AsyncWriter(self._index)
        content = self.textify(content)
        writer.add_document(path=path, filename=filename, title=title, content=content)
        writer.commit()

    def delete(self, path: str, filename: str):
        writer = AsyncWriter(self._index)
        q = query.And([query.Term("path", path), query.Term("filename", filename)])
        writer.delete_by_query(q)
        writer.commit()

    def index_all(self, wiki_directory: str, files: List[Tuple[str, str, str]]):
        writer = AsyncWriter(self._index)
        for path, title, relpath in files:
            fpath = os.path.join(wiki_directory, relpath, path)
            with open(fpath, encoding="utf8") as f:
                content = f.read()
            content = self.textify(content)
            writer.add_document(
                path=relpath, filename=path, title=title, content=content
            )
        writer.commit()

    def close(self):
        self._index.close()


class Watchdog(FileSystemEventHandler):
    wiki_directory: str
    search_directory: str
    search: Search
    proc: Process

    def __init__(self, wiki_directory: str, search_directory: str):
        self.wiki_directory = Path(wiki_directory).absolute()
        self.search_directory = search_directory
        self.search = Search(self.search_directory)

    def rel_path(self, path: str):
        base_path = Path(path)
        rel_path = base_path.relative_to(self.wiki_directory)
        if len(rel_path.parts) == 0:
            return "."
        else:
            return str(rel_path)

    def on_created(self, event: FileSystemEvent):
        # Switch to dest_path if it exists because it means move
        file_path = event.src_path
        if hasattr(event, "dest_path"):
            file_path = event.dest_path

        if not os.path.splitext(file_path)[1].lower() == ".md":
            return

        base_path, filename = os.path.split(file_path)
        rel_path = self.rel_path(base_path)
        title, _ = os.path.splitext(filename)
        with open(file_path, encoding="utf8") as f:
            content = f.read()
        self.search.index(rel_path, filename, title, content)

    def on_deleted(self, event: FileSystemEvent):
        if not os.path.splitext(event.src_path)[1].lower() == ".md":
            return

        base_path, filename = os.path.split(event.src_path)
        rel_path = self.rel_path(base_path)
        self.search.delete(rel_path, filename)

    def on_moved(self, event: FileSystemEvent):
        self.on_deleted(event)
        self.on_created(event)

    def on_modified(self, event: FileSystemEvent):
        self.on_deleted(event)
        self.on_created(event)

    def watchdog(self):
        observer = Observer()
        observer.schedule(self, self.wiki_directory, recursive=True)
        observer.start()
        try:
            while observer.is_alive():
                observer.join(1)
                time.sleep(1)
        finally:
            observer.stop()
            observer.join()

    def start(self):
        try:
            self.proc = Process(target=self.watchdog)
            self.proc.daemon = True
            self.proc.start()
        except KeyboardInterrupt:
            self.proc.terminate()

    def stop(self):
        if self.proc.is_alive():
            self.proc.terminate()
