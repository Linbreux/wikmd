import os
import datetime
import time
import re
import logging
import uuid
import pypandoc
import knowledge_graph

from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename
from random import randint
from git import Repo, InvalidGitRepositoryError, GitCommandError, NoSuchPathError

from config import get_config


CONFIG = get_config()

UPLOAD_FOLDER = CONFIG["wiki_directory"] + '/' + CONFIG["images_route"]
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

SYSTEM_SETTINGS = {
    "darktheme": False,
    "listsortMTime": False,
}


app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

logger = logging.getLogger('werkzeug')
logger.setLevel(logging.ERROR)


def is_git_repo(path: str) -> bool:
    """
    Function that determines if the given path is a git repo.
    :return: True if is a repo, False otherwise.
    """
    try:
        _ = Repo(path).git_dir
        return True
    except (InvalidGitRepositoryError, NoSuchPathError):
        return False


def git_repo_init() -> Repo:
    """
    Function that initializes the git repo of the Wiki.
    The repo can be local or remote (it will be cloned), according to the config setting.
    :return: initialized repo
    """
    git_repo = None
    if is_git_repo(CONFIG["wiki_directory"]):
        git_repo = git_get_existing_repo()
        print("existing")
    else:
        if CONFIG["remote_url"]:  # if a remote url has been set, clone the repo
            git_repo = git_clone_remote()
            print("remote clone")
        else:
            git_repo = git_new_local()
            print("new local")

    # Configure git username and email
    if git_repo:  # if the repo has been initialized
        git_repo.config_writer().set_value("user", "name", "wikmd").release()
        git_repo.config_writer().set_value("user", "email", "wikmd@no-mail.com").release()

    return git_repo


def git_get_existing_repo() -> Repo:
    """
    Function that gets the existing repo in the wiki_directory.
    Could be local or remote.
    :return: Repo
    """
    git_repo = None
    try:
        app.logger.info("Initializing existing repo ...")
        git_repo = Repo(CONFIG["wiki_directory"])
        git_repo.git.checkout()  # don't specify branch, it could be main or master
    except (InvalidGitRepositoryError, GitCommandError, NoSuchPathError) as e:
        app.logger.error(f"Error during existing git repo initialization: {str(e)}")

    return git_repo


def git_clone_remote() -> Repo:
    """
    Function that clones a remote git repo according to the remote_url and the wiki_directory set in the config.
    :return: Repo
    """
    git_repo = None
    try:
        app.logger.info(f"Cloning {CONFIG['remote_url']} ...")
        git_repo = Repo.clone_from(url=CONFIG["remote_url"], to_path=CONFIG["wiki_directory"])
    except (InvalidGitRepositoryError, GitCommandError, NoSuchPathError) as e:
        app.logger.error(f"Error during remote git repo cloning: {str(e)}")
    return git_repo


def git_new_local() -> Repo:
    """
    Function that inits a new local git repo according to the wiki_directory set in the config.
    :return: Repo
    """
    git_repo = None
    try:
        app.logger.info("Creating a new local git repo ...")
        git_repo = Repo.init(path=CONFIG["wiki_directory"])
        git_repo.git.checkout("-b", "main")  # create a new (-b) main branch
    except (InvalidGitRepositoryError, GitCommandError, NoSuchPathError) as e:
        app.logger.error(f"Error during new local git repo initialization: {str(e)}")
    return git_repo


def git_pull():
    """
    Function that pulls from the remote wiki repo.
    """
    try:
        # git pull
        repo.git.pull()
        app.logger.info(f"Pulled from the repo")
    except Exception as e:
        app.logger.info(f"Error during git pull: {str(e)}")


def git_commit(page_name="", commit_type=""):
    """
    Function that commits changes to the wiki repo.
    :param commit_type: could be 'Add', 'Edit' or 'Remove'.
    :param page_name: name of the page that has been changed.
    """
    try:
        # git add --all
        repo.git.add("--all")
        date = datetime.datetime.now()
        commit_msg = f"{commit_type} page '{page_name}' on {str(date)}"
        # git commit -m
        repo.git.commit('-m', commit_msg)
        app.logger.info(f"New git commit: {commit_msg}")
    except Exception as e:
        app.logger.info(f"Nothing to commit: {str(e)}")


def git_push():
    """
    Function that pushes changes to the remote wiki repo.
    """
    try:
        # git push
        repo.git.push("-u", "origin", "master")
        app.logger.info("Pushed to the repo.")
    except Exception as e:
        app.logger.info(f"Error during git push: {str(e)}")


