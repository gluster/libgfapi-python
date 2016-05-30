#  Copyright (c) 2012-2015 Red Hat, Inc.
#  This file is part of libgfapi-python project
#  (http://review.gluster.org/#/q/project:libgfapi-python)
#  which is a subproject of GlusterFS ( www.gluster.org)
#
#  This file is licensed to you under your choice of the GNU Lesser
#  General Public License, version 3 or any later version (LGPLv3 or
#  later), or the GNU General Public License, version 2 (GPLv2), in all
#  cases as published by the Free Software Foundation.


import ctypes
import os
import math
import time
import stat
import errno
from gluster import api
from gluster.exceptions import LibgfapiException

# TODO: Move this utils.py
python_mode_to_os_flags = {}


def _populate_mode_to_flags_dict():
    # http://pubs.opengroup.org/onlinepubs/9699919799/functions/fopen.html
    for mode in ['r', 'rb']:
        python_mode_to_os_flags[mode] = os.O_RDONLY
    for mode in ['w', 'wb']:
        python_mode_to_os_flags[mode] = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
    for mode in ['a', 'ab']:
        python_mode_to_os_flags[mode] = os.O_WRONLY | os.O_CREAT | os.O_APPEND
    for mode in ['r+', 'rb+', 'r+b']:
        python_mode_to_os_flags[mode] = os.O_RDWR
    for mode in ['w+', 'wb+', 'w+b']:
        python_mode_to_os_flags[mode] = os.O_RDWR | os.O_CREAT | os.O_TRUNC
    for mode in ['a+', 'ab+', 'a+b']:
        python_mode_to_os_flags[mode] = os.O_RDWR | os.O_CREAT | os.O_APPEND

_populate_mode_to_flags_dict()


