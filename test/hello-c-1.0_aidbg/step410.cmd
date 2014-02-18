# Debianize (initial)
L "rm -rf ${PROJECT}"
L "debmake -a ${PROJECT}.tar.gz -b',-dbg' -s -i debuild"
