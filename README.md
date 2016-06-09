### Overview

This is the official python bindings for the
[GlusterFS](http://www.gluster.org) libgfapi C library interface.

Complete API reference and documentation can be found at
[ReadTheDocs](http://libgfapi-python.readthedocs.io/)

### Installation

```
$ git clone https://review.gluster.org/libgfapi-python
$ cd libgfapi-python
$ sudo python setup.py install
```

### Example Usage

```python
from gluster import gfapi

# Create virtual mount
volume = gfapi.Volume('10.7.1.99', 'datavolume')
volume.mount()

# Create directory
volume.mkdir('dir1', 0755)

# List directories
volume.listdir('/')

# Create new file and write to it
with volume.fopen('somefile.txt', 'w+') as f:
    f.write("Winter is coming.")

# Open and read file
with volume.fopen('somefile.txt', 'r') as f:
  print f.read()

# Delete file
volume.unlink('somefile.txt')

# Unmount the volume
volume.unmount()
```

### TODOs

* Submit to pypy to enable installing using pip
* Add support for py3
* Implement async I/O APIs
* Implement file locking APIs
* Implement os.scandir() like API that leverages d\_type
* Improve Volume.walk() by leveraging scandir.
* Test and allow protocols other than TCP such as rdma and socket.

Please follow the [Developer Guide](doc/markdown/dev_guide.md) to contribute code.
