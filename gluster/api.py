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
from ctypes.util import find_library


# LD_LIBRARY_PATH is not looked up by ctypes.util.find_library()
so_file_name = find_library("gfapi")

if so_file_name is None:
    for name in ["libgfapi.so.0", "libgfapi.so"]:
        try:
            ctypes.CDLL(name, ctypes.RTLD_GLOBAL, use_errno=True)
        except OSError:
            pass
        else:
            so_file_name = name
            break
    if so_file_name is None:
        # The .so file cannot be found (or loaded)
        # May be you need to run ldconfig command
        raise Exception("libgfapi.so not found")

# Looks like ctypes is having trouble with dependencies, so just force them to
# load with RTLD_GLOBAL until I figure that out.
try:
    client = ctypes.CDLL(so_file_name, ctypes.RTLD_GLOBAL, use_errno=True)
    # The above statement "may" fail with OSError on some systems if
    # libgfapi.so is located in /usr/local/lib/. This happens when glusterfs
    # is installed from source. Refer to: http://bugs.python.org/issue18502
except OSError:
    raise ImportError("ctypes.CDLL() cannot load {0}. You might want to set "
                      "LD_LIBRARY_PATH env variable".format(so_file_name))

# Wow, the Linux kernel folks really play nasty games with this structure.  If
# you look at the man page for stat(2) and then at this definition you'll note
# two discrepancies.  First, we seem to have st_nlink and st_mode reversed.  In
# fact that's exactly how they're defined *for 64-bit systems*; for 32-bit
# they're in the man-page order.  Even uglier, the man page makes no mention of
# the *nsec fields, but they are very much present and if they're not included
# then we get memory corruption because libgfapi has a structure definition
# that's longer than ours and they overwrite some random bit of memory after
# the space we allocated.  Yes, that's all very disgusting, and I'm still not
# sure this will really work on 32-bit because all of the field types are so
# obfuscated behind macros and feature checks.


class Stat (ctypes.Structure):
    _fields_ = [
        ("st_dev", ctypes.c_ulong),
        ("st_ino", ctypes.c_ulong),
        ("st_nlink", ctypes.c_ulong),
        ("st_mode", ctypes.c_uint),
        ("st_uid", ctypes.c_uint),
        ("st_gid", ctypes.c_uint),
        ("st_rdev", ctypes.c_ulong),
        ("st_size", ctypes.c_ulong),
        ("st_blksize", ctypes.c_ulong),
        ("st_blocks", ctypes.c_ulong),
        ("st_atime", ctypes.c_ulong),
        ("st_atimensec", ctypes.c_ulong),
        ("st_mtime", ctypes.c_ulong),
        ("st_mtimensec", ctypes.c_ulong),
        ("st_ctime", ctypes.c_ulong),
        ("st_ctimensec", ctypes.c_ulong),
    ]


class Statvfs (ctypes.Structure):
    _fields_ = [
        ("f_bsize", ctypes.c_ulong),
        ("f_frsize", ctypes.c_ulong),
        ("f_blocks", ctypes.c_ulong),
        ("f_bfree", ctypes.c_ulong),
        ("f_bavail", ctypes.c_ulong),
        ("f_files", ctypes.c_ulong),
        ("f_ffree", ctypes.c_ulong),
        ("f_favail", ctypes.c_ulong),
        ("f_fsid", ctypes.c_ulong),
        ("f_flag", ctypes.c_ulong),
        ("f_namemax", ctypes.c_ulong),
        ("__f_spare", ctypes.c_int * 6),
    ]


class Dirent (ctypes.Structure):
    _fields_ = [
        ("d_ino", ctypes.c_ulong),
        ("d_off", ctypes.c_ulong),
        ("d_reclen", ctypes.c_ushort),
        ("d_type", ctypes.c_char),
        ("d_name", ctypes.c_char * 256),
    ]


