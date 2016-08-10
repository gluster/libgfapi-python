# Copyright (c) 2016 Red Hat, Inc.
#
# This file is part of libgfapi-python project which is a
# subproject of GlusterFS ( www.gluster.org)
#
# This file is licensed to you under your choice of the GNU Lesser
# General Public License, version 3 or any later version (LGPLv3 or
# later), or the GNU General Public License, version 2 (GPLv2), in all
# cases as published by the Free Software Foundation.

import os
import errno
from functools import wraps
from gluster.gfapi.exceptions import VolumeNotMounted


def validate_mount(func):
    """
    Decorator to assert that volume is initialized and mounted before any
    further I/O calls are invoked by methods.

    :param func: method to be decorated and checked.
    """
    def _exception(volname):
        raise VolumeNotMounted('Volume "%s" not mounted.' % (volname))

    @wraps(func)
    def wrapper(*args, **kwargs):
        self = args[0]
        if self.fs and self._mounted:
            return func(*args, **kwargs)
        else:
            return _exception(self.volname)
    wrapper.__wrapped__ = func

    return wrapper


def validate_glfd(func):
    """
    Decorator to assert that glfd is valid.

    :param func: method to be decorated and checked.
    """
    def _exception():
        raise OSError(errno.EBADF, os.strerror(errno.EBADF))

    @wraps(func)
    def wrapper(*args, **kwargs):
        self = args[0]
        if self.fd:
            return func(*args, **kwargs)
        else:
            return _exception()
    wrapper.__wrapped__ = func

    return wrapper
