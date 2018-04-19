# Copyright (c) 2016 Red Hat, Inc.
#
# This file is part of libgfapi-python project which is a
# subproject of GlusterFS ( www.gluster.org)
#
# This file is licensed to you under your choice of the GNU Lesser
# General Public License, version 3 or any later version (LGPLv3 or
# later), or the GNU General Public License, version 2 (GPLv2), in all
# cases as published by the Free Software Foundation.

from __future__ import unicode_literals

import ctypes
import sys
import os
import math
import time
import stat
import errno
import uuid
from collections import Iterator

from gluster.gfapi import api
from gluster.gfapi.exceptions import LibgfapiException, Error
from gluster.gfapi.utils import validate_mount, validate_glfd

# TODO: Move this utils.py
python_mode_to_os_flags = {}


PY3 = sys.version_info >= (3, 0)
if PY3:
    string_types = (str,)
else:
    string_types = (str, unicode)


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


def decode_to_bytes(text):
    """
    Decode unicode object to bytes
    or return original object if already bytes
    """
    if isinstance(text, string_types):
        return text.encode('utf-8')
    elif isinstance(text, bytes):
        return text
    else:
        raise ValueError('Cannot convert object with type %s' % type(text))


def encode_to_string(text):
    """
    Encode bytes objects to unicode str
    or return original object if already unicode
    """
    if isinstance(text, string_types):
        return text
    elif isinstance(text, bytes):
        return text.decode('utf-8')
    else:
        raise ValueError('Cannot convert object with type %s' % type(text))


