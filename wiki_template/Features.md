---
title: Features
author: Linbreux
---
<!--Not used-->

# Footnotes
```
Here is a footnote reference,[^1] and another.

[^1]: Here is the footnote.
```
Here is a footnote reference,[^1] and another.

[^1]: Here is the footnote.

```
Here is an inline note.^[Inlines notes are easier to write, since
you don't have to pick an identifier and move down to type the
note.]
```

Here is an inline note.^[Inlines notes are easier to write, since
you don't have to pick an identifier and move down to type the
note.]

```
(@good)  This is a good example.

As (@good) illustrates, ...

```

(@good)  This is a good example.

As (@good) illustrates, ...

# Split lists

```
1.  one
2.  two
3.  three

<!-- -->

1.  uno
2.  dos
3.  tres
```
1.  one
2.  two
3.  three


<!-- -->

1.  uno
2.  dos
3.  tres


## Change image size
```
![](https://i.ibb.co/Dzp0SfC/download.jpg){width="50%"}
```
![](https://i.ibb.co/Dzp0SfC/download.jpg){width="50%"}

## References

For references we use [pandoc-xnos](https://github.com/tomduck/pandoc-xnos)

### Images

```
![This is a landscape](https://i.ibb.co/Dzp0SfC/download.jpg){#fig:id width="50%"}

As show in @fig:id theire is a nice landscape
```
![This is a landscape](https://i.ibb.co/Dzp0SfC/download.jpg){#fig:landscape width="50%"}


As show in @fig:landscape theire is a nice landscape


## Math
```
$y = mx + b$ {#eq:id}

This is visible in @eq:id
```
$y = mx + b$ {#eq:id}

This is visible in @eq:id

## Etc

This is also possible for tables and sections. Same princip but with

```
{#tbl:id} (for tables)
{#sec:2} (for sections)
```

# Pandoc

All default pandoc features are supported with the extend of mathjax and pandoc-xnos.
![caption](/img/3a2ce07d2109eb82f779f71748be8990.webp)
![caption](/img/pixil-frame-07165101.png)