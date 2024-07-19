#!/bin/sh
# spec file
SPEC=$(ls -1 ./*.spec.in | head -n1)
if [ -e $SPEC ]; then
  sed -n -e '/^Summary:/p/Summary: *//p' *.spec.in
else
  echo "Short description here"
fi
