### Overview

This is the official python bindings for the
[GlusterFS](http://www.gluster.org) libgfapi C library interface.

Complete API reference and documentation can be found at
[ReadTheDocs](http://libgfapi-python.readthedocs.io/)

### TODOs

* Submit to pypy to enable installing using pip
* Add support for py3
* Implement async I/O APIs
* Implement file locking APIs
* Implement os.scandir() like API that leverages d\_type
* Improve Volume.walk() by leveraging scandir.
* Test and allow protocols other than TCP such as rdma and socket.

Please follow the [Developer Guide](doc/markdown/dev_guide.md) to contribute code.
