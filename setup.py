#!/usr/bin/python3
# vi:se ts=4 sts=4 et ai:
from distutils.core import setup

from debmake import __programname__, __version__

import glob

setup(name=__programname__,
    version=__version__,
    description='Debian package making utility',
    long_description='Debian source package making utility to populate the debian directory.',
    author='Osamu Aoki',
    author_email='osamu@debian.org',
    url='http://people.debian.org/~osamu/',
    packages=[__programname__],
    package_dir={__programname__: __programname__},
    scripts=['scripts/' + __programname__ ],
    data_files=[
        ('share/debmake/extra', glob.glob('extra/*')),
        ('share/doc/debmake', glob.glob('doc/*')),
        ],
    classifiers = ['Development Status :: 3 - Alpha',
        'Environment :: Console', 
        'Intended Audience :: Developers', 
        'License :: OSI Approved :: MIT License', 
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3',
        'Topic :: Utilities',
    ],
    platforms   = 'POSIX',
    license     = 'GNU General Public License v2 or later (GPLv2+)'
)


