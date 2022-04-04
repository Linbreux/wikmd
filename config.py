import os
import yaml

WIKMD_CONFIG_FILE = "wikmd-config.yaml"

# Default config parameters
WIKMD_HOST_DEFAULT = "0.0.0.0"
WIKMD_PORT_DEFAULT = 5000
WIKMD_LOGGING_DEFAULT = 1
WIKMD_LOGGING_FILE_DEFAULT = "wikmd.log"

GIT_EMAIL_DEFAULT = "wikmd@no-mail.com"
GIT_USER_DEFAULT = "wikmd"

MAIN_BRANCH_NAME_DEFAULT = "main"
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
        Each configuration parameter is stored into a class attribute.
        Env. vars take precedence.
        """
        # .yaml config file
        with open(WIKMD_CONFIG_FILE) as f:
            yaml_config = yaml.safe_load(f)

        # Load config parameters from env. vars, yaml or default values (the firsts take precedence)
        self.wikmd_host = os.getenv("WIKMD_HOST") or yaml_config["wikmd_host"] or WIKMD_HOST_DEFAULT
        self.wikmd_port = os.getenv("WIKMD_PORT") or yaml_config["wikmd_port"] or WIKMD_PORT_DEFAULT
        self.wikmd_logging = os.getenv("WIKMD_LOGGING") or yaml_config["wikmd_logging"] or WIKMD_LOGGING_DEFAULT
        self.wikmd_logging_file = os.getenv("WIKMD_LOGGING_FILE") or yaml_config["wikmd_logging_file"] or WIKMD_LOGGING_FILE_DEFAULT

        self.git_user = os.getenv("GIT_USER") or yaml_config["git_user"] or GIT_USER_DEFAULT
        self.git_email = os.getenv("GIT_EMAIL") or yaml_config["git_email"] or GIT_EMAIL_DEFAULT

        self.main_branch_name = os.getenv("MAIN_BRANCH_NAME") or yaml_config["main_branch_name"] or MAIN_BRANCH_NAME_DEFAULT
        self.sync_with_remote = os.getenv("SYNC_WITH_REMOTE") or yaml_config["sync_with_remote"] or SYNC_WITH_REMOTE_DEFAULT
        self.remote_url = os.getenv("REMOTE_URL") or yaml_config["remote_url"] or REMOTE_URL_DEFAULT

        self.wiki_directory = os.getenv("WIKI_DIRECTORY") or yaml_config["wiki_directory"] or WIKI_DIRECTORY_DEFAULT
        self.images_route = os.getenv("IMAGES_ROUTE") or yaml_config["images_route"] or IMAGES_ROUTE_DEFAULT
        self.homepage = os.getenv("HOMEPAGE") or yaml_config["homepage"] or HOMEPAGE_DEFAULT
        self.homepage_title = os.getenv("HOMEPAGE_TITLE") or yaml_config["homepage_title"] or HOMEPAGE_TITLE_DEFAULT
