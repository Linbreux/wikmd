## Git

We use git as a version control system. Everytime you save a file it will commit it to git. You could also use the cli to add and commit files, make sure you are in the "wiki" folder, if you are still in the "wikmd" folder you are using the wrong git folder. 

```
git add . (or the specific file)
git commit -m "your message" (default date of today)
```

or you could just go to the homepage of the wiki, this will do all these automatic.

## How to go to previous file?

cd inside 'wikmd/wiki'

Find the version you would like to revert to.

```
git log -p file.md
```

This will give you a long commit string. Copy the first part of it. (for example b4b580411b)

Modify the file

```
git checkout b4b580411b -- file.md
```

Now reload the homepage or use [git](#git) 
