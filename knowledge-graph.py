import os
import re

WIKI_DATA = os.getenv('WIKI_DATA', "wiki")
IMAGES_ROUTE = os.getenv('IMAGES_ROUTE', 'img')
HOMEPAGE_TITLE = os.getenv('HOMEPAGE_TITLE', "homepage")
HOMEPAGE = os.getenv('HOMEPAGE', "homepage.md")

allFiles = []

def find_links():
    # regex for links (excluding images)
    pattern = r'[^!]\[(.+?)\]\((.+?)\)'
    # walk trough all files
    for root, subfolder, files in os.walk(WIKI_DATA):
        for item in files:
            path = os.path.join(root, item)
            if os.path.join(WIKI_DATA, '.git') in str(path):
                # We don't want to search there
                continue
            if os.path.join(WIKI_DATA, IMAGES_ROUTE) in str(path):
                # Nothing interesting there too
                continue
            with open(root + '/' + item, encoding="utf8") as f:
                fin = f.read()
                print("--------------------")
                print("filename: ", item)
                try:
                    for match in re.finditer(pattern,fin):
                        description, url = match.groups()
                        # only show files that are in the wiki. Not external sites.
                        if (url+".md") in files:
                            print("found!")
                            print("url: ", url)
                except Exception as e:
                    print("error: " ,e)

find_links()
# find links in every file

# put the destination in the files