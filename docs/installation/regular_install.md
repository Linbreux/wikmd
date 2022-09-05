---
layout: default
title: Regular installation
parent: Installation
nav_order: 1
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

Create a virtual env and activate it(optional)
```
virtualenv venv
source venv/bin/activate
```
Install requirements
```
pip install -r requirements.txt
```
Run the wiki
```
export FLASK_APP=wiki.py
flask run --host=0.0.0.0
```
or 
```
python wiki.py
```

Now visit localhost:5000 and you will see the wiki. With the 0.0.0.0. option it will show up everywhere on the network.

If there are problems feel free to open an github issue you could post the output of wikmd.log to it.

## Linux

Maybe you need to install pandoc on your system before this works.
```
sudo apt-get update && sudo apt-get install pandoc
```
You may experience an issue when running `pip install -r requirements.txt` where you receive the following error:
```
  psutil/_psutil_common.c:9:10: fatal error: Python.h: No such file or directory
      9 | #include <Python.h>
        |          ^~~~~~~~~~
  compilation terminated.
  error: command '/usr/lib64/ccache/gcc' failed with exit code 1
  ----------------------------------------
  ERROR: Failed building wheel for psutil
 ```

You can fix this by installing the python 3 dev package.

Ubuntu, Debian:
```
sudo apt-get install python3-dev
```
Fedora:
```
sudo dnf install python3-devel
```
For other distros, you can search up `[distro] install python 3 dev`.

You may experience an error when running `pip install -r requirements.txt` where it asks you to install `gcc python3-dev`. Example:
```
  unable to execute 'x86_64-linux-gnu-gcc': No such file or directory
  C compiler or Python headers are not installed on this system. Try to run:
  sudo apt-get install gcc python3-dev
  error: command 'x86_64-linux-gnu-gcc' failed with exit status 1
  ----------------------------------------
  ERROR: Failed building wheel for psutil
```

Simply install `gcc python3-dev`.


### Runing the wiki as a service

You can run the wiki as a service. Doing this will allow the wiki to boot at startup.

First, create the following file as `wiki.service` in `/etc/systemd/system`, and replace the placeholder entries.

```
[Unit]
Description=Wikmd
After=network.target

[Service]
User=<user>
WorkingDirectory=<path to the wiki>
Environment=FLASK_APP=wiki.py
ExecStart=<path to the wiki>/env/bin/python3 wiki.py
Restart=always

[Install]
WantedBy=multi-user.target

```

Run the following commands to enable and start the serivce

```
systemctl daemon-reload
systemctl enable wiki.service
systemctl start wiki.service
```

If the wiki opens, but does not display any text, run `systemctl status wiki.service`.

You may see the following error:
```
ERROR in wiki: Conversion to HTML failed >>> Pandoc died with exitcode "83" during conversion: b'Error running filter pandoc-xnos:\nCould not find executable pandoc-xnos\n'
```
To fix, run the following commands:
```
sudo su
cd ~
umask 022
pip install -r <path to the wiki>/requirements.txt
```
This will install the python packages system-wide, allowing the wiki service to access it.

Run `systemctl restart wiki.service` and it should be working.


## Windows

You should install [pandoc](https://pandoc.org/installing.html) on your windows system. Now you should be able to start
the server.
```
python wiki.py
```
If the content of the markdown files are not visible you should add the `pandoc-xnos` location to your path variable. Info about [Environment variables](https://www.computerhope.com/issues/ch000549.htm).
```
pip show --files pandoc-xnos
# look for "location" in the output
# example: C:\users\<user>\appdata\local\packages\pythonsoftwarefoundation.python.3.x\localcache\local-packages\python38\site-packages
# change "site-packages" to "Scripts"
# example: C:\Users\<user>\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.x\LocalCache\local-packages\Python38\Scripts
# open your Environment variables and add the changed line to the path
SET PATH=%PATH%;C:\Users\<user>\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.x\LocalCache\local-packages\Python38\Scripts
```
