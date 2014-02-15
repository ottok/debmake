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
import debmake.control
import debmake.copyright
import debmake.sed
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
        '@DATE@': para['date'],
        '@DEBMAKEVER@': para['program_version'],
        '@BINPACKAGE@': package,
        '@COMPAT@': para['compat'],
    }
    if para['native']:
        substlist['@PKGFORMAT@'] = '3.0 (native)'
        substlist['@VERREV@'] = para['version']
    else:
        substlist['@PKGFORMAT@'] = '3.0 (quilt)'
        substlist['@VERREV@'] = para['version'] + '-' + para['revision']
    ###################################################################
    # check which package have the documentation
    ###################################################################
    binlist = {'bin', 'perl', 'python', 'python3', 'ruby', 'script'}
    docpackage = ''
    for deb in para['debs']:
        if deb['type'] == 'doc':
            docpackage = deb['package']
    if docpackage == '':
        for deb in para['debs']:
            if deb['type'] in binlist:
                docpackage = deb['package']
                break
    if docpackage == '':
        docpackage = para['debs'][0]['package']
    #######################################################################
    # set export string
    #######################################################################
    export_dir = para['base_path'] + '/share/debmake/extra0export/'
    substlist['@EXPORT@'] = ''
    if 'compiler' in para['export']:
        substlist['@EXPORT@'] += debmake.read.read(export_dir + 'compiler').rstrip() + '\n'
    if 'java' in para['export']:
        substlist['@EXPORT@'] += debmake.read.read(export_dir + 'java').rstrip() + '\n'

    #######################################################################
    # set override string
    #######################################################################
    override_dir = para['base_path'] + '/share/debmake/extra0override/'
    substlist['@OVERRIDE@'] = ''
    if len(para['debs']) == 1:
        build_dir = 'debian/' + para['debs'][0]['package']
    else:
        build_dir = 'debian/tmp'
    if 'dbg' in para['override']:
        substlist['@OVERRIDE@'] += debmake.read.read(override_dir + 'dbg').format(build_dir).rstrip() + '\n'
    if 'python3' in para['override']:
        substlist['@OVERRIDE@'] += debmake.read.read(override_dir + 'python3').format(build_dir).strip() + '\n'
    if 'multiarch' in para['override']:
        substlist['@OVERRIDE@'] += debmake.read.read(override_dir + 'multiarch').rstrip() + '\n'
    if 'java' in para['override']:
        substlist['@OVERRIDE@'] += debmake.read.read(override_dir + 'java').rstrip() + '\n'

    ###################################################################
    # 4 configuration files which must exist (level=0)
    ###################################################################
    debmake.cat.cat('debian/control', debmake.control.control(para))
    debmake.cat.cat('debian/copyright', debmake.copyright.copyright(para['package'], para['license'], para['bdata'], para['binary_files'], para['huge_files']))
    if para['dh_with'] == set(): # no dh_with
        substlist['@DHWITH@'] = ''
    else:
        substlist['@DHWITH@'] = '--with "{}"'.format(','.join(para['dh_with']))
    confdir = para['base_path'] + '/share/debmake/extra0/'
    debmake.sed.sed(confdir, 'debian/', substlist, package) # changelog, rules
    os.chmod('debian/rules', 0o755)
    ###################################################################
    # These should be created for the new source (level=1)
    # Basic configuration files for debhelper(7) etc.
    # No interactive editting required to work.
    ###################################################################
    if extra >= 1:
        confdir = para['base_path'] + '/share/debmake/extra1/'
        debmake.sed.sed(confdir, 'debian/', substlist, package)
        confdir = para['base_path'] + '/share/debmake/extra1source/'
        debmake.sed.sed(confdir, 'debian/source/', substlist, package)
        if not para['native']:
            confdir = para['base_path'] + '/share/debmake/extra1patches/'
            debmake.sed.sed(confdir, 'debian/patches/', substlist, package)
    ###################################################################
    # Optional files which is nice to be created for the new source (level=2)
    # Harmless but some interactive editting are desirable.
    # * create templates only for the first binary package:
    #   package.menu, package.docs, package.examples, package.manpages, 
    #   package.preinst, package.prerm, package.postinst, package.postrm
    # * create for all binary packages: package.install
    # * create for lib package: package.symbol
    ###################################################################
    if extra >= 2:
        if len(para['debs']) == 1: # if single binary deb
            confdir = para['base_path'] + '/share/debmake/extra2single/'
            debmake.sed.sed(confdir, 'debian/', substlist, package)
        else: # if multi-binary debs
            confdir = para['base_path'] + '/share/debmake/extra2multi/'
            debmake.sed.sed(confdir, 'debian/', substlist, package)
            for deb in para['debs']:
                substlist['@BINPACKAGE@'] = deb['package']
                type = deb['type']
                if type in binlist:
                    if deb['package'] == docpackage:
                        type = 'binall'
                    else:
                        type = 'bin'
                confdir = para['base_path'] + '/share/debmake/extra2' + type + '/'
                debmake.sed.sed(confdir, 'debian/', substlist, deb['package'])
    ###################################################################
    # Rarely used optional files (level=3)
    # Provided as the dh_make compatibilities. (files with ".ex" postfix)
    #     (create templates only for the first binary package)
    ###################################################################
    substlist['@BINPACKAGE@'] = package # just in case
    if extra >= 3:
        confdir = para['base_path'] + '/share/debmake/extra3/'
        debmake.sed.sed(confdir, 'debian/', substlist, package)
    ###################################################################
    # copyright file examples (level=4)
    ###################################################################
    if extra >= 4:
        confdir = para['base_path'] + '/share/debmake/extra4/'
        debmake.sed.sed(confdir, 'debian/license-examples/', substlist, package)
    else:
        print('I: run "debmake -x{}" to get more template files'.format(extra + 1), file=sys.stderr)
    return

#######################################################################
# Test script
#######################################################################
if __name__ == '__main__':
    print('no test')

