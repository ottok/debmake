echo "The debmake usage library packaging"
echo "This needs to be run under jessie/sid"

# This is leader script to set up $TESTDIR
# Following should output nothing
CD $BASEDIR >/dev/null
cd $BASEDIR
rm -rf $TESTDIR
mkdir -p $TESTDIR
CD $TESTDIR >/dev/null
cd $TESTDIR
