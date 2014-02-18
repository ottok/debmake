echo "The basic debmake usage (Makefile): vcsdir/ w/o tar (1 step)"
# This is leader script to set up $TESTDIR
# Following should output nothing
CD $BASEDIR >/dev/null
cd $BASEDIR
rm -rf $TESTDIR
mkdir -p $TESTDIR
cp -a ${COMMONDIR}/base/${PROJECT}/. ${TESTDIR}/${PROJECT}
mv ${TESTDIR}/${PROJECT} ${TESTDIR}/vcsdir
CD $TESTDIR >/dev/null
cd $TESTDIR
