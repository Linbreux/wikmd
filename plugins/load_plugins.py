import importlib

class PluginLoader():
    def __init__(self, plugins:list=[]):
        # Checking if plugin were sent
        if plugins != []:
            # create a list of plugins
            self._plugins = [
                importlib.import_module(plugin,".").Plugin() for plugin in plugins
            ]
        else:
            self._plugins = []

        for plugin in self._plugins:
            print(plugin.get_plugin_name())

    def get_plugins(self):
        
        return self._plugins