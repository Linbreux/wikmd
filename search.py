import os
from collections import namedtuple
from typing import List, NamedTuple, Tuple

from whoosh import index
from whoosh.fields import SchemaClass, DATETIME, TEXT, ID
from whoosh.highlight import SentenceFragmenter
from whoosh.qparser import QueryParser


class SearchSchema(SchemaClass):
    path: ID = ID(stored=True, unique=True)
    title: TEXT = TEXT(stored=True)
    content: TEXT = TEXT(stored=True)


SearchResult = namedtuple("Result", "path title score highlights")


class Search:
    _index: index
    _schema: SearchSchema
    newly_created: bool = False

    def __init__(self, index_path: str):
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
        frag = SentenceFragmenter(maxchars=500)
        with self._index.searcher() as searcher:
            results = [
                SearchResult(
                    r.get("path"),
                    r.get("title"),
                    r.score,
                    r.highlights("content"),
                )
                for r in searcher.search(query)
            ]
        return results

    def index(self, path: str, title: str, content: str):
        writer = self._index.writer()
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
            writer.add_document(path=path, title=title, content=content)
        writer.commit()
