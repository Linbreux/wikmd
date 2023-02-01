import yaml
import os


class Sidebar():
    def __init__(self):
        self.html = ""
        self.SIDEBAR_FILE = "default_sidebar.yaml"

    def recursive(self, yaml_object):
        for item in yaml_object:
            self.html += "<li class=\"nav-item with-indicator\">\n"
            self.html += """<a class="nav-link text-light d-none d-md-block\""""
            if "sub" in item:
                self.html += """
                data-bs-toggle="collapse" 
                href="#"""+ item["item"] + """\" role="button" aria-expanded="false"
                aria-controls=\"""" + item["item"] + "\""
            elif "link" in item:
                self.html += "href=\"" + item["link"] + "\""

            self.html += ">"
            self.html += item["item"] + "</a>"
            if "sub" in item:
                self.html += """<ul class="collapse" id=\"""" + item["item"] +"""\">\n"""
                self.recursive(item["sub"])
                self.html += "</ul>\n"
            self.html += "</li>\n"

    def read_sidebar_yaml(self):
        __location__ = os.path.realpath(
        os.path.join(os.getcwd(), os.path.dirname(__file__)))
        try:
            # .yaml config file
            with open(os.path.join(__location__,self.SIDEBAR_FILE)) as f:
                yaml_sidebar = yaml.safe_load(f)

            self.html += "<ul class=\"nav flex-column\">\n"
            self.recursive(yaml_sidebar["menu"])
            self.html += "</ul>\n"

            return self.html
        except:
            print("there was an error")
