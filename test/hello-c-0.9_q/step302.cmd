# fake editor session
echo ' $ dquilt header -e'
echo ' ... '
mv ${PROJECTDIR}/debian/patches/0001-destdir.patch ${PROJECTDIR}/debian/patches/0001-destdir.patchx
echo "From: Foo Bar <foo@example.org>" >${PROJECTDIR}/debian/patches/0001-destdir.patch
echo "Description: make Makefile to support GNU coding standard" >>${PROJECTDIR}/debian/patches/0001-destdir.patch
echo " \$DESTDIR: debian/hello-c" >>${PROJECTDIR}/debian/patches/0001-destdir.patch
echo " \$prefix:  /usr/local -> /usr" >>${PROJECTDIR}/debian/patches/0001-destdir.patch
echo "" >>${PROJECTDIR}/debian/patches/0001-destdir.patch
cat ${PROJECTDIR}/debian/patches/0001-destdir.patchx >> ${PROJECTDIR}/debian/patches/0001-destdir.patch
rm ${PROJECTDIR}/debian/patches/0001-destdir.patchx
L "cat debian/patches/0001-destdir.patch"
L "dquilt pop -a"
L 'cat debian/patches/series'
