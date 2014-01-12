#!/usr/bin/python3
# vim:se tw=0 sts=4 ts=4 et ai:
"""
Copyright © 2014 Osamu Aoki

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be included
in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""
import os
import re
import sys
###########################################################################
# sanity: called from debmake.main()
###########################################################################
def sanity(para):
    #######################################################################
    # Normalize para[] for each exclusive build case (-d -t -a)
    #######################################################################
    if para['archive']: # -a
        parent = ''
        if not os.path.isfile(para['tarball']):
            print('E: Non-existing tarball name {}'.format(para['tarball']), file=sys.stderr)
            exit(1)
        # tarball: package-version.tar.gz or package_version.tar.gz
        rebasetar = re.match(r'([^/]+)[-_]([^-/_]+)\.(tar\.gz|tar\.bz2|tar\.xz)$', para['tarball'])
        # tarball: package_version.orig.tar.gz
        reorigtar = re.match(r'([^/]+)_([^-/_]+)\.orig\.(tar\.gz|tar\.bz2|tar\.xz)$', para['tarball'])
        if para['package'] and para['version'] and para['targz']:
            pass # manual package/version/targz
        else:
            if rebasetar:
                para['package'] = rebasetar.group(1)
                para['version'] = rebasetar.group(2)
                para['targz'] = rebasetar.group(3)
            elif reorigtar:
                para['package'] = reorigtar.group(1)
                para['version'] = reorigtar.group(2)
                para['targz'] = reorigtar.group(3)
            else:
                print('E: Non-supported tarball name {}'.format(para['tarball']), file=sys.stderr)
                exit(1)
    #######################################################################
    if not para['archive']: # not -a
        parent = os.path.basename(os.getcwd())
        # set para['targz']
        if para['targz'] == '':
            para['targz'] = 'tar.gz'
        elif para['targz'][0] == 'g':
            para['targz'] = 'tar.gz'
        elif para['targz'][0] == 'b':
            para['targz'] = 'tar.bz2'
        elif para['targz'][0] == 'x':
            para['targz'] = 'tar.xz'
        elif para['targz'] == 'tar.gz':
            pass
        elif para['targz'] == 'tar.bz2':
            pass
        elif para['targz'] == 'tar.xz':
            pass
        else:
            print('E: --targz (-z) value is invalid: {}'.format(para['targz']), file=sys.stderr)
            exit(1)
    #######################################################################
    # check changelog for package/version/revision (non-native package)
    if not para['native'] and os.path.isfile('debian/changelog'):
        with open('debian/changelog', 'r') as f:
            line = f.readline()
        pkgver = re.match('([^ \t]+)[ \t]+\(([^()]+)-([^-()]+)\)', line)
        if pkgver:
            if para['package'] == '':
                para['package'] = pkgver.group(1)
            elif para['package'] != pkgver.group(1):
                print('E: -p "{}" != changelog "{}"'.format(para['package'], pkgver.group(1)), file=sys.stderr)
                exit(1)
            if para['version'] == '':
                para['version'] = pkgver.group(2)
            elif para['version'] != pkgver.group(2):
                print('E: -u "{}" != changelog "{}"'.format(para['version'], pkgver.group(2)), file=sys.stderr)
                exit(1)
            if para['revision'] == '':
                para['revision'] = pkgver.group(3)
            elif para['revision'] != pkgver.group(3):
                print('E: -r "{}" != changelog "{}"'.format(para['version'], pkgver.group(3)), file=sys.stderr)
                exit(1)
        else:
            print('E: changelog start with "{}"'.format(line), file=sys.stderr)
            exit(1)
    #######################################################################
    # set parent/basedir/tarball/package/version/revision
    para['parent'] = parent
    if para['archive']:
        para['basedir'] = para['package'] + '-' + para['version']
    elif para['dist']: # -d
        # differ version/tarball/basedir
        if para['package'] == '':
            para['package'] = parent
        para['version'] = ''
        para['basedir'] = ''
        para['tarball'] = ''
    else: # -t or normal (native/non-native)
        pkgver = re.match('^([^_]+)-([^-_]+)$', parent)
        if pkgver:
            if para['package'] == '':
                para['package'] = pkgver.group(1)
            elif para['package'] != pkgver.group(1):
                print('E: -p "{}" != changelog "{}"'.format(para['package'], pkgver.group(1)), file=sys.stderr)
                exit(1)
            if para['version'] == '':
                para['version'] = pkgver.group(2)
            elif para['version'] != pkgver.group(2):
                print('E: -u "{}" != changelog "{}"'.format(para['version'], pkgver.group(2)), file=sys.stderr)
                exit(1)
        else:
            print('E: invalid parent directory: {}'.format(parent), file=sys.stderr)
            print('E: rename parent directory to "packagename-version".', file=sys.stderr)
            exit(1)
        para['basedir'] = para['package'] + '-' + para['version']
        para['tarball'] = para['package'] + '-' + para['version'] + '.' + para['targz']
    if para['revision'] == '':
        para['revision'] = '1'
    #######################################################################
    # Dynamic content with package name etc.
    #######################################################################
    para['section'] = 'unknown'
    para['priority'] = 'extra'
    para['homepage'] = '<insert the upstream URL, if relevant>'
    para['vcsvcs'] = 'git://anonscm.debian.org/collab-maint/' + para['package'] + '.git'
    para['vcsbrowser'] = 'http://anonscm.debian.org/gitweb/?p=collab-maint/' + para['package'] + '.git'
    return para