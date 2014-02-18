# Debianize (mainual patch)
# This is behind the scene
# quietly to ${TESTDIR}
cd ${TESTDIR}
#
GOOD=hello-c-1.0
cp -a ${COMMONDIR}/base/$GOOD/. $TESTDIR/$GOOD
# diff without time stamp
echo "From: Foo Bar <foo@example.org" >${PROJECTDIR}/debian/patches/0001-destdir.patch
echo "Description: make Makefile to support GNU coding standard" >>${PROJECTDIR}/debian/patches/0001-destdir.patch
echo " \$DESTDIR: debian/hello-c" >>${PROJECTDIR}/debian/patches/0001-destdir.patch
echo " \$prefix:  /usr/local -> /usr" >>${PROJECTDIR}/debian/patches/0001-destdir.patch
echo "" >>${PROJECTDIR}/debian/patches/0001-destdir.patch
# we should be at ${TESTDIR}
diff -u ${PROJECT}/Makefile ${GOOD}/Makefile |\
sed -e 's/^\([-+][-+][-+] [^ ][^ ]*\)\t.*$/\1/' >>${PROJECTDIR}/debian/patches/0001-destdir.patch
rm -rf $TESTDIR/$GOOD
# quietly back to ${PROJECTDIR}
cd ${PROJECTDIR}
# show what has been done
L "cat debian/patches/0001-destdir.patch"
