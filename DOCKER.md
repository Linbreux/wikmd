# wikmd Docker image

[wikmd](https://github.com/Linbreux/wikmd) is a file based wiki that uses markdown.

## Usage

Here are some example snippets to help you get started creating a container.

Build the image,

```bash
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
      - HOMEPAGE=homepage.md #optional
      - HOMEPAGE_TITLE=homepage.md #optional
      - WIKMD_LOGGING=1 #optional
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
  -e HOMEPAGE=homepage.md `#optional` \
  -e HOMEPAGE_TITLE=homepage.md `#optional` \
  -e WIKMD_LOGGING=1 `#optional` \
  -p 5000:5000 \
  -v /path/to/wiki:/wiki \
  --restart unless-stopped \
  linbreux/wikmd:latest
```

## Parameters

Container images are configured using parameters passed at runtime (such as those above). These parameters are separated by a colon and indicate `<external>:<internal>` respectively. For example, `-p 5000:5000` would expose port `5000` from inside the container to be accessible from the host's IP on port `5000` outside the container.

| Parameter | Function |
| :----: | --- |
| `-p 5000` | Port for wikmd webinterface. |
| `-e PUID=1000` | for UserID - see below for explanation |
| `-e PGID=1000` | for GroupID - see below for explanation |
| `-e TZ=Europe/Paris` | Specify a timezone to use EG Europe/Paris |
| `-e HOMEPAGE=homepage.md` | Specify the file to use as a homepage |
| `-e HOMEPAGE_TITLE=title` | Specify the homepage's title |
| `-e WIKMD_LOGGING=1` | Enable/disable file logging |
| `-v /wiki` | Path to the file-based wiki. |

## User / Group Identifiers

When using volumes (`-v` flags) permissions issues can arise between the host OS and the container, we avoid this issue by allowing you to specify the user `PUID` and group `PGID`.

Ensure any volume directories on the host are owned by the same user you specify and any permissions issues will vanish like magic.

In this instance `PUID=1000` and `PGID=1000`, to find yours use `id user` as below:

```bash
  $ id username
    uid=1000(dockeruser) gid=1000(dockergroup) groups=1000(dockergroup)
```

## Remote Git Repo

Pass the following environment parameters:

```bash
  -e SYNC_WITH_REMOTE=1 \
  -e REMOTE_URL="<ssh url of the remote git repo>"
```

Along with the parameters you will need four more files. 

1. SSH config file
    ```
      Host <hostname or remote repo>
        User git
        IdentityFile /root/.ssh/id_ed25519
        IdentitiesOnly yes                 # Optional to make sure you don't 
                                            get too many authentication failure
    ```
2. SSH key file uploaded to your remote
3. SSH Public key
4. SSH Known Hosts file

    As you wont be able to add the remote host's to the docker's known hosts 
    file you have to provide the file

    ```bash
      ssh-keyscan -t ed25519 <host url> >> known_hosts
    ```

The files need to be owned by root not by the UID and GID passed by you. Save 
the files in a folder *ssh* along with the *wiki* folder and pass both the folders as such.

```bash
    -v wiki:/wiki \
    -v ssh:/root/.ssh
```

## Support Info

* Shell access whilst the container is running: `docker exec -it wikmd /bin/bash`
* To monitor the logs of the container in realtime: `docker logs -f wikmd`
