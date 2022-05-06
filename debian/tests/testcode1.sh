#!/bin/sh
# check if installed as executable
LC_ALL=en_US.UTF-8
export LC_ALL
debmake --version 2>&1 | grep -q -e 'Copyright © [-0-9 ]* Osamu Aoki <osamu@debian.org>'

