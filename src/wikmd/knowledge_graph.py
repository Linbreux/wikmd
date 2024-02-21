import os
import re
from urllib.parse import unquote

from wikmd.config import WikmdConfig

cfg = WikmdConfig()


def extend_ids(links):
    for link in links:
        for l in link["links"]:
            for i in links:
                if i["path"] == l["filename"]:
                    l["id"] = i["id"]
    return links


def find_links():
    links = []
    # regex for links (excluding images)
    pattern = r'[^!]\[(.+?)\]\((.+?)\)'
    id = 1
    # walk through all files
    for root, subfolder, files in os.walk(cfg.wiki_directory):
        for item in files:
            pagename, _ = os.path.splitext(item)
            path = os.path.join(root, item)
            value = {
                "id": id,
                "pagename": pagename,
                "path": path[len(cfg.wiki_directory)+1:-len(".md")],
                "weight": 0,
                "links": [],
            }
            id += 1
            if os.path.join(cfg.wiki_directory, '.git') in str(path):
                # We don't want to search there
                continue
            if os.path.join(cfg.wiki_directory, cfg.images_route) in str(path):
                # Nothing interesting there too
                continue
            with open(os.path.join(root, item), encoding="utf8", errors='ignore') as f:
                fin = f.read()
                print("--------------------")
                print("filename: ", pagename)
                try:
                    for match in re.finditer(pattern, fin):
                        description, url = match.groups()
                        # only show files that are in the wiki. Not external sites.
                        if url.startswith("/"):
                            url = url[1:]
                        url = unquote(url)
                        if os.path.exists(os.path.join(cfg.wiki_directory, f"{url}.md")):
                            info = {
                                "filename": url,
                            }
                            value["links"].append(info)
                            print(url)
                            
                except Exception as e:
                    print("error: ", e)
                
            links.append(value)
    links = extend_ids(links)
    return links
