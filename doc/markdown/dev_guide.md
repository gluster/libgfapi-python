#Developer Guide

## Development Environment Setup

The workflow for libgfapi-python is largely based upon the [Gluster-Swift Developer Guide][]  and [OpenStack Gerrit Workflow][]. Refer to those documents for setting up a Gerrit account and a complete development environment.

This document focuses on setting up a quick environment for running tox tests (especially the functional tests). This document also assumes that GlusterFS is already installed. On CentOS/RHEL you will need to setup GlsuterFS and EPEL repos.


### Package Requirements
Type the following to install the required packages:

* Ubuntu

```
sudo apt-get -y install gcc python-dev python-setuptools libffi-dev \
    git xfsprogs memcached
```

* Fedora 19

```
sudo yum install gcc python-devel python-setuptools libffi-devel \
    git rpm-build xfsprogs memcached
```

#### Pip installation
Install the python pip tool by executing the following command:

```
easy_install pip
```

### Git Setup
If this is your first time using git, you will need to setup the
following configuration:

```
git config --global user.name "Firstname Lastname"
git config --global user.email "your_email@youremail.com"
```

### Download the Source

The source for libgfapi-python is available in review.gluster.org. To download type:

```
git clone https://review.gluster.org/libgfapi-python
cd libgfapi-python
```

### Tox and Nose

libgfapi-python uses tox python virtual environment for its unit and functional tests. There is currently an incompatibility issue with the latest version of tox and virtualenv. To work around these issues, install install tox, nose and virutalenv by typing this:

```
sudo pip install --upgrade "tox>=1.6,<1.7"
sudo pip install --upgrade "virtualenv>=1.10,<1.11"
sudo pip install --upgrade nose
```

### Git Review
The tool `git review` is a simple tool to automate interaction with Gerrit.
It is recommended to use this tool to upload, modify, and query changes in Gerrit.
The tool can be installed by running the following command:

```
sudo pip install --upgrade git-review
```

While many Linux distributions offer a version of `git review`,
they do not necessarily keep it up to date. Pip provides the latest version
of the application which avoids problems with various versions of Gerrit.

You now need to setup `git review` to communicate with review.gluster.org.
First, determine your `git review` setup by typing:

```
git review -s
```

If there is no output, then everything is setup correctly.  If the output
contains the string *We don't know where your gerrit is*, then you need to
setup a remote repo with the name `gerrit`.  You can inspect the current
remote repo's by typing the following command.

```
git remote -v
```

To add the Gerrit remote repo, type the following:

```
git remote add gerrit ssh://<username>@review.gluster.org/libgfapi-python
git remote -v
```

Now we can confirm that `git review` has been setup by typing the
following and noticing no output is returned:

```
git review -s
```

### Workflow

#### Create a topic branch
It is recommended to create a branch in git when working on a specific topic.
If you are currently on the *master* branch, you can type the following
to create a topic branch:

```
git checkout -b TOPIC-BRANCH
```

where *TOPIC-BRANCH* is either bug/bug-number (e.g. bug/123456) or
a meaningful name for the topic (e.g. feature_xyz)

## Running tests

### Start services

Type the following to start the glusterfs service:

```
service glusterd start
```

Type the following to start the service automatically on system startup:

```
chkconfig glusterd on
```

### Gluster Volume Setup

#### Loopback Storage Setup

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

### Create a GlusterFS Volume

You now need to create a GlusterFS volume

```
mkdir /export/brick/b1
gluster volume create test <hostname>:/export/brick/b1
gluster volume start test
```

### Important Notes:

#### Definining a hostname
GlusterFS does not allow for specifiyng `localhost` as a valid hostname when creating a volume. Make sure to set host and volume information in test/test.conf file. The default host is 'gfshost' and default volume name is 'test'.

#### Stopping services
For the purpose of running this test, stop the `firewalld` service and disable `selinux`.

```
service firewalld stop
```

### Quality Checking

#### PEP8

To test that the code adheres to the Python PEP8 specification, please type:

```
tox -e pep8
```

#### Unit Tests

Once you have made your changes, you can test the quality of the code by executing the automated unit tests as follows:

```
tox -e ENV
```

where ENV is either py27 for systems with Python 2.7+, or py26 for systems with Python 2.6+.

If new functionality has been added, it is highly recommended that one or more tests be added to the automated unit test suite. Unit tests are available under the test/unit directory.

### Functional tests

The functional tests expects a GlusterFS `test` volume to be created and accessible.

To run the functional tests, please type:

```
tox -e functest
```

### Commiting changes
After making the changes needed, you can commit your changes by typing:

```
git commit -as
```

where the commit message should follow the following recommendations:

1. The first line should be a brief message and contain less than 50
characters.
2. Second line blank
3. A line, or multiple line description of the change where each line
contains less than 70 characters.
4. Blank line
5. If this is a bug fix, then it should have a line as follows:
`BUG 12345: <url to bug>`
6. Blank line.

For more information on commit messages, please visit the
[Git Commit Messages][] page in OpenStack.org.

### Uploading to Gerrit
Once you have the changes ready for review, you can submit it to Gerrit
by typing:

```
git review
```

After the change is reviewed, you might have to make some
additional modifications to your change.  To continue the work for
a specific change, you can query Gerrit for the change number by
typing:

```
git review -l
```

Then download the change to make the new modifications by typing:

```
git review -d CHANGE_NUMBER
```

where CHANGE_NUMBER is the Gerrit change number.

If you need to create a new patch for a change and include your update(s)
to your last commit type:

```
git commit -as --amend
```

Now that you have finished updating your change, you need to re-upload
to Gerrit using the following command:

```
git review
```


[OpenStack Gerrit Workflow]: https://wiki.openstack.org/wiki/Gerrit_Workflow
[Gerrit]: https://code.google.com/p/gerrit/
[Gluster-Swift Developer Guide]: https://github.com/gluster/gluster-swift/blob/master/doc/markdown/dev_guide.md
[Git Commit Messages]: https://wiki.openstack.org/wiki/GitCommitMessages
