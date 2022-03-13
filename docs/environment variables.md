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

## Custom port and host

You can change the host and port value by respectively changing the `WIKI_HOST` and `WIKI_PORT` variable.

```
export WIKI_HOST=0.0.0.0
export WIKI_PORT=80
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

## Change logging file

In case you need to rename the log file you can use `WIKMD_LOGGING_FILE`.

`Default = wikmd.log`


```
export WIKMD_LOGGING_FILE=custom_log.log
```

## Disable logging

You could optionaly choose to disable logging by setting the environment variable `WIKMD_LOGGING` to `0`.

`Default = 1`

```
export WIKMD_LOGGING=0
```
