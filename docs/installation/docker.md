---
layout: default
title: Docker
parent: Installation
nav_order: 2
---

# Docker install

## Build docker
```
docker build -t wiki-md:latest .
```
## Run Docker

You may need to create wiki/data in your homefolder or you can change it if you want another place.

```
sudo docker run -d -p 5000:5000 -v ~/wiki/data:/app/wiki wiki-md
```
If you would like to have the default files inside your instance, you should copy the wiki files to ```~/wiki/data``` in this case.
Also highly recommended is to create a folder ```img``` inside ```wiki/```

```
cp wikmd/wiki/* ~/wiki/data/
mkdir ~/wiki/img
```