class File(object):

    def __init__(self, fd, path=None, mode=None):
        """
        Create a File object equivalent to Python's built-in File object.

        :param fd: glfd pointer
        :param path: Path of the file. This is optional.
        :param mode: The I/O mode of the file.
        """
        self.fd = fd
        self.originalpath = path
        self._mode = mode
        self._validate_init()

    def __enter__(self):
        # __enter__ should only be called within the context
        # of a 'with' statement when opening a file through
        # Volume.fopen()
        self._validate_init()
        return self

    def __exit__(self, type, value, tb):
        if self.fd:
            self.close()

    def _validate_init(self):
        if self.fd is None:
            raise ValueError("I/O operation on invalid fd")
        elif not isinstance(self.fd, int):
            raise ValueError("I/O operation on invalid fd")

    @property
    def fileno(self):
        """
        Return the internal file descriptor (glfd) that is used by the
        underlying implementation to request I/O operations.
        """
        return self.fd

    @property
    def mode(self):
        """
        The I/O mode for the file. If the file was created using the
        Volume.fopen() function, this will be the value of the mode
        parameter. This is a read-only attribute.
        """
        return self._mode

    @property
    def name(self):
        """
        If the file object was created using Volume.fopen(),
        the name of the file.
        """
        return self.originalpath

    @property
    def closed(self):
        """
        Bool indicating the current state of the file object. This is a
        read-only attribute; the close() method changes the value.
        """
        return not self.fd

    @validate_glfd
    def close(self):
        """
        Close the file. A closed file cannot be read or written any more.

        :raises: OSError on failure
        """
        ret = api.glfs_close(self.fd)
        if ret < 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))
        self.fd = None

    @validate_glfd
    def discard(self, offset, length):
        """
        This is similar to UNMAP command that is used to return the
        unused/freed blocks back to the storage system. In this
        implementation, fallocate with FALLOC_FL_PUNCH_HOLE is used to
        eventually release the blocks to the filesystem. If the brick has
        been mounted with '-o discard' option, then the discard request
        will eventually reach the SCSI storage if the storage device
        supports UNMAP.

        :param offset: Starting offset
        :param len: Length or size in bytes to discard
        :raises: OSError on failure
        """
        ret = api.glfs_discard(self.fd, offset, length)
        if ret < 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))

    @validate_glfd
    def dup(self):
        """
        Return a duplicate of File object. This duplicate File class instance
        encapsulates a duplicate glfd obtained by invoking glfs_dup().

        :raises: OSError on failure
        """
        dupfd = api.glfs_dup(self.fd)
        if not dupfd:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))
        return File(dupfd, self.originalpath)

    @validate_glfd
    def fallocate(self, mode, offset, length):
        """
        This is a Linux-specific sys call, unlike posix_fallocate()

        Allows the caller to directly manipulate the allocated disk space for
        the file for the byte range starting at offset and continuing for
        length bytes.

        :param mode: Operation to be performed on the given range
        :param offset: Starting offset
        :param length: Size in bytes, starting at offset
        :raises: OSError on failure
        """
        ret = api.glfs_fallocate(self.fd, mode, offset, length)
        if ret < 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))

    @validate_glfd
    def fchmod(self, mode):
        """
        Change this file's mode

        :param mode: new mode
        :raises: OSError on failure
        """
        ret = api.glfs_fchmod(self.fd, mode)
        if ret < 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))

    @validate_glfd
    def fchown(self, uid, gid):
        """
        Change this file's owner and group id

        :param uid: new user id for file
        :param gid: new group id for file
        :raises: OSError on failure
        """
        ret = api.glfs_fchown(self.fd, uid, gid)
        if ret < 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))

    @validate_glfd
    def fdatasync(self):
        """
        Flush buffer cache pages pertaining to data, but not the ones
        pertaining to metadata.

        :raises: OSError on failure
        """
        ret = api.glfs_fdatasync(self.fd)
        if ret < 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))

    @validate_glfd
    def fgetsize(self):
        """
        Return the size of a file, as reported by fstat()

        :returns: the size of the file in bytes
        """
        return self.fstat().st_size

    @validate_glfd
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
        :raises: OSError on failure
        """
        if size == 0:
            size = api.glfs_fgetxattr(self.fd, decode_to_bytes(key), None, size)
            if size < 0:
                err = ctypes.get_errno()
                raise OSError(err, os.strerror(err))

        buf = ctypes.create_string_buffer(size)
        rc = api.glfs_fgetxattr(self.fd, decode_to_bytes(key), buf, size)
        if rc < 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))
        return encode_to_string(buf.value[:rc])

    @validate_glfd
    def flistxattr(self, size=0):
        """
        Retrieve list of extended attributes for the file.

        :param size: If size is specified as zero, we first determine the
                     size of list and then allocate a buffer accordingly.
                     If size is non-zero, it is assumed the caller knows
                     the size of the list.
        :returns: List of extended attributes.
        :raises: OSError on failure
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
            if PY3:
                new_xa = str(bytes([buf.raw[i]]), 'utf-8')
            else:
                new_xa = buf.raw[i]
            i += 1
            while i < rc:
                if PY3:
                    next_char = str(bytes([buf.raw[i]]), 'utf-8')
                else:
                    next_char = buf.raw[i]
                i += 1
                if next_char == '\0':
                    xattrs.append(new_xa)
                    break
                new_xa += next_char
        xattrs.sort()
        return [ encode_to_string(x) for x in xattrs ]

    @validate_glfd
    def fsetxattr(self, key, value, flags=0):
        """
        Set extended attribute of file.

        :param key: The key of extended attribute.
        :param value: The valiue of extended attribute.
        :param flags: Possible values are 0 (default), 1 and 2.
                      If 0 - xattr will be created if it does not exist, or
                      the value will be replaced if the xattr exists. If 1 -
                      it performs a pure create, which fails if the named
                      attribute already exists. If 2 - it performs a pure
                      replace operation, which fails if the named attribute
                      does not already exist.
        :raises: OSError on failure
        """
        ret = api.glfs_fsetxattr(self.fd, decode_to_bytes(key), decode_to_bytes(value), len(decode_to_bytes(value)), flags)
        if ret < 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))

    @validate_glfd
    def fremovexattr(self, key):
        """
        Remove a extended attribute of the file.

        :param key: The key of extended attribute.
        :raises: OSError on failure
        """
        ret = api.glfs_fremovexattr(self.fd, decode_to_bytes(key))
        if ret < 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))

    @validate_glfd
    def fstat(self):
        """
        Returns Stat object for this file.

        :return: Returns the stat information of the file.
        :raises: OSError on failure
        """
        s = api.Stat()
        rc = api.glfs_fstat(self.fd, ctypes.byref(s))
        if rc < 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))
        return s

    @validate_glfd
    def fsync(self):
        """
        Flush buffer cache pages pertaining to data and metadata.

        :raises: OSError on failure
        """
        ret = api.glfs_fsync(self.fd)
        if ret < 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))

    @validate_glfd
    def ftruncate(self, length):
        """
        Truncated the file to a size of length bytes.

        If the file previously was larger than this size, the extra data is
        lost. If the file previously was shorter, it is extended, and the
        extended part reads as null bytes.

        :param length: Length to truncate the file to in bytes.
        :raises: OSError on failure
        """
        ret = api.glfs_ftruncate(self.fd, length)
        if ret < 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))

    @validate_glfd
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
        :raises: OSError on failure
        """
        ret = api.glfs_lseek(self.fd, pos, how)
        if ret < 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))
        return ret

    @validate_glfd
    def read(self, size=-1):
        """
        Read at most size bytes from the file.

        :param buflen: length of read buffer. If less than 0, then whole
                       file is read. Default is -1.
        :returns: buffer of 'size' length
        :raises: OSError on failure
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

    @validate_glfd
    def readinto(self, buf):
        """
        Read up to len(buf) bytes into buf which must be a bytearray.
        (buf cannot be a string as strings are immutable in python)

        This method is useful when you have to read a large file over
        multiple read calls. While read() allocates a buffer every time
        it's invoked, readinto() copies data to an already allocated
        buffer passed to it.

        :returns: the number of bytes read (0 for EOF).
        :raises: OSError on failure
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

    @validate_glfd
    def write(self, data, flags=0):
        """
        Write data to the file.

        :param data: The data to be written to file.
        :returns: The size in bytes actually written
        :raises: OSError on failure
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

    @validate_glfd
    def zerofill(self, offset, length):
        """
        Fill 'length' number of bytes with zeroes starting from 'offset'.

        :param offset: Start at offset location
        :param length: Size/length in bytes
        :raises: OSError on failure
        """
        ret = api.glfs_zerofill(self.fd, offset, length)
        if ret < 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))


class Dir(Iterator):

    def __init__(self, fd, readdirplus=False):
        # Add a reference so the module-level variable "api" doesn't
        # get yanked out from under us (see comment above File def'n).
        self._api = api
        self.fd = fd
        self.readdirplus = readdirplus
        self.cursor = ctypes.POINTER(api.Dirent)()

    def __del__(self):
        self._api.glfs_closedir(self.fd)
        self._api = None

    def __next__(self):
        entry = api.Dirent()
        entry.d_reclen = 256

        if self.readdirplus:
            stat_info = api.Stat()
            ret = api.glfs_readdirplus_r(self.fd, ctypes.byref(stat_info),
                                         ctypes.byref(entry),
                                         ctypes.byref(self.cursor))
        else:
            ret = api.glfs_readdir_r(self.fd, ctypes.byref(entry),
                                     ctypes.byref(self.cursor))

        if ret != 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))

        if (not self.cursor) or (not self.cursor.contents):
            # Reached end of directory stream
            raise StopIteration

        if self.readdirplus:
            return (entry, stat_info)
        else:
            return entry

    next = __next__  # Python 2


