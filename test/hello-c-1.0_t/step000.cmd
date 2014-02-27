echo "The basic debmake usage (Makefile): hello-c with tar (2 steps)"
# This is leader script to set up $TESTDIR
# Following should output nothing
CD $BASEDIR >/dev/null
cd $BASEDIR
rm -rf $TESTDIR
mkdir -p $TESTDIR
cp -a ${COMMONDIR}/base/${PROJECT}/. ${TESTDIR}/hello-c
CD $TESTDIR >/dev/null
cd $TESTDIR
