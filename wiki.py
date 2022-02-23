from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
import logging
from werkzeug.utils import secure_filename
from random import randint
import datetime
import time
import git
import pypandoc
import markdown
import os
import re
import uuid

HOMEPAGE = os.getenv('HOMEPAGE', "homepage.md")
HOMEPAGE_TITLE = os.getenv('HOMEPAGE_TITLE', "homepage")
WIKI_DATA = os.getenv('WIKI_DATA', "wiki")
IMAGES_ROUTE = os.getenv('IMAGES_ROUTE', 'img')
UPLOAD_FOLDER = WIKI_DATA + '/' + IMAGES_ROUTE
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

SYSTEM_SETTINGS = {
    "darktheme": False,
    "listsortMTime": False,
}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)


def save(page_name):
    content = request.form['CT']
    app.logger.info("saving " + page_name)
    try:
        filename = os.path.join(WIKI_DATA, page_name + '.md')
        dirname = os.path.dirname(filename)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        with open(filename, 'w') as f:
            f.write(content)
    except Exception as e:
        app.logger.error("Error while saving: " + str(e))
    gitcom(pagename=page_name)


def search():
    search_term = request.form['ss']
    escaped_search_term = re.escape(search_term)
    found = []

    app.logger.info("searching for " + search_term + " ...")

    for root, subfolder, files in os.walk(WIKI_DATA):
        for item in files:
            path = os.path.join(root, item)
            if os.path.join(WIKI_DATA, '.git') in str(path):
                # We don't want to search there
                app.logger.debug("skipping " + path + " : is git file")
                continue
            if os.path.join(WIKI_DATA, IMAGES_ROUTE) in str(path):
                # Nothing interesting there too
                continue
            with open(root + '/' + item, encoding="utf8") as f:
                fin = f.read()
                try:
                    if (re.search(escaped_search_term, root + '/' + item, re.IGNORECASE) or
                            re.search(escaped_search_term, fin, re.IGNORECASE) != None):
                        # Stripping 'wiki/' part of path before serving as a search result
                        folder = root[len(WIKI_DATA + "/"):]
                        if folder == "":
                            url = os.path.splitext(root[len(WIKI_DATA + "/"):] + "/" + item)[0]
                        else:
                            url = "/" + os.path.splitext(root[len(WIKI_DATA + "/"):] + "/" + item)[0]

                        info = {'doc': item,
                                'url': url,
                                'folder': folder,
                                'folder_url': root[len(WIKI_DATA + "/"):]}
                        found.append(info)
                        app.logger.info("found " + search_term + " in " + item)
                except Exception as e:
                    app.logger.error("There was an error: " + str(e))

    return render_template('search.html', zoekterm=found, system=SYSTEM_SETTINGS)


@app.route('/list/', methods=['GET'])
def list_full_wiki():
    return list_wiki("")


@app.route('/list/<path:folderpath>/', methods=['GET'])
def list_wiki(folderpath):
    list = []
    for root, subfolder, files in os.walk(os.path.join(WIKI_DATA, folderpath)):
        if root[-1] == '/':
            root = root[:-1]
        for item in files:
            path = os.path.join(root, item)
            mtime = os.path.getmtime(os.path.join(root,item))
            if os.path.join(WIKI_DATA, '.git') in str(path):
                # We don't want to search there
                app.logger.debug("skipping " + path + " : is git file")
                continue
            if os.path.join(WIKI_DATA, IMAGES_ROUTE) in str(path):
                # Nothing interesting there too
                continue

            folder = root[len(WIKI_DATA + "/"):]
            if folder == "":
                if item == HOMEPAGE:
                    continue
                url = os.path.splitext(root[len(WIKI_DATA + "/"):] + "/" + item)[0]
            else:
                url = "/" + os.path.splitext(root[len(WIKI_DATA + "/"):] + "/" + item)[0]

            info = {'doc': item,
                    'url': url,
                    'folder': folder,
                    'folder_url': folder,
                    'mtime':mtime,
                    }
            list.append(info)

    if SYSTEM_SETTINGS['listsortMTime']:
        list.sort(key=lambda x: x["mtime"],reverse=True)
    else:
        list.sort(key=lambda x: (str(x["url"]).casefold()))

    return render_template('list_files.html', list=list, folder=folderpath, system=SYSTEM_SETTINGS)


def gitcom(pagename=""):
    try:
        repo = git.Repo.init(WIKI_DATA)
        repo.git.checkout("-b", "master")
        repo.config_writer().set_value("user", "name", "wikmd").release()
        repo.config_writer().set_value("user", "email", "wikmd@no-mail.com").release()
        app.logger.info("There doesn't seem to be a repo, creating one...")

    except Exception as e:
        None

    repo.git.add("--all")
    date = datetime.datetime.now()
    commit = "Commit add " + pagename + " " + str(date)

    try:
        repo.git.commit('-m', commit)
        app.logger.info("there was a new commit: " + commit)
    except Exception as e:
        app.logger.info("nothing commit: " + str(e))


