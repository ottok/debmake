#!/bin/sh
# check if debmake works as expected
LC_ALL=en_US.UTF-8
export LC_ALL
mkdir foo-1.0
cd foo-1.0
echo "DUMMY" > dummy
cd ..
tar -cvzf foo-1.0.tar.gz foo-1.0
ln -s foo-1.0.tar.gz foo_1.0.orig.tar.gz
cd foo-1.0
debmake
test -x debian/rules

