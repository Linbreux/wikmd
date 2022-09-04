import os
from shutil import ExecError
import time
import re
import logging
import uuid
from lxml.html.clean import clean_html
import pypandoc
import knowledge_graph
import random
import string

from flask import Flask, render_template, request, redirect, url_for, send_from_directory, make_response
from werkzeug.utils import secure_filename
from random import randint
from threading import Thread
from hashlib import sha256

from config import WikmdConfig
from git_manager import WikiRepoManager
from web_dependencies import get_web_deps


ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

SESSIONS = []

cfg = WikmdConfig()
UPLOAD_FOLDER = f"{cfg.wiki_directory}/{cfg.images_route}"

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# console logger
app.logger.setLevel(logging.INFO)

# file logger
logger = logging.getLogger('werkzeug')
logger.setLevel(logging.ERROR)

wrm = WikiRepoManager(flask_app=app)

SYSTEM_SETTINGS = {
    "darktheme": False,
    "listsortMTime": False,
    "web_deps": get_web_deps(cfg.local_mode, app.logger)
}

def save(page_name):
    """
    Function that saves a *.md page.
    :param page_name: name of the page
    """
    content = request.form['CT']
    app.logger.info(f"Saving >>> '{page_name}' ...")

    try:
        filename = os.path.join(cfg.wiki_directory, page_name + '.md')
        dirname = os.path.dirname(filename)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        with open(filename, 'w') as f:
            f.write(content)
    except Exception as e:
        app.logger.error(f"Error while saving '{page_name}' >>> {str(e)}")


def search():
    """
    Function that searches for a term and shows the results.
    """
    search_term = request.form['ss']
    escaped_search_term = re.escape(search_term)
    found = []

    app.logger.info(f"Searching >>> '{search_term}' ...")

    for root, subfolder, files in os.walk(cfg.wiki_directory):
        for item in files:
            path = os.path.join(root, item)
            if os.path.join(cfg.wiki_directory, '.git') in str(path):
                # We don't want to search there
                app.logger.debug(f"Skipping {path} is git file")
                continue
            if os.path.join(cfg.wiki_directory, cfg.images_route) in str(path):
                # Nothing interesting there too
                continue
            with open(root + '/' + item, encoding="utf8", errors='ignore') as f:
                fin = f.read()
                try:
                    if (re.search(escaped_search_term, root + '/' + item, re.IGNORECASE) or
                            re.search(escaped_search_term, fin, re.IGNORECASE) is not None):
                        # Stripping 'wiki/' part of path before serving as a search result
                        folder = root[len(cfg.wiki_directory + "/"):]
                        if folder == "":
                            url = os.path.splitext(
                                root[len(cfg.wiki_directory + "/"):] + "/" + item)[0]
                        else:
                            url = "/" + \
                                  os.path.splitext(
                                      root[len(cfg.wiki_directory + "/"):] + "/" + item)[0]

                        info = {'doc': item,
                                'url': url,
                                'folder': folder,
                                'folder_url': root[len(cfg.wiki_directory + "/"):]}
                        found.append(info)
                        app.logger.info(f"Found '{search_term}' in '{item}'")
                except Exception as e:
                    app.logger.error(f"Error while searching >>> {str(e)}")

    return render_template('search.html', zoekterm=found, system=SYSTEM_SETTINGS)


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
    folder_list = []
    app.logger.info("Showing >>> 'all files'")
    safe_folder = cfg.wiki_directory
    requested_path = os.path.join(cfg.wiki_directory,folderpath) 
    print(requested_path)
    if os.path.commonprefix((os.path.realpath(requested_path),os.path.realpath(safe_folder))) != os.path.realpath(safe_folder): 
        return index()
    for root, subfolder, files in os.walk(requested_path):
        if root[-1] == '/':
            root = root[:-1]
        for item in files:
            path = os.path.join(root, item)
            mtime = os.path.getmtime(os.path.join(root, item))
            if os.path.join(cfg.wiki_directory, '.git') in str(path):
                # We don't want to search there
                app.logger.debug(f"skipping {path}: is git file")
                continue
            if os.path.join(cfg.wiki_directory, cfg.images_route) in str(path):
                # Nothing interesting there too
                continue

            folder = root[len(cfg.wiki_directory + "/"):]
            if folder == "":
                if item == cfg.homepage:
                    continue
                url = os.path.splitext(
                    root[len(cfg.wiki_directory + "/"):] + "/" + item)[0]
            else:
                url = "/" + \
                    os.path.splitext(
                        root[len(cfg.wiki_directory + "/"):] + "/" + item)[0]

            info = {'doc': item,
                    'url': url,
                    'folder': folder,
                    'folder_url': folder,
                    'mtime': mtime,
                    }
            folder_list.append(info)

    if SYSTEM_SETTINGS['listsortMTime']:
        folder_list.sort(key=lambda x: x["mtime"], reverse=True)
    else:
        folder_list.sort(key=lambda x: (str(x["url"]).casefold()))

    return render_template('list_files.html', list=folder_list, folder=folderpath, system=SYSTEM_SETTINGS)


