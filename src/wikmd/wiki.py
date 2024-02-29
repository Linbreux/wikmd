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
from typing import TypeVar

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
from wikmd.plugin_manager import PluginManager
from wikmd.search import Search, Watchdog
from wikmd.utils import pathify, secure_filename
from wikmd.web_dependencies import get_web_deps

PC_T = TypeVar("PC_T", bound="PageContent")

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


app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER_PATH
app.config["SECRET_KEY"] = cfg.secret_key

# console logger
app.logger.setLevel(logging.INFO)

# file logger
logger = logging.getLogger("werkzeug")
logger.setLevel(logging.ERROR)

web_deps = get_web_deps(cfg.local_mode, app.logger)

# plugins
plugin_manager = PluginManager(
    flask_app=app,
    config=cfg,
    plugins=cfg.plugins,
    web_deps=web_deps)

wrm = WikiRepoManager(flask_app=app)
cache = Cache(cfg.cache_dir)
im = ImageManager(app, cfg)

SYSTEM_SETTINGS = {
    "darktheme": False,
    "listsortMTime": False,
    "web_deps": web_deps,
    "plugins": plugin_manager.plugins,
}


@app.context_processor
def inject_file_list() -> dict:
    """Context processor that injects our file list into every call."""
    return {"file_list": wiki_tree(Path(cfg.wiki_directory))}


class PageContent:
    """Holds the content of a wiki page."""

    def __init__(self, title: str = "", content: str = ""):
        self._title = title
        self.content = content
        self.errors = []

        self.is_new_page = True
        """set is_new_page to false we are editing a page rather than creating a new"""

    @classmethod
    def load_from_request(cls: type[PC_T]) -> PC_T:
        """Load the page content from the pages request form."""
        return cls(request.form["PN"], request.form["CT"])

    @property
    def _formatted(self) -> str:
        if self._title[-4:] == "{id}":
            return f"{self._title[:-4]}{uuid.uuid4().hex}"
        return self._title

    @property
    def title(self) -> str:
        """The fully qualified path including any directories, but without a suffix."""
        return Path(self._formatted).with_suffix("").as_posix()\
            if self._formatted else ""

    @property
    def file_name(self) -> str:
        """The name, any directories are strip out, with a suffix."""
        # If the title is empty that means we are creating
        # a new file and should return it empty.
        if not self._formatted:
            return self._formatted
        t = Path(self._formatted)
        # If the path doesn't have a suffix we add .md
        return t.name if t.suffix != "" else t.with_suffix(".md").name

    @property
    def relative_file_path(self) -> Path:
        """The relative path to the file. Excluding 'wiki' directory.

        This should just be the title but with a suffix.
        """
        p = Path(self._formatted)
        return p if p.suffix != "" else p.with_suffix(".md")

    @property
    def file_path(self) -> Path:
        """The path to the file. This will include the 'wiki' directory."""
        p = Path(safe_join(cfg.wiki_directory, self._formatted))
        return p if p.suffix != "" else p.with_suffix(".md")

    def validate(self) -> bool:
        """Validate the page name, add errors to the error list for later retrival."""
        can_create_page = self.is_new_page is True and self.file_path.exists()
        safe_name = "/".join([secure_filename(part) for part in self.title.split("/")])
        filename_is_ok = safe_name == self.title
        if not can_create_page and filename_is_ok and self.title:  # Early exist
            return True

        if can_create_page:
            self.errors.append("A page with that name already exists. "
                               "The page name needs to be unique.")

        if not filename_is_ok:
            self.errors.append(f"Page name not accepted. Try using '{safe_name}'.")

        if not self.title:
            self.errors.append("Your page needs a name.")
        return False


def process(page: PageContent) -> str:
    """Process the content with the plugins.

    It also manages CRLF to LF conversion.
    """
    # Convert Win line ending (CRLF) to standard Unix (LF)
    processed = page.content.replace("\r\n", "\n")

    # Process the content with the plugins
    return plugin_manager.broadcast("process_md", processed)


def save(page: PageContent) -> None:
    """Get file content from the form and save it."""
    app.logger.info("Saving >>> '%s' ...", page.title)

    try:
        page.file_path.parent.mkdir(exist_ok=True)

        with page.file_path.open("w", encoding="utf-8") as f:
            f.write(page.content)
    except Exception as e:
        # TODO: Use Flask Abort?
        app.logger.exception("Error while saving '%s'", page.title)


def search(search_term: str, page: int) -> str:
    """Preform a search for a term and shows the results."""
    app.logger.info("Searching >>> '%s' ...", search_term)
    search_index = Search(cfg.search_dir)
    page = int(page)
    search_result = search_index.search(search_term, page)
    results, num_results, num_pages, suggestions = search_result
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


