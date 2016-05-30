# Copyright (c) 2016 Red Hat, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import errno
from functools import wraps
from gluster.exceptions import VolumeNotMounted


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
