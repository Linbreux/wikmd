import os
from collections import namedtuple
from datetime import datetime
from typing import List, NamedTuple, Tuple

from whoosh import index
from whoosh.fields import SchemaClass, DATETIME, TEXT, ID
from whoosh.qparser import QueryParser


class SearchSchema(SchemaClass):
    path: ID = ID(stored=True)
    title: TEXT = TEXT(stored=True)
    content: TEXT = TEXT
    updated: DATETIME = DATETIME


SearchResult = namedtuple("Result", "path title")


class Search:
    _index: index
    _schema: SearchSchema
    newly_created: bool = False

    def __init__(self, index_path: str = "_searchindex"):
        self._schema = SearchSchema()
        if not os.path.exists(index_path):
            os.mkdir(index_path)
            self._index = index.create_in(index_path, self._schema)
            self.newly_created = True
        else:
            self._index = index.open_dir(index_path)

    def search(self, term: str) -> List[NamedTuple]:
        query_parser = QueryParser("content", schema=self._schema)
        query = query_parser.parse(term)
        with self._index.searcher() as searcher:
            results = [
                SearchResult(r.get("path"), r.get("title"))
                for r in searcher.search(query)
            ]
        return results

    def index(self, path: str, title: str, content: str, updated: datetime):
        writer = self._index.writer()
        writer.add_document(path=path, title=title, content=content, updated=updated)
        writer.commit()

    def update(self, path: str, title: str, content: str, updated: datetime):
        writer = self._index.writer()
        writer.update_document(path=path, title=title, content=content)
        writer.commit()

    def delete(self, path: str):
        self._index.delete_by_term("path", path)
        self._index.commit()

    def index_all(self, files: List[Tuple[str, str]]):
        writer = self._index.writer()
        for path, title in files:
            with open(path) as content:
                writer.add_document(
                    path=path, title=title, content=str(content), updated=datetime.now()
                )
        writer.commit()