class File(object):

    def __init__(self, fd, path=None, mode=None):
        self.fd = fd
        self.originalpath = path
        self._mode = mode
        self._closed = False

    def __enter__(self):
        if self.fd is None:
            # __enter__ should only be called within the context
            # of a 'with' statement when opening a file through
            # Volume.open()
            raise ValueError("I/O operation on closed file")
        return self

    def __exit__(self, type, value, tb):
        self.close()

    @property
    def fileno(self):
        # TODO: Make self.fd private (self._fd)
        return self.fd

    @property
    def mode(self):
        return self._mode

    @property
    def name(self):
        return self.originalpath

    @property
    def closed(self):
        return self._closed

    def close(self):
        """
        Close the file. A closed file cannot be read or written any more.
        Calling close() more than once is allowed.
        """
        if not self._closed:
            ret = api.glfs_close(self.fd)
            if ret < 0:
                err = ctypes.get_errno()
                raise OSError(err, os.strerror(err))
            self._closed = True

    def discard(self, offset, len):
        ret = api.glfs_discard(self.fd, offset, len)
        if ret < 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))

    def dup(self):
        dupfd = api.glfs_dup(self.fd)
        if not dupfd:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))
        return File(dupfd, self.originalpath)

    def fallocate(self, mode, offset, length):
        """
        This is a Linux-specific sys call, unlike posix_fallocate()

        Allows the caller to directly manipulate the allocated disk space for
        the file for the byte range starting at offset and continuing for
        length bytes.

        :param mode: Operation to be performed on the given range
        :param offset: Starting offset
        :param length: Size in bytes, starting at offset
        """
        ret = api.glfs_fallocate(self.fd, mode, offset, length)
        if ret < 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))

    def fchmod(self, mode):
        """
        Change this file's mode

        :param mode: new mode
        """
        ret = api.glfs_fchmod(self.fd, mode)
        if ret < 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))

    def fchown(self, uid, gid):
        """
        Change this file's owner and group id

        :param uid: new user id for file
        :param gid: new group id for file
        """
        ret = api.glfs_fchown(self.fd, uid, gid)
        if ret < 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))

    def fdatasync(self):
        """
        Flush buffer cache pages pertaining to data, but not the ones
        pertaining to metadata.
        """
        ret = api.glfs_fdatasync(self.fd)
        if ret < 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))

    def fgetsize(self):
        """
        Return the size of a file, as reported by fstat()

        :returns: the size of the file in bytes
        """
        return self.fstat().st_size

    def fgetxattr(self, key, size=0):
        """
        Retrieve the value of the extended attribute identified by key
        for the file.

        :param key: Key of extended attribute
        :param size: If size is specified as zero, we first determine the
                     size of xattr and then allocate a buffer accordingly.
                     If size is non-zero, it is assumed the caller knows
                     the size of xattr.
        :returns: Value of extended attribute corresponding to key specified.
        """
        if size == 0:
            size = api.glfs_fgetxattr(self.fd, key, None, size)
            if size < 0:
                err = ctypes.get_errno()
                raise OSError(err, os.strerror(err))

        buf = ctypes.create_string_buffer(size)
        rc = api.glfs_fgetxattr(self.fd, key, buf, size)
        if rc < 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))
        return buf.value[:rc]

    def flistxattr(self, size=0):
        """
        Retrieve list of extended attributes for the file.

        :param size: If size is specified as zero, we first determine the
                     size of list and then allocate a buffer accordingly.
                     If size is non-zero, it is assumed the caller knows
                     the size of the list.
        :returns: List of extended attributes.
        """
        if size == 0:
            size = api.glfs_flistxattr(self.fd, None, 0)
            if size < 0:
                err = ctypes.get_errno()
                raise OSError(err, os.strerror(err))

        buf = ctypes.create_string_buffer(size)
        rc = api.glfs_flistxattr(self.fd, buf, size)
        if rc < 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))
        xattrs = []
        # Parsing character by character is ugly, but it seems like the
        # easiest way to deal with the "strings separated by NUL in one
        # buffer" format.
        i = 0
        while i < rc:
            new_xa = buf.raw[i]
            i += 1
            while i < rc:
                next_char = buf.raw[i]
                i += 1
                if next_char == '\0':
                    xattrs.append(new_xa)
                    break
                new_xa += next_char
        xattrs.sort()
        return xattrs

    def fsetxattr(self, key, value, flags=0):
        """
        Set extended attribute of file.

        :param key: The key of extended attribute.
        :param value: The valiue of extended attribute.
        :param flags: Possible values are 0 (default), 1 and 2
                      0: xattr will be created if it does not exist, or the
                         value will be replaced if the xattr exists.
                      1: Perform a pure create, which fails if the named
                         attribute already exists.
                      2: Perform a pure replace operation, which fails if the
                         named attribute does not already exist.
        """
        ret = api.glfs_fsetxattr(self.fd, key, value, len(value), flags)
        if ret < 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))

    def fremovexattr(self, key):
        """
        Remove a extended attribute of the file.

        :param key: The key of extended attribute.
        """
        ret = api.glfs_fremovexattr(self.fd, key)
        if ret < 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))

    def fstat(self):
        """
        Returns Stat object for this file.

        :return: Returns the stat information of the file.
        """
        s = api.Stat()
        rc = api.glfs_fstat(self.fd, ctypes.byref(s))
        if rc < 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))
        return s

    def fsync(self):
        """
        Flush buffer cache pages pertaining to data and metadata.
        """
        ret = api.glfs_fsync(self.fd)
        if ret < 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))

    def ftruncate(self, length):
        """
        Truncated the file to a size of length bytes.

        If the file previously was larger than this size, the extra data is
        lost. If the file previously was shorter, it is extended, and the
        extended part reads as null bytes.

        :param length: Length to truncate the file to in bytes.
        """
        ret = api.glfs_ftruncate(self.fd, length)
        if ret < 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))

    def lseek(self, pos, how):
        """
        Set the read/write offset position of this file.
        The new position is defined by 'pos' relative to 'how'

        :param pos: sets new offset position according to 'how'
        :param how: SEEK_SET, sets offset position 'pos' bytes relative to
                    beginning of file, SEEK_CUR, the position is set relative
                    to the current position and SEEK_END sets the position
                    relative to the end of the file.
        :returns: the new offset position
        """
        ret = api.glfs_lseek(self.fd, pos, how)
        if ret < 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))
        return ret

    def read(self, size=-1):
        """
        Read at most size bytes from the file.

        :param buflen: length of read buffer. If less than 0, then whole
                       file is read. Default is -1.
        :returns: buffer of 'size' length
        """
        if size < 0:
            size = self.fgetsize()
        rbuf = ctypes.create_string_buffer(size)
        ret = api.glfs_read(self.fd, rbuf, size, 0)
        if ret > 0:
            # In python 2.x, read() always returns a string. It's really upto
            # the consumer to decode this string into whatever encoding it was
            # written with.
            return rbuf.raw[:ret]
        elif ret < 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))

    def readinto(self, buf):
        """
        Read up to len(buf) bytes into buf which must be a bytearray.
        (buf cannot be a string as strings are immutable in python)

        This method is useful when you have to read a large file over
        multiple read calls. While read() allocates a buffer every time
        it's invoked, readinto() copies data to an already allocated
        buffer passed to it.

        Returns the number of bytes read (0 for EOF).
        """
        if type(buf) is bytearray:
            buf_ptr = (ctypes.c_ubyte * len(buf)).from_buffer(buf)
        else:
            # TODO: Allow reading other types such as array.array
            raise TypeError("buffer must of type bytearray")
        nread = api.glfs_read(self.fd, buf_ptr, len(buf_ptr), 0)
        if nread < 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))
        return nread

    def write(self, data, flags=0):
        """
        Write data to the file.

        :param data: The data to be written to file.
        :returns: The size in bytes actually written
        """
        # creating a ctypes.c_ubyte buffer to handle converting bytearray
        # to the required C data type

        if type(data) is bytearray:
            buf = (ctypes.c_ubyte * len(data)).from_buffer(data)
        else:
            buf = data
        ret = api.glfs_write(self.fd, buf, len(buf), flags)
        if ret < 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))
        return ret

    def zerofill(self, offset, length):
        ret = api.glfs_zerofill(self.fd, offset, length)
        if ret < 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))


