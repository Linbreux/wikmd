import os
import re
from urllib.parse import unquote

WIKI_DATA = os.getenv('WIKI_DATA', "wiki")
IMAGES_ROUTE = os.getenv('IMAGES_ROUTE', 'img')
HOMEPAGE_TITLE = os.getenv('HOMEPAGE_TITLE', "homepage")
HOMEPAGE = os.getenv('HOMEPAGE', "homepage.md")

def extend_ids(links):
    for link in links:
        for l in link["links"]:
            for i in links:
                print(i["path"] + " : " + l["filename"])
                if i["path"]==l["filename"]:
                    l["id"] = i["id"]
    
    return links

def find_links():
    links = []
    # regex for links (excluding images)
    pattern = r'[^!]\[(.+?)\]\((.+?)\)'
    id = 1
    # walk trough all files
    for root, subfolder, files in os.walk(WIKI_DATA):
        for item in files:
            pagename = item.split(".")[0]
            path = os.path.join(root, item)
            value = {
                "id": id,
                "pagename":pagename,
                "path":path[len(WIKI_DATA)+1:-len(".md")],
                "weight": 0,
                "links":[],
                }
            id += 1
            if os.path.join(WIKI_DATA, '.git') in str(path):
                # We don't want to search there
                continue
            if os.path.join(WIKI_DATA, IMAGES_ROUTE) in str(path):
                # Nothing interesting there too
                continue
            with open(root + '/' + item, encoding="utf8", errors='ignore') as f:
                fin = f.read()
                print("--------------------")
                print("filename: ", pagename)
                try:
                    for match in re.finditer(pattern,fin):
                        description, url = match.groups()
                        # only show files that are in the wiki. Not external sites.
                        if url.startswith("/"):
                            url = url[1:]
                        url = unquote(url)
                        if os.path.exists(WIKI_DATA+"/"+url+".md"):
                            info = {
                                "filename": url,
                            }
                            value["links"].append(info)
                            print(url)
                            
                except Exception as e:
                    print("error: " ,e)
                
            links.append(value)
    links = extend_ids(links)
    return links