def wiki_tree(path: Path) -> dict:
    """Build a dictionary structure from the passed in folder."""
    try:
        p_url = path.relative_to(cfg.wiki_directory).with_suffix("")
    except ValueError:
        p_url = Path()
    tree = {
        "name": path.stem,
        "children": [],
        "url": p_url.as_posix(),
        "parts": len(p_url.parts),
        "id": hash(p_url),
        "item_mtime": path.stat().st_mtime,
    }

    for name in path.iterdir():
        fn = name.as_posix()
        if fn.startswith(HIDDEN_PATHS):  # skip hidden paths
            continue
        fn = Path(fn)
        if fn.is_dir():
            tree["children"].append(wiki_tree(fn))
        else:
            url = fn.relative_to(cfg.wiki_directory)
            tree["children"].append({
                "name": name.stem,
                "url": url.as_posix(),
                "parts": len(url.parts),
                "id": hash(url),
                "item_mtime": path.stat().st_mtime,
            })
    return tree


def sort_tree_children(dictionary: dict, sort_by: str) -> dict:
    """Reorders the dictionary and its children."""
    children = sorted(dictionary.get("children"), key=lambda item: item[sort_by])
    dictionary["children"] = children
    for child in children:
        if "children" in child:
            child["children"] = sort_tree_children(child, sort_by)
    return dictionary


def get_html(page: PageContent) -> [str, str]:
    """Get the content of the file."""
    mod = "Last modified: %s" % time.ctime(page.file_path.stat().st_mtime)

    cached_entry = cache.get(page.file_path.as_posix())
    if cached_entry:
        app.logger.info("Showing HTML page from cache >>> '%s'", page.file_name)
        cached_entry = plugin_manager.broadcast("process_html", cached_entry)
        return cached_entry, mod

    app.logger.info("Converting to HTML with pandoc >>> '%s' ...", page.file_name)

    if page.file_path.suffix == ".md":
        html = pypandoc.convert_file(
            page.file_path,
            "html5",
            format="md",
            extra_args=["--mathjax"],
            filters=["pandoc-xnos"],
        )
    else:
        # If the page isn't an .md page load it without
        # running it through the converter.
        with page.file_path.open("r", encoding="utf-8", errors="ignore") as f:
            html = f.read()

    if html.strip():
        html = clean_html(html)

    html = plugin_manager.broadcast("process_before_cache_html", html)

    cache.set(page.file_path.as_posix(), html)

    html = plugin_manager.broadcast("process_html", html)

    app.logger.info("Showing HTML page >>> '%s'", page.file_name)

    return html, mod


@app.get("/list/")
def list_full_wiki() -> str:
    """Get files in the wiki root."""
    return list_wiki("")


@app.get("/list/<path:folderpath>/")
def list_wiki(folderpath: str) -> str:
    """List all the pages in a given folder of the wiki."""
    requested_path = safe_join(cfg.wiki_directory, folderpath)
    if requested_path is None:
        app.logger.info("Requested unsafe path >>> showing homepage")
        return index()
    app.logger.info("Showing >>> all files in %s", folderpath)
    requested_path = Path(requested_path)

    file_list = wiki_tree(requested_path)
    # Sorting
    if SYSTEM_SETTINGS["listsortMTime"]:
        file_list = sort_tree_children(file_list, "listsortMTime")
    else:
        file_list = sort_tree_children(file_list, "url")

    return render_template(
        "list_files.html",
        list=file_list,
        folder=folderpath,
        system=SYSTEM_SETTINGS)


@app.get("/search")
def search_route() -> str | Response:
    """Route to get result from a search."""
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

    page = PageContent(title=file_page)
    try:
        html_content, mod = get_html(page)
    except FileNotFoundError as e:
        app.logger.info(e)
        return redirect("/add_new?page=" + file_page)

    page.content = html_content
    return render_template(
        "content.html",
        form=page,
        folder="",
        info=html_content,
        modif=mod,
        system=SYSTEM_SETTINGS,
    )


