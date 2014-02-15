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
import re
import sys
import debmake.read
import debmake.compat
import debmake.scanfiles
import debmake.yn
###########################################################################
# interpreter: warn binary dependency etc. if they are top 3 popular files
###########################################################################
def popular(type, msg, debs, extcount, yes):
    n = 3 # check files with the top 3 popular extensions
    if type in dict(extcount[0:n]).keys():
        settype = False
        for deb in debs:
            if deb['type'] == type:
                settype = True
                break
        if not settype:
            print('W: many ext = "{}" programs without -b set with "{}".'.format(type, deb['type']), file=sys.stderr)
            pass
            #
            debmake.yn.yn('do you continue packaging', 'pass', yes)
    return
###########################################################################
# analyze: called from debmake.main()
###########################################################################
def analyze(para):
    #######################################################################
    # binary package types: para['debs']
    #######################################################################
    setcompiler = False # for export
    setmultiarch = False # for override
    for i, deb in enumerate(para['debs']):
        # update binary package dependency by package type etc.
        # interpreters
        if deb['type'] == 'perl':
            para['debs'][i]['depends'].update({'perl'})
        elif deb['type'] == 'python':
            para['dh_with'].update({'python2'})
            para['debs'][i]['depends'].update({'python'})
        elif deb['type'] == 'python3':
            para['dh_with'].update({'python3'})
            para['debs'][i]['depends'].update({'python3'})
            para['override'].update({'python3'})
        elif deb['type'] == 'ruby':
            # XXX FIXME XXX what to set
            #para['dh_with'].update({'ruby'})
            para['debs'][i]['depends'].update({'ruby'})
        elif deb['type'] == 'script':
            pass
        elif deb['type'] == 'doc':
            pass
        elif deb['type'] == 'data':
            pass
        # ELF executables
        elif deb['type'] == 'bin':
            setcompiler = True
            if len(para['debs']) == 1:
                setmultiarch = True
        elif deb['type'] == 'lib':
            setcompiler = True
            setmultiarch = True
        else: # -dev -dbg
            pass
    if setcompiler:
        para['export'].update({'compiler'})
    if para['monoarch']:
        setmultiarch = False
    #######################################################################
    # auto-set build system by files in the base directory
    #######################################################################
    para['build_type'] = '' # reset value
    # check if '*.pro' for Qmake project exist in advance. 
    pro = glob.glob('*.pro')
    if pro:
        pro = pro[0]
    else:
        pro = ''
    # GNU coding standard with autotools = autoconf+automake
    if os.path.isfile('configure.ac') and \
            os.path.isfile('Makefile.am') and \
            os.path.isfile('configure') and \
            not ('autoreconf' in para['dh_with']):
        para['dh_with'].update({'autotools-dev'})
        para['build_type']      = 'Autotools'
        para['build_depends'].update({'autotools-dev'})
    elif os.path.isfile('configure.in') and \
            os.path.isfile('Makefile.am') and \
            os.path.isfile('configure') and \
            not ('autoreconf' in para['dh_with']):
        para['dh_with'].update({'autotools-dev'})
        para['build_type']      = 'Autotools (old)'
        para['build_depends'].update({'autotools-dev'})
        print('W: Use of configure.in has been deprecated since 2001.', file=sys.stderr)
    elif os.path.isfile('configure.ac') and \
            os.path.isfile('Makefile.am'):
        para['dh_with'].update({'autoreconf'})
        para['build_type']      = 'Autotools with autoreconf'
        para['build_depends'].update({'dh-autoreconf'})
    elif os.path.isfile('configure.in') and \
            os.path.isfile('Makefile.am'):
        para['dh_with'].update({'autoreconf'})
        para['build_type']      = 'Autotools with autoreconf (old)'
        para['build_depends'].update({'dh-autoreconf'})
        print('W: Use of configure.in has been deprecated since 2001.', file=sys.stderr)
    elif 'autoreconf' in para['dh_with']:
        print('E: missing configure.ac or Makefile.am required for "dh --with autoreconf".', file=sys.stderr)
        exit(1)
    # GNU coding standard with configure
    elif os.path.isfile('configure'):
        para['build_type']      = 'configure'
        if setmultiarch:
            para['override'].update({'multiarch'})
    # GNU coding standard with make
    elif os.path.isfile('Makefile'):
        para['build_type']      = 'make'
        if setmultiarch:
            para['override'].update({'multiarch'})
    # GNU coding standard with Cmake
    elif os.path.isfile('CMakeLists.txt'):
        para['build_type']      = 'Cmake'
        para['build_depends'].update({'cmake'})
        if setmultiarch:
            para['override'].update({'multiarch'})
    # Python distutils
    elif os.path.isfile('setup.py'):
        with open('setup.py', 'r') as f:
            line = f.readline()
        if re.search('python3', line):
            # http://docs.python.org/3/distutils/
            para['dh_with'].update({'python3'})
            para['build_type']      = 'Python3 distutils'
            para['build_depends'].update({'python3-all'})
            para['override'].update({'python3'})
        elif re.search('python', line):
            # http://docs.python.org/2/distutils/
            if debmake.compat.compat(para['compat']) < 9:
                para['dh_with'].update({'python2'})
            para['build_type']      = 'Python distutils'
            para['build_depends'].update({'python-all'})
        else:
            print('E: unknown python version.  check setup.py.', file=sys.stderr)
            exit(1)
    # Perl
    elif os.path.isfile('Build.PL'):
        # Prefered over Makefile.PL after debhelper v8
        para['build_type']      = 'Perl Module::Build'
        para['build_depends'].update({'perl'})
    elif os.path.isfile('Makefile.PL'):
        para['build_type']      = 'Perl ExtUtils::MakeMaker'
        para['build_depends'].update({'perl'})
    # Ruby
    elif os.path.isfile('setup.rb'):
        print('W: dh-make-ruby(1) (gem2deb package) may provide better packaging results.', file=sys.stderr)
        para['build_type']      = 'Ruby setup.rb'
        para['build_depends'].update({'ruby', 'gem2deb'})
    # Java
    elif os.path.isfile('build.xml'):
        para['build_type']      = 'Java ant'
        para['dh_with'].update({'javahelper'})
        # XXX FIXME XXX which compiler to use?
        para['build_depends'].update({'javahelper', 'gcj'})
        para['export'].update({'java', 'compiler'})
        para['override'].update({'java'})
        if setmultiarch:
            para['override'].update({'multiarch'})
    # Qmake
    elif os.path.isfile(pro):
        # XXX FIXME XXX Is this right?
        para['build_type']      = 'QMake'
        para['build_depends'].update({'qt4-qmake'})
        if setmultiarch:
            para['override'].update({'multiarch'})
    else:
        para['build_type']      = 'Unknown'
        if setmultiarch:
            para['override'].update({'multiarch'})
    print('I: build_type = {}'.format(para['build_type']), file=sys.stderr)
    #######################################################################
    # analize copyright+license content + file extensions
    # copyright, control: build/binary dependency, rules export/override
    #######################################################################
    # skip slow license+copyright check if debian/copyright exists
    if os.path.isfile('debian/copyright'):
        check = False
    else:
        check = True
    (para['bdata'], para['binary_files'], para['huge_files'], para['extcount']) = debmake.scanfiles.scanfiles(check=check)
    #######################################################################
    # compiler: set build dependency etc. if they are used
    if 'c' in dict(para['extcount']).keys():
        para['export'].update({'compiler'})
        if setmultiarch and para['build_type'][0:9] != 'Autotools':
            para['override'].update({'multiarch'})
    if 'java' in dict(para['extcount']).keys():
        if para['build_type'][0:4] != 'Java':
            # Non-ant build system
            para['build_type']      = 'Java'
            para['dh_with'].update({'javahelper'})
            para['build_depends'].update({'javahelper', 'gcj'})
            para['export'].update({'java', 'compiler'})
            para['override'].update({'java'})
            if setmultiarch and para['build_type'][0:9] != 'Autotools':
                para['override'].update({'multiarch'})
    if para['build_type'][0:4] == 'Java':
        print('W: Java support is not perfect. (/usr/share/doc/javahelper/tutorials.html)', file=sys.stderr)
    if 'vala' in dict(para['extcount']).keys():
        para['build_type']      = 'Vala'
        para['build_depends'].update({'valac'})
        para['export'].update({'compiler'})
        if setmultiarch and para['build_type'][0:9] != 'Autotools':
            para['override'].update({'multiarch'})
    #######################################################################
    # interpreter: warn binary dependency etc. if they are top 3 popular files
    popular('perl', '-b":perl, ..." missing. Continue?', para['debs'], para['extcount'], para['yes'])
    popular('python', '-b":python, ..." or -b":python3" missing. Continue?', para['debs'], para['extcount'], para['yes'])
    popular('ruby', '-b":ruby, ..." missing. Continue?', para['debs'], para['extcount'], para['yes'])
    #######################################################################
    # set build dependency if --with requests (to be safe)
    #######################################################################
    if 'python2' in para['dh_with']:
        para['build_depends'].update({'python-all'})
    if 'python3' in para['dh_with']:
        para['build_depends'].update({'python3-all'})
    #######################################################################
    return para

if __name__ == '__main__':
    print('no test')

