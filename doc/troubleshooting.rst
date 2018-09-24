Troubleshooting
===============

Mount GlusterFS volume as non-root user (Glusterfs <3.7.3)
----------------------------------------------------------

.. versionchanged:: 3.7.3
    GlusterFS versions prior to version **3.7.3** requires the following
    additional steps to allow non-root users to mount the volume over libgfapi.
    Following these steps is **NOT required** for recent versions i.e >= 3.7.3

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
