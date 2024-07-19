#!/bin/sh
if [ -e setup.py ]; then
  python3 setup.py --description
else
  echo "Short description here"
fi