@app.route('/<path:file_page>', methods=['POST', 'GET'])
def file_page(file_page):
    if request.method == 'POST':
        return search()
    else:
        html = ""
        mod = ""
        folder = ""

        if "favicon" not in file_page:  # if the GET request is not for the favicon
            try:
                md_file_path = os.path.join(cfg.wiki_directory, file_page + ".md")
                # latex = pypandoc.convert_file("wiki/" + file_page + ".md", "tex", format="md")
                # html = pypandoc.convert_text(latex,"html5",format='tex', extra_args=["--mathjax"])

                app.logger.info(f"Converting to HTML with pandoc >>> '{md_file_path}' ...")
                html = pypandoc.convert_file(md_file_path, "html5",
                                             format='md', extra_args=["--mathjax"], filters=['pandoc-xnos'])
                html = clean_html(html)
                mod = "Last modified: %s" % time.ctime(os.path.getmtime(md_file_path))
                folder = file_page.split("/")
                file_page = folder[-1:][0]
                folder = folder[:-1]
                folder = "/".join(folder)
                app.logger.info(f"Showing HTML page >>> '{file_page}'")
            except Exception as a:
                app.logger.info(a)

        return render_template('content.html', title=file_page, folder=folder, info=html, modif=mod,
                               system=SYSTEM_SETTINGS)


@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        return search()
    else:
        html = ""
        app.logger.info("Showing HTML page >>> 'homepage'")
        try:
            app.logger.info("Converting to HTML with pandoc >>> 'homepage' ...")
            html = pypandoc.convert_file(
                os.path.join(cfg.wiki_directory, cfg.homepage), "html5", format='md', extra_args=["--mathjax"],
                filters=['pandoc-xnos'])
            html = clean_html(html)

        except Exception as e:
            app.logger.error(f"Conversion to HTML failed >>> {str(e)}")

        return render_template('index.html', homepage=html, system=SYSTEM_SETTINGS)


@app.route('/add_new', methods=['POST', 'GET'])
def add_new():
    if(bool(cfg.protect_edit_by_password) and (request.cookies.get('session_wikmd') not in SESSIONS)):
        return login("/add_new")
    if request.method == 'POST':
        page_name = fetch_page_name()
        save(page_name)
        git_sync_thread = Thread(target=wrm.git_sync, args=(page_name, "Add"))
        git_sync_thread.start()

        return redirect(url_for("file_page", file_page=page_name))
    else:
        return render_template('new.html', upload_path=cfg.images_route, system=SYSTEM_SETTINGS)


@app.route('/edit/homepage', methods=['POST', 'GET'])
def edit_homepage():
    if(bool(cfg.protect_edit_by_password) and (request.cookies.get('session_wikmd') not in SESSIONS)):
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
                               system=SYSTEM_SETTINGS)


