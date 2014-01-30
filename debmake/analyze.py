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
###########################################################################
# analyze: called from debmake.main()
###########################################################################
def analyze(para):
    #######################################################################
    # analize source (preparation)
    #######################################################################
    # check if '*.pro' for Qmake project exist? set pro
    pro = glob.glob('*.pro')
    if pro:
        pro = pro[0]
    else:
        pro = ''
    #######################################################################
    # analize source for main build system (main)
    #######################################################################
    if os.path.isfile('configure.ac') and \
            os.path.isfile('Makefile.am') and \
            os.path.isfile('configure') and \
            not ('autoreconf' in para['dh_with']):
        para['dh_with'].update({'autotools-dev'})
        para['build_type']      = 'Autotools'
        para['build_depends'].update({'autotools-dev'})
    elif os.path.isfile('configure.ac') and \
            os.path.isfile('Makefile.am'):
        para['dh_with'].update({'autoreconf'})
        para['build_type']      = 'Autotools with autoreconf'
        para['build_depends'].update({'dh-autoreconf'})
    elif 'autoreconf' in para['dh_with']:
        print('E: missing configure.ac or Makefile.am required for "dh --with autoreconf".', file=sys.stderr)
        exit(1)
    elif os.path.isfile('configure'):
        para['build_type']      = 'configure'
    elif os.path.isfile('Makefile'):
        para['build_type']      = 'make'
    elif os.path.isfile('CMakeLists.txt'):
        para['build_type']      = 'Cmake'
        para['build_depends'].update({'cmake'})
    elif os.path.isfile('setup.py'):
        # Python distutils
        with open('setup.py', 'r') as f:
            line = f.readline()
        if re.search('python3', line):
            # http://docs.python.org/3/distutils/
            para['dh_with'].update({'python3'})
            para['build_type']      = 'Python3 distutils'
            para['build_depends'].update({'python3-all'})
        elif re.search('python', line):
            # http://docs.python.org/2/distutils/
            para['dh_with'].update({'python2'})
            para['build_type']      = 'Python distutils'
            para['build_depends'].update({'python-all'})
        else:
            print('E: unknown python version.  check setup.py.', file=sys.stderr)
            exit(1)
    elif os.path.isfile('Build.PL'):
        # Prefered over Makefile.PL after debhelper v8
        para['dh_with'].update({'perl_build'})
        para['build_type']      = 'Perl Module::Build'
        para['build_depends'].update({'perl'})
    elif os.path.isfile('Makefile.PL'):
        para['dh_with'].update({'perl_makemaker'})
        para['build_type']      = 'Perl ExtUtils::MakeMaker'
        para['build_depends'].update({'perl'})
    elif os.path.isfile('build.xml'):
        # XXX FIXME XXX Is this right?
        para['build_type']      = 'Java Ant'
        para['build_depends'].update({'javac'})
    elif os.path.isfile(pro):
        # XXX FIXME XXX Is this right?
        para['build_type']      = 'QMake'
        para['build_depends'].update({'qt4-qmake'})
    else:
        para['build_type']      = 'Unknown'
    #######################################################################
    # binary package type induced build dependency
    #######################################################################
    for i, deb in enumerate(para['debs']):
        # update binary package dependency by package type etc.
        if deb['type'] == 'perl':
            #para['dh_with'].update({'perl'})
            print('W: no "dh -with perl" added.  Maybe default works OK.', file=sys.stderr)
            para['debs'][i]['depends'].update({'perl'})
        elif deb['type'] == 'python':
            para['dh_with'].update({'python2'})
            para['debs'][i]['depends'].update({'python'})
        elif deb['type'] == 'python3':
            para['dh_with'].update({'python3'})
            para['debs'][i]['depends'].update({'python3'})
        else:
            pass
    #######################################################################
    # extra build depends if --with requests
    #######################################################################
    if 'python2' in para['dh_with']:
        para['build_depends'].update({'python-all'})
    if 'python3' in para['dh_with']:
        para['build_depends'].update({'python3-all'})
    if 'perl_build' in para['dh_with']:
        para['build_depends'].update({'perl'})
    if 'perl_makemaker' in para['dh_with']:
        para['build_depends'].update({'perl'})
    #######################################################################
    # set override string
    #######################################################################
    para['override'] = ''
    if len(para['debs']) == 1:
        build_dir = 'debian/' + para['debs'][0]['package']
    else:
        build_dir = 'debian/tmp'
    #
    override_dir = para['base_path'] + '/share/debmake/extra0override/'
    #
    if 'python3' in para['dh_with']:
        para['override'] += debmake.read.read(override_dir + 'python3').format(build_dir).rstrip() + '\n'
    #
    if not para['monoarch']:
        para['override'] += debmake.read.read(override_dir + 'multiarch').format(build_dir).rstrip() + '\n'
    #
    for deb in para['debs']:
        if deb['type'] == 'dbg':
            para['override'] += debmake.read.read(override_dir + 'dbg').format(deb['package']).rstrip() + '\n'
            break
    #######################################################################
    return para

if __name__ == '__main__':
    print('no test')

