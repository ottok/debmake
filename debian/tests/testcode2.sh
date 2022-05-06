#!/bin/sh
# check if debmake works as expected
LC_ALL=en_US.UTF-8
export LC_ALL
rm -rf foo-1.0
mkdir foo-1.0
cd foo-1.0
echo "DUMMY" > dummy
cd ..
rm -f foo-1.0.tar.gz foo_1.0.orig.tar.gz
tar -cvzf foo-1.0.tar.gz foo-1.0
ln -sf foo-1.0.tar.gz foo_1.0.orig.tar.gz
cd foo-1.0
debmake 2>&1
test -x debian/rules

