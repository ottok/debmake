#!/bin/sh
# ruby
if [ -e Rakefile ]; then
  sed -n -e '/gem.summary *=/s/gem.summary *= *//p' Rakefile | sed -e "s/^'//" -e "s/'$//" -e 's/^"//' -e 's/"$//'
else
  echo "Short description here"
fi
