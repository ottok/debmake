echo "The basic debmake usage (autotools)"
# This is leader script to set up $TESTDIR
# Following should output nothing
CD $BASEDIR >/dev/null
cd $BASEDIR
rm -rf $TESTDIR
mkdir -p $TESTDIR
cp -a ${COMMONDIR}/base/${PROJECT}/. ${TESTDIR}/${PROJECT}
CD $TESTDIR >/dev/null
cd $TESTDIR
tar -czf ${PROJECT}.tar.gz ${PROJECT} >/dev/null
rm -rf $TESTDIR/${PROJECT}
