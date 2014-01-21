#Developer Guide

##Development Environment Setup

The workflow for libgfapi-python is largely based upon the [Gluster-Swift Developer Guide][]  and [OpenStack Gerrit Workflow][]. Refer to those documents for setting up a Gerrit account and a complete development environment.

This document focuses on setting up a quick environment for running tox tests (especially the functional tests).

## Required Package Installation
Install and start the required packages on your system to create a GlusterFS volume.
```
yum install gcc python-devel python-setuptools libffi-devel glusterfs \
    glusterfs-server git rpm-build xfsprogs
```

Install the python pip tool by executing the following command:

```
easy_install pip
```

#### Tox and Nose

libgfapi-python uses tox python virtual environment for its unit and functional tests. To install tox type:

```
pip install --upgrade tox nose
```

### Start services

Type the following to start the glusterfs service:

```
service glusterd start
```

Type the following to start the service automatically on system startup:

```
chkconfig glusterd on
```

## Gluster Volume Setup

### Loopback Storage Setup

If you do not have a separate partition, please execute the following instructions to create a disk image as a file:

```
truncate -s 5GB /srv/xfsdisk
mkfs.xfs -i size=512 /srv/xfsdisk
mkdir -p /export/brick
```

Add the following line to `/etc/fstab` to mount the storage automatically on system startup:

```
/srv/xfsdisk /export/brick   xfs   loop,inode64,noatime,nodiratime 0 0
```

Now type the following to mount the storage:

```
mount -a
```

## Create a GlusterFS Volume

You now need to create a GlusterFS volume

```
mkdir /export/brick/b1
gluster volume create test <hostname>:/export/brick/b1
gluster volume start test
```

## Download the Source

The source for libgfapi-python is available in Github. To download type:

```
git clone https://github.com/gluster/libgfapi-python.git
cd libgfapi-python
```

## Running tests

### PEP8

To test that the code adheres to the Python PEP8 specification, please type:

```
tox -e pep8
```

### Unit Tests

Once you have made your changes, you can test the quality of the code by executing the automated unit tests as follows:
```
tox -e ENV
```

where ENV is either py27 for systems with Python 2.7+, or py26 for systems with Python 2.6+.

If new functionality has been added, it is highly recommended that one or more tests be added to the automated unit test suite. Unit tests are available under the test/unit directory.

### Functional tests
The functional tests expects a `test` volume to be created and accessible.

To run the functional tests, please type:

```
tox -e functest
```
####Important Notes:
##### Definining a hostname
GlusterFS does not allow for specifiyng `localhost` as a valid hostname when creating a volume, so `gfshost` was used in the functional tests. If you use a different hostname when creating the gluster volume, be sure to update the functional tests.

##### Stopping services
For the purpose of running this test, stop the `firewalld` service and disable `selinux`.

```
service firewalld stop
```


[OpenStack Gerrit Workflow]: https://wiki.openstack.org/wiki/Gerrit_Workflow
[Gerrit]: https://code.google.com/p/gerrit/
[Gluster-Swift Developer Guide]: https://github.com/gluster/gluster-swift/blob/master/doc/markdown/dev_guide.md
