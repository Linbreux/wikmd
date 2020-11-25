from flask import Flask, render_template, request,redirect, url_for
import datetime
import time
import git
import pypandoc
import markdown
import os
import re

app = Flask(__name__)

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
            latex = pypandoc.convert_file("wiki/" + file_page + ".md", "tex", format="md")
            html = pypandoc.convert_text(latex,"html5",format='tex', extra_args=["--mathjax"])
            #html = pypandoc.convert_file("wiki/"+ file_page +".md","html5",format='md', extra_args=["--mathjax"])
            mod = "Last modified: %s" % time.ctime(os.path.getmtime("wiki/"+file_page + ".md"))
        except:
            None
        return render_template('content.html', title=file_page, info=html, modif=mod)


@app.route('/', methods = ['POST','GET'])
def index():
    if request.method=='POST':
      return search()
    else:
        html = ""
        try:
            latex = pypandoc.convert_file("wiki/homepage.md", "tex", format="md")
            html = pypandoc.convert_text(latex,"html5",format='tex', extra_args=["--mathjax"])
            #tml = pypandoc.convert_file("wiki/homepage.md","html5", extra_args=["--mathjax"])
        except:
            None
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


if __name__ == '__main__':
    gitcom()
    app.run()


