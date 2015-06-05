# Overview

Python bindings for the [GlusterFS](http://www.gluster.org) libgfapi interface

# Installation

1) Clone the git repo

```
$ git clone https://review.gluster.org/libgfapi-python
$ cd libgfapi-python
```

2) Run the setup script

```
$ sudo python setup.py install
```
# Usage

```python
from gluster import gfapi
import os

## Create virtual mount
volume = gfapi.Volume(....)
volume.mount()

## Create a new directory
volume.mkdir('newdir', 0755)

## Create a new directory recursively
volume.makedirs('/somedir/dir',0755)

## Delete a directory
volume.rmdir('/somedir/dir')

## Create a file from a string using fopen.  w+: open file for reading and writing
with volume.fopen('somefile.txt', 'w+') as fd:
    fd.write("shadowfax")

## Read a file.  r: open file for only reading
with volume.fopen('somefile.txt', 'r') as fd:
  print fd.read()

## Write to an existing file. a+:  open a file for reading and appending
with volume.fopen('somefile.txt','a+') as fd:
  fd.write("\n some new line in our file")

## Delete a file
volume.unlink('somefile.txt')

## Unmount a volume
volume.unmount()

```
# Development

* [Developer Guide](doc/markdown/dev_guide.md)
