import os
import re
import string

from zlib import compress
from base64 import b64encode
from flask import Flask
from wikmd.config import WikmdConfig


class Plugin:

    def __init__(self, flask_app: Flask, config: WikmdConfig, web_dep):
        self.name = "plantuml"
        self.plugname = "plantuml"
        self.flask_app = flask_app
        self.config = config
        self.this_location = os.path.dirname(__file__)
        self.web_dep = web_dep

        plantuml_alphabet = string.digits + string.ascii_uppercase + string.ascii_lowercase + '-_'
        base64_alphabet = string.ascii_uppercase + string.ascii_lowercase + string.digits + '+/'
        self.b64_to_plantuml = bytes.maketrans(base64_alphabet.encode('utf-8'), plantuml_alphabet.encode('utf-8'))

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
        # replace all blocks [[plantuml (compressed_part)]] with img tags
        plantuml_blocks = re.findall(r"(\[\[plantuml(.*?)]])", html, re.DOTALL)
        for plantuml_block in plantuml_blocks:
            full_block, compressed_part = plantuml_block
            html = html.replace(full_block, self.get_img_tag(self.remove_redundant_symbols(compressed_part)))
        return html

    def process_md_before_html_convert(self, md: str) -> str:
        """
        returns the md file after before html convertation
        """
        plantuml_code_blocks = re.findall(r"(```plantuml(.*?)```)", md, re.DOTALL)
        for code_block in plantuml_code_blocks:
            full_block, code = code_block
            compressed_code = self.encode_plantuml(code)
            md = md.replace(full_block, "[[plantuml " + compressed_code + "]]")
        return md

    def request_html(self, get_html_callback):
        self.get_html = get_html_callback

    def get_img_tag(self, encoded_plantuml: str)  -> str:
        """
        returns the img tag for the given encoded plantuml
        """
        return f'<br><img src="{self.config.plantuml_server_url}/png/{encoded_plantuml}"><br>'

    def encode_plantuml(self, plantuml_text: str) -> str:
        """
        Compresses the plantuml code and encodes it in base64.
        """
        compressed_string = compress(plantuml_text.encode('utf-8'))[2:-4]
        return b64encode(compressed_string).translate(self.b64_to_plantuml).decode('utf-8')

    def remove_redundant_symbols(self, s: str) -> str:
        return s.replace("\n", "").replace("\r", "").replace(" ", "")
