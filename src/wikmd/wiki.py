from __future__ import annotations

import logging
import os
import secrets
import shutil
import time
import uuid
from hashlib import sha256
from pathlib import Path
from threading import Thread

import pypandoc
from flask import (
    Flask,
    Response,
    flash,
    make_response,
    redirect,
    render_template,
    request,
    send_file,
    send_from_directory,
    url_for,
)
from lxml.html.clean import clean_html
from werkzeug.utils import safe_join

from wikmd import knowledge_graph
from wikmd.cache import Cache
from wikmd.config import WikmdConfig
from wikmd.git_manager import WikiRepoManager
from wikmd.image_manager import ImageManager
from wikmd.plugins.load_plugins import PluginLoader
from wikmd.search import Search, Watchdog
from wikmd.utils import pathify, secure_filename
from wikmd.web_dependencies import get_web_deps

SESSIONS = []

cfg = WikmdConfig()

UPLOAD_FOLDER_PATH = pathify(cfg.wiki_directory, cfg.images_route)
GIT_FOLDER_PATH = pathify(cfg.wiki_directory, ".git")
HIDDEN_FOLDER_PATH_LIST = [pathify(cfg.wiki_directory, hidden_folder)
                           for hidden_folder in cfg.hide_folder_in_wiki]
HOMEPAGE_PATH = pathify(cfg.wiki_directory, cfg.homepage)
HIDDEN_PATHS = (UPLOAD_FOLDER_PATH, GIT_FOLDER_PATH,
                HOMEPAGE_PATH, *HIDDEN_FOLDER_PATH_LIST)

_project_folder = Path(__file__).parent
app = Flask(__name__,
            template_folder=_project_folder / "templates",
            static_folder=_project_folder / "static")

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER_PATH
app.config['SECRET_KEY'] = cfg.secret_key

# console logger
app.logger.setLevel(logging.INFO)

# file logger
logger = logging.getLogger("werkzeug")
logger.setLevel(logging.ERROR)

web_deps = get_web_deps(cfg.local_mode, app.logger)

# plugins
plugins = PluginLoader(
    flask_app=app,
    config=cfg,
    plugins=cfg.plugins,
    web_deps=web_deps).get_plugins()

wrm = WikiRepoManager(flask_app=app)
cache = Cache(cfg.cache_dir)
im = ImageManager(app, cfg)

SYSTEM_SETTINGS = {
    "darktheme": False,
    "listsortMTime": False,
    "web_deps": web_deps,
    "plugins": plugins,
}


def process(content: str, page_name: str) -> str:
    """Process the content with the plugins.

    It also manages CRLF to LF conversion.
    :param content: content
    :param page_name: name of the page
    :return processed content
    """
    # Convert Win line ending (CRLF) to standard Unix (LF)
    processed = content.replace("\r\n", "\n")

    # Process the content with the plugins
    for plugin in plugins:
        if "process_md" in dir(plugin):
            app.logger.info("Plug/%s - process_md >>> %s",
                            plugin.get_plugin_name(), page_name)
            processed = plugin.process_md(processed)

    return processed


def ensure_page_can_be_created(page: str, page_name: str) -> None | str:
    """Check that a path name is valid."""
    filename = safe_join(cfg.wiki_directory, f"{page_name}.md")
    if filename is None:
        flash(f"Page name not accepted. Contains disallowed characters.")
        app.logger.info(f"Page name isn't secure >>> {page_name}.")
    else:
        path_exists = os.path.exists(filename)
        safe_name = "/".join([secure_filename(part) for part in page_name.split("/")])
        filename_is_ok = safe_name == page_name
        if not path_exists and filename_is_ok and page_name:  # Early exist
            return None

        if path_exists:
            flash("A page with that name already exists. The page name needs to be unique.")
            app.logger.info("Page name exists >>> %s.", page_name)

        if not filename_is_ok:
            flash(f"Page name not accepted. Try using '{safe_name}'.")
            app.logger.info("Page name isn't secure >>> %s.", page_name)

        if not page_name:
            flash("Your page needs a name.")
            app.logger.info("No page name provided.")

    content = process(request.form["CT"], page_name)
    return render_template("new.html",
                           content=content, title=page,
                           upload_path=cfg.images_route,
                           image_allowed_mime=cfg.image_allowed_mime,
                           system=SYSTEM_SETTINGS)


