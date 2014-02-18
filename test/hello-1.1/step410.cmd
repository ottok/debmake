# Debianize (initial)
L "rm -rf hello-1.1"
L "debmake -b'-c,-c-dbg,-data:data,-sh:script' -a hello-1.1.tar.gz"
