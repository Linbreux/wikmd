import os
import yaml

WIKMD_CONFIG_FILE = "../config.yaml"

def config_list(yaml_config, config_item_name):
    """
    Function that gets a config item of type list.
    Priority is in the following order either from environment variables or yaml file or default value.
    """
    default_value = ["image/gif", "image/jpeg", "image/png", "image/svg+xml", "image/webp"]
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
        self.wikmd_host = yaml_config.get("wikmd_host")
        self.wikmd_port =  yaml_config.get("wikmd_port")
        self.wikmd_logging = yaml_config.get("wikmd_logging")
        self.wikmd_logging_file = yaml_config.get("wikmd_logging_file")

        self.git_user = yaml_config.get("git_user")
        self.git_email = yaml_config.get("git_email")

        self.main_branch_name = yaml_config.get("main_branch_name")
        self.sync_with_remote = yaml_config.get("sync_with_remote")
        self.remote_url = yaml_config.get("remote_url")

        self.wiki_directory = yaml_config.get("wiki_directory")
        self.homepage = yaml_config.get("homepage")
        self.homepage_title = yaml_config.get("homepage_title")
        self.images_route = yaml_config.get("images_route")

        self.hide_folder_in_wiki = yaml_config.get("hide_folder_in_wiki")

        self.plugins = yaml_config.get("plugins")

        self.protect_edit_by_password = yaml_config.get("protect_edit_by_password")
        self.password_in_sha_256 = yaml_config.get("password_in_sha_256")

        self.local_mode = yaml_config.get("local_mode")

        self.image_allowed_mime = config_list(yaml_config, "image_allowed_mime")
        self.optimize_images = yaml_config.get("optimize_images", )

        self.cache_dir = yaml_config.get("cache_dir")
        self.search_dir = yaml_config.get("search_dir")

        self.secret_key = yaml_config.get("secret_key")
