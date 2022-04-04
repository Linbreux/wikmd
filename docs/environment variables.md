---
layout: default
title: Configuration with environment variables
nav_order: 5
---
# Configuration with environment variables

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

You can change the host and port value by respectively changing the `WIKMD_HOST` and `WIKMD_PORT` variable.

```
export WIKMD_HOST=0.0.0.0
export WIKMD_PORT=80
```


## Custom data path

Usually, wikmd looks for content in the subfolder `wiki`. In case you want to store your wiki data somewhere else, you 
can set a custom data path via the environment variable `WIKI_DIRECTORY`:

```
export WIKI_DIRECTORY="~/.wikidata"
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

## Enable synchronization with remote repo

You could specify if you want to synchronize the wiki with your personal remote git repo. 

To do this, set the environment variable `SYNC_WITH_REMOTE` to `1`.

`Default = 0`

```
export SYNCH_WITH_REMOTE=1
```

Also set the environment variable `REMOTE_URL` to your remote repo URL. 

`Default = ""`

```
export REMOTE_URL="https://github.com/user/wiki_repo.git"
```

## Custom git user and email

If you want to use custom git user and email, set the environment variables `GIT_USER` and `GIT_EMAIL`.

The default user is `wikmd` and the email is `wikmd@no-mail.com`.

```
export GIT_USER="your_user"
export GIT_EMAIL="your_email@domain.com"
```

## Custom main branch name

You can specify a custom name for the main branch of the wiki repo setting the `MAIN_BRANCH_NAME` environment variable.
The default value is `main`.

```
export MAIN_BRANCH_NAME="master"
```