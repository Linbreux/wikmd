import os
import re

WIKI_DATA = os.getenv('WIKI_DATA', "wiki")
IMAGES_ROUTE = os.getenv('IMAGES_ROUTE', 'img')
HOMEPAGE_TITLE = os.getenv('HOMEPAGE_TITLE', "homepage")
HOMEPAGE = os.getenv('HOMEPAGE', "homepage.md")

def extend_ids(links):
    for link in links:
        for l in link["links"]:
            for i in links:
                if i["pagename"]==l["filename"]:
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
                "links":[],
                }
            id += 1
            if os.path.join(WIKI_DATA, '.git') in str(path):
                # We don't want to search there
                continue
            if os.path.join(WIKI_DATA, IMAGES_ROUTE) in str(path):
                # Nothing interesting there too
                continue
            with open(root + '/' + item, encoding="utf8") as f:
                fin = f.read()
                #print("--------------------")
                #print("filename: ", pagename)
                try:
                    for match in re.finditer(pattern,fin):
                        description, url = match.groups()
                        # only show files that are in the wiki. Not external sites.
                        if (url+".md") in files:
                            #print("file: ", url)
                            info = {
                                "filename": url,
                            }
                            value["links"].append(info)
                            
                except Exception as e:
                    print("error: " ,e)
                
            links.append(value)
    links = extend_ids(links)
    return links