def git_sync(page_name="", commit_type=""):
    """
    Function that manages the synchronization with a git repo, that could be local or remote.
    If SYNC_WITH_REMOTE is set, it also pull before committing and then pushes changes to the remote repo.
    :param commit_type: could be 'Add', 'Edit' or 'Remove'.
    :param page_name: name of the page that has been changed.
    """
    if CONFIG["sync_with_remote"]:
        git_pull()

    git_commit(page_name=page_name, commit_type=commit_type)

    if CONFIG["sync_with_remote"]:
        git_push()


repo = git_repo_init()


def save(page_name):
    """
    Function that saves a *.md page.
    :param page_name: name of the page
    """
    content = request.form['CT']
    app.logger.info(f"Saving {page_name}")

    try:
        filename = os.path.join(CONFIG["wiki_directory"], page_name + '.md')
        dirname = os.path.dirname(filename)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        with open(filename, 'w') as f:
            f.write(content)
    except Exception as e:
        app.logger.error(f"Error while saving {page_name}: {str(e)}")


def search():
    """
    Function that searches for a term and shows the results.
    """
    search_term = request.form['ss']
    escaped_search_term = re.escape(search_term)
    found = []

    app.logger.info(f"searching for {search_term} ...")

    for root, subfolder, files in os.walk(CONFIG["wiki_directory"]):
        for item in files:
            path = os.path.join(root, item)
            if os.path.join(CONFIG["wiki_directory"], '.git') in str(path):
                # We don't want to search there
                app.logger.debug(f"skipping {path} is git file")
                continue
            if os.path.join(CONFIG["wiki_directory"], CONFIG["images_route"]) in str(path):
                # Nothing interesting there too
                continue
            with open(root + '/' + item, encoding="utf8") as f:
                fin = f.read()
                try:
                    if (re.search(escaped_search_term, root + '/' + item, re.IGNORECASE) or
                            re.search(escaped_search_term, fin, re.IGNORECASE) is not None):
                        # Stripping 'wiki/' part of path before serving as a search result
                        folder = root[len(CONFIG["wiki_directory"] + "/"):]
                        if folder == "":
                            url = os.path.splitext(
                                root[len(CONFIG["wiki_directory"] + "/"):] + "/" + item)[0]
                        else:
                            url = "/" + \
                                  os.path.splitext(
                                      root[len(CONFIG["wiki_directory"] + "/"):] + "/" + item)[0]

                        info = {'doc': item,
                                'url': url,
                                'folder': folder,
                                'folder_url': root[len(CONFIG["wiki_directory"] + "/"):]}
                        found.append(info)
                        app.logger.info(f"found {search_term} in {item}")
                except Exception as e:
                    app.logger.error(f"There was an error: {str(e)}")

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
    app.logger.info("Showing 'all files'")
    for root, subfolder, files in os.walk(os.path.join(CONFIG["wiki_directory"], folderpath)):
        if root[-1] == '/':
            root = root[:-1]
        for item in files:
            path = os.path.join(root, item)
            mtime = os.path.getmtime(os.path.join(root, item))
            if os.path.join(CONFIG["wiki_directory"], '.git') in str(path):
                # We don't want to search there
                app.logger.debug(f"skipping {path}: is git file")
                continue
            if os.path.join(CONFIG["wiki_directory"], CONFIG["images_route"]) in str(path):
                # Nothing interesting there too
                continue

            folder = root[len(CONFIG["wiki_directory"] + "/"):]
            if folder == "":
                if item == CONFIG["homepage"]:
                    continue
                url = os.path.splitext(
                    root[len(CONFIG["wiki_directory"] + "/"):] + "/" + item)[0]
            else:
                url = "/" + \
                    os.path.splitext(
                        root[len(CONFIG["wiki_directory"] + "/"):] + "/" + item)[0]

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
                md_file_path = os.path.join(CONFIG["wiki_directory"], file_page + ".md")
                # latex = pypandoc.convert_file("wiki/" + file_page + ".md", "tex", format="md")
                # html = pypandoc.convert_text(latex,"html5",format='tex', extra_args=["--mathjax"])

                app.logger.info(f"Converting '{md_file_path}' to HTML with pandoc")
                html = pypandoc.convert_file(md_file_path, "html5",
                                             format='md', extra_args=["--mathjax"], filters=['pandoc-xnos'])

                mod = "Last modified: %s" % time.ctime(os.path.getmtime(md_file_path))
                folder = file_page.split("/")
                file_page = folder[-1:][0]
                folder = folder[:-1]
                folder = "/".join(folder)
                app.logger.info(f"Showing HTML page of '{file_page}'")
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
        app.logger.info("Showing HTML page of 'homepage'")
        try:
            app.logger.info(f"Converting 'homepage' to HTML with pandoc")
            html = pypandoc.convert_file(
                os.path.join(CONFIG["wiki_directory"], CONFIG["homepage"]), "html5", format='md', extra_args=["--mathjax"],
                filters=['pandoc-xnos'])

        except Exception as e:
            app.logger.error("Error during 'homepage' to HTML conversion")

        return render_template('index.html', homepage=html, system=SYSTEM_SETTINGS)