@app.get("/")
def index() -> None | str | Response:
    """Render home page."""
    app.logger.info("Showing HTML page >>> 'homepage'")

    md_file_path = Path(cfg.wiki_directory) / cfg.homepage
    cached_entry = cache.get(md_file_path.as_posix())
    if cached_entry:
        page = PageContent(cfg.homepage_title, cached_entry)
        app.logger.info("Showing HTML page from cache >>> 'homepage'")
        return render_template(
            "index.html",
            form=page,
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

    page = PageContent(cfg.homepage_title, html)
    return render_template("index.html", form=page, system=SYSTEM_SETTINGS)


@app.get("/add_new")
def add_new_view() -> str | Response:
    """Add a new page."""
    if (bool(cfg.protect_edit_by_password) and
            (request.cookies.get("session_wikmd") not in SESSIONS)):
        return login("/add_new")

    page = PageContent(request.args.get("page") or "", "")
    return render_template(
        "new.html",
        upload_path=cfg.images_route,
        image_allowed_mime=cfg.image_allowed_mime,
        form=page,
        system=SYSTEM_SETTINGS,
    )


@app.post("/add_new")
def add_new_post() -> str | Response:
    """Add a new page."""
    if (bool(cfg.protect_edit_by_password) and
            (request.cookies.get("session_wikmd") not in SESSIONS)):
        return login("/add_new")
    page = PageContent.load_from_request()

    page.is_new_page = True
    if not page.validate():
        return render_template("new.html",
                               form=page,
                               upload_path=cfg.images_route,
                               image_allowed_mime=cfg.image_allowed_mime,
                               system=SYSTEM_SETTINGS)

    save(page)
    git_sync_thread = Thread(target=wrm.git_sync, args=(page.title, "Add"))
    git_sync_thread.start()

    return redirect(url_for("wiki_page", file_page=page.relative_file_path))


@app.get("/edit/homepage")
def edit_homepage_view() -> str | Response:
    """Get the edit home page view."""
    if (bool(cfg.protect_edit_by_password) and
            (request.cookies.get("session_wikmd") not in SESSIONS)):
        return login("edit/homepage")

    with (Path(cfg.wiki_directory) / cfg.homepage).open("r",
                                                        encoding="utf-8",
                                                        errors="ignore") as f:
        str_content = f.read()
    page = PageContent(cfg.homepage_title, str_content)
    return render_template(
        "new.html",
        form=page,
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

    page = PageContent.load_from_request()
    page.is_new_page = False
    if not page.validate():
        return render_template(
            "new.html",
            form=page,
            upload_path=cfg.images_route,
            image_allowed_mime=cfg.image_allowed_mime,
            system=SYSTEM_SETTINGS,
        )

    save(page)
    git_sync_thread = Thread(target=wrm.git_sync, args=(page.title, "Edit"))
    git_sync_thread.start()

    return redirect(url_for("wiki_page", file_page=page.relative_file_path))


@app.get("/remove/<path:page>")
def remove(page: str) -> Response:  # TODO: This shouldn't be a GET
    """Remove a page."""
    if (bool(cfg.protect_edit_by_password) and
            (request.cookies.get("session_wikmd") not in SESSIONS)):
        return redirect(url_for("wiki_page", file_page=page))

    page = PageContent(title=page)
    page.file_path.unlink()

    if not any(page.file_path.parent.iterdir()):
        page.file_path.parent.rmdir()
    git_sync_thread = Thread(target=wrm.git_sync, args=(page, "Remove"))
    git_sync_thread.start()
    return redirect("/")


@app.get("/edit/<path:page_name>")
def edit_view(page_name: str) -> Response | str:
    """View the edit page populated with current content."""
    if (bool(cfg.protect_edit_by_password) and
            (request.cookies.get("session_wikmd") not in SESSIONS)):
        return login("edit/" + page_name)

    page = PageContent(page_name, "")
    if page.file_path.exists():
        with page.file_path.open("r", encoding="utf-8", errors="ignore") as f:
            page.content = f.read()

    return render_template(
        "new.html",
        form=page,
        upload_path=cfg.images_route,
        image_allowed_mime=cfg.image_allowed_mime,
        system=SYSTEM_SETTINGS,
    )


@app.post("/edit/<path:page_name>")
def edit(page_name: str) -> Response | str:
    """Change page content."""
    if (bool(cfg.protect_edit_by_password) and
            (request.cookies.get("session_wikmd") not in SESSIONS)):
        return login("edit/" + page_name)

    page = PageContent.load_from_request()
    page.is_new_page = False
    if not page.validate():
        return render_template(
            "new.html",
            form=page,
            upload_path=cfg.images_route,
            image_allowed_mime=cfg.image_allowed_mime,
            system=SYSTEM_SETTINGS,
        )

    if page.title != page_name:
        (Path(cfg.wiki_directory) / page_name).unlink()

    save(page)
    git_sync_thread = Thread(target=wrm.git_sync, args=(page.title, "Edit"))
    git_sync_thread.start()

    return redirect(url_for("wiki_page", file_page=page.relative_file_path))


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
def communicate_plugins() -> None | Response:
    """Send the request to the plugins."""
    if (bool(cfg.protect_edit_by_password) and
            (request.cookies.get("session_wikmd") not in SESSIONS)):
        return login()
    plugin_manager.broadcast("communicate_plugin", request)
    return None


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
def login(page: str) -> None | str | Response:
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
    return None


@app.get("/nav/<path:id>/")
def nav_id_to_page(id_: str) -> Response:
    """Translate id to page path."""
    for i in links:
        if i["id"] == int(id_):
            return redirect("/" + i["path"])
    return redirect("/")


@app.get(f"/{cfg.images_route}/<path:image_name>")
def display_image(image_name: str) -> str | Response:
    """Get the image path route."""
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
    """Set up search index."""
    search_index = Search(cfg.search_dir, create=True)

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

    search_index.index_all(cfg.wiki_directory, items)


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
    app.logger.info("Starting Wikmd with wiki directory %s",
                    Path(cfg.wiki_directory).resolve())

    plugin_manager.broadcast("request_html", get_html)

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
