echo ' $ vim Makefile'
echo ' ...'
GOOD=hello-c-1.0
cp -f ${COMMONDIR}/base/$GOOD/Makefile Makefile
L "cat Makefile"
L "dquilt refresh"
L "cat debian/patches/0001-destdir.patch"
