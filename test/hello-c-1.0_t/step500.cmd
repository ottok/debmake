# make deb
PROJECT=$(echo hello-c*.orig.tar.gz|sed -e s/hello-c_/hello-c-/ -e s/.orig.tar.gz//)
VERSION=$(echo hello-c*.orig.tar.gz|sed -e s/hello-c_// -e s/.orig.tar.gz//)
echo "$VERSION" >$BASEDIR/version.log
echo ":snapshotversion: $VERSION" >$BASEDIR/snapshotversion.log
CD $PROJECT
cd $PROJECT
L "debuild"
