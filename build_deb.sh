#!/bin/sh

# clean up from last build
rm -r deb_dist

# build binary package
python setup.py --command-packages=stdeb.command bdist_deb
