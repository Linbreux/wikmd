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

def save():
    page_name = request.form['PN']
    content = request.form['CT']
    with open('wiki/' + page_name + '.md', 'w') as f:
        f.write(content)
    gitcom()

def search():
    search_term = request.form['ss']
    found = []
    for fil in os.listdir('wiki/'):
        path = os.path.join('wiki/', fil)
        if os.path.isdir(path):
            # skip directories
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
            except:
                None
    return render_template('search.html', zoekterm=found )

def gitcom():
    try:
        repo = git.Repo.init("wiki/")
        repo.git.checkout("-b","master")
    except:
        None
    repo.git.add("--all")
    date = datetime.datetime.now()
    commit = "Commit add " + str(date)
    try:
        repo.git.commit('-m', commit)
    except:
        print("nothing to commit")


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
        except Exception as a:
            app.logger.info(a)
        return render_template('content.html', title=file_page, info=html, modif=mod)


@app.route('/', methods = ['POST','GET'])
def index():
    if request.method=='POST':
      return search()
    else:
        html = ""
        print("homepage displaying")
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
    # Upload image when POST
    if request.method == "POST":
        file_names=[]
        for key in request.files:
            file = request.files[key]
            filename = secure_filename(file.filename)
            for fil in os.listdir('wiki/img'):
                if fil == filename:
                    print("duplicate!")
                    filename, file_extension = os.path.splitext(filename)
                    filename=filename+str(randint(1,9999999))+file_extension

            file_names.append(filename)
            try:
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            except:
                print('save fail ')
        return filename

    # DELETE when DELETE
    if request.method =="DELETE":
        # request data is in format "b'nameoffile.png" decode by utf-8
        filename = request.data.decode("utf-8")
        print(str(filename))
        try:
            os.remove((os.path.join(app.config['UPLOAD_FOLDER'], filename)))
        except:
            print("Could not remove")
        return 'OK'

@app.route('/img/<path:filename>')
def display_image(filename):
    #print('display_image filename: ' + filename)
    return send_from_directory(UPLOAD_FOLDER,filename,as_attachment=False)

if __name__ == '__main__':
    gitcom()
    app.run(debug=False, host="0.0.0.0")


