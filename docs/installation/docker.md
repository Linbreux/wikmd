---
layout: default
title: Docker installation
parent: Installation
nav_order: 2
---

## Usage

Here are some example snippets to help you get started creating a container.

Pull down [the latest image from Docker Hub](https://hub.docker.com/r/linbreux/wikmd):

```bash
docker pull linbreux/wikmd
```

Or, build the image after cloning the source code itself:

```bash
git clone https://github.com/linbreux/wikmd.git && cd wikmd
docker build -t linbreux/wikmd:latest -f Dockerfile .
```

### docker-compose (recommended, [click here for more info](https://docs.linuxserver.io/general/docker-compose))

```yaml
---
version: "2.1"
services:
  wikmd:
    image: linbreux/wikmd:latest
    container_name: wikmd
    environment:
      - PUID=1000
      - PGID=1000
      - TZ=Europe/Paris
    volumes:
      - /path/to/wiki:/wiki
    ports:
      - 5000:5000
    restart: unless-stopped
```

### docker cli ([click here for more info](https://docs.docker.com/engine/reference/commandline/cli/))

```bash
docker run -d \
  --name wikmd \
  -e TZ=Europe/Paris \
  -e PUID=1000 \
  -e PGID=1000 \
  -e WIKMD_LOGGING=1 `#optional` \
  -p 5000:5000 \
  -v /path/to/wiki:/wiki \
  --restart unless-stopped \
  linbreux/wikmd:latest
```

## Parameters

Container images are configured using parameters passed at runtime (such as those above). These parameters are separated by a colon and indicate `<external>:<internal>` respectively. For example, `-p 5000:5000` would expose port `5000` from inside the container to be accessible from the host's IP on port `5000` outside the container.

| Parameter                 | Function                                  |
|:--------------------------|-------------------------------------------|
| `-p 5000`                 | Port for wikmd webinterface.              |
| `-e PUID=1000`            | for UserID - see below for explanation    |
| `-e PGID=1000`            | for GroupID - see below for explanation   |
| `-e TZ=Europe/Paris`      | Specify a timezone to use EG Europe/Paris |
| `-e HOMEPAGE=homepage.md` | Specify the file to use as a homepage     |
| `-e HOMEPAGE_TITLE=title` | Specify the homepage's title              |
| `-e WIKMD_LOGGING=1`      | Enable/disable file logging               |
| `-v /wiki`                | Path to the file-based wiki.              |

## User / Group Identifiers

When using volumes (`-v` flags) permissions issues can arise between the host OS and the container, we avoid this issue by allowing you to specify the user `PUID` and group `PGID`.

Ensure any volume directories on the host are owned by the same user you specify and any permissions issues will vanish like magic.

In this instance `PUID=1000` and `PGID=1000`, to find yours use `id user` as below:

```bash
  $ id username
    uid=1000(dockeruser) gid=1000(dockergroup) groups=1000(dockergroup)
```

## Support Info

* Shell access whilst the container is running: `docker exec -it wikmd /bin/bash`
* To monitor the logs of the container in realtime: `docker logs -f wikmd`