# Here is the reference card of libgfapi library exported
# apis with its different versions.
#
#   GFAPI_3.4.0 {
#               glfs_new;
#               glfs_set_volfile;
#               glfs_set_volfile_server;
#               glfs_set_logging;
#               glfs_init;
#               glfs_fini;
#               glfs_open;
#               glfs_creat;
#               glfs_close;
#               glfs_from_glfd;
#               glfs_set_xlator_option;
#               glfs_read;
#               glfs_write;
#               glfs_read_async;
#               glfs_write_async;
#               glfs_readv;
#               glfs_writev;
#               glfs_readv_async;
#               glfs_writev_async;
#               glfs_pread;
#               glfs_pwrite;
#               glfs_pread_async;
#               glfs_pwrite_async;
#               glfs_preadv;
#               glfs_pwritev;
#               glfs_preadv_async;
#               glfs_pwritev_async;
#               glfs_lseek;
#               glfs_truncate;
#               glfs_ftruncate;
#               glfs_ftruncate_async;
#               glfs_lstat;
#               glfs_stat;
#               glfs_fstat;
#               glfs_fsync;
#               glfs_fsync_async;
#               glfs_fdatasync;
#               glfs_fdatasync_async;
#               glfs_access;
#               glfs_symlink;
#               glfs_readlink;
#               glfs_mknod;
#               glfs_mkdir;
#               glfs_unlink;
#               glfs_rmdir;
#               glfs_rename;
#               glfs_link;
#               glfs_opendir;
#               glfs_readdir_r;
#               glfs_readdirplus_r;
#               glfs_telldir;
#               glfs_seekdir;
#               glfs_closedir;
#               glfs_statvfs;
#               glfs_chmod;
#               glfs_fchmod;
#               glfs_chown;
#               glfs_lchown;
#               glfs_fchown;
#               glfs_utimens;
#               glfs_lutimens;
#               glfs_futimens;
#               glfs_getxattr;
#               glfs_lgetxattr;
#               glfs_fgetxattr;
#               glfs_listxattr;
#               glfs_llistxattr;
#               glfs_flistxattr;
#               glfs_setxattr;
#               glfs_lsetxattr;
#               glfs_fsetxattr;
#               glfs_removexattr;
#               glfs_lremovexattr;
#               glfs_fremovexattr;
#               glfs_getcwd;
#               glfs_chdir;
#               glfs_fchdir;
#               glfs_realpath;
#               glfs_posix_lock;
#               glfs_dup;
#
#	        }
#
#   GFAPI_3.4.2 {
#               glfs_setfsuid;
#               glfs_setfsgid;
#               glfs_setfsgroups;
#               glfs_h_lookupat;
#               glfs_h_creat;
#               glfs_h_mkdir;
#               glfs_h_mknod;
#               glfs_h_symlink;
#               glfs_h_unlink;
#               glfs_h_close;
#               glfs_h_truncate;
#               glfs_h_stat;
#               glfs_h_getattrs;
#               glfs_h_setattrs;
#               glfs_h_readlink;
#               glfs_h_link;
#               glfs_h_rename;
#               glfs_h_extract_handle;
#               glfs_h_create_from_handle;
#               glfs_h_opendir;
#               glfs_h_open;
#               }
#
#   GFAPI_3.5.0 {
#
#               glfs_get_volumeid;
#               glfs_readdir;
#               glfs_readdirplus;
#               glfs_fallocate;
#               glfs_discard;
#               glfs_discard_async;
#               glfs_zerofill;
#               glfs_zerofill_async;
#               glfs_caller_specific_init;
#               glfs_h_setxattrs;
#
#               }
#
#   GFAPI_3.5.1 {
#
#               glfs_unset_volfile_server;
#               glfs_h_getxattrs;
#               glfs_h_removexattrs;
#
#               }
#
#   GFAPI_3.6.0 {
#
#               glfs_get_volfile;
#               glfs_h_access;
#
#               }
#

# Define function prototypes for the wrapper functions.

glfs_init = ctypes.CFUNCTYPE(
    ctypes.c_int, ctypes.c_void_p)(('glfs_init', client))

glfs_statvfs = ctypes.CFUNCTYPE(ctypes.c_int,
                                ctypes.c_void_p,
                                ctypes.c_char_p,
                                ctypes.c_void_p)(('glfs_statvfs', client))

glfs_new = ctypes.CFUNCTYPE(
    ctypes.c_void_p, ctypes.c_char_p)(('glfs_new', client))

glfs_set_volfile_server = ctypes.CFUNCTYPE(ctypes.c_int,
                                           ctypes.c_void_p,
                                           ctypes.c_char_p,
                                           ctypes.c_char_p,
                                           ctypes.c_int)(('glfs_set_volfile_server', client))  # noqa

glfs_set_logging = ctypes.CFUNCTYPE(ctypes.c_int,
                                    ctypes.c_void_p,
                                    ctypes.c_char_p,
                                    ctypes.c_int)(('glfs_set_logging', client))

glfs_fini = ctypes.CFUNCTYPE(
    ctypes.c_int, ctypes.c_void_p)(('glfs_fini', client))

