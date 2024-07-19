#!/bin/sh
if [ -e setup.py ]; then
  python3 setup.py --long-descriiption
else
  echo " Long description here"
fi