class DirEntry(object):
    """
    Object yielded by scandir() to expose the file path and other file
    attributes of a directory entry. scandir() will provide stat information
    without making additional calls. DirEntry instances are not intended to be
    stored in long-lived data structures; if you know the file metadata has
    changed or if a long time has elapsed since calling scandir(), call
    Volume.stat(entry.path) to fetch up-to-date information.

    DirEntry() instances from Python 3.5 have follow_symlinks set to True by
    default. In this implementation, follow_symlinks is set to False by
    default as it incurs an additional stat call over network.
    """

    __slots__ = ('_name', '_vol', '_lstat', '_stat', '_path')

    def __init__(self, vol, scandir_path, name, lstat):
        self._name = encode_to_string(name)
        self._vol = vol
        self._lstat = lstat
        self._stat = None
        self._path = os.path.join(scandir_path, self._name)

    @property
    def name(self):
        """
        The entry's base filename, relative to the scandir() path argument.
        """
        return self._name

    @property
    def path(self):
        """
        The entry's full path name: equivalent to os.path.join(scandir_path,
        entry.name) where scandir_path is the scandir() path argument. The path
        is only absolute if the scandir() path argument was absolute.
        """
        return self._path

    def stat(self, follow_symlinks=False):
        """
        Returns information equivalent of a lstat() system call on the entry.
        This does not follow symlinks by default.
        """
        if follow_symlinks:
            if self._stat is None:
                if self.is_symlink():
                    self._stat = self._vol.stat(self.path)
                else:
                    self._stat = self._lstat
            return self._stat
        else:
            return self._lstat

    def is_dir(self, follow_symlinks=False):
        """
        Return True if this entry is a directory; return False if the entry is
        any other kind of file, or if it doesn't exist anymore.
        """
        if follow_symlinks and self.is_symlink():
            try:
                st = self.stat(follow_symlinks=follow_symlinks)
            except OSError as err:
                if err.errno != errno.ENOENT:
                    raise
                return False
            else:
                return stat.S_ISDIR(st.st_mode)
        else:
            return stat.S_ISDIR(self._lstat.st_mode)

    def is_file(self, follow_symlinks=False):
        """
        Return True if this entry is a file; return False if the entry is a
        directory or other non-file entry, or if it doesn't exist anymore.
        """
        if follow_symlinks and self.is_symlink():
            try:
                st = self.stat(follow_symlinks=follow_symlinks)
            except OSError as err:
                if err.errno != errno.ENOENT:
                    raise
                return False
            else:
                return stat.S_ISREG(st.st_mode)
        else:
            return stat.S_ISREG(self._lstat.st_mode)

    def is_symlink(self):
        """
        Return True if this entry is a symbolic link (even if broken); return
        False if the entry points to a directory or any kind of file, or if it
        doesn't exist anymore.
        """
        return stat.S_ISLNK(self._lstat.st_mode)

    def inode(self):
        """
        Return the inode number of the entry.
        """
        return self._lstat.st_ino

    def __str__(self):
        return '<{0}: {1!r}>'.format(self.__class__.__name__, self.name)

    __repr__ = __str__


