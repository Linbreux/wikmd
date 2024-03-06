import os
import re

from flask import Flask
from wikmd.config import WikmdConfig


class Plugin:
    def __init__(self, flask_app: Flask, config: WikmdConfig, web_dep ):
        self.name = "Alerts system"
        self.plugname = "alerts"
        self.flask_app = flask_app
        self.config = config
        self.this_location = os.path.dirname(__file__)
        self.web_dep = web_dep

    def get_plugin_name(self) -> str:
        """
        returns the name of the plugin
        """
        return self.name

    def process_before_cache_html(self, html: str) -> str:
        """
        returns the html file after process the input file
        """
        return self.search_in_html_for_informational(html)


    def search_in_html_for_informational(self,file: str) -> str:
        """
        search for [[informational]](text to show) in "file" and replace it with the content of a corresponding drawfile
        """

        warning_icon = "<i class=\"bi-exclamation-triangle-fill mr-2\"></i>"
        info_icon = "<i class=\"bi-info-circle-fill mr-2\"></i>"
        danger_icon = "<i class=\"bi-exclamation-octagon-fill mr-2\"></i>"
        success_icon = "<i class=\"bi-check-circle-fill mr-2\"></i>"


        result = file
        result = re.sub(r"(?i)(\<p)()(\>)\[\[warning\]\](.*)\<\/p\>", r"<div class='alert alert-warning d-flex'\3"+warning_icon+r" <a>\4</a></div>", result)
        result = re.sub(r"(?i)(\<p)()(\>)\[\[info\]\](.*)\<\/p\>", r"<div class='alert alert-info d-flex'\3"+info_icon+r" <a>\4</a></div>", result)
        result = re.sub(r"(?i)(\<p)()(\>)\[\[danger\]\](.*)\<\/p\>", r"<div class='alert alert-danger d-flex'\3"+danger_icon+r" <a>\4</a></div>", result)
        result = re.sub(r"(?i)(\<p)()(\>)\[\[success\]\](.*)\<\/p\>", r"<div class='alert alert-success d-flex'\3"+success_icon+r" <a>\4</a></div>", result)

        return result


