libgfapi-python
===============

This is the official python bindings for `GlusterFS <http://www.gluster.org>`_
libgfapi C library interface.

Installation
------------

Install from source:

.. code-block:: console

   $ git clone https://review.gluster.org/libgfapi-python
   $ cd libgfapi-python
   $ sudo python setup.py install

Example Usage
-------------

.. code-block:: python

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


API Reference
-------------

.. toctree::
   :maxdepth: 2

   api-reference