glfs_creat = ctypes.CFUNCTYPE(ctypes.c_void_p,
                              ctypes.c_void_p,
                              ctypes.c_char_p,
                              ctypes.c_int,
                              ctypes.c_uint,
                              use_errno=True)(('glfs_creat', client))

glfs_open = ctypes.CFUNCTYPE(ctypes.c_void_p,
                             ctypes.c_void_p,
                             ctypes.c_char_p,
                             ctypes.c_int,
                             use_errno=True)(('glfs_open', client))

glfs_close = ctypes.CFUNCTYPE(
    ctypes.c_int, ctypes.c_void_p)(('glfs_close', client))

glfs_lstat = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_void_p, ctypes.c_char_p,
                              ctypes.POINTER(Stat))(('glfs_lstat', client))

glfs_stat = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_void_p, ctypes.c_char_p,
                             ctypes.POINTER(Stat))(('glfs_stat', client))

glfs_fstat = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_void_p, ctypes.POINTER(
    Stat))(('glfs_fstat', client))

glfs_chmod = ctypes.CFUNCTYPE(ctypes.c_int,
                              ctypes.c_void_p,
                              ctypes.c_char_p,
                              ctypes.c_ushort)(('glfs_chmod', client))

glfs_fchmod = ctypes.CFUNCTYPE(ctypes.c_int,
                               ctypes.c_void_p,
                               ctypes.c_ushort)(('glfs_fchmod', client))

glfs_chown = ctypes.CFUNCTYPE(ctypes.c_int,
                              ctypes.c_void_p,
                              ctypes.c_char_p,
                              ctypes.c_uint,
                              ctypes.c_uint)(('glfs_chown', client))

glfs_lchown = ctypes.CFUNCTYPE(ctypes.c_int,
                               ctypes.c_void_p,
                               ctypes.c_char_p,
                               ctypes.c_uint,
                               ctypes.c_uint)(('glfs_lchown', client))

glfs_fchown = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_void_p, ctypes.c_uint,
                               ctypes.c_uint)(('glfs_fchown', client))

glfs_dup = ctypes.CFUNCTYPE(
    ctypes.c_void_p, ctypes.c_void_p)(('glfs_dup', client))

glfs_fdatasync = ctypes.CFUNCTYPE(
    ctypes.c_int, ctypes.c_void_p)(('glfs_fdatasync', client))

glfs_fsync = ctypes.CFUNCTYPE(
    ctypes.c_int, ctypes.c_void_p)(('glfs_fsync', client))

glfs_lseek = ctypes.CFUNCTYPE(ctypes.c_ulong, ctypes.c_void_p, ctypes.c_ulong,
                              ctypes.c_int)(('glfs_lseek', client))

glfs_read = ctypes.CFUNCTYPE(ctypes.c_ssize_t,
                             ctypes.c_void_p,
                             ctypes.c_void_p,
                             ctypes.c_size_t,
                             ctypes.c_int)(('glfs_read', client))

glfs_write = ctypes.CFUNCTYPE(ctypes.c_ssize_t,
                              ctypes.c_void_p,
                              ctypes.c_void_p,
                              ctypes.c_size_t,
                              ctypes.c_int)(('glfs_write', client))

glfs_getxattr = ctypes.CFUNCTYPE(ctypes.c_ssize_t,
                                 ctypes.c_void_p,
                                 ctypes.c_char_p,
                                 ctypes.c_char_p,
                                 ctypes.c_void_p,
                                 ctypes.c_size_t)(('glfs_getxattr', client))

glfs_listxattr = ctypes.CFUNCTYPE(ctypes.c_ssize_t,
                                  ctypes.c_void_p,
                                  ctypes.c_char_p,
                                  ctypes.c_void_p,
                                  ctypes.c_size_t)(('glfs_listxattr', client))

glfs_removexattr = ctypes.CFUNCTYPE(ctypes.c_int,
                                    ctypes.c_void_p,
                                    ctypes.c_char_p,
                                    ctypes.c_char_p)(('glfs_removexattr', client))  # noqa

glfs_setxattr = ctypes.CFUNCTYPE(ctypes.c_int,
                                 ctypes.c_void_p,
                                 ctypes.c_char_p,
                                 ctypes.c_char_p,
                                 ctypes.c_void_p,
                                 ctypes.c_size_t,
                                 ctypes.c_int)(('glfs_setxattr', client))

glfs_rename = ctypes.CFUNCTYPE(ctypes.c_int,
                               ctypes.c_void_p,
                               ctypes.c_char_p,
                               ctypes.c_char_p)(('glfs_rename', client))