def save(page_name: str) -> None:
    """Get file content from the form and save it."""
    content = process(request.form["CT"], page_name)
    app.logger.info("Saving >>> '%s' ...", page_name)

    try:
        filename = Path(safe_join(cfg.wiki_directory, f"{page_name}.md"))
        dirname = filename.parent
        dirname.mkdir(exist_ok=True)

        with filename.open("w", encoding="utf-8") as f:
            f.write(content)
    except Exception as e:
        # TODO: Use Flask Abort?
        app.logger.exception("Error while saving '%s'", page_name)


def search(search_term: str, page: int) -> str:
    """Preform a search for a term and shows the results."""
    app.logger.info("Searching >>> '%s' ...", search_term)
    search = Search(cfg.search_dir)
    page = int(page)
    results, num_results, num_pages, suggestions = search.search(search_term, page)
    return render_template(
        "search.html",
        search_term=search_term,
        num_results=num_results,
        num_pages=num_pages,
        current_page=page,
        suggestions=suggestions,
        results=results,
        system=SYSTEM_SETTINGS,
    )


def fetch_page_name() -> str:
    """Get the name of the page from the form."""
    page_name = request.form["PN"]
    if page_name[-4:] == "{id}":
        page_name = f"{page_name[:-4]}{uuid.uuid4().hex}"
    return page_name


def get_html(file_page: str) -> [str, str]:
    """Get the content of the file."""
    md_file_path = Path(safe_join(cfg.wiki_directory, f"{file_page}.md"))
    mod = "Last modified: %s" % time.ctime(md_file_path.stat().st_mtime)
    folder = file_page.split("/")
    file_page = folder[-1:][0]

    cached_entry = cache.get(md_file_path.as_posix())
    if cached_entry:
        app.logger.info("Showing HTML page from cache >>> '%s'", file_page)

        for plugin in plugins:
            if "process_html" in dir(plugin):
                app.logger.info("Plug/%s - process_html >>> %s",
                                plugin.get_plugin_name(), file_page)
                cached_entry = plugin.process_html(cached_entry)

        return cached_entry, mod

    app.logger.info("Converting to HTML with pandoc >>> '%s' ...", md_file_path)

    html = pypandoc.convert_file(
        md_file_path,
        "html5",
        format="md",
        extra_args=["--mathjax"],
        filters=["pandoc-xnos"],
    )

    if html.strip():
        html = clean_html(html)

    for plugin in plugins:
        if "process_before_cache_html" in dir(plugin):
            app.logger.info("Plug/%s - process_before_cache_html >>> %s",
                            plugin.get_plugin_name(), file_page)
            html = plugin.process_before_cache_html(html)

    cache.set(md_file_path.as_posix(), html)

    for plugin in plugins:
        if "process_html" in dir(plugin):
            app.logger.info("Plug/%s - process_html >>> %s",
                            plugin.get_plugin_name(), file_page)
            html = plugin.process_html(html)

    app.logger.info("Showing HTML page >>> '%s'", file_page)

    return html, mod


@app.get("/list/")
def list_full_wiki() -> str:
    """Get files in the wiki root."""
    return list_wiki("")


@app.get("/list/<path:folderpath>/")
def list_wiki(folderpath: str) -> str:
    """List all the pages in a given folder of the wiki."""
    files_list = []

    requested_path = safe_join(cfg.wiki_directory, folderpath)
    if requested_path is None:
        app.logger.info("Requested unsafe path >>> showing homepage")
        return index()
    app.logger.info("Showing >>> all files in %s", folderpath)

    for item in os.listdir(requested_path):
        item_path = Path(pathify(requested_path, item))  # wiki/dir1/dir2/...
        item_mtime = item_path.stat().st_mtime

        if not item_path.as_posix().startswith(HIDDEN_PATHS):  # skip hidden paths

            rel_item_path = item_path.relative_to(cfg.wiki_directory)
            item_url = rel_item_path.with_suffix("")  # drop the extension
            folder = rel_item_path.as_posix() if item_path.is_dir() else ""
            info = {
                "doc": item,
                "url": item_url,
                "folder": folder,
                "folder_url": folder,
                "mtime": item_mtime,
            }
            files_list.append(info)

    # Sorting
    if SYSTEM_SETTINGS["listsortMTime"]:
        files_list.sort(key=lambda x: x["mtime"], reverse=True)
    else:
        files_list.sort(key=lambda x: (str(x["url"]).casefold()))

    return render_template(
        "list_files.html",
        list=files_list,
        folder=folderpath,
        system=SYSTEM_SETTINGS)


