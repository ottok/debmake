echo "The basic debmake usage (empty)"
# This is leader script to set up $TESTDIR
# Following should output nothing
CD $BASEDIR >/dev/null
cd $BASEDIR
rm -rf $TESTDIR
PROJECT="package"
echo $PROJECT > $BASEDIR/project
mkdir -p $TESTDIR/$PROJECT
CD $TESTDIR >/dev/null
cd $TESTDIR
