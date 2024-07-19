#!/bin/sh
if [ -e META.yml ]; then
  sed -n -e '/^abstract:/s/abstract: *//p' META.yml | sed -e "s/^'//" -e "s/'$//" -e 's/^"//' -e 's/"$//'
else
  echo "Short description here"
fi