class Volume(object):

    def __init__(self, host, volname,
                 proto="tcp", port=24007, log_file="/dev/null", log_level=7):
        """
        Create a Volume object instance.

        :param host: Host with glusterd management daemon running OR
        :            path to socket file which glusterd is listening on.
        :param volname: Name of GlusterFS volume to be mounted and used.
        :param proto: Transport protocol to be used to connect to management
                      daemon. Permitted values are "tcp" and "rdma".
        :param port: Port number where gluster management daemon is listening.
        :param log_file: Path to log file. When this is set to None, a new
                         logfile will be created in default log directory
                         i.e /var/log/glusterfs. The default is "/dev/null"
        :param log_level: Integer specifying the degree of verbosity.
                          Higher the value, more verbose the logging.

        """
        # TODO: Provide an interface where user can specify volfile directly
        # instead of providing host and other details. This is helpful in cases
        # where user wants to load some non default xlator on client side. For
        # example, aux-gfid-mount or mount volume as read-only.

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
        if proto not in ('tcp', 'rdma', 'unix'):
            raise LibgfapiException("Invalid protocol specified.")
        if not isinstance(port, int):
            raise LibgfapiException("Invalid port specified.")

        self.host = host
        self.volname = volname
        self.volid = None
        self.protocol = proto
        self.port = port

    @property
    def mounted(self):
        """
        Read-only attribute that returns True if the volume is mounted.
        The value of the attribute is internally changed on invoking
        mount() and umount() functions.
        """
        return self._mounted

    def mount(self):
        """
        Mount a GlusterFS volume for use.

        :raises: LibgfapiException on failure
        """
        if self.fs and self._mounted:
            # Already mounted
            return

        self.fs = api.glfs_new(decode_to_bytes(self.volname))
        if not self.fs:
            err = ctypes.get_errno()
            raise LibgfapiException("glfs_new(%s) failed: %s" %
                                    (self.volname, os.strerror(err)))

        ret = api.glfs_set_volfile_server(self.fs, decode_to_bytes(self.protocol),
                                          decode_to_bytes(self.host), self.port)
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

        :raises: LibgfapiException on failure
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
            ret = api.glfs_set_logging(self.fs, decode_to_bytes(log_file), log_level)
            if ret < 0:
                err = ctypes.get_errno()
                raise LibgfapiException("glfs_set_logging(%s, %s) failed: %s" %
                                        (log_file, log_level,
                                         os.strerror(err)))
        self.log_file = log_file
        self.log_level = log_level

    def disable_logging(self):
        """
        Sends logs to /dev/null effectively disabling them
        """
        self.set_logging("/dev/null", self.log_level)

    @validate_mount
    def get_volume_id(self):
        """
        Returns the volume ID (of type uuid.UUID) for the currently mounted
        volume.
        """
        if self.volid is not None:
            return self.volid
        size = 16
        buf = ctypes.create_string_buffer(size)
        ret = api.glfs_get_volumeid(self.fs, buf, size)
        if ret < 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))
        self.volid = uuid.UUID(bytes=buf.raw)
        return self.volid

    @validate_mount
    def access(self, path, mode):
        """
        Use the real uid/gid to test for access to path.

        :param path: Path to be checked.
        :param mode: mode should be F_OK to test the existence of path, or
                     it can be the inclusive OR of one or more of R_OK, W_OK,
                     and X_OK to test permissions
        :returns: True if access is allowed, False if not
        """
        ret = api.glfs_access(self.fs, decode_to_bytes(path), mode)
        if ret == 0:
            return True
        else:
            return False

    @validate_mount
    def chdir(self, path):
        """
        Change the current working directory to the given path.

        :param path: Path to change current working directory to
        :raises: OSError on failure
        """
        ret = api.glfs_chdir(self.fs, decode_to_bytes(path))
        if ret < 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))

    @validate_mount
    def chmod(self, path, mode):
        """
        Change mode of path

        :param path: the item to be modified
        :param mode: new mode
        :raises: OSError on failure
        """
        ret = api.glfs_chmod(self.fs, decode_to_bytes(path), mode)
        if ret < 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))

    @validate_mount
    def chown(self, path, uid, gid):
        """
        Change owner and group id of path

        :param path: the path to be modified
        :param uid: new user id for path
        :param gid: new group id for path
        :raises: OSError on failure
        """
        ret = api.glfs_chown(self.fs, decode_to_bytes(path), uid, gid)
        if ret < 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))

    def exists(self, path):
        """
        Returns True if path refers to an existing path. Returns False for
        broken symbolic links. This function may return False if permission is
        not granted to execute stat() on the requested file, even if the path
        physically exists.
        """
        try:
            self.stat(path)
        except OSError:
            return False
        return True

    def getatime(self, path):
        """
        Returns the last access time as reported by stat()
        """
        return self.stat(path).st_atime

    def getctime(self, path):
        """
        Returns the time when changes were made to the path as reported by
        stat(). This time is updated when changes are made to the file or
        dir's inode or the contents of the file
        """
        return self.stat(path).st_ctime

    @validate_mount
    def getcwd(self):
        """
        Returns current working directory.
        """
        PATH_MAX = 4096
        buf = ctypes.create_string_buffer(PATH_MAX)
        ret = api.glfs_getcwd(self.fs, buf, PATH_MAX)
	# TODO FIXME
	# Does this really makes sense ? ret contains the path
	# api.py states in returns bytearray... "ctypes.c_char_p"
        #if ret < 0:
        #    err = ctypes.get_errno()
        #    raise OSError(err, os.strerror(err))
        #return buf.value
        if not ret:
            raise OSError(errno.ENOENT, os.strerror(errno.ENOENT))
        return encode_to_string(buf.value)

    def getmtime(self, path):
        """
        Returns the time when changes were made to the content of the path
        as reported by stat()
        """
        return self.stat(path).st_mtime

    def getsize(self, path):
        """
        Return the size of a file in bytes, reported by stat()
        """
        return self.stat(path).st_size

    @validate_mount
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
        :raises: OSError on failure
        """
        if size == 0:
            size = api.glfs_getxattr(self.fs, decode_to_bytes(path), decode_to_bytes(key), None, 0)
            if size < 0:
                err = ctypes.get_errno()
                raise OSError(err, os.strerror(err))

        buf = ctypes.create_string_buffer(size)
        rc = api.glfs_getxattr(self.fs, decode_to_bytes(path), decode_to_bytes(key), buf, size)
        if rc < 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))
        return encode_to_string(buf.value[:rc])

    def isdir(self, path):
        """
        Returns True if path is an existing directory. Returns False on all
        failure cases including when path does not exist.
        """
        try:
            s = self.stat(path)
        except OSError:
            return False
        return stat.S_ISDIR(s.st_mode)

    def isfile(self, path):
        """
        Return True if path is an existing regular file. Returns False on all
        failure cases including when path does not exist.
        """
        try:
            s = self.stat(path)
        except OSError:
            return False
        return stat.S_ISREG(s.st_mode)

    def islink(self, path):
        """
        Return True if path refers to a directory entry that is a symbolic
        link. Returns False on all failure cases including when path does
        not exist.
        """
        try:
            s = self.lstat(path)
        except OSError:
            return False
        return stat.S_ISLNK(s.st_mode)

    def listdir(self, path):
        """
        Return a list containing the names of the entries in the directory
        given by path. The list is in arbitrary order. It does not include
        the special entries '.' and '..' even if they are present in the
        directory.

        :param path: Path to directory
        :raises: OSError on failure
        :returns: List of names of directory entries
        """
        dir_list = []
        for entry in self.opendir(path):
            if not isinstance(entry, api.Dirent):
                break
            name = encode_to_string(entry.d_name[:entry.d_reclen])
            if name not in (".", ".."):
                dir_list.append(name)
        return dir_list

    def listdir_with_stat(self, path):
        """
        Return a list containing the name and stat of the entries in the
        directory given by path. The list is in arbitrary order. It does
        not include the special entries '.' and '..' even if they are present
        in the directory.

        :param path: Path to directory
        :raises: OSError on failure
        :returns: A list of tuple. The tuple is of the form (name, stat) where
                  name is a string indicating name of the directory entry and
                  stat contains stat info of the entry.
        """
        # List of tuple. Each tuple is of the form (name, stat)
        entries_with_stat = []
        for (entry, stat_info) in self.opendir(path, readdirplus=True):
            if not (isinstance(entry, api.Dirent) and
                    isinstance(stat_info, api.Stat)):
                break
            name = encode_to_string(entry.d_name[:entry.d_reclen])
            if name not in (".", ".."):
                entries_with_stat.append((name, stat_info))
        return entries_with_stat

    def scandir(self, path):
        """
        Return an iterator of :class:`DirEntry` objects corresponding to the
        entries in the directory given by path. The entries are yielded in
        arbitrary order, and the special entries '.' and '..' are not
        included.

        Using scandir() instead of listdir() can significantly increase the
        performance of code that also needs file type or file attribute
        information, because :class:`DirEntry` objects expose this
        information.

        scandir() provides same functionality as listdir_with_stat() except
        that scandir() does not return a list and is an iterator. Hence scandir
        is less memory intensive on large directories.

        :param path: Path to directory
        :raises: OSError on failure
        :yields: Instance of :class:`DirEntry` class.
        """
        for (entry, lstat) in self.opendir(path, readdirplus=True):
            name = entry.d_name[:entry.d_reclen]
            if name not in (b".", b".."):
                yield DirEntry(self, path, name, lstat)

    @validate_mount
    def listxattr(self, path, size=0):
        """
        Retrieve list of extended attribute keys for the specified path.

        :param path: Path to file or directory.
        :param size: If size is specified as zero, we first determine the
                     size of list and then allocate a buffer accordingly.
                     If size is non-zero, it is assumed the caller knows
                     the size of the list.
        :returns: List of extended attribute keys.
        :raises: OSError on failure
        """
        if size == 0:
            size = api.glfs_listxattr(self.fs, decode_to_bytes(path), None, 0)
            if size < 0:
                err = ctypes.get_errno()
                raise OSError(err, os.strerror(err))

        buf = ctypes.create_string_buffer(size)
        rc = api.glfs_listxattr(self.fs, decode_to_bytes(path), buf, size)
        if rc < 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))
        xattrs = []
        # Parsing character by character is ugly, but it seems like the
        # easiest way to deal with the "strings separated by NUL in one
        # buffer" format.
        i = 0
        while i < rc:
            if PY3:
                new_xa = str(bytes([buf.raw[i]]), 'utf-8')
            else:
                new_xa = buf.raw[i]
            i += 1
            while i < rc:
                if PY3:
                    next_char = str(bytes([buf.raw[i]]), 'utf-8')
                else:
                    next_char = buf.raw[i]
                i += 1
                if next_char == '\0':
                    xattrs.append(new_xa)
                    break
                new_xa += next_char
        xattrs.sort()
        return [ encode_to_string(x) for x in xattrs ]

    @validate_mount
    def lstat(self, path):
        """
        Return stat information of path. If path is a symbolic link, then it
        returns information about the link itself, not the file that it refers
        to.

        :raises: OSError on failure
        """
        s = api.Stat()
        rc = api.glfs_lstat(self.fs, decode_to_bytes(path), ctypes.byref(s))
        if rc < 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))
        return s

    def makedirs(self, path, mode=0o777):
        """
        Recursive directory creation function. Like mkdir(), but makes all
        intermediate-level directories needed to contain the leaf directory.
        The default mode is 0777 (octal).

        :raises: OSError if the leaf directory already exists or cannot be
                 created. Can also raise OSError if creation of any non-leaf
                 directories fails.
        """
        head, tail = os.path.split(path)
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
        self.mkdir(path, mode)

    @validate_mount
    def mkdir(self, path, mode=0o777):
        """
        Create a directory named path with numeric mode mode.
        The default mode is 0777 (octal).

        :raises: OSError on failure
        """
        ret = api.glfs_mkdir(self.fs, decode_to_bytes(path), mode)
        if ret < 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))

    @validate_mount
    def fopen(self, path, mode='r'):
        """
        Similar to Python's built-in File object returned by Python's open()

        Unlike Python's open(), fopen() provided here is only for convenience
        and it does NOT invoke glibc's fopen and does NOT do any kind of
        I/O bufferring as of today.

        The most commonly-used values of mode are 'r' for reading, 'w' for
        writing (truncating the file if it already exists), and 'a' for
        appending. If mode is omitted, it defaults to 'r'.

        Modes 'r+', 'w+' and 'a+' open the file for updating (reading and
        writing); note that 'w+' truncates the file.

        Append 'b' to the mode to open the file in binary mode but this has
        no effect as of today.

        :param path: Path of file to be opened
        :param mode: Mode to open the file with. This is a string.
        :returns: an instance of File class
        :raises: OSError on failure to create/open file.
                 TypeError and ValueError if mode is invalid.
        """
        if not isinstance(mode, string_types):
            raise TypeError("Mode must be a string")
        try:
            flags = python_mode_to_os_flags[mode]
        except KeyError:
            raise ValueError("Invalid mode")
        else:
            if (os.O_CREAT & flags) == os.O_CREAT:
                fd = api.glfs_creat(self.fs, decode_to_bytes(path), flags, 0o666)
            else:
                fd = api.glfs_open(self.fs, decode_to_bytes(path), flags)
            if not fd:
                err = ctypes.get_errno()
                raise OSError(err, os.strerror(err))
            return File(fd, path=path, mode=mode)

    @validate_mount
    def open(self, path, flags, mode=0o777):
        """
        Similar to Python's os.open()

        As of today, the only way to consume the raw glfd returned is by
        passing it to File class.

        :param path: Path of file to be opened
        :param flags: Integer which flags must include one of the following
                      access modes: os.O_RDONLY, os.O_WRONLY, or os.O_RDWR.
        :param mode: specifies the permissions to use in case a new
                     file is created. The default mode is 0777 (octal)
        :returns: the raw glfd (pointer to memory in C, number in python)
        :raises: OSError on failure to create/open file.
                 TypeError if flags is not an integer.
        """
        if not isinstance(flags, int):
            raise TypeError("flags must evaluate to an integer")

        if (os.O_CREAT & flags) == os.O_CREAT:
            fd = api.glfs_creat(self.fs, decode_to_bytes(path), flags, mode)
        else:
            fd = api.glfs_open(self.fs, decode_to_bytes(path), flags)
        if not fd:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))

        return fd

    @validate_mount
    def opendir(self, path, readdirplus=False):
        """
        Open a directory.

        :param path: Path to the directory
        :param readdirplus: Enable readdirplus which will also fetch stat
                            information for each entry of directory.
        :returns: Returns a instance of Dir class
        :raises: OSError on failure
        """
        fd = api.glfs_opendir(self.fs, decode_to_bytes(path))
        if not fd:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))
        return Dir(fd, readdirplus)

    @validate_mount
    def readlink(self, path):
        """
        Return a string representing the path to which the symbolic link
        points. The result may be either an absolute or relative pathname.

        :param path: Path of symbolic link
        :returns: Contents of symlink
        :raises: OSError on failure
        """
        PATH_MAX = 4096
        buf = ctypes.create_string_buffer(PATH_MAX)
        ret = api.glfs_readlink(self.fs, decode_to_bytes(path), buf, PATH_MAX)
        if ret < 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))
        return encode_to_string(buf.value[:ret])

    def remove(self, path):
        """
        Remove (delete) the file path. If path is a directory, OSError
        is raised. This is identical to the unlink() function.

        :raises: OSError on failure
        """
        return self.unlink(path)

    @validate_mount
    def removexattr(self, path, key):
        """
        Remove a extended attribute of the path.

        :param path: Path to the file or directory.
        :param key: The key of extended attribute.
        :raises: OSError on failure
        """
        ret = api.glfs_removexattr(self.fs, decode_to_bytes(path), decode_to_bytes(key))
        if ret < 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))

    @validate_mount
    def rename(self, src, dst):
        """
        Rename the file or directory from src to dst. If dst is a directory,
        OSError will be raised. If dst exists and is a file, it will be
        replaced silently if the user has permission.

        :raises: OSError on failure
        """
        ret = api.glfs_rename(self.fs, decode_to_bytes(src), decode_to_bytes(dst))
        if ret < 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))

    @validate_mount
    def rmdir(self, path):
        """
        Remove (delete) the directory path. Only works when the directory is
        empty, otherwise, OSError is raised. In order to remove whole
        directory trees, rmtree() can be used.

        :raises: OSError on failure
        """
        ret = api.glfs_rmdir(self.fs, decode_to_bytes(path))
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
        :raises: OSError on failure if onerror is None
        """
        if ignore_errors:
            def onerror(*args):
                pass
        elif onerror is None:
            def onerror(*args):
                raise
        if self.islink(path):
            raise OSError("Cannot call rmtree on a symbolic link")

        try:
            for entry in self.scandir(path):
                fullname = os.path.join(path, entry.name)
                if entry.is_dir(follow_symlinks=False):
                    self.rmtree(fullname, ignore_errors, onerror)
                else:
                    try:
                        self.unlink(fullname)
                    except OSError as e:
                        onerror(self.unlink, fullname, e)
        except OSError as e:
            # self.scandir() is not a list and is a true iterator, it can
            # raise an exception and blow-up. The try-except block here is to
            # handle it gracefully and return.
            onerror(self.scandir, path, e)

        try:
            self.rmdir(path)
        except OSError as e:
            onerror(self.rmdir, path, e)

    def setfsuid(self, uid):
        """
        setfsuid() changes the value of the caller's filesystem user ID-the
        user ID that the Linux kernel uses to check for all accesses to the
        filesystem.

        :raises: OSError on failure
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

        :raises: OSError on failure
        """
        ret = api.glfs_setfsgid(gid)
        if ret < 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))

    @validate_mount
    def setxattr(self, path, key, value, flags=0):
        """
        Set extended attribute of the path.

        :param path: Path to file or directory.
        :param key: The key of extended attribute.
        :param value: The valiue of extended attribute.
        :param flags: Possible values are 0 (default), 1 and 2.
                      If 0 - xattr will be created if it does not exist, or
                      the value will be replaced if the xattr exists. If 1 -
                      it performs a pure create, which fails if the named
                      attribute already exists. If 2 - it performs a pure
                      replace operation, which fails if the named attribute
                      does not already exist.

        :raises: OSError on failure
        """
        ret = api.glfs_setxattr(self.fs, decode_to_bytes(path), decode_to_bytes(key), decode_to_bytes(value), len(decode_to_bytes(value)), flags)
        if ret < 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))

    @validate_mount
    def stat(self, path):
        """
        Returns stat information of path.

        :raises: OSError on failure
        """
        s = api.Stat()
        rc = api.glfs_stat(self.fs, decode_to_bytes(path), ctypes.byref(s))
        if rc < 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))
        return s

    @validate_mount
    def statvfs(self, path):
        """
        Returns information about a mounted glusterfs volume. path is the
        pathname of any file within the mounted filesystem.

        :returns: An object whose attributes describe the filesystem on the
                  given path, and correspond to the members of the statvfs
                  structure, namely: f_bsize, f_frsize, f_blocks, f_bfree,
                  f_bavail, f_files, f_ffree, f_favail, f_fsid, f_flag,
                  and f_namemax.

        :raises: OSError on failure
        """
        s = api.Statvfs()
        rc = api.glfs_statvfs(self.fs, decode_to_bytes(path), ctypes.byref(s))
        if rc < 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))
        return s

    @validate_mount
    def link(self, source, link_name):
        """
        Create a hard link pointing to source named link_name.

        :raises: OSError on failure
        """
        ret = api.glfs_link(self.fs, decode_to_bytes(source), decode_to_bytes(link_name))
        if ret < 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))

    @validate_mount
    def symlink(self, source, link_name):
        """
        Create a symbolic link 'link_name' which points to 'source'

        :raises: OSError on failure
        """
        ret = api.glfs_symlink(self.fs, decode_to_bytes(source), decode_to_bytes(link_name))
        if ret < 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))

    @validate_mount
    def unlink(self, path):
        """
        Delete the file 'path'

        :raises: OSError on failure
        """
        ret = api.glfs_unlink(self.fs, decode_to_bytes(path))
        if ret < 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))

    @validate_mount
    def utime(self, path, times):
        """
        Set the access and modified times of the file specified by path. If
        times is None, then the file's access and modified times are set to
        the current time. (The effect is similar to running the Unix program
        touch on the path.) Otherwise, times must be a 2-tuple of numbers,
        of the form (atime, mtime) which is used to set the access and
        modified times, respectively.


        :raises: OSError on failure to change time.
                 TypeError if invalid times is passed.
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

        ret = api.glfs_utimens(self.fs, decode_to_bytes(path), timespec_array)
        if ret < 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))

    def walk(self, top, topdown=True, onerror=None, followlinks=False):
        """
        Generate the file names in a directory tree by walking the tree either
        top-down or bottom-up.

        Slight difference in behaviour in comparison to os.walk():
        When os.walk() is called with 'followlinks=False' (default), symlinks
        to directories are included in the 'dirnames' list. When Volume.walk()
        is called with 'followlinks=False' (default), symlinks to directories
        are included in 'filenames' list. This is NOT a bug.
        http://python.6.x6.nabble.com/os-walk-with-followlinks-False-td3559133.html

        :param top: Directory path to walk
        :param topdown: If topdown is True or not specified, the triple for a
                        directory is generated before the triples for any of
                        its subdirectories. If topdown is False, the triple
                        for a directory is generated after the triples for all
                        of its subdirectories.
        :param onerror: If optional argument onerror is specified, it should be
                        a function; it will be called with one argument, an
                        OSError instance. It can report the error to continue
                        with the walk, or raise exception to abort the walk.
        :param followlinks: Set followlinks to True to visit directories
                            pointed to by symlinks.
        :raises: OSError on failure if onerror is None
        :yields: a 3-tuple (dirpath, dirnames, filenames) where dirpath is a
                 string, the path to the directory. dirnames is a list of the
                 names of the subdirectories in dirpath (excluding '.' and
                 '..'). filenames is a list of the names of the non-directory
                 files in dirpath.
        """
        dirs = []  # List of DirEntry objects
        nondirs = []  # List of names (strings)

        try:
            for entry in self.scandir(top):
                if entry.is_dir(follow_symlinks=followlinks):
                    dirs.append(entry)
                else:
                    nondirs.append(entry.name)
        except OSError as err:
            # self.scandir() is not a list and is a true iterator, it can
            # raise an exception and blow-up. The try-except block here is to
            # handle it gracefully and return.
            if onerror is not None:
                onerror(err)
            return

        if topdown:
            yield top, [d.name for d in dirs], nondirs

        for directory in dirs:
            # NOTE: Both is_dir() and is_symlink() can be true for the same
            # path when follow_symlinks is set to True
            if followlinks or not directory.is_symlink():
                new_path = os.path.join(top, directory.name)
                for x in self.walk(new_path, topdown, onerror, followlinks):
                    yield x

        if not topdown:
            yield top, [d.name for d in dirs], nondirs

    def samefile(self, path1, path2):
        """
        Return True if both pathname arguments refer to the same file or
        directory (as indicated by device number and inode number). Raise an
        exception if a stat() call on either pathname fails.

        :param path1: Path to one file
        :param path2: Path to another file
        :raises: OSError if stat() fails
        """
        s1 = self.stat(path1)
        s2 = self.stat(path2)
        return s1.st_ino == s2.st_ino and s1.st_dev == s2.st_dev

    @classmethod
    def copyfileobj(self, fsrc, fdst, length=128 * 1024):
        """
        Copy the contents of the file-like object fsrc to the file-like object
        fdst. The integer length, if given, is the buffer size. Note that if
        the current file position of the fsrc object is not 0, only the
        contents from the current file position to the end of the file will be
        copied.

        :param fsrc: Source file object
        :param fdst: Destination file object
        :param length: Size of buffer in bytes to be used in copying
        :raises: OSError on failure
        """
        buf = bytearray(length)
        while True:
            nread = fsrc.readinto(buf)
            if not nread or nread <= 0:
                break
            if nread == length:
                # Entire buffer is filled, do not slice.
                fdst.write(buf)
            else:
                # TODO:
                # Use memoryview to avoid internal copy done on slicing.
                fdst.write(buf[0:nread])

    def copyfile(self, src, dst):
        """
        Copy the contents (no metadata) of the file named src to a file named
        dst. dst must be the complete target file name.  If src and dst are
        the same, Error is raised. The destination location must be writable.
        If dst already exists, it will be replaced. Special files such as
        character or block devices and pipes cannot be copied with this
        function. src and dst are path names given as strings.

        :param src: Path of source file
        :param dst: Path of destination file
        :raises: Error if src and dst file are same file.
                 OSError on failure to read/write.
        """
        _samefile = False
        try:
            _samefile = self.samefile(src, dst)
        except OSError:
            # Dst file need not exist.
            pass

        if _samefile:
            raise Error("`%s` and `%s` are the same file" % (src, dst))

        with self.fopen(src, 'rb') as fsrc:
            with self.fopen(dst, 'wb') as fdst:
                self.copyfileobj(fsrc, fdst)

    def copymode(self, src, dst):
        """
        Copy the permission bits from src to dst. The file contents, owner,
        and group are unaffected. src and dst are path names given as strings.

        :param src: Path of source file
        :param dst: Path of destination file
        :raises: OSError on failure.
        """
        st = self.stat(src)
        mode = stat.S_IMODE(st.st_mode)
        self.chmod(dst, mode)

    def copystat(self, src, dst):
        """
        Copy the permission bits, last access time, last modification time,
        and flags from src to dst. The file contents, owner, and group are
        unaffected. src and dst are path names given as strings.

        :param src: Path of source file
        :param dst: Path of destination file
        :raises: OSError on failure.
        """
        st = self.stat(src)
        mode = stat.S_IMODE(st.st_mode)
        self.utime(dst, (st.st_atime, st.st_mtime))
        self.chmod(dst, mode)
        # TODO: Handle st_flags on FreeBSD

    def copy(self, src, dst):
        """
        Copy data and mode bits ("cp src dst")

        Copy the file src to the file or directory dst. If dst is a directory,
        a file with the same basename as src is created (or overwritten) in
        the directory specified. Permission bits are copied. src and dst are
        path names given as strings.

        :param src: Path of source file
        :param dst: Path of destination file or directory
        :raises: OSError on failure
        """
        if self.isdir(dst):
            dst = os.path.join(dst, os.path.basename(src))
        self.copyfile(src, dst)
        self.copymode(src, dst)

    def copy2(self, src, dst):
        """
        Similar to copy(), but metadata is copied as well - in fact, this is
        just copy() followed by copystat(). This is similar to the Unix command
        cp -p.

        The destination may be a directory.

        :param src: Path of source file
        :param dst: Path of destination file or directory
        :raises: OSError on failure
        """
        if self.isdir(dst):
            dst = os.path.join(dst, os.path.basename(src))
        self.copyfile(src, dst)
        self.copystat(src, dst)

    def copytree(self, src, dst, symlinks=False, ignore=None):
        """
        Recursively copy a directory tree using copy2().

        The destination directory must not already exist.
        If exception(s) occur, an Error is raised with a list of reasons.

        If the optional symlinks flag is true, symbolic links in the
        source tree result in symbolic links in the destination tree; if
        it is false, the contents of the files pointed to by symbolic
        links are copied.

        The optional ignore argument is a callable. If given, it
        is called with the 'src' parameter, which is the directory
        being visited by copytree(), and 'names' which is the list of
        'src' contents, as returned by os.listdir():

            callable(src, names) -> ignored_names

        Since copytree() is called recursively, the callable will be
        called once for each directory that is copied. It returns a
        list of names relative to the 'src' directory that should
        not be copied.
        """
        def _isdir(path, statinfo, follow_symlinks=False):
            if stat.S_ISDIR(statinfo.st_mode):
                return True
            if follow_symlinks and stat.S_ISLNK(statinfo.st_mode):
                return self.isdir(path)
            return False

        # Can't used scandir() here to support ignored_names functionality
        names_with_stat = self.listdir_with_stat(src)
        if ignore is not None:
            ignored_names = ignore(src, [n for n, s in names_with_stat])
        else:
            ignored_names = set()

        self.makedirs(dst)
        errors = []
        for (name, st) in names_with_stat:
            name = encode_to_string(name)
            if name in ignored_names:
                continue
            srcpath = os.path.join(src, name)
            dstpath = os.path.join(dst, name)
            try:
                if symlinks and stat.S_ISLNK(st.st_mode):
                    linkto = self.readlink(srcpath)
                    self.symlink(linkto, dstpath)
                # shutil's copytree() calls os.path.isdir() which will return
                # true even if it's a symlink pointing to a dir. Mimicking the
                # same behaviour here with _isdir()
                elif _isdir(srcpath, st, follow_symlinks=not symlinks):
                    self.copytree(srcpath, dstpath, symlinks)
                else:
                    # The following is equivalent of copy2(). copy2() is not
                    # invoked directly to avoid multiple duplicate stat calls.
                    with self.fopen(srcpath, 'rb') as fsrc:
                        with self.fopen(dstpath, 'wb') as fdst:
                            self.copyfileobj(fsrc, fdst)
                    self.utime(dstpath, (st.st_atime, st.st_mtime))
                    self.chmod(dstpath, stat.S_IMODE(st.st_mode))
            except (Error, EnvironmentError, OSError) as why:
                errors.append((srcpath, dstpath, str(why)))

        try:
            self.copystat(src, dst)
        except OSError as why:
            errors.append((src, dst, str(why)))

        if errors:
            raise Error(errors)
