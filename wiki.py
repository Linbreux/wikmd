import os
import time
import logging
import uuid
from lxml.html.clean import clean_html
import pypandoc
import knowledge_graph
import secrets

from flask import Flask, render_template, request, redirect, url_for, make_response, safe_join, send_file, \
    send_from_directory
from threading import Thread
from hashlib import sha256
from cache import Cache
from image_manager import ImageManager
from config import WikmdConfig
from git_manager import WikiRepoManager
from search import Search, Watchdog
from web_dependencies import get_web_deps
from plugins.load_plugins import PluginLoader

from utils import pathify

SESSIONS = []

cfg = WikmdConfig()

UPLOAD_FOLDER_PATH = pathify(cfg.wiki_directory, cfg.images_route)
GIT_FOLDER_PATH = pathify(cfg.wiki_directory, '.git')
HIDDEN_FOLDER_PATH_LIST = [pathify(cfg.wiki_directory, hidden_folder) for hidden_folder in cfg.hide_folder_in_wiki]
HOMEPAGE_PATH = pathify(cfg.wiki_directory, cfg.homepage)
HIDDEN_PATHS = tuple([UPLOAD_FOLDER_PATH, GIT_FOLDER_PATH, HOMEPAGE_PATH] + HIDDEN_FOLDER_PATH_LIST)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER_PATH

# console logger
app.logger.setLevel(logging.INFO)

# file logger
logger = logging.getLogger('werkzeug')
logger.setLevel(logging.ERROR)

web_deps = get_web_deps(cfg.local_mode, app.logger)

# plugins
plugins = PluginLoader(flask_app=app, config=cfg, plugins=cfg.plugins, web_deps=web_deps).get_plugins()

wrm = WikiRepoManager(flask_app=app)
cache = Cache(cfg.cache_dir)
im = ImageManager(app, cfg)

SYSTEM_SETTINGS = {
    "darktheme": False,
    "listsortMTime": False,
    "web_deps": web_deps,
    "plugins": plugins
}


