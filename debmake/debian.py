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
import glob
import os
import sys
import debmake.cat
import debmake.changelog
import debmake.control
import debmake.copyright
import debmake.local_options
import debmake.readme_debian
import debmake.rules
import debmake.sed
import debmake.watch
#######################################################################
def debian(para):
    ###################################################################
    # set level for the extra file outputs
    ###################################################################
    if para['extra'] == '': # default
        if os.path.isfile('debian/changelog'):
            print('I: found "debian/changelog"', file=sys.stderr)
            para['extra'] = '0'
        elif os.path.isfile('debian/control'):
            print('I: found "debian/control"', file=sys.stderr)
            para['extra'] = '0'
        elif os.path.isfile('debian/copyright'):
            print('I: found "debian/copyright"', file=sys.stderr)
            para['extra'] = '0'
        elif os.path.isfile('debian/rules'):
            print('I: found "debian/rules"', file=sys.stderr)
            para['extra'] = '0'
        elif len(para['debs']) == 1:
            print('I: single binary package', file=sys.stderr)
            para['extra'] = '1'
        else:
            print('I: multi binary packages: {}'.format(len(para['debs'])), file=sys.stderr)
            para['extra'] = '2'
    try:
        extra = int(para['extra'])
    except:
        extra = 4
    print('I: debmake -x "{}" ...'.format(extra), file=sys.stderr)
    ###################################################################
    # common variables
    ###################################################################
    package = para['debs'][0]['package']    # the first binary package name
    substlist = {
        '@PACKAGE@': package,
        '@UCPACKAGE@': package.upper(),
        '@YEAR@': para['year'],
        '@FULLNAME@': para['fullname'],
        '@EMAIL@': para['email'],
        '@SHORTDATE@': para['shortdate'],
        '@BINPACKAGE@': package,
    }
    binlist = {'script', 'perl', 'python', 'python3', 'bin'}
    have_doc = False
    for deb in para['debs']:
        if deb['type'] == 'doc':
            have_doc = True
    ###################################################################
    # must have files (level=0)
    ###################################################################
    debmake.cat.cat('debian/changelog', debmake.changelog.changelog(para))
    debmake.cat.cat('debian/control', debmake.control.control(para))
    debmake.cat.cat('debian/copyright', debmake.copyright.copyright(para['package'], para['license']))
    debmake.cat.cat('debian/rules', debmake.rules.rules(para))
    os.chmod('debian/rules', 0o755)
    ###################################################################
    # optional files which should be created for the new source (level=1)
    # no interactive editting required.
    ###################################################################
    if extra >= 1:
        if para['native']:
            debmake.cat.cat('debian/source/format', '3.0 (native)')
        else:
            debmake.cat.cat('debian/source/format', '3.0 (quilt)')
        debmake.cat.cat('debian/compat', para['compat'])
        debmake.cat.cat('debian/watch', debmake.watch.watch(para))
        debmake.cat.cat('debian/source/local-options', debmake.local_options.local_options())
        debmake.cat.cat('debian/README.Debian', debmake.readme_debian.readme_debian(para))
    ###################################################################
    # optional files which should be created for the new source (level=2)
    # some interactive editting are desirable.
    # * create templates only for the first binary package:
    #   package.menu, package.docs, package.examples, package.manpages, 
    #   package.preinst, package.prerm, package.postinst, package.postrm
    # * create for all binary packages:
    #   package.install
    ###################################################################
    if extra >= 2:
        srcdir = para['base_path'] + '/share/debmake/extra2/'
        destdir = 'debian/'
        debmake.sed.sed(srcdir, destdir, substlist, package)
        if len(para['debs']) == 1: # if single binary deb
            srcdir = para['base_path'] + '/share/debmake/extra2single/'
            debmake.sed.sed(srcdir, destdir, substlist, package)
        else: # if multi-binary debs
            for deb in para['debs']:
                substlist['@BINPACKAGE@'] = deb['package']
                type = deb['type']
                if type in binlist:
                    if have_doc:
                        type = 'bin'
                    else: # no -doc package
                        type = 'binall'
                srcdir = para['base_path'] + '/share/debmake/extra2' + type + '/'
                debmake.sed.sed(srcdir, destdir, substlist, deb['package'])
    ###################################################################
    # rarely used optional files (level=3)
    # provided as the dh_make compatibilities. (files with ".ex" postfix)
    #     (create templates only for the first binary package)
    ###################################################################
    if extra >= 3:
        srcdir = para['base_path'] + '/share/debmake/extra3/'
        destdir = 'debian/'
        debmake.sed.sed(srcdir, destdir, substlist, package)
    ###################################################################
    # copyright file examples (level=4)
    ###################################################################
    if extra >= 4:
        srcdir = para['base_path'] + '/share/debmake/extra4/'
        destdir = 'debian/license-examples/'
        debmake.sed.sed(srcdir, destdir, substlist, package)
    else:
        print('I: run "debmake -x{}" to get more template files'.format(extra + 1), file=sys.stderr)
    return

#######################################################################
# Test script
#######################################################################
if __name__ == '__main__':
    print('no test')