@app.route('/add_new', methods=['POST', 'GET'])
def add_new():
    if request.method == 'POST':
        page_name = fetch_page_name()
        save(page_name)
        git_sync(page_name, "Add")

        return redirect(url_for("file_page", file_page=page_name))
    else:
        return render_template('new.html', upload_path=CONFIG["images_route"], system=SYSTEM_SETTINGS)


@app.route('/edit/homepage', methods=['POST', 'GET'])
def edit_homepage():
    if request.method == 'POST':
        page_name = fetch_page_name()
        save(page_name)
        git_sync(page_name, "Edit")

        return redirect(url_for("file_page", file_page=page_name))
    else:
        with open(os.path.join(CONFIG["wiki_directory"], CONFIG["homepage"]), 'r', encoding="utf-8") as f:
            content = f.read()
        return render_template("new.html", content=content, title=CONFIG["homepage_title"], upload_path=CONFIG["images_route"],
                               system=SYSTEM_SETTINGS)


@app.route('/remove/<path:page>', methods=['GET'])
def remove(page):
    filename = os.path.join(CONFIG["wiki_directory"], page + '.md')
    os.remove(filename)
    git_sync(page_name=page, commit_type="Remove")
    return redirect("/")


@app.route('/edit/<path:page>', methods=['POST', 'GET'])
def edit(page):
    filename = os.path.join(CONFIG["wiki_directory"], page + '.md')
    if request.method == 'POST':
        page_name = fetch_page_name()
        if page_name != page:
            os.remove(filename)

        save(page_name)
        git_sync(page_name, "Edit")

        return redirect(url_for("file_page", file_page=page_name))
    else:
        with open(filename, 'r', encoding="utf-8") as f:
            content = f.read()
        return render_template("new.html", content=content, title=page, upload_path=CONFIG["images_route"],
                               system=SYSTEM_SETTINGS)


@app.route('/' + CONFIG["images_route"], methods=['POST', 'DELETE'])
def upload_file():
    app.logger.info("uploading image...")
    # Upload image when POST
    if request.method == "POST":
        file_names = []
        for key in request.files:
            file = request.files[key]
            filename = secure_filename(file.filename)
            # bug found by cat-0
            while filename in os.listdir(os.path.join(CONFIG["wiki_directory"], CONFIG["images_route"])):
                app.logger.info(
                    "There is a duplicate, solving this by extending the filename...")
                filename, file_extension = os.path.splitext(filename)
                filename = filename + str(randint(1, 9999999)) + file_extension

            file_names.append(filename)
            try:
                app.logger.info(f"Saving {filename}")
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            except Exception as e:
                app.logger.error(f"Error while saving image: {str(e)}")
        return filename

    # DELETE when DELETE
    if request.method == "DELETE":
        # request data is in format "b'nameoffile.png" decode by utf-8
        filename = request.data.decode("utf-8")
        try:
            app.logger.info(f"removing {str(filename)}")
            os.remove((os.path.join(app.config['UPLOAD_FOLDER'], filename)))
        except Exception as e:
            app.logger.error(f"Could not remove {str(filename)}")
        return 'OK'


@app.route('/knowledge-graph', methods=['GET'])
def graph():
    global links
    links = knowledge_graph.find_links()
    return render_template("knowledge-graph.html", links=links, system=SYSTEM_SETTINGS)

# Translate id to page path


@app.route('/nav/<path:id>/', methods=['GET'])
def nav_id_to_page(id):
    for i in links:
        if i["id"] == int(id):
            return redirect("/"+i["path"])
    return redirect("/")


@app.route('/' + CONFIG["images_route"] + '/<path:filename>')
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
    if int(CONFIG["wikmd_logging"]) == 1:
        logging.basicConfig(filename=CONFIG["wikmd_logging_file"], level=logging.INFO)

    app.run(debug=True, host=CONFIG["wikmd_host"], port=CONFIG["wikmd_port"])


if __name__ == '__main__':
    run_wiki()


