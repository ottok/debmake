echo "The basic debmake usage (Makefile): ${PROJECT}/ w/o tar (1 step)"
echo "*** This should fail later ***"
# This is leader script to set up $TESTDIR
# Following should output nothing
CD $BASEDIR >/dev/null
cd $BASEDIR
rm -rf $TESTDIR
mkdir -p $TESTDIR
cp -a ${COMMONDIR}/base/${PROJECT}/. ${TESTDIR}/${PROJECT}
CD $TESTDIR >/dev/null
cd $TESTDIR
