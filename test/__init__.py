# Copyright (c) 2012-2014 Red Hat, Inc.
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
import ConfigParser


def get_test_config():
    """
    Reads test.conf config file which contains configurable options
    to run functional tests.

    :returns: ConfigParser instance if test.conf found, None otherwise.
    """
    dirname = os.path.dirname(__file__)
    conf_file = dirname + "/test.conf"
    if os.path.exists(conf_file):
        config = ConfigParser.ConfigParser()
        config.read(conf_file)
        return config
    return None