@app.get('/search')
def search_route():
    if request.args.get("q"):
        return search(request.args.get("q"), request.args.get("page", 1))
    flash("You didn't enter anything to search for")
    return redirect("/")


@app.get("/<path:file_page>")
def wiki_page(file_page: str) -> None | str | Response:
    """Get wiki page."""
    git_sync_thread = Thread(target=wrm.git_pull, args=())
    git_sync_thread.start()

    if "favicon" in file_page:  # if the GET request is not for the favicon
        return None

    try:
        html_content, mod = get_html(file_page)
    except FileNotFoundError as e:
        app.logger.info(e)
        return redirect("/add_new?page=" + file_page)

    return render_template(
        "content.html",
        title=file_page,
        folder="",
        info=html_content,
        modif=mod,
        system=SYSTEM_SETTINGS,
    )


@app.get("/")
def index() -> None | str | Response:
    """Render home page."""

    html = ""
    app.logger.info("Showing HTML page >>> 'homepage'")

    md_file_path = Path(cfg.wiki_directory) / cfg.homepage
    cached_entry = cache.get(md_file_path.as_posix())
    if cached_entry:
        app.logger.info("Showing HTML page from cache >>> 'homepage'")
        return render_template(
            "index.html",
            homepage=cached_entry,
            system=SYSTEM_SETTINGS,
        )

    try:
        app.logger.info("Converting to HTML with pandoc >>> 'homepage' ...")
        html = pypandoc.convert_file(
            md_file_path, "html5", format="md", extra_args=["--mathjax"],
            filters=["pandoc-xnos"])
        html = clean_html(html)
        cache.set(md_file_path.as_posix(), html)

    except Exception as e:
        # TODO: Use Flask Abort?
        app.logger.exception("Conversion to HTML failed")

    return render_template("index.html", homepage=html, system=SYSTEM_SETTINGS)


@app.get("/add_new")
def add_new_view() -> str | Response:
    """Add a new page."""
    if (bool(cfg.protect_edit_by_password) and
            (request.cookies.get("session_wikmd") not in SESSIONS)):
        return login("/add_new")

    page_name = request.args.get("page")
    if page_name is None:
        page_name = ""
    return render_template(
        "new.html",
        upload_path=cfg.images_route,
        image_allowed_mime=cfg.image_allowed_mime,
        title=page_name,
        system=SYSTEM_SETTINGS,
    )


@app.post("/add_new")
def add_new_post() -> str | Response:
    """Add a new page."""
    if (bool(cfg.protect_edit_by_password) and
            (request.cookies.get("session_wikmd") not in SESSIONS)):
        return login("/add_new")

    page_name = fetch_page_name()

    re_render_page = ensure_page_can_be_created(page_name, page_name)
    if re_render_page:
        return re_render_page

    save(page_name)
    git_sync_thread = Thread(target=wrm.git_sync, args=(page_name, "Add"))
    git_sync_thread.start()

    return redirect(url_for("wiki_page", file_page=page_name))


@app.get("/edit/homepage")
def edit_homepage_view() -> str | Response:
    """Get the edit home page view."""
    if (bool(cfg.protect_edit_by_password) and
            (request.cookies.get("session_wikmd") not in SESSIONS)):
        return login("edit/homepage")

    with (Path(cfg.wiki_directory) / cfg.homepage).open("r",
                                                        encoding="utf-8",
                                                        errors="ignore") as f:
        content = f.read()

    return render_template(
        "new.html",
        content=content,
        title=cfg.homepage_title,
        upload_path=cfg.images_route,
        image_allowed_mime=cfg.image_allowed_mime,
        system=SYSTEM_SETTINGS,
    )


