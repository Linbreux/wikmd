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
