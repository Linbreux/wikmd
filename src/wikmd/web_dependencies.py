from collections import namedtuple
from os import path

import requests

WebDependency = namedtuple("WebDependency", ["local", "external"])
WEB_DEPENDENCIES = {
    "bootstrap.min.css": WebDependency(
        local="/static/css/bootstrap.min.css",
        external="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css"
    ),
    "dark.min.css": WebDependency(
        local="/static/css/dark.min.css",
        external="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.3.1/styles/dark.min.css"
    ),
    "default.min.css": WebDependency(
        local="/static/css/default.min.css",
        external="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.3.1/styles/default.min.css"
    ),
    "bootstrap.bundle.min.js": WebDependency(
        local="/static/js/bootstrap.bundle.min.js",
        external="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"
    ),
    "bootstrap-icons.css": WebDependency(
        local="/static/css/bootstrap-icons.css",
        external="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.5.0/font/bootstrap-icons.css"
    ),
    "jquery.slim.min.js": WebDependency(
        local="/static/js/jquery.slim.min.js",
        external="https://cdn.jsdelivr.net/npm/jquery@3.6.0/dist/jquery.slim.min.js"
    ),
    "polyfill.min.js": WebDependency(
        local="/static/js/polyfill.min.js",
        external="https://polyfill.io/v3/polyfill.min.js?features=es6"
    ),
    "tex-mml-chtml.js": WebDependency(
        local="/static/js/tex-mml-chtml.js",
        external="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"
    ),
    "highlight.min.js": WebDependency(
        local="/static/js/highlight.min.js",
        external="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.3.1/highlight.min.js"
    ),
    "codemirror.min.css": WebDependency(
        local="/static/css/codemirror.min.css",
        external="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.52.2/codemirror.min.css"
    ),
    "codemirror.min.js": WebDependency(
        local="/static/js/codemirror.min.js",
        external="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.52.2/codemirror.min.js"
    ),
    "markdown.min.js": WebDependency(
        local="/static/js/markdown.min.js",
        external="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.52.2/mode/markdown/markdown.min.js"
    ),
    "vis-network.min.js": WebDependency(
        local="/static/js/vis-network.min.js",
        external="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"
    ),
    "filepond.js": WebDependency(
        local="/static/js/filepond.js",
        external="https://unpkg.com/filepond/dist/filepond.js"
    ),
    "filepond.css": WebDependency(
        local="/static/css/filepond.css",
        external="https://unpkg.com/filepond/dist/filepond.css"
    ),
    "filepond-plugin-file-validate-type.js": WebDependency(
        local="/static/js/filepond-plugin-file-validate-type.js",
        external="https://unpkg.com/filepond-plugin-file-validate-type@1.2.8/dist/filepond-plugin-file-validate-type.js"
    ),
    "notyf.min.js": WebDependency(
        local="/static/js/notyf.min.js",
        external="https://cdn.jsdelivr.net/npm/notyf@3/notyf.min.js"
    ),
    "notyf.min.css": WebDependency(
        local="/static/css/notyf.min.css",
        external="https://cdn.jsdelivr.net/npm/notyf@3/notyf.min.css"
    ),
    "mermaid.min.js": WebDependency(
        local="/static/js/mermaid.min.js",
        external="https://cdn.jsdelivr.net/npm/mermaid@9.3.0/dist/mermaid.min.js"
    ),
    "quicksand.woff2": WebDependency(
        local="/static/fonts/quicksand.woff2",
        external="https://fonts.gstatic.com/s/quicksand/v31/6xKtdSZaM9iE8KbpRA_hK1QN.woff2"
    ),
    "swagger-ui-bundle.js": WebDependency(
        local="/static/js/swagger-ui-bundle.js",
        external="https://unpkg.com/swagger-ui-dist@4.5.0/swagger-ui-bundle.js"
    ),
    "swagger-ui.css": WebDependency(
        local="/static/css/swagger-ui.css",
        external="https://unpkg.com/swagger-ui-dist@4.5.0/swagger-ui.css"
    )
}


def get_web_deps(local_mode, logger):
    """
    Returns a dict with dependency_name as key and web_path as value.
    If local_mode: a local copy of the dependency gets served
    Else: a public CDNs gets used to serve those dependencies
    """
    if local_mode:
        download_web_deps(logger)
        return {dep: WEB_DEPENDENCIES[dep].local for dep in WEB_DEPENDENCIES}
    else:
        return {dep: WEB_DEPENDENCIES[dep].external for dep in WEB_DEPENDENCIES}


def download_web_deps(logger):
    """
    Downloads the dependencies, if they don't already exist on disk
    """
    for dep_name in WEB_DEPENDENCIES:
        dep = WEB_DEPENDENCIES[dep_name]
        dep_file_path = path.join(path.dirname(__file__), dep.local[1:])  # Drop the first '/' so join works

        # File is not present and has to be downloaded
        if not path.exists(dep_file_path):
            logger.info(f"Downloading dependency {dep.external}")
            result = requests.get(dep.external)
            if not result.ok:
                raise Exception(f"Error while trying to GET {dep.external} Statuscode: {result.status_code}")

            logger.info(f"Writing dependency >>> {dep_file_path}")
            with open(dep_file_path, "wb") as file:
                file.write(result.content)
