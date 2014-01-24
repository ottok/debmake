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
        ('share/debmake/extra0', glob.glob('extra0/*')),
        ('share/debmake/extra0desc', glob.glob('extra0desc/*')),
        ('share/debmake/extra0desc_long', glob.glob('extra0desc_long/*')),
        ('share/debmake/extra0override', glob.glob('extra0override/*')),
        ('share/debmake/extra1', glob.glob('extra1/*')),
        ('share/debmake/extra1patches', glob.glob('extra1patches/*')),
        ('share/debmake/extra1source', glob.glob('extra1source/*')),
        ('share/debmake/extra2bin', glob.glob('extra2bin/*')),
        ('share/debmake/extra2binall', glob.glob('extra2binall/*')),
        ('share/debmake/extra2data', glob.glob('extra2data/*')),
        ('share/debmake/extra2dbg', glob.glob('extra2dbg/*')),
        ('share/debmake/extra2dev', glob.glob('extra2dev/*')),
        ('share/debmake/extra2doc', glob.glob('extra2doc/*')),
        ('share/debmake/extra2lib', glob.glob('extra2lib/*')),
        ('share/debmake/extra2multi', glob.glob('extra2multi/*')),
        ('share/debmake/extra2single', glob.glob('extra2single/*')),
        ('share/debmake/extra3', glob.glob('extra3/*')),
        ('share/debmake/extra4', glob.glob('extra4/*')),
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
    license     = 'MIT License'
)