@app.route('/remove/<path:page>', methods=['GET'])
def remove(page):
    app.logger.info(request.cookies.get('session_wikmd'))
    if(bool(cfg.protect_edit_by_password) and (request.cookies.get('session_wikmd') not in SESSIONS)):
        return redirect(url_for("file_page", file_page=page))

    filename = os.path.join(cfg.wiki_directory, page + '.md')
    os.remove(filename)
    git_sync_thread = Thread(target=wrm.git_sync, args=(page, "Remove"))
    git_sync_thread.start()
    return redirect("/")


@app.route('/edit/<path:page>', methods=['POST', 'GET'])
def edit(page):
    if(bool(cfg.protect_edit_by_password) and (request.cookies.get('session_wikmd') not in SESSIONS)):
        return login(page)
    filename = os.path.join(cfg.wiki_directory, page + '.md')
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
                               system=SYSTEM_SETTINGS)


@app.route('/' + cfg.images_route, methods=['POST', 'DELETE'])
def upload_file():
    app.logger.info(f"Uploading new image ...")
    # Upload image when POST
    if request.method == "POST":
        file_names = []
        for key in request.files:
            file = request.files[key]
            filename = secure_filename(file.filename)
            # bug found by cat-0
            while filename in os.listdir(os.path.join(cfg.wiki_directory, cfg.images_route)):
                app.logger.info(
                    "There is a duplicate, solving this by extending the filename...")
                filename, file_extension = os.path.splitext(filename)
                filename = filename + str(randint(1, 9999999)) + file_extension

            file_names.append(filename)
            try:
                app.logger.info(f"Saving image >>> '{filename}' ...")
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            except Exception as e:
                app.logger.error(f"Error while saving image >>> {str(e)}")
        return filename

    # DELETE when DELETE
    if request.method == "DELETE":
        # request data is in format "b'nameoffile.png" decode by utf-8
        filename = request.data.decode("utf-8")
        try:
            app.logger.info(f"Removing >>> '{str(filename)}' ...")
            os.remove((os.path.join(app.config['UPLOAD_FOLDER'], filename)))
        except Exception as e:
            app.logger.error(f"Could not remove {str(filename)}")
        return 'OK'


@app.route('/knowledge-graph', methods=['GET'])
def graph():
    global links
    links = knowledge_graph.find_links()
    return render_template("knowledge-graph.html", links=links, system=SYSTEM_SETTINGS)


@app.route('/login', methods=['GET','POST'])
def login(page):
    if request.method == "POST":
        password = request.form["password"]
        sha_string = sha256(password.encode('utf-8')).hexdigest()
        if sha_string == cfg.password_in_sha_256.lower():
            app.logger.info("User successfully logged in")
            resp = make_response(redirect(page))
            session = ''.join(random.choice(string.ascii_lowercase) for i in range(231))
            resp.set_cookie("session_wikmd",session)
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
            return redirect("/"+i["path"])
    return redirect("/")


@app.route('/' + cfg.images_route + '/<path:filename>')
def display_image(filename):
    # print('display_image filename: ' + filename)
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=False)


@app.route('/toggle-darktheme/', methods=['GET'])
def toggle_darktheme():
    SYSTEM_SETTINGS['darktheme'] = not SYSTEM_SETTINGS['darktheme']
    return redirect(request.referrer)  # redirect to the same page URL


@app.route('/toggle-sorting/', methods=['GET'])
def toggle_sort():
    SYSTEM_SETTINGS['listsortMTime'] = not SYSTEM_SETTINGS['listsortMTime']
    return redirect("/list")


def run_wiki():
    """
    Function that runs the wiki as a Flask app.
    """
    if int(cfg.wikmd_logging) == 1:
        logging.basicConfig(filename=cfg.wikmd_logging_file, level=logging.INFO)

    app.run(host=cfg.wikmd_host, port=cfg.wikmd_port, debug=True, use_reloader=False)


if __name__ == '__main__':
    run_wiki()
