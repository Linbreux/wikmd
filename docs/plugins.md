---
layout: default
title: Plugins
nav_order: 10
---

# Plugins

The plugin system is still in **beta** for now.

## Supported Plugins

The plugins are used to extend the functionality of the wiki. Most of them are accessible through the use of `tags`.
For now there are only a few supported.  

- `[[draw]]` Allows you to add an **interactive drawio drawing** to the wiki.  
- `[[info]]`, `[[warning]]`, `[[danger]]`, `[[success]]` Adds a nice **alert message**.
- `[[ page: some-page ]]` Allows to show an other page in the current one.
- `[[swagger link]]` Allows to insert a **swagger** block into the wiki page. Link in annotation should lead 
  to a GET endpoint with .json openapi file. `[[swagger https://petstore3.swagger.io/api/v3/openapi.json]]` 
  can be used as an example

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

#### process_html(md: str) -> str *optional*

This method will be called before showing the html page. The returned string is the content of the html file that will be shown.

#### communicate_plugin(request) -> str *optional*

The parameter `request` is the `POST` request thats returned by `/plug_com` (plugin communication).