def process(content: str, page_name: str):
    """
    Function that processes the content with the plugins.
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
            app.logger.info(f"Plug/{plugin.get_plugin_name()} - process_md >>> {page_name}")
            processed = plugin.process_md(processed)

    return processed


def save(page_name):
    """
    Function that processes and saves a *.md page.
    :param page_name: name of the page
    """
    content = process(request.form['CT'], page_name)
    app.logger.info(f"Saving >>> '{page_name}' ...")

    try:
        filename = safe_join(cfg.wiki_directory, f"{page_name}.md")
        dirname = os.path.dirname(filename)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        with open(filename, 'w', encoding="utf-8") as f:
            f.write(content)
    except Exception as e:
        app.logger.error(f"Error while saving '{page_name}' >>> {str(e)}")


def search(search_term: str, page: int):
    """
    Function that searches for a term and shows the results.
    """
    app.logger.info(f"Searching >>> '{search_term}' ...")
    search = Search(cfg.search_dir)
    page = int(page)
    results, num_results, num_pages, suggestions = search.search(search_term, page)
    return render_template(
        'search.html',
        search_term=search_term,
        num_results=num_results,
        num_pages=num_pages,
        current_page=page,
        suggestions=suggestions,
        results=results,
        system=SYSTEM_SETTINGS,
    )


def fetch_page_name() -> str:
    page_name = request.form['PN']
    if page_name[-4:] == "{id}":
        page_name = f"{page_name[:-4]}{uuid.uuid4().hex}"
    return page_name


@app.route('/list/', methods=['GET'])
def list_full_wiki():
    return list_wiki("")


@app.route('/list/<path:folderpath>/', methods=['GET'])
def list_wiki(folderpath):
    """
    Lists all the pages in a given folder of the wiki.
    """
    files_list = []

    requested_path = safe_join(cfg.wiki_directory, folderpath)
    if requested_path is None:
        app.logger.info("Requested unsafe path >>> showing homepage")
        return index()
    app.logger.info(f"Showing >>> all files in {folderpath}")

    for item in os.listdir(requested_path):
        item_path = pathify(requested_path, item)  # wiki/dir1/dir2/...
        item_mtime = os.path.getmtime(item_path)

        if not item_path.startswith(HIDDEN_PATHS):  # skip hidden paths
            rel_item_path = item_path[len(cfg.wiki_directory + "/"):]  # dir1/dir2/...
            item_url = os.path.splitext(rel_item_path)[0]  # eventually drop the extension
            folder = rel_item_path if os.path.isdir(item_path) else ""

            info = {
                'doc': item,
                'url': item_url,
                'folder': folder,
                'folder_url': folder,
                'mtime': item_mtime,
            }
            files_list.append(info)

    # Sorting
    if SYSTEM_SETTINGS['listsortMTime']:
        files_list.sort(key=lambda x: x["mtime"], reverse=True)
    else:
        files_list.sort(key=lambda x: (str(x["url"]).casefold()))

    return render_template('list_files.html', list=files_list, folder=folderpath, system=SYSTEM_SETTINGS)


@app.route('/<path:file_page>', methods=['GET'])
def file_page(file_page):
    if request.args.get("q"):
        return search(request.args.get("q"), request.args.get("page", 1))
    else:
        html = ""
        mod = ""
        folder = ""

        if "favicon" in file_page:  # if the GET request is not for the favicon
            return

        try:
            md_file_path = safe_join(cfg.wiki_directory, f"{file_page}.md")
            mod = "Last modified: %s" % time.ctime(os.path.getmtime(md_file_path))
            folder = file_page.split("/")
            file_page = folder[-1:][0]
            folder = folder[:-1]
            folder = "/".join(folder)

            cached_entry = cache.get(md_file_path)
            if cached_entry:
                app.logger.info(f"Showing HTML page from cache >>> '{file_page}'")

                for plugin in plugins:
                    if "process_html" in dir(plugin):
                        app.logger.info(f"Plug/{plugin.get_plugin_name()} - process_html >>> {file_page}")
                        cached_entry = plugin.process_html(cached_entry)

                return render_template(
                    'content.html', title=file_page, folder=folder, info=cached_entry, modif=mod,
                    system=SYSTEM_SETTINGS
                )

            try:
                app.logger.info(f"Converting to HTML with pandoc >>> '{md_file_path}' ...")

                html = pypandoc.convert_file(md_file_path, "html5",
                                             format='md', extra_args=["--mathjax"], filters=['pandoc-xnos'])

                html = clean_html(html)

                for plugin in plugins:
                    if "process_before_cache_html" in dir(plugin):
                        app.logger.info(f"Plug/{plugin.get_plugin_name()} - process_before_cache_html >>> {file_page}")
                        html = plugin.process_before_cache_html(html)

                cache.set(md_file_path, html)

                for plugin in plugins:
                    if "process_html" in dir(plugin):
                        app.logger.info(f"Plug/{plugin.get_plugin_name()} - process_html >>> {file_page}")
                        html = plugin.process_html(html)

                app.logger.info(f"Showing HTML page >>> '{file_page}'")
            except Exception as a:
                app.logger.info(a)

            return render_template('content.html', title=file_page, folder=folder, info=html, modif=mod,
                                   system=SYSTEM_SETTINGS)
        except FileNotFoundError as e:
            app.logger.info(e)
            return redirect("/add_new?page=" + file_page)


@app.route('/', methods=['GET'])
def index():
    if request.args.get("q"):
        return search(request.args.get("q"), request.args.get("page", 1))
    else:
        html = ""
        app.logger.info("Showing HTML page >>> 'homepage'")

        md_file_path = os.path.join(cfg.wiki_directory, cfg.homepage)
        cached_entry = cache.get(md_file_path)
        if cached_entry:
            app.logger.info("Showing HTML page from cache >>> 'homepage'")
            return render_template(
                'index.html', homepage=cached_entry, system=SYSTEM_SETTINGS
            )

        try:
            app.logger.info("Converting to HTML with pandoc >>> 'homepage' ...")
            html = pypandoc.convert_file(
                md_file_path, "html5", format='md', extra_args=["--mathjax"],
                filters=['pandoc-xnos'])
            html = clean_html(html)
            cache.set(md_file_path, html)

        except Exception as e:
            app.logger.error(f"Conversion to HTML failed >>> {str(e)}")

        return render_template('index.html', homepage=html, system=SYSTEM_SETTINGS)


@app.route('/add_new', methods=['POST', 'GET'])
def add_new():
    if bool(cfg.protect_edit_by_password) and (request.cookies.get('session_wikmd') not in SESSIONS):
        return login("/add_new")
    if request.method == 'POST':
        page_name = fetch_page_name()
        save(page_name)
        git_sync_thread = Thread(target=wrm.git_sync, args=(page_name, "Add"))
        git_sync_thread.start()

        return redirect(url_for("file_page", file_page=page_name))
    else:
        page_name = request.args.get("page")
        if page_name is None:
            page_name = ""
        return render_template('new.html', upload_path=cfg.images_route,
                               image_allowed_mime=cfg.image_allowed_mime, title=page_name, system=SYSTEM_SETTINGS)


@app.route('/edit/homepage', methods=['POST', 'GET'])
def edit_homepage():
    if bool(cfg.protect_edit_by_password) and (request.cookies.get('session_wikmd') not in SESSIONS):
        return login("/edit/homepage")

    if request.method == 'POST':
        page_name = fetch_page_name()
        save(page_name)
        git_sync_thread = Thread(target=wrm.git_sync, args=(page_name, "Edit"))
        git_sync_thread.start()

        return redirect(url_for("file_page", file_page=page_name))
    else:

        with open(os.path.join(cfg.wiki_directory, cfg.homepage), 'r', encoding="utf-8", errors='ignore') as f:

            content = f.read()
        return render_template("new.html", content=content, title=cfg.homepage_title, upload_path=cfg.images_route,
                               image_allowed_mime=cfg.image_allowed_mime, system=SYSTEM_SETTINGS)


@app.route('/remove/<path:page>', methods=['GET'])
def remove(page):
    if bool(cfg.protect_edit_by_password) and (request.cookies.get('session_wikmd') not in SESSIONS):
        return redirect(url_for("file_page", file_page=page))

    filename = safe_join(cfg.wiki_directory, f"{page}.md")
    os.remove(filename)
    git_sync_thread = Thread(target=wrm.git_sync, args=(page, "Remove"))
    git_sync_thread.start()
    return redirect("/")


@app.route('/edit/<path:page>', methods=['POST', 'GET'])
def edit(page):
    if bool(cfg.protect_edit_by_password) and (request.cookies.get('session_wikmd') not in SESSIONS):
        return login(page)

    filename = safe_join(cfg.wiki_directory, f"{page}.md")
    if request.method == 'POST':
        page_name = fetch_page_name()
        if page_name != page:
            os.remove(filename)

        save(page_name)
        git_sync_thread = Thread(target=wrm.git_sync, args=(page_name, "Edit"))
        git_sync_thread.start()

        return redirect(url_for("file_page", file_page=page_name))
    else:
        with open(filename, 'r', encoding="utf-8", errors='ignore') as f:
            content = f.read()
        return render_template("new.html", content=content, title=page, upload_path=cfg.images_route,
                               image_allowed_mime=cfg.image_allowed_mime, system=SYSTEM_SETTINGS)


@app.route(os.path.join("/", cfg.images_route), methods=['POST', 'DELETE'])
def upload_file():
    if bool(cfg.protect_edit_by_password) and (request.cookies.get('session_wikmd') not in SESSIONS):
        return login()
    app.logger.info(f"Uploading new image ...")
    # Upload image when POST
    if request.method == "POST":
        return im.save_images(request.files)

    # DELETE when DELETE
    if request.method == "DELETE":
        # request data is in format "b'nameoffile.png" decode to utf-8
        file_name = request.data.decode("utf-8")
        im.delete_image(file_name)
        return 'OK'


@app.route("/plug_com", methods=['POST'])
def communicate_plugins():
    if bool(cfg.protect_edit_by_password) and (request.cookies.get('session_wikmd') not in SESSIONS):
        return login()
    if request.method == "POST":
        for plugin in plugins:
            if "communicate_plugin" in dir(plugin):
                return plugin.communicate_plugin(request)
    return "nothing to do"


@app.route('/knowledge-graph', methods=['GET'])
def graph():
    global links
    links = knowledge_graph.find_links()
    return render_template("knowledge-graph.html", links=links, system=SYSTEM_SETTINGS)


@app.route('/login', methods=['GET', 'POST'])
def login(page):
    if request.method == "POST":
        password = request.form["password"]
        sha_string = sha256(password.encode('utf-8')).hexdigest()
        if sha_string == cfg.password_in_sha_256.lower():
            app.logger.info("User successfully logged in")
            resp = make_response(redirect(page))
            session = secrets.token_urlsafe(1024 // 8)
            resp.set_cookie("session_wikmd", session)
            SESSIONS.append(session)
            return resp
        else:
            app.logger.info("Login failed!")
    else:
        app.logger.info("Display login page")
    return render_template("login.html", system=SYSTEM_SETTINGS)


# Translate id to page path


@app.route('/nav/<path:id>/', methods=['GET'])
def nav_id_to_page(id):
    for i in links:
        if i["id"] == int(id):
            return redirect("/" + i["path"])
    return redirect("/")


@app.route(os.path.join("/", cfg.images_route, "<path:image_name>"))
def display_image(image_name):
    image_path = safe_join(UPLOAD_FOLDER_PATH, image_name)
    app.logger.info(f"Showing image >>> '{image_path}'")
    response = send_file(image_path)
    # cache indefinitely
    response.headers["Cache-Control"] = "max-age=31536000, immutable"
    return response


@app.route('/toggle-darktheme/', methods=['GET'])
def toggle_darktheme():
    SYSTEM_SETTINGS['darktheme'] = not SYSTEM_SETTINGS['darktheme']
    return redirect(request.args.get("return", "/"))  # redirect to the same page URL


@app.route('/toggle-sorting/', methods=['GET'])
def toggle_sort():
    SYSTEM_SETTINGS['listsortMTime'] = not SYSTEM_SETTINGS['listsortMTime']
    return redirect("/list")


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


def setup_search():
    search = Search(cfg.search_dir, create=True)

    app.logger.info("Search index creation...")
    items = []
    for root, subfolder, files in os.walk(cfg.wiki_directory):
        for item in files:
            if (
                    root.startswith(os.path.join(cfg.wiki_directory, '.git')) or
                    root.startswith(os.path.join(cfg.wiki_directory, cfg.images_route))
            ):
                continue
            page_name, ext = os.path.splitext(item)
            if ext.lower() != ".md":
                continue
            path = os.path.relpath(root, cfg.wiki_directory)
            items.append((item, page_name, path))

    search.index_all(cfg.wiki_directory, items)


def run_wiki():
    """
    Function that runs the wiki as a Flask app.
    """
    if int(cfg.wikmd_logging) == 1:
        logging.basicConfig(filename=cfg.wikmd_logging_file, level=logging.INFO)

    if not os.path.exists(UPLOAD_FOLDER_PATH):
        app.logger.info(f"Creating upload folder >>> {UPLOAD_FOLDER_PATH}")
        os.mkdir(UPLOAD_FOLDER_PATH)

    im.cleanup_images()
    setup_search()
    app.logger.info("Spawning search indexer watchdog")
    watchdog = Watchdog(cfg.wiki_directory, cfg.search_dir)
    watchdog.start()
    app.run(host=cfg.wikmd_host, port=cfg.wikmd_port, debug=True, use_reloader=False)


if __name__ == '__main__':
    run_wiki()