@app.post("/edit/homepage")
def edit_homepage_post() -> str | Response:
    """Change home page content."""
    if (bool(cfg.protect_edit_by_password) and
            (request.cookies.get("session_wikmd") not in SESSIONS)):
        return login("edit/homepage")

    page_name = "homepage"

    save(page_name)
    git_sync_thread = Thread(target=wrm.git_sync, args=(page_name, "Edit"))
    git_sync_thread.start()

    return redirect(url_for("/"))


@app.get("/remove/<path:page>")
def remove(page: str) -> Response:  # TODO: This shouldn't be a GET
    """Remove a page."""
    if (bool(cfg.protect_edit_by_password) and
            (request.cookies.get("session_wikmd") not in SESSIONS)):
        return redirect(url_for("wiki_page", file_page=page))

    filename = Path(safe_join(cfg.wiki_directory, f"{page}.md"))
    filename.unlink()
    if not any(filename.parent.iterdir()):
        filename.parent.rmdir()
    git_sync_thread = Thread(target=wrm.git_sync, args=(page, "Remove"))
    git_sync_thread.start()
    return redirect("/")


@app.get("/edit/<path:page>")
def edit_view(page: str) -> Response | str:
    """View the edit page populated with current content."""
    if (bool(cfg.protect_edit_by_password) and
            (request.cookies.get("session_wikmd") not in SESSIONS)):
        return login("edit/" + page)

    filename = Path(safe_join(cfg.wiki_directory, f"{page}.md"))
    if filename.exists():
        with filename.open("r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        return render_template(
            "new.html",
            content=content,
            title=page,
            upload_path=cfg.images_route,
            image_allowed_mime=cfg.image_allowed_mime,
            system=SYSTEM_SETTINGS,
        )

    logger.error("%s does not exists. Creating a new one.", filename)
    return render_template(
        "new.html",
        content="",
        title=page,
        upload_path=cfg.images_route,
        image_allowed_mime=cfg.image_allowed_mime,
        system=SYSTEM_SETTINGS,
    )


@app.post("/edit/<path:page>")
def edit(page: str) -> Response | str:
    """Change page content."""
    if (bool(cfg.protect_edit_by_password) and
            (request.cookies.get("session_wikmd") not in SESSIONS)):
        return login("edit/" + page)

    filename = Path(safe_join(cfg.wiki_directory, f"{page}.md"))
    page_name = fetch_page_name()

    if page_name != page:
        re_render_page = ensure_page_can_be_created(page_name, page_name)
        if re_render_page:
            return re_render_page

        filename.unlink()

    save(page_name)
    git_sync_thread = Thread(target=wrm.git_sync, args=(page_name, "Edit"))
    git_sync_thread.start()

    return redirect(url_for("wiki_page", file_page=page_name))


@app.post(f"/{cfg.images_route}")
def upload_file() -> str:
    """Upload file to the wiki."""
    if (bool(cfg.protect_edit_by_password) and
            (request.cookies.get("session_wikmd") not in SESSIONS)):
        return login()

    app.logger.info("Uploading new image ...")
    return im.save_images(request.files)


@app.delete(f"/{cfg.images_route}")
def delete_file() -> str:
    """Delete file from the wiki."""
    if (bool(cfg.protect_edit_by_password) and
            (request.cookies.get("session_wikmd") not in SESSIONS)):
        return login()

    # request data is in format "b'nameoffile.png" decode to utf-8
    file_name = request.data.decode("utf-8")
    im.delete_image(file_name)
    return "OK"


@app.post("/plug_com")
def communicate_plugins() -> str:
    """Send the request to the plugins."""
    if (bool(cfg.protect_edit_by_password) and
            (request.cookies.get("session_wikmd") not in SESSIONS)):
        return login()
    for plugin in plugins:
        if "communicate_plugin" in dir(plugin):
            return plugin.communicate_plugin(request)
    return "nothing to do"


@app.get("/knowledge-graph")
def graph() -> str:
    """Get the knowledge-graph."""
    global links
    links = knowledge_graph.find_links()
    return render_template("knowledge-graph.html", links=links, system=SYSTEM_SETTINGS)


@app.get("/login")
def login_view() -> str | Response:
    """Get login view."""
    app.logger.info("Display login page")
    return render_template("login.html", system=SYSTEM_SETTINGS)


