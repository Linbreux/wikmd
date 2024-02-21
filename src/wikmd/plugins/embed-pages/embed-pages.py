import os
import re

from flask import Flask
from wikmd.config import WikmdConfig


class Plugin:
    def __init__(self, flask_app: Flask, config: WikmdConfig, web_dep):
        self.name = "embed-pages"
        self.plugname = "embed-pages"
        self.flask_app = flask_app
        self.config = config
        self.this_location = os.path.dirname(__file__)
        self.web_dep = web_dep

    def get_plugin_name(self) -> str:
        """
        returns the name of the plugin
        """
        return self.name

    def process_md(self, md: str) -> str:
        """
        returns the md file after process the input file
        """
        return md

    def process_html(self, html: str) -> str:
        """
        returns the html file after process the input file
        """
        return self.search_for_page_implementation(html)

    def request_html(self, get_html_callback):
        self.get_html = get_html_callback

    def search_for_page_implementation(self, file: str) -> str:
        """
        search for [[ page: test/testpage ]] in "file" and replace it with the content of a linked page
        """
        pages = re.findall(r"\<p\>\[\[\s*page:\s*(.*?)\s*\]\]\<\/p\>", file)
        result = file
        for page in pages:
            # get the html of the page
            try:
                raw_page_html, _ = self.get_html(page)
            except:
                return file

            integrate_html = f"<div id=\"{page}\" class=\"html-integration\"><p><i>{page}</i></p>{raw_page_html}</div>"

            # integrate the page into this one.
            result = re.sub(r"\<p\>\[\[\s*page:\s*"+page+r"\s*\]\]\<\/p\>", integrate_html, result)

        return result

