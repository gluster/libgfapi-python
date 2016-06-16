Installation
============

Install glusterfs:

.. code-block:: console

    $ yum install glusterfs-api

Install libgfapi-python from source:

.. code-block:: console

   $ git clone https://review.gluster.org/libgfapi-python
   $ cd libgfapi-python
   $ sudo python setup.py install

Mount GlusterFS volume as non-root user
---------------------------------------

One can follow the following steps to allow a non-root user to virtual mount
a GlusterFS volume over libgfapi. This requires a configuration change which
enables GlusterFS server to accept client connections from non-priveledged
ports.

.. code-block:: console

    # gluster volume set <volname> server.allow-insecure on
    # gluster volume stop <volname>
    # gluster volume start <volname>

Edit `/etc/glusterfs/glusterd.vol` or `/usr/local/etc/glusterfs/glusterd.vol`
and set:

.. code-block:: aconf

    option rpc-auth-allow-insecure on

Restart glusterd service:

.. code-block:: console

    # service glusterd restart

Further, use `chown` and/or `chmod` commands to change permissions on mount
point or required directories to allow non-root access to appropriate users.
