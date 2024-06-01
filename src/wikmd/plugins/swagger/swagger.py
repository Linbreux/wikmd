import os
import re

from flask import Flask
from wikmd.config import WikmdConfig


class Plugin:
    def import_head(self):
        return '<link rel="stylesheet" href="' + self.web_dep['swagger-ui.css'] + '" />'

    def __init__(self, flask_app: Flask, config: WikmdConfig, web_dep):
        self.name = "swagger"
        self.plugname = "swagger"
        self.flask_app = flask_app
        self.config = config
        self.this_location = os.path.dirname(__file__)
        self.web_dep = web_dep
        self.injected_html = f"""
            <div id='{{id}}', style=\"--bg-codeblock-light: rgba(0, 0, 0, 0);\"></div>
            <script src=\"{self.web_dep['swagger-ui-bundle.js']}\" crossorigin></script>
            <script>
            window.onload = () => {{
                window.ui = SwaggerUIBundle({{
                url: '{{url}}',
                dom_id: '#{{id}}',
                }});
            }};
            </script>
        """

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
        return self.insert_swagger_divs(html)

    def request_html(self, get_html_callback):
        self.get_html = get_html_callback

    def insert_swagger_divs(self, file: str) -> str:
        """
        inserts the swagger divs into the html file
        """
        annotations = re.findall(r"(\[\[" + self.name + r".*?]])", file, re.DOTALL)
        result = file
        for i, annotation in enumerate(annotations):
            link_start = annotation.find("http")
            if link_start != -1:
                link = annotation[link_start:-2]
                result = re.sub(re.escape(annotation), self.prepare_html_string(link, i), result, count=1)
        return result

    def prepare_html_string(self, link: str, id: int) -> str:
        """
        returns the html string with id and url
        """
        return self.injected_html.replace("{id}", "swagger-ui-div-" + str(id)).replace("{url}", link)

