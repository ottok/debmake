# Debianize (initial)
CD ./debian
cd ./debian
L "rm -f *.do* *.examples *.info *.links *.m*  *.p*"
L "rm hello-c-dbg.install"
L "echo usr/bin/hello > hello-c.install" 
L "echo usr/share/hello/hello.data > hello-data.install"
L "echo usr/bin/hello-sh > hello-sh.install"
