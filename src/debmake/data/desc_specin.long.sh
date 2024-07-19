#!/bin/sh
SPEC=$(ls -1 ./*.spec.in | head -n1)
if [ -e $SPEC ]; then
  sed -e '1,/^%description/d' $SPEC | sed -e '/^%/,$d'
else
  echo " Long description here"
fi
