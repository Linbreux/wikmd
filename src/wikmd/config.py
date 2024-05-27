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
HOMEPAGE_DEFAULT = "homepage.md"
HOMEPAGE_TITLE_DEFAULT = "homepage"
IMAGES_ROUTE_DEFAULT = "img"
DRAWINGS_ROUTE_DEFAULT = ".drawings"

HIDE_FOLDER_IN_WIKI = []

PLUGINS = []

PROTECT_EDIT_BY_PASSWORD = 0
PASSWORD_IN_SHA_256 = "0E9C700FAB2D5B03B0581D080E74A2D7428758FC82BD423824C6C11D6A7F155E" #pw: wikmd

# if False: Uses external CDNs to serve some files
LOCAL_MODE = False

IMAGE_ALLOWED_MIME_DEFAULT = ["image/gif", "image/jpeg", "image/png", "image/svg+xml", "image/webp"]
# you need to have cwebp installed for optimization to work
OPTIMIZE_IMAGES_DEFAULT = "no"

CACHE_DIR = "/dev/shm/wikmd/cache"
SEARCH_DIR = "/dev/shm/wikmd/searchindex"

SECRET_KEY = '\xfd{H\xe5<\x95\xf9\xe3\x96.5\xd1\x01O<!\xd5\xa2\xa0\x9fR"\xa1\xa8'

def config_list(yaml_config, config_item_name, default_value):
    """
    Function that gets a config item of type list.
    Priority is in the following order either from environment variables or yaml file or default value.
    """
    if os.getenv(config_item_name.upper()):
        # Env Var in the form `EXAMPLE="a, b, c, d"` or `EXAMPLE="a,b,c,d"`
        return [ext.strip() for ext in os.getenv(config_item_name.upper()).split(",")]
    elif yaml_config[config_item_name.lower()]:
        return yaml_config[config_item_name.lower()]
    else:
        return default_value


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
        __location__ = os.path.realpath(
            os.path.join(os.getcwd(), os.path.dirname(__file__)))

        # .yaml config file
        with open(os.path.join(__location__, WIKMD_CONFIG_FILE)) as f:
            yaml_config = yaml.safe_load(f)

        # Load config parameters from env. vars, yaml or default values (the firsts take precedence)
        self.wikmd_host = os.getenv("WIKMD_HOST") or yaml_config.get("wikmd_host", WIKMD_HOST_DEFAULT)
        self.wikmd_port = os.getenv("WIKMD_PORT") or yaml_config.get("wikmd_port", WIKMD_PORT_DEFAULT)
        self.wikmd_logging = os.getenv("WIKMD_LOGGING") or yaml_config.get("wikmd_logging", WIKMD_LOGGING_DEFAULT)
        self.wikmd_logging_file = os.getenv("WIKMD_LOGGING_FILE") or yaml_config.get("wikmd_logging_file", WIKMD_LOGGING_FILE_DEFAULT)

        self.git_user = os.getenv("GIT_USER") or yaml_config.get("git_user", GIT_USER_DEFAULT)
        self.git_email = os.getenv("GIT_EMAIL") or yaml_config.get("git_emai", GIT_EMAIL_DEFAULT)

        self.main_branch_name = os.getenv("MAIN_BRANCH_NAME") or yaml_config.get("main_branch_name", MAIN_BRANCH_NAME_DEFAULT)
        self.sync_with_remote = os.getenv("SYNC_WITH_REMOTE") or yaml_config.get("sync_with_remote", SYNC_WITH_REMOTE_DEFAULT)
        self.remote_url = os.getenv("REMOTE_URL") or yaml_config.get("remote_url", REMOTE_URL_DEFAULT)

        self.wiki_directory = os.getenv("WIKI_DIRECTORY") or yaml_config.get("wiki_directory", WIKI_DIRECTORY_DEFAULT)
        self.homepage = os.getenv("HOMEPAGE") or yaml_config.get("homepage", HOMEPAGE_DEFAULT)
        self.homepage_title = os.getenv("HOMEPAGE_TITLE") or yaml_config.get("homepage_title", HOMEPAGE_TITLE_DEFAULT)
        self.images_route = os.getenv("IMAGES_ROUTE") or yaml_config.get("images_route", IMAGES_ROUTE_DEFAULT)
        self.drawings_route = DRAWINGS_ROUTE_DEFAULT

        self.hide_folder_in_wiki = os.getenv("HIDE_FOLDER_IN_WIKI") or yaml_config.get("hide_folder_in_wiki", HIDE_FOLDER_IN_WIKI)

        self.plugins = os.getenv("WIKI_PLUGINS") or yaml_config.get("plugins", PLUGINS)

        self.protect_edit_by_password = os.getenv("PROTECT_EDIT_BY_PASSWORD") or yaml_config.get("protect_edit_by_password", PROTECT_EDIT_BY_PASSWORD)
        self.password_in_sha_256 = os.getenv("PASSWORD_IN_SHA_256") or yaml_config.get("password_in_sha_256", PASSWORD_IN_SHA_256)

        self.local_mode = (os.getenv("LOCAL_MODE") in ["True", "true", "Yes", "yes"]) or yaml_config.get("local_mode", LOCAL_MODE)

        self.image_allowed_mime = config_list(yaml_config, "IMAGE_ALLOWED_MIME", IMAGE_ALLOWED_MIME_DEFAULT)
        self.optimize_images = os.getenv("OPTIMIZE_IMAGES") or yaml_config.get("optimize_images", OPTIMIZE_IMAGES_DEFAULT)

        self.cache_dir = os.getenv("CACHE_DIR") or yaml_config.get("cache_dir", CACHE_DIR)
        self.search_dir = os.getenv("SEARCH_DIR") or yaml_config.get("search_dir", SEARCH_DIR)

        self.secret_key = os.getenv("SECRET_KEY") or yaml_config.get("secret_key", SECRET_KEY)
