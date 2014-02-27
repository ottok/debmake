# Fake download session
PACKAGE=libkkc
VERSION=0.3.2
TARBALL=${PACKAGE}-${VERSION}.tar.gz
export URL=https://bitbucket.org/libkkc/libkkc/downloads/${TARBALL}
echo "${PACKAGE}-${VERSION}" >${BASEDIR}/project
# cheat download if you already done it once
# ../../../../ = /debmake/test/remote-lib_a/test/
if [ -f ../../../../${TARBALL} ]; then
  echo " \$ wget $URL"
  echo " ..."
  echo "Saving to: ‘${TARBALL}’"
  echo " ..."
  cp -f ../../../../${TARBALL} ${TARBALL}
else
  L "wget $URL"
  cp -f ${TARBALL} ../../../../${TARBALL}
fi
