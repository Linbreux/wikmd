import uuid
import os
import re
import shutil

class Plugin:
    def __init__(self):
        self.name = "DrawIO integration"

    def get_plugin_name(self):
        return self.name

    def process_markdown(self, md: str) -> str:
        return self.search_for_pattern_and_replace_with_uniqueid(md)

    def process_html(self, html: str) -> str:
        return self.search_in_html_for_draw(html)

    def look_for_existing_drawid(self, drawid: str) -> str:
        """
        look for a drawId in the wiki/draw folder and return the file as a string
        """
        try:
            test = open(os.path.join("wiki/draw",drawid))
            return test.read()
        except Exception:
            print("Did not find the file")
            return ""

    def create_draw_file(self, filename: str) -> None:
        """
        Copy the default drawing to a new one with this filename
        """
        path_to_file = "wiki/draw/"+filename
        shutil.copyfile("wiki/draw/default", path_to_file)
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
        result = re.sub("\[\[draw\]\]", "[[" + filename + "]]", file)
        print(result)
        self.create_draw_file(filename)
        return result

    def search_in_html_for_draw(self,file: str) -> str:
        """
        search for [[draw_<unique_id>]] in "file" and replace it with the content of a corresponding drawfile
        """
        draws = re.findall("\[\[(draw_.*)\]\]", file)
        print(draws)
        result = file
        for draw in draws:
            result = re.sub("\[\["+draw+"\]\]", self.look_for_existing_drawid(draw), result)
        return result


