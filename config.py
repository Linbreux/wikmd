import os
import yaml

WIKMD_CONFIG_FILE = "wikmd-config.yaml"

# Default config parameters
WIKMD_HOST_DEFAULT = "0.0.0.0"
WIKMD_PORT_DEFAULT = 5000
WIKMD_LOGGING_DEFAULT = 1
WIKMD_LOGGING_FILE_DEFAULT = "wikmd.log"

SYNC_WITH_REMOTE_DEFAULT = 0
REMOTE_URL_DEFAULT = ""
WIKI_DIRECTORY_DEFAULT = "wiki"
IMAGES_ROUTE_DEFAULT = "img"

HOMEPAGE_DEFAULT = "homepage.md"
HOMEPAGE_TITLE_DEFAULT = "homepage"


class WikmdConfig:
    """
    Class that stores the configuration of wikmd.
    """
    def __init__(self):
        """
        Function that gets the configuration parameters from .yaml file, os environment variables or default values.
        The .yaml file takes precedence.
        """
        # .yaml config file
        with open(WIKMD_CONFIG_FILE) as f:
            yaml_config = yaml.safe_load(f)

        # Load config parameters from yaml, env vars or default values (the firsts take precedence)
        self.wikmd_host = yaml_config["wikmd_host"] or os.getenv("WIKMD_HOST") or WIKMD_HOST_DEFAULT
        self.wikmd_port = yaml_config["wikmd_port"] or os.getenv("WIKMD_PORT") or WIKMD_PORT_DEFAULT
        self.wikmd_logging = yaml_config["wikmd_logging"] or os.getenv("WIKMD_LOGGING") or WIKMD_LOGGING_DEFAULT
        self.wikmd_logging_file = yaml_config["wikmd_logging_file"] or os.getenv("WIKMD_LOGGING_FILE") or WIKMD_LOGGING_FILE_DEFAULT

        self.sync_with_remote = yaml_config["sync_with_remote"] or os.getenv("SYNC_WITH_REMOTE") or SYNC_WITH_REMOTE_DEFAULT
        self.remote_url = yaml_config["remote_url"] or os.getenv("REMOTE_URL") or REMOTE_URL_DEFAULT
        self.wiki_directory = yaml_config["wiki_directory"] or os.getenv("WIKI_DIRECTORY") or WIKI_DIRECTORY_DEFAULT
        self.images_route = yaml_config["images_route"] or os.getenv("IMAGES_ROUTE") or IMAGES_ROUTE_DEFAULT

        self.homepage = yaml_config["homepage"] or os.getenv("HOMEPAGE") or HOMEPAGE_DEFAULT
        self.homepage_title = yaml_config["homepage_title"] or os.getenv("HOMEPAGE_TITLE") or HOMEPAGE_TITLE_DEFAULT
