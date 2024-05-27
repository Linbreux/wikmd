import os
import re
import shutil
import uuid

from flask import Flask
from wikmd.config import WikmdConfig


class Plugin:
    def import_head(self):
        return "<script type='text/javascript' src='/static/js/drawio.js'></script>"

    def __init__(self, flask_app: Flask, config: WikmdConfig, web_dep):
        self.name = "DrawIO integration"
        self.plugname = "draw"
        self.flask_app = flask_app
        self.config = config
        self.this_location = os.path.dirname(__file__)
        self.web_dep = web_dep
        self.drawings_folder = None

    def post_setup(self) -> bool:
        """
        configure the drawings folder
        returns True if folder did not exist and created it
        """
        self.drawings_folder = os.path.join(self.config.wiki_directory, self.config.drawings_route)
        if not os.path.exists(self.drawings_folder):
            os.mkdir(self.drawings_folder)

            # allow backward compatibility and move all the contents in the plugins
            # drawing folder to the wiki drawings folder
            for item in os.listdir(os.path.join(self.this_location, "drawings")):
                print(f"copy {item} to {self.drawings_folder}")
                shutil.copy2(os.path.join(self.this_location, "drawings",item), os.path.join(self.drawings_folder, item))
            return True

        return False

    def get_plugin_name(self) -> str:
        """
        returns the name of the plugin
        """
        return self.name

    def process_md(self, md: str) -> str:
        """
        returns the md file after process the input file
        """
        return self.search_for_pattern_and_replace_with_uniqueid(md)

    def process_html(self, html: str) -> str:
        """
        returns the html file after process the input file
        """
        return self.search_in_html_for_draw(html)

    def communicate_plugin(self, request):
        """
        communication from "/plug_com"
        """
        id = request.form['id']
        image = request.form['image']

        self.flask_app.logger.info(f"Plug/{self.name} - changing drawing {id}")

        # look for folder
        location = os.path.join(self.drawings_folder, id)
        if os.path.exists(location):
            file = open(location, "w")
            file.write(image)
            file.close()

        return "ok"

    def look_for_existing_drawid(self, drawid: str) -> str:
        """
        look for a drawId in the wiki/draw folder and return the file as a string
        """
        try:
            file = open(os.path.join(self.drawings_folder, drawid), "r")
            return file.read()
        except Exception:
            print("Did not find the file")
            return ""

    def create_draw_file(self, filename: str) -> None:
        """
        Copy the default drawing to a new one with this filename
        """
        path_to_file = os.path.join(self.drawings_folder, filename)
        shutil.copyfile(os.path.join(self.this_location, "default_draw"), path_to_file)
        s = open(path_to_file,"r")
        result = re.sub("id=\"\"","id=\"" + filename + "\"",s.read())
        s.close()
        s = open(path_to_file,"w")
        s.write(result)
        s.close()


    def search_for_pattern_and_replace_with_uniqueid(self, file: str) -> str:
        """
        search for [[draw]] and replace with draw_<uniqueid>
        """
        filename = "draw_" + str(uuid.uuid4())
        result = re.sub(r"^\[\[draw\]\]", "[[" + filename + "]]", file, flags=re.MULTILINE)
        print(file)
        self.create_draw_file(filename)
        return result

    def search_in_html_for_draw(self,file: str) -> str:
        """
        search for [[draw_<unique_id>]] in "file" and replace it with the content of a corresponding drawfile
        """
        draws = re.findall(r"\[\[(draw_.*)\]\]", file)
        result = file
        for draw in draws:
            result = re.sub(r"\[\["+draw+r"\]\]", self.look_for_existing_drawid(draw), result)
        return result


