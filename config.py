import os
import yaml

WIKMD_CONFIG_FILE = "wikmd-config.yaml"

# Default config parameters
WIKMD_HOST_DEFAULT = "0.0.0.0"
WIKMD_PORT_DEFAULT = 5000
WIKMD_LOGGING_DEFAULT = 1
WIKMD_LOGGING_FILE_DEFAULT = "wikmd.log"

SYNC_WITH_REMOTE_DEFAULT = 0
WIKI_DIRECTORY_DEFAULT = "wiki"
IMAGES_ROUTE_DEFAULT = "img"

HOMEPAGE_DEFAULT = "homepage.md"
HOMEPAGE_TITLE_DEFAULT = "homepage"


def get_config() -> dict:
    """
    Function that gets the configuration parameters from .yaml file, os environment variables or default values.
    The .yaml file takes precedence.
    :return: configuration dictionary.
    """
    config = {}

    # .yaml config file
    with open(WIKMD_CONFIG_FILE) as f:
        yaml_config = yaml.safe_load(f)

    # Load config parameters from yaml, env vars or default values (the firsts take precedence)
    config["wikmd_host"] = yaml_config["wikmd_host"] or os.getenv("WIKMD_HOST") or WIKMD_HOST_DEFAULT
    config["wikmd_port"] = yaml_config["wikmd_port"] or os.getenv("WIKMD_PORT") or WIKMD_PORT_DEFAULT
    config["wikmd_logging"] = yaml_config["wikmd_logging"] or os.getenv("WIKMD_LOGGING") or WIKMD_LOGGING_DEFAULT
    config["wikmd_logging_file"] = yaml_config["wikmd_logging_file"] or os.getenv("WIKMD_LOGGING_FILE") or WIKMD_LOGGING_FILE_DEFAULT

    config["sync_with_remote"] = yaml_config["sync_with_remote"] or os.getenv("SYNC_WITH_REMOTE") or SYNC_WITH_REMOTE_DEFAULT
    config["wiki_directory"] = yaml_config["wiki_directory"] or os.getenv("WIKI_DIRECTORY") or WIKI_DIRECTORY_DEFAULT
    config["images_route"] = yaml_config["images_route"] or os.getenv("IMAGES_ROUTE") or IMAGES_ROUTE_DEFAULT

    config["homepage"] = yaml_config["homepage"] or os.getenv("HOMEPAGE") or HOMEPAGE_DEFAULT
    config["homepage_title"] = yaml_config["homepage_title"] or os.getenv("HOMEPAGE_TITLE") or HOMEPAGE_TITLE_DEFAULT

    return config
