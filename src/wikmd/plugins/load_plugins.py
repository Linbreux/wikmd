import importlib

from flask import Flask
from wikmd.config import WikmdConfig


class PluginLoader():
    """
    The plugin loader will load all plugins inside "plugins" folder
    a plugin should have a folder and a file inside the folder,
    both with the name of the plugin
    """
    def __init__(self, flask_app: Flask, config: WikmdConfig, web_deps= None, plugins:list=[], ):
        # Checking if plugin were sent
        if plugins != []:
            # create a list of plugins
            self._plugins = [
                importlib.import_module(f"wikmd.plugins.{plugin}.{plugin}",".").Plugin(flask_app, config, web_deps) for plugin in plugins
            ]
        else:
            self._plugins = []

        for plugin in self._plugins:
            print(plugin.get_plugin_name())

    def get_plugins(self):
        """
        returns a list of plugins
        """
        return self._plugins