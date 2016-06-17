#!/bin/bash
#
# Copyright (c) 2016 Red Hat, Inc.
#
# This file is licensed to you under your choice of the GNU Lesser
# General Public License, version 3 or any later version (LGPLv3 or
# later), or the GNU General Public License, version 2 (GPLv2), in all
# cases as published by the Free Software Foundation.

cd $(dirname $0)/test/unit
nosetests -v --exe --with-coverage --cover-package gluster --cover-erase --cover-html --cover-branches $@

saved_status=$?
rm -f .coverage
exit $saved_status
