from flask import Flask, render_template, request,redirect, url_for, flash, send_from_directory
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

UPLOAD_FOLDER = 'wiki/img'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

def save():
    page_name = request.form['PN']
    content = request.form['CT']
    app.logger.info("saving "+page_name)
    try:
        with open('wiki/' + page_name + '.md', 'w') as f:
            f.write(content)
    except Exception as e:
        app.logger.error("Error while saving: "+str(e))
    gitcom(pagename=page_name)

def search():
    search_term = request.form['ss']
    found = []
    
    app.logger.info("searching for "+search_term +" ...")

    for fil in os.listdir('wiki/'):
        path = os.path.join('wiki/', fil)
        if os.path.isdir(path):
            # skip directories
            app.logger.debug("skipping " + path + " : is dir")
            continue
        if fil == "wiki/images":
            continue
        with open('wiki/' + fil, encoding="utf8") as f:
            fin = f.read()
            try:
                if re.search(search_term,fil, re.IGNORECASE) or re.search(search_term,fin, re.IGNORECASE) != None:
                    info = {'doc': fil,
                            'url': os.path.splitext(fil)[0]}
                    found.append(info)
                    app.logger.info("found "+search_term+ " in "+fil)
            except Exception as e:
                app.logger.error("There was an error: " + str(e)) 

    return render_template('search.html', zoekterm=found )

def gitcom(pagename=""):
    try:
        repo = git.Repo.init("wiki/")
        repo.git.checkout("-b","master")
        repo.config_writer().set_value("user", "name", "wikmd").release()
        repo.config_writer().set_value("user", "email", "wikmd@no-mail.com").release()
        app.logger.info("There doesn't seem to be a repo, creating one...")

    except Exception as e:
        None

    repo.git.add("--all")
    date = datetime.datetime.now()
    commit = "Commit add "+pagename+" " + str(date)

    try:
        repo.git.commit('-m', commit)
        app.logger.info("there was a new commit: " + commit)
    except Exception as e:
        app.logger.info("nothing commit: "+ str(e))


@app.route('/<file_page>', methods = ['POST', 'GET'])
def file_page(file_page):
    if request.method == 'POST':
        return search()
    else:
        html =""
        mod = ""
        try:
            #latex = pypandoc.convert_file("wiki/" + file_page + ".md", "tex", format="md")
            #html = pypandoc.convert_text(latex,"html5",format='tex', extra_args=["--mathjax"])
            html = pypandoc.convert_file("wiki/"+ file_page +".md","html5",format='md', extra_args=["--mathjax"], filters=['pandoc-xnos'])
            mod = "Last modified: %s" % time.ctime(os.path.getmtime("wiki/"+file_page + ".md"))
            app.logger.info("showing html page of " + file_page)
        except Exception as a:
            app.logger.info(a)
        return render_template('content.html', title=file_page, info=html, modif=mod)


@app.route('/', methods = ['POST','GET'])
def index():
    if request.method=='POST':
      return search()
    else:
        html = ""
        app.logger.info("homepage displaying")
        try:
            html = pypandoc.convert_file("wiki/homepage.md","html5",format='md', extra_args=["--mathjax"], filters=['pandoc-xnos'])

        except Exception as a:
            app.logger.error(a)

        gitcom()
        return render_template('index.html', homepage = html)

@app.route('/add_new', methods = ['POST','GET'])
def add_new():
    if request.method=='POST':
        save()

        return redirect(url_for("file_page",file_page = request.form['PN']))
    else:
        return render_template('new.html')

@app.route('/edit/homepage', methods = ['POST','GET'])
def edit_homepage():
    if request.method == 'POST':
        save()

        return redirect(url_for("file_page",file_page = request.form['PN']))
    else:
        with open('wiki/homepage.md', 'r', encoding="utf-8") as f:
            content = f.read()
        return render_template("new.html", content = content, title = "homepage")

@app.route('/edit/<page>', methods = ['POST','GET'])
def edit(page):
    if request.method == 'POST':
        name = request.form['PN']
        if name != page:
            os.remove('wiki/' + page +'.md')

        save()
        return redirect(url_for("file_page",file_page = name))
    else:
        with open('wiki/'+page+'.md', 'r', encoding="utf-8") as f:
            content = f.read()
        return render_template("new.html", content = content, title = page)

@app.route('/img', methods=['POST', 'DELETE'])
def upload_file():
    app.logger.info("uploading image...")
    # Upload image when POST
    if request.method == "POST":
        file_names=[]
        for key in request.files:
            file = request.files[key]
            filename = secure_filename(file.filename)
            #bug found by cat-0
            while filename in os.listdir('wiki/img'):
                app.logger.info("There is a duplicate, solving this by extending the filename...")
                filename, file_extension = os.path.splitext(filename)
                filename=filename+str(randint(1,9999999))+file_extension

            file_names.append(filename)
            try:
                app.logger.info("Saving " + filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            except Exception as e:
                app.logger.error("error while saving image: "+ str(e))
        return filename

    # DELETE when DELETE
    if request.method =="DELETE":
        # request data is in format "b'nameoffile.png" decode by utf-8
        filename = request.data.decode("utf-8")
        try:
            app.logger.info("removing " + str(filename))
            os.remove((os.path.join(app.config['UPLOAD_FOLDER'], filename)))
        except:
            app.logger.error("Could not remove " + str(filename))
        return 'OK'

@app.route('/img/<path:filename>')
def display_image(filename):
    #print('display_image filename: ' + filename)
    return send_from_directory(UPLOAD_FOLDER,filename,as_attachment=False)

logging.basicConfig(filename='wikmd.log',level=logging.INFO)

if __name__ == '__main__':
    gitcom()
    app.run(debug=True, host="0.0.0.0")


