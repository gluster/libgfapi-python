#!/bin/bash

# Copyright (c) 2014 Red Hat, Inc.
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

# This program expects to be run by tox in a virtual python environment
# so that it does not pollute the host development system

sudo_env()
{
    sudo bash -c "PATH=$PATH $*"
}

cleanup()
{
        sudo rm -rf /export/brick/b1/* > /dev/null 2>&1
}

quit()
{
        echo "$1"
        exit 1
}


fail()
{
        cleanup
	quit "$1"
}

### MAIN ###


# Check the directories exist
DIRS="/export/brick/b1"
for d in $DIRS ; do
	if [ ! -x $d ] ; then
		quit "$d must exist as GlusterFS volume"
	fi
done


mkdir functional_tests > /dev/null 2>&1
nosetests -v --exe \
	--with-xunit \
	--xunit-file functional_tests/libgfapi-python.xml \
    --with-html-output \
    --html-out-file functional_tests/libgfapi-python-result.html \
    test/functional || fail "Functional tests failed"

cleanup
exit 0
