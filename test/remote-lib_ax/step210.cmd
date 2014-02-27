# Debianize (initial)
# ${PROJECT} = libkkc-<<version>>
echo " \$ debmake -b'libkkc2,-utils,libkkc2-dbg,-utils-dbg,-dev,-common:data'\\"
echo "            -s -a ${PROJECT}.tar.gz"
debmake -b'libkkc2,-utils,libkkc2-dbg,-utils-dbg,-dev,-common:data' -s -a ${PROJECT}.tar.gz