@app.post("/login")
def login(page: str) -> str | Response:
    """Login Route."""
    password = request.form["password"]
    sha_string = sha256(password.encode("utf-8")).hexdigest()
    if sha_string == cfg.password_in_sha_256.lower():
        app.logger.info("User successfully logged in")
        resp = make_response(redirect("/" + page))
        session = secrets.token_urlsafe(1024 // 8)
        resp.set_cookie("session_wikmd", session)
        SESSIONS.append(session)
        return resp
    app.logger.info("Login failed!")

@app.get("/nav/<path:id>/")
def nav_id_to_page(id: str) -> Response:
    """Translate id to page path."""
    for i in links:
        if i["id"] == int(id):
            return redirect("/" + i["path"])
    return redirect("/")


@app.get(f"/{cfg.images_route}/<path:image_name>")
def display_image(image_name: str) -> str | Response:
    image_path = (Path(UPLOAD_FOLDER_PATH) / image_name).resolve().as_posix()
    try:
        response = send_file(Path(image_path).resolve())
    except Exception:
        # TODO: Use Flask Abort(404)?
        app.logger.exception("Could not find image: %s", image_path)
        return ""

    app.logger.info("Showing image >>> '%s'", image_path)
    # cache indefinitely
    response.headers["Cache-Control"] = "max-age=31536000, immutable"
    return response


@app.get("/toggle-darktheme/")
def toggle_darktheme() -> Response:
    """Toggle dark theme."""
    SYSTEM_SETTINGS["darktheme"] = not SYSTEM_SETTINGS["darktheme"]
    return redirect(request.args.get("return", "/"))  # redirect to the same page URL


@app.get("/toggle-sorting/")
def toggle_sort() -> Response:
    """Toggle sort mode."""
    SYSTEM_SETTINGS["listsortMTime"] = not SYSTEM_SETTINGS["listsortMTime"]
    return redirect("/list")


@app.get("/favicon.ico")
def favicon() -> Response:
    """Favicon."""
    return send_from_directory(Path(app.root_path) / "static",
                               "favicon.ico", mimetype="image/vnd.microsoft.icon")


def setup_search() -> None:
    search = Search(cfg.search_dir, create=True)

    app.logger.info("Search index creation...")
    items = []
    for root, _, files in os.walk(cfg.wiki_directory):
        for item in files:
            if (
                    root.startswith((f"{cfg.wiki_directory}/.git",
                                    f"{cfg.wiki_directory}/{cfg.images_route}"))
            ):
                continue
            item_ = Path(item)
            page_name, ext = item_.stem, item_.suffix
            if ext.lower() != ".md":
                continue
            path = os.path.relpath(root, cfg.wiki_directory)
            items.append((item, page_name, path))

    search.index_all(cfg.wiki_directory, items)


def setup_wiki_template() -> bool:
    """Copy wiki_template files into the wiki directory if it's empty."""
    root = Path(__file__).parent

    if not Path(cfg.wiki_directory).exists():
        app.logger.info("Wiki directory doesn't exists, copy template")
        shutil.copytree(root / "wiki_template", cfg.wiki_directory)
        return True
    if not any(Path(cfg.wiki_directory).iterdir()):
        app.logger.info("Wiki directory is empty, copy template")
        shutil.copytree(root / "wiki_template", cfg.wiki_directory, dirs_exist_ok=True)
        return True
    return False


def run_wiki() -> None:
    """Run the wiki as a Flask app."""
    app.logger.info("Starting Wikmd with wiki directory %s", Path(cfg.wiki_directory).resolve())

    for plugin in plugins:
        if "request_html" in dir(plugin):
            plugin.request_html(get_html)

    if int(cfg.wikmd_logging) == 1:
        logging.basicConfig(filename=cfg.wikmd_logging_file, level=logging.INFO)

    setup_wiki_template()

    upload_folder = Path(UPLOAD_FOLDER_PATH)
    upload_folder.mkdir(exist_ok=True)

    wrm.initialize()
    im.cleanup_images()
    setup_search()
    app.logger.info("Spawning search indexer watchdog")
    watchdog = Watchdog(cfg.wiki_directory, cfg.search_dir)
    watchdog.start()
    app.run(
        host=cfg.wikmd_host,
        port=cfg.wikmd_port,
        debug=True,
        use_reloader=False,
    )


if __name__ == "__main__":
    run_wiki()
