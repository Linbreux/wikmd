---
layout: default
title: Environment variables
nav_order: 5
---
# Environment variables

You can change static locations using Environment variables. Using (in linux):
```
export <env>=<value or path>
```

## Homepage

The homepage is defaulted to the "homepage.md" file. If you want to use a different file, 
you can specify the file to use for the homepage with the environment variable `HOMEPAGE` as well as the title with `HOMEPAGE_TITLE`.


```
export HOMEPAGE=<location>
export HOMEPAGE_TITLE=<title>
```

## Custom data path

Usually, wikmd looks for content in the subfolder `wiki`. In case you want to store your wiki data somewhere else, you can set a custom data path via the environment variable `WIKI_DATA`:

```
export WIKI_DATA="~/.wikidata"
```

## Custom picture upload

It's possible to add a custom picture upload path. This is done by adding a `IMAGE_ROUTE` environment variable.

```
export IMAGES_ROUTE="media/pictures"
```