@app.route('/<path:file_page>', methods=['POST', 'GET'])
def file_page(file_page):
    if request.method == 'POST':
        return search()
    else:
        html = ""
        mod = ""
        folder = ""
        try:
            filename = os.path.join(WIKI_DATA, file_page + ".md")
            # latex = pypandoc.convert_file("wiki/" + file_page + ".md", "tex", format="md")
            # html = pypandoc.convert_text(latex,"html5",format='tex', extra_args=["--mathjax"])
            html = pypandoc.convert_file(filename, "html5",
                                         format='md', extra_args=["--mathjax"], filters=['pandoc-xnos'])
            mod = "Last modified: %s" % time.ctime(os.path.getmtime(filename))
            folder = file_page.split("/")
            file_page = folder[-1:][0]
            folder = folder[:-1]
            folder = "/".join(folder)
            app.logger.info("showing html page of " + file_page)
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
        app.logger.info("homepage displaying")
        try:
            html = pypandoc.convert_file(
                os.path.join(WIKI_DATA, HOMEPAGE), "html5", format='md', extra_args=["--mathjax"],
                filters=['pandoc-xnos'])

        except Exception as a:
            app.logger.error(a)

        gitcom()
        return render_template('index.html', homepage=html, system=SYSTEM_SETTINGS)


@app.route('/add_new', methods=['POST', 'GET'])
def add_new():
    if request.method == 'POST':
        page_name = fetch_page_name()
        save(page_name)

        return redirect(url_for("file_page", file_page=page_name))
    else:
        return render_template('new.html', upload_path=IMAGES_ROUTE, system=SYSTEM_SETTINGS)


@app.route('/edit/homepage', methods=['POST', 'GET'])
def edit_homepage():
    if request.method == 'POST':
        page_name = fetch_page_name()
        save(page_name)

        return redirect(url_for("file_page", file_page=page_name))
    else:
        with open(os.path.join(WIKI_DATA, HOMEPAGE), 'r', encoding="utf-8") as f:
            content = f.read()
        return render_template("new.html", content=content, title=HOMEPAGE_TITLE, upload_path=IMAGES_ROUTE,
                               system=SYSTEM_SETTINGS)


def fetch_page_name() -> str:
    page_name = request.form['PN']
    if page_name[-4:] == "{id}":
        page_name = f"{page_name[:-4]}{uuid.uuid4().hex}"
    return page_name


@app.route('/remove/<path:page>', methods=['GET'])
def remove(page):
    filename = os.path.join(WIKI_DATA, page + '.md')
    os.remove(filename)

    return redirect("/")


@app.route('/edit/<path:page>', methods=['POST', 'GET'])
def edit(page):
    filename = os.path.join(WIKI_DATA, page + '.md')
    if request.method == 'POST':
        page_name = fetch_page_name()
        if page_name != page:
            os.remove(filename)

        save(page_name)
        return redirect(url_for("file_page", file_page=page_name))
    else:
        with open(filename, 'r', encoding="utf-8") as f:
            content = f.read()
        return render_template("new.html", content=content, title=page, upload_path=IMAGES_ROUTE,
                               system=SYSTEM_SETTINGS)


@app.route('/' + IMAGES_ROUTE, methods=['POST', 'DELETE'])
def upload_file():
    app.logger.info("uploading image...")
    # Upload image when POST
    if request.method == "POST":
        file_names = []
        for key in request.files:
            file = request.files[key]
            filename = secure_filename(file.filename)
            # bug found by cat-0
            while filename in os.listdir(os.path.join(WIKI_DATA, IMAGES_ROUTE)):
                app.logger.info(
                    "There is a duplicate, solving this by extending the filename...")
                filename, file_extension = os.path.splitext(filename)
                filename = filename + str(randint(1, 9999999)) + file_extension

            file_names.append(filename)
            try:
                app.logger.info("Saving " + filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            except Exception as e:
                app.logger.error("error while saving image: " + str(e))
        return filename

    # DELETE when DELETE
    if request.method == "DELETE":
        # request data is in format "b'nameoffile.png" decode by utf-8
        filename = request.data.decode("utf-8")
        try:
            app.logger.info("removing " + str(filename))
            os.remove((os.path.join(app.config['UPLOAD_FOLDER'], filename)))
        except:
            app.logger.error("Could not remove " + str(filename))
        return 'OK'


@app.route('/' + IMAGES_ROUTE + '/<path:filename>')
def display_image(filename):
    # print('display_image filename: ' + filename)
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=False)


@app.route('/toggle-darktheme/', methods=['GET'])
def toggle_darktheme():
    SYSTEM_SETTINGS['darktheme'] = not SYSTEM_SETTINGS['darktheme']
    return index()

@app.route('/toggle-sorting/', methods=['GET'])
def toggle_sort():
    SYSTEM_SETTINGS['listsortMTime'] = not SYSTEM_SETTINGS['listsortMTime']
    return redirect("/list")


logging.basicConfig(filename='wikmd.log', level=logging.INFO)

if __name__ == '__main__':
    gitcom()
    app.run(debug=True, host="0.0.0.0")
