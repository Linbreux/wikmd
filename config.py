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
IMAGES_FILE_UID = os.getuid()
IMAGES_FILE_GID = os.getgid()
IMAGES_FILE_MODE = '600'
IMAGES_CLEANUP = False

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
        with open(os.path.join(__location__,WIKMD_CONFIG_FILE)) as f:
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
        self.homepage = os.getenv("HOMEPAGE") or yaml_config["homepage"] or HOMEPAGE_DEFAULT
        self.homepage_title = os.getenv("HOMEPAGE_TITLE") or yaml_config["homepage_title"] or HOMEPAGE_TITLE_DEFAULT
        self.images_route = os.getenv("IMAGES_ROUTE") or yaml_config["images_route"] or IMAGES_ROUTE_DEFAULT
        self.images_file_uid = os.getenv("IMAGES_FILE_UID") or yaml_config["images_file_uid"] or IMAGES_FILE_UID
        self.images_file_gid = os.getenv("IMAGES_FILE_GID") or yaml_config["images_file_gid"] or IMAGES_FILE_GID
        self.images_file_mode = os.getenv("IMAGES_FILE_MODE") or yaml_config["images_file_mode"] or IMAGES_FILE_MODE
        self.images_cleanup = os.getenv("IMAGES_CLEANUP") or yaml_config["images_cleanup"] or IMAGES_CLEANUP

        self.hide_folder_in_wiki = os.getenv("hide_folder_in_wiki")or yaml_config["hide_folder_in_wiki"] or HIDE_FOLDER_IN_WIKI

        self.plugins = os.getenv("WIKI_PLUGINS")or yaml_config["plugins"] or PLUGINS

        self.protect_edit_by_password = os.getenv("PROTECT_EDIT_BY_PASSWORD") or yaml_config["protect_edit_by_password"] or PROTECT_EDIT_BY_PASSWORD
        self.password_in_sha_256 = os.getenv("PASSWORD_IN_SHA_256") or yaml_config["password_in_sha_256"] or PASSWORD_IN_SHA_256

        self.local_mode = (os.getenv("LOCAL_MODE") in ["True", "true", "Yes", "yes"]) or yaml_config["local_mode"] or LOCAL_MODE

        self.image_allowed_mime = config_list(yaml_config, "IMAGE_ALLOWED_MIME", IMAGE_ALLOWED_MIME_DEFAULT)
        self.optimize_images = os.getenv("OPTIMIZE_IMAGES") or yaml_config["optimize_images"] or OPTIMIZE_IMAGES_DEFAULT

        self.cache_dir = os.getenv("CACHE_DIR") or yaml_config["cache_dir"] or CACHE_DIR
        self.search_dir = os.getenv("SEARCH_DIR") or yaml_config["search_dir"] or SEARCH_DIR
