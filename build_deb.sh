#!/bin/sh

# clean up from last build
if [ -d "deb_dist" ]; then
   rm -r "deb_dist"
fi

# build binary package
python setup.py --command-packages=stdeb.command bdist_deb