glfs_symlink = ctypes.CFUNCTYPE(ctypes.c_int,
                                ctypes.c_void_p,
                                ctypes.c_char_p,
                                ctypes.c_char_p)(('glfs_symlink', client))

glfs_unlink = ctypes.CFUNCTYPE(
    ctypes.c_int, ctypes.c_void_p, ctypes.c_char_p)(('glfs_unlink', client))

glfs_readdir_r = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_void_p,
                                  ctypes.POINTER(Dirent),
                                  ctypes.POINTER(ctypes.POINTER(Dirent)))(('glfs_readdir_r', client))  # noqa

glfs_closedir = ctypes.CFUNCTYPE(
    ctypes.c_int, ctypes.c_void_p)(('glfs_closedir', client))


glfs_mkdir = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_void_p, ctypes.c_char_p,
                              ctypes.c_ushort)(('glfs_mkdir', client))

glfs_opendir = ctypes.CFUNCTYPE(ctypes.c_void_p,
                                ctypes.c_void_p,
                                ctypes.c_char_p)(('glfs_opendir', client))

glfs_rmdir = ctypes.CFUNCTYPE(ctypes.c_int,
                              ctypes.c_void_p,
                              ctypes.c_char_p)(('glfs_rmdir', client))

glfs_setfsuid = ctypes.CFUNCTYPE(ctypes.c_int,
                                 ctypes.c_uint)(('glfs_setfsuid', client))

glfs_setfsgid = ctypes.CFUNCTYPE(ctypes.c_int,
                                 ctypes.c_uint)(('glfs_setfsgid', client))

glfs_ftruncate = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_void_p,
                                  ctypes.c_int)(('glfs_ftruncate', client))

glfs_fgetxattr = ctypes.CFUNCTYPE(ctypes.c_ssize_t,
                                  ctypes.c_void_p,
                                  ctypes.c_char_p,
                                  ctypes.c_void_p,
                                  ctypes.c_size_t)(('glfs_fgetxattr', client))

glfs_fremovexattr = ctypes.CFUNCTYPE(ctypes.c_int,
                                     ctypes.c_void_p,
                                     ctypes.c_char_p)(('glfs_fremovexattr',
                                                      client))

glfs_fsetxattr = ctypes.CFUNCTYPE(ctypes.c_int,
                                  ctypes.c_void_p,
                                  ctypes.c_char_p,
                                  ctypes.c_void_p,
                                  ctypes.c_size_t,
                                  ctypes.c_int)(('glfs_fsetxattr', client))

glfs_flistxattr = ctypes.CFUNCTYPE(ctypes.c_ssize_t,
                                   ctypes.c_void_p,
                                   ctypes.c_void_p,
                                   ctypes.c_size_t)(('glfs_flistxattr',
                                                    client))

glfs_access = ctypes.CFUNCTYPE(ctypes.c_int,
                               ctypes.c_void_p,
                               ctypes.c_char_p,
                               ctypes.c_int)(('glfs_access', client))

glfs_readlink = ctypes.CFUNCTYPE(ctypes.c_int,
                                 ctypes.c_void_p,
                                 ctypes.c_char_p,
                                 ctypes.c_char_p,
                                 ctypes.c_size_t)(('glfs_readlink', client))

glfs_chdir = ctypes.CFUNCTYPE(ctypes.c_int,
                              ctypes.c_void_p,
                              ctypes.c_char_p)(('glfs_chdir', client))

glfs_getcwd = ctypes.CFUNCTYPE(ctypes.c_char_p,
                               ctypes.c_void_p,
                               ctypes.c_char_p,
                               ctypes.c_size_t)(('glfs_getcwd', client))


# TODO: # discard and fallocate fails with "AttributeError: /lib64/libgfapi.so.0: undefined symbol: glfs_discard", # noqa
#  for time being, using it from api.* # noqa
# glfs_discard = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_void_p, ctypes.c_ulong, ctypes.c_size_t)(('glfs_discard', client)) # noqa
#_glfs_fallocate = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_void_p, ctypes.c_int, ctypes.c_ulong, ctypes.c_size_t) # noqa
#                                   (('glfs_fallocate', client)) # noqa



#glfs_discard = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_void_p, ctypes.c_ulong, ctypes.c_size_t)(('glfs_discard', client)) # noqa
#glfs_fallocate = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_void_p, ctypes.c_int, ctypes.c_ulong, ctypes.c_size_t)(('glfs_fallocate', client)) # noqa