class Dir(object):

    def __init__(self, fd):
        # Add a reference so the module-level variable "api" doesn't
        # get yanked out from under us (see comment above File def'n).
        self._api = api
        self.fd = fd
        self.cursor = ctypes.POINTER(api.Dirent)()

    def __del__(self):
        self._api.glfs_closedir(self.fd)
        self._api = None

    def next(self):
        entry = api.Dirent()
        entry.d_reclen = 256
        rc = api.glfs_readdir_r(self.fd, ctypes.byref(entry),
                                ctypes.byref(self.cursor))

        if (rc < 0) or (not self.cursor) or (not self.cursor.contents):
            return rc

        return entry


class Volume(object):

    def __init__(self, host, volname,
                 proto="tcp", port=24007, log_file=None, log_level=7):
        """
        Create a Volume object instance.

        :param host: Host with glusterd management daemon running.
        :param volname: Name of GlusterFS volume to be mounted and used.
        :param proto: Transport protocol to be used to connect to management
                      daemon. Permitted values are "tcp" and "rdma".
        :param port: Port number where gluster management daemon is listening.
        :param log_file: Path to log file. When this is set to None, a new
                         logfile will be created in default log directory
                         i.e /var/log/glusterfs
        :param log_level: Integer specifying the degree of verbosity.
                          Higher the value, more verbose the logging.

        TODO: Provide an interface where user can specify volfile directly
        instead of providing host and other details. This is helpful in cases
        where user wants to load some non default xlator on client side. For
        example, aux-gfid-mount or mount volume as read-only.
        """
        # Add a reference so the module-level variable "api" doesn't
        # get yanked out from under us (see comment above File def'n).
        self._api = api

        self._mounted = False
        self.fs = None
        self.log_file = log_file
        self.log_level = log_level

        if None in (volname, host):
            # TODO: Validate host based on regex for IP/FQDN.
            raise LibgfapiException("Host and Volume name should not be None.")
        if proto not in ('tcp', 'rdma'):
            raise LibgfapiException("Invalid protocol specified.")
        if not isinstance(port, (int, long)):
            raise LibgfapiException("Invalid port specified.")

        self.host = host
        self.volname = volname
        self.protocol = proto
        self.port = port

    @property
    def mounted(self):
        return self._mounted

    def mount(self):
        """
        Mount a GlusterFS volume for use.
        """
        if self.fs and self._mounted:
            # Already mounted
            return

        self.fs = api.glfs_new(self.volname)
        if not self.fs:
            err = ctypes.get_errno()
            raise LibgfapiException("glfs_new(%s) failed: %s" %
                                    (self.volname, os.strerror(err)))

        ret = api.glfs_set_volfile_server(self.fs, self.protocol,
                                          self.host, self.port)
        if ret < 0:
            err = ctypes.get_errno()
            raise LibgfapiException("glfs_set_volfile_server(%s, %s, %s, "
                                    "%s) failed: %s" % (self.fs, self.protocol,
                                                        self.host, self.port,
                                                        os.strerror(err)))

        self.set_logging(self.log_file, self.log_level)

        if self.fs and not self._mounted:
            ret = api.glfs_init(self.fs)
            if ret < 0:
                err = ctypes.get_errno()
                raise LibgfapiException("glfs_init(%s) failed: %s" %
                                        (self.fs, os.strerror(err)))
            else:
                self._mounted = True

    def umount(self):
        """
        Unmount a mounted GlusterFS volume.

        Provides users a way to free resources instead of just waiting for
        python garbage collector to call __del__() at some point later.
        """
        if self.fs:
            ret = self._api.glfs_fini(self.fs)
            if ret < 0:
                err = ctypes.get_errno()
                raise LibgfapiException("glfs_fini(%s) failed: %s" %
                                        (self.fs, os.strerror(err)))
            else:
                # Succeeded. Protect against multiple umount() calls.
                self._mounted = False
                self.fs = None

    def __del__(self):
        try:
            self.umount()
        except LibgfapiException:
            pass

    def set_logging(self, log_file, log_level):
        """
        Set logging parameters. Can be invoked either before or after
        invoking mount().

        When invoked before mount(), the preferred log file and log level
        choices are recorded and then later enforced internally as part of
        mount()

        When invoked at any point after mount(), the change in log file
        and log level is instantaneous.

        :param log_file: Path of log file.
                         If set to "/dev/null", nothing will be logged.
                         If set to None, a new logfile will be created in
                         default log directory (/var/log/glusterfs)
        :param log_level: Integer specifying the degree of verbosity.
                          Higher the value, more verbose the logging.
        """
        if self.fs:
            ret = api.glfs_set_logging(self.fs, self.log_file, self.log_level)
            if ret < 0:
                err = ctypes.get_errno()
                raise LibgfapiException("glfs_set_logging(%s, %s) failed: %s" %
                                        (self.log_file, self.log_level,
                                         os.strerror(err)))
        self.log_file = log_file
        self.log_level = log_level

    def access(self, path, mode):
        """
        Use the real uid/gid to test for access to path.

        :param path: Path to be checked.
        :param mode: mode should be F_OK to test the existence of path, or
                     it can be the inclusive OR of one or more of R_OK, W_OK,
                     and X_OK to test permissions
        :returns: True if access is allowed, False if not
        """
        ret = api.glfs_access(self.fs, path, mode)
        if ret == 0:
            return True
        else:
            return False

    def chdir(self, path):
        """
        Change the current working directory to the given path.

        :param path: Path to change current working directory to
        """
        ret = api.glfs_chdir(self.fs, path)
        if ret < 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))

    def chmod(self, path, mode):
        """
        Change mode of path

        :param path: the item to be modified
        :mode: new mode
        :returns: 0 if success, raises OSError if it fails
        """
        ret = api.glfs_chmod(self.fs, path, mode)
        if ret < 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))

    def chown(self, path, uid, gid):
        """
        Change owner and group id of path

        :param path: the item to be modified
        :param uid: new user id for item
        :param gid: new group id for item
        :returns: 0 if success, raises OSError if it fails
        """
        ret = api.glfs_chown(self.fs, path, uid, gid)
        if ret < 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))

    def exists(self, path):
        """
        Test whether a path exists.
        Returns False for broken symbolic links.
        """
        try:
            self.stat(path)
        except OSError:
            return False
        return True

    def getatime(self, path):
        """
        Returns the last access time as reported by stat
        """
        return self.stat(path).st_atime

    def getctime(self, path):
        """
        Returns the time when changes were made to the path as reported by stat
        This time is updated when changes are made to the file or dir's inode
        or the contents of the file
        """
        return self.stat(path).st_ctime

    def getcwd(self):
        """
        Returns current working directory.
        """
        PATH_MAX = 4096
        buf = ctypes.create_string_buffer(PATH_MAX)
        ret = api.glfs_getcwd(self.fs, buf, PATH_MAX)
        if ret < 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))
        return buf.value

    def getmtime(self, path):
        """
        Returns the time when changes were made to the content of the path
        as reported by stat
        """
        return self.stat(path).st_mtime

    def getsize(self, filename):
        """
        Return the size of a file, reported by stat()
        """
        return self.stat(filename).st_size

    def getxattr(self, path, key, size=0):
        """
        Retrieve the value of the extended attribute identified by key
        for path specified.

        :param path: Path to file or directory
        :param key: Key of extended attribute
        :param size: If size is specified as zero, we first determine the
                     size of xattr and then allocate a buffer accordingly.
                     If size is non-zero, it is assumed the caller knows
                     the size of xattr.
        :returns: Value of extended attribute corresponding to key specified.
        """
        if size == 0:
            size = api.glfs_getxattr(self.fs, path, key, None, 0)
            if size < 0:
                err = ctypes.get_errno()
                raise OSError(err, os.strerror(err))

        buf = ctypes.create_string_buffer(size)
        rc = api.glfs_getxattr(self.fs, path, key, buf, size)
        if rc < 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))
        return buf.value[:rc]

    def isdir(self, path):
        """
        Test whether a path is an existing directory
        """
        try:
            s = self.stat(path)
        except OSError:
            return False
        return stat.S_ISDIR(s.st_mode)

    def isfile(self, path):
        """
        Test whether a path is a regular file
        """
        try:
            s = self.stat(path)
        except OSError:
            return False
        return stat.S_ISREG(s.st_mode)

    def islink(self, path):
        """
        Test whether a path is a symbolic link
        """
        try:
            s = self.lstat(path)
        except OSError:
            return False
        return stat.S_ISLNK(s.st_mode)

    def listdir(self, path):
        """
        Return list of entries in a given directory 'path'.
        "." and ".." are not included, and the list is not sorted.
        """
        dir_list = []
        d = self.opendir(path)
        while True:
            ent = d.next()
            if not isinstance(ent, api.Dirent):
                break
            name = ent.d_name[:ent.d_reclen]
            if name not in [".", ".."]:
                dir_list.append(name)
        return dir_list

    def listxattr(self, path, size=0):
        """
        Retrieve list of extended attribute keys for the specified path.

        :param path: Path to file or directory.
        :param size: If size is specified as zero, we first determine the
                     size of list and then allocate a buffer accordingly.
                     If size is non-zero, it is assumed the caller knows
                     the size of the list.
        :returns: List of extended attribute keys.
        """
        if size == 0:
            size = api.glfs_listxattr(self.fs, path, None, 0)
            if size < 0:
                err = ctypes.get_errno()
                raise OSError(err, os.strerror(err))

        buf = ctypes.create_string_buffer(size)
        rc = api.glfs_listxattr(self.fs, path, buf, size)
        if rc < 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))
        xattrs = []
        # Parsing character by character is ugly, but it seems like the
        # easiest way to deal with the "strings separated by NUL in one
        # buffer" format.
        i = 0
        while i < rc:
            new_xa = buf.raw[i]
            i += 1
            while i < rc:
                next_char = buf.raw[i]
                i += 1
                if next_char == '\0':
                    xattrs.append(new_xa)
                    break
                new_xa += next_char
        xattrs.sort()
        return xattrs

    def lstat(self, path):
        """
        Return stat information of path. If path is a symbolic link, then it
        returns information about the link itself, not the file that it refers
        to.
        """
        s = api.Stat()
        rc = api.glfs_lstat(self.fs, path, ctypes.byref(s))
        if rc < 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))
        return s

    def makedirs(self, name, mode=0777):
        """
        Create directories defined in 'name' recursively.
        """
        head, tail = os.path.split(name)
        if not tail:
            head, tail = os.path.split(head)
        if head and tail and not self.exists(head):
            try:
                self.makedirs(head, mode)
            except OSError as err:
                if err.errno != errno.EEXIST:
                    raise
            if tail == os.curdir:
                return
        self.mkdir(name, mode)

    def mkdir(self, path, mode=0777):
        """
        Create a directory
        """
        ret = api.glfs_mkdir(self.fs, path, mode)
        if ret < 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))

    def fopen(self, path, mode='r'):
        """
        Similar to Python's built-in File object returned by Python's open()

        Unlike Python's open(), fopen() provided here is only for convenience
        and it does NOT invoke glibc's fopen and does NOT do any kind of
        I/O bufferring as of today.

        :param path: Path of file to be opened
        :param mode: Mode to open the file with. This is a string.
        :returns: an instance of File class
        """
        if not isinstance(mode, basestring):
            raise TypeError("Mode must be a string")
        try:
            flags = python_mode_to_os_flags[mode]
        except KeyError:
            raise ValueError("Invalid mode")
        else:
            if (os.O_CREAT & flags) == os.O_CREAT:
                fd = api.glfs_creat(self.fs, path, flags, 0666)
            else:
                fd = api.glfs_open(self.fs, path, flags)
            if not fd:
                err = ctypes.get_errno()
                raise OSError(err, os.strerror(err))
            return File(fd, path=path, mode=mode)

    def open(self, path, flags, mode=0777):
        """
        Similar to Python's os.open()

        As of today, the only way to consume the raw glfd returned is by
        passing it to File class.

        :param path: Path of file to be opened
        :param flags: Integer which flags must include one of the following
                      access modes: os.O_RDONLY, os.O_WRONLY, or os.O_RDWR.
        :param mode: specifies the permissions to use in case a new
                     file is created.
        :returns: the raw glfd
        """
        if not isinstance(flags, int):
            raise TypeError("flags must evaluate to an integer")

        if (os.O_CREAT & flags) == os.O_CREAT:
            fd = api.glfs_creat(self.fs, path, flags, mode)
        else:
            fd = api.glfs_open(self.fs, path, flags)
        if not fd:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))

        return fd

    def opendir(self, path):
        """
        Open a directory.

        :param path: Path to the directory
        :returns: Returns a instance of Dir class
        """
        fd = api.glfs_opendir(self.fs, path)
        if not fd:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))
        return Dir(fd)

    def readlink(self, path):
        """
        Read contents of symbolic link path.

        :param path: Path of symbolic link
        :returns: Contents of symlink
        """
        PATH_MAX = 4096
        buf = ctypes.create_string_buffer(PATH_MAX)
        ret = api.glfs_readlink(self.fs, path, buf, PATH_MAX)
        if ret < 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))
        return buf.value[:ret]

    def remove(self, path):
        """
        Remove (delete) the file path. If path is a directory,
        OSError is raised.
        """
        return self.unlink(path)

    def removexattr(self, path, key):
        """
        Remove a extended attribute of the file.

        :param path: Path to the file or directory.
        :param key: The key of extended attribute.
        """
        ret = api.glfs_removexattr(self.fs, path, key)
        if ret < 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))

    def rename(self, src, dst):
        """
        Rename the file or directory from src to dst.
        """
        ret = api.glfs_rename(self.fs, src, dst)
        if ret < 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))

    def rmdir(self, path):
        """
        Remove (delete) the directory path. Only works when the directory is
        empty, otherwise, OSError is raised. In order to remove whole
        directory trees, rmtree() can be used.
        """
        ret = api.glfs_rmdir(self.fs, path)
        if ret < 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))

    def rmtree(self, path, ignore_errors=False, onerror=None):
        """
        Delete a whole directory tree structure. Raises OSError
        if path is a symbolic link.

        :param path: Directory tree to remove
        :param ignore_errors: If True, errors are ignored
        :param onerror: If set, it is called to handle the error with arguments
                        (func, path, exc) where func is the function that
                        raised the error, path is the argument that caused it
                        to fail; and exc is the exception that was raised.
                        If ignore_errors is False and onerror is None, an
                        exception is raised
        """
        if ignore_errors:
            def onerror(*args):
                pass
        elif onerror is None:
            def onerror(*args):
                raise
        if self.islink(path):
            raise OSError("Cannot call rmtree on a symbolic link")
        names = []
        try:
            names = self.listdir(path)
        except OSError as e:
            onerror(self.listdir, path, e)
        for name in names:
            fullname = os.path.join(path, name)
            if self.isdir(fullname):
                self.rmtree(fullname, ignore_errors, onerror)
            else:
                try:
                    self.unlink(fullname)
                except OSError as e:
                    onerror(self.unlink, fullname, e)
        try:
            self.rmdir(path)
        except OSError as e:
            onerror(self.rmdir, path, e)

    def setfsuid(self, uid):
        """
        setfsuid() changes the value of the caller's filesystem user ID-the
        user ID that the Linux kernel uses to check for all accesses to the
        filesystem.
        """
        ret = api.glfs_setfsuid(uid)
        if ret < 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))

    def setfsgid(self, gid):
        """
        setfsgid() changes the value of the caller's filesystem group ID-the
        group ID that the Linux kernel uses to check for all accesses to the
        filesystem.
        """
        ret = api.glfs_setfsgid(gid)
        if ret < 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))

    def setxattr(self, path, key, value, flags=0):
        """
        Set extended attribute of the path.

        :param path: Path to file or directory.
        :param key: The key of extended attribute.
        :param value: The valiue of extended attribute.
        :param flags: Possible values are 0 (default), 1 and 2
                      0: xattr will be created if it does not exist, or the
                         value will be replaced if the xattr exists.
                      1: Perform a pure create, which fails if the named
                         attribute already exists.
                      2: Perform a pure replace operation, which fails if the
                         named attribute does not already exist.
        """
        ret = api.glfs_setxattr(self.fs, path, key, value, len(value), flags)
        if ret < 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))

    def stat(self, path):
        """
        Returns stat information of path.
        """
        s = api.Stat()
        rc = api.glfs_stat(self.fs, path, ctypes.byref(s))
        if rc < 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))
        return s

    def statvfs(self, path):
        """
        Returns information about a mounted glusterfs volume. path is the
        pathname of any file within the mounted filesystem.
        """
        s = api.Statvfs()
        rc = api.glfs_statvfs(self.fs, path, ctypes.byref(s))
        if rc < 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))
        return s

    def symlink(self, source, link_name):
        """
        Create a symbolic link 'link_name' which points to 'source'
        """
        ret = api.glfs_symlink(self.fs, source, link_name)
        if ret < 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))

    def unlink(self, path):
        """
        Delete the file 'path'

        :param path: file to be deleted
        :returns: 0 if success, raises OSError if it fails
        """
        ret = api.glfs_unlink(self.fs, path)
        if ret < 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))

    def utime(self, path, times):
        """
        Set the access and modified times of the file specified by path. If
        times is None, then the file's access and modified times are set to
        the current time. (The effect is similar to running the Unix program
        touch on the path.) Otherwise, times must be a 2-tuple of numbers,
        of the form (atime, mtime) which is used to set the access and
        modified times, respectively.
        """
        if times is None:
            now = time.time()
            times = (now, now)
        else:
            if type(times) is not tuple or len(times) != 2:
                raise TypeError("utime() arg 2 must be a tuple (atime, mtime)")

        timespec_array = (api.Timespec * 2)()

        # Set atime
        decimal, whole = math.modf(times[0])
        timespec_array[0].tv_sec = int(whole)
        timespec_array[0].tv_nsec = int(decimal * 1e9)

        # Set mtime
        decimal, whole = math.modf(times[1])
        timespec_array[1].tv_sec = int(whole)
        timespec_array[1].tv_nsec = int(decimal * 1e9)

        ret = api.glfs_utimens(self.fs, path, timespec_array)
        if ret < 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))

    def walk(self, top, topdown=True, onerror=None, followlinks=False):
        """
        Directory tree generator. Yields a 3-tuple dirpath, dirnames, filenames

        dirpath is the path to the directory, dirnames is a list of the names
        of the subdirectories in dirpath. filenames is a list of the names of
        the non-directiry files in dirpath
        """
        try:
            names = self.listdir(top)
        except OSError as err:
            if onerror is not None:
                onerror(err)
            return

        dirs, nondirs = [], []
        for name in names:
            if self.isdir(os.path.join(top, name)):
                dirs.append(name)
            else:
                nondirs.append(name)

        if topdown:
            yield top, dirs, nondirs
        for name in dirs:
            new_path = os.path.join(top, name)
            if followlinks or not self.islink(new_path):
                for x in self.walk(new_path, topdown, onerror, followlinks):
                    yield x
        if not topdown:
            yield top, dirs, nondirs
