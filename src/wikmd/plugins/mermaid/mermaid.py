import os
from flask import Flask
from wikmd.config import WikmdConfig

injected_script = """
    <script>
        mermaid.initialize({startOnLoad:true});
        document.querySelectorAll('pre.mermaid, pre>code.language-mermaid').forEach($el => {
        if ($el.tagName === 'CODE')
            $el = $el.parentElement
        $el.outerHTML = `
            <div class="mermaid">${$el.textContent}</div>
        `
        })
    </script>
    """

class Plugin:
    def import_head(self):
        return "<script src='" + self.web_dep["mermaid.min.js"] + "'></script>"
    
    def add_script(self):
        return injected_script

    def __init__(self, flask_app: Flask, config: WikmdConfig, web_dep ):
        self.name = "Mermaid integration"
        self.plugname = "mermaid"
        self.flask_app = flask_app
        self.config = config
        self.this_location = os.path.dirname(__file__)
        self.web_dep = web_dep
        
    def get_plugin_name(self) -> str:
        """
        returns the name of the plugin
        """
        return self.name
