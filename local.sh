#!/usr/bin/bash

# local.sh
#

echo "Cleaning builddir directory"
rm -r builddir

echo "Rebuilding"
meson setup builddir
if [ -z "$1" ]
  then
    meson configure builddir -Dprefix="$(pwd)/builddir" -Dbuildtype=debug 
  else
    meson configure builddir -Dprefix="$(pwd)/builddir" -Dbuildtype=debug -Ddnf_backend=$1
fi
ninja -C builddir install

echo "Running"
ninja -C builddir run
