---
layout: default
title: Development
parent: Installation
nav_order: 12
---

# Regular installation
! It's tested on windows and linux based systems.
! Runs on flask server

Clone the repository
```
git clone https://github.com/Linbreux/wikmd.git
```

cd in wikmd
```
cd wikmd
```

Create a virtual env and activate it (optional, but highly recommended)
```
virtualenv venv
source venv/bin/activate
```

Install it in [development mode aka editable install](https://setuptools.pypa.io/en/latest/userguide/development_mode.html)  
```
bash: python -m pip install --editable .[dev]
zsh: python -m pip install --editable '.[dev]'
```

Run the wiki
```
python -m wikmd.wiki
```

## Adding a plugin

Add the plugin to the `plugins` folder and add the `foldername` to section `plugins` in the `wikmd-config.yaml` file.

## Construction

Plugins are listed inside the `plugins` folder. 

```
plugins/
├─ plugin1/
│  ├─ plugin1.py
│  ├─ ...
├─ plugin2/
│  ├─ plugin2.py
│  ├─ ...
├─ .../
```

The name of the plugin should be the same as the folder. Inside the python file should be a `Plugin` class, this is the class that will be loaded into the python program.  

### Methods

For now there are only a few supported methods that can be added to the `Plugin` class. Feel free to extend them!

#### get_plugin_name() -> str *required*

This method should return the name of the plugin.

#### process_md(md: str) -> str *optional*

This method will be called before saving the markdown file. The returned string is the content of the saved file.

#### process_md_before_html_convert(md: str) -> str *optional*

This method will be called before converting markdown file into html and after saving the markdown file. All changes 
made in this method are not going to be saved in .md file, but will be shown on the html page.

#### process_html(md: str) -> str *optional*

This method will be called before showing the html page. The returned string is the content of the html file that will be shown.

#### communicate_plugin(request) -> str *optional*

The parameter `request` is the `POST` request thats returned by `/plug_com` (plugin communication).

