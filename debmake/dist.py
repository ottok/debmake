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
import subprocess
import sys
###########################################################################
# dist: called from debmake.main()
###########################################################################
def dist(para):
    print('I: pwd = "{}"'.format(os.getcwd()), file=sys.stderr)
    #######################################################################
    # make distribution tarball using the Autotools
    #######################################################################
    if os.path.isfile('configure.ac') and os.path.isfile('Makefile.am'):
        command = 'autoreconf -ivf && ./configure --prefix "/usr" && make distcheck'
        print('I: {}'.format(command), file=sys.stderr)
        if subprocess.call(command, shell=True) != 0:
            print('E: autotools failed.', file=sys.stderr)
            exit(1)
        distdir = '.'
    #######################################################################
    # make distribution tarball using setup.py
    #######################################################################
    elif os.path.isfile('setup.py'):
        # Python distutils
        with open('setup.py', 'r') as f:
            line = f.readline()
        if re.search('python3', line):
            # http://docs.python.org/3/distutils/
            command = 'python3 setup.py sdist'
        else:
            # http://docs.python.org/2/distutils/
            command = 'python setup.py sdist'
        print('I: {}'.format(command), file=sys.stderr)
        if subprocess.call(command, shell=True) != 0:
            print('E: setup.py failed.', file=sys.stderr)
            exit(1)
        distdir = 'dist'
    #######################################################################
    # make distribution tarball using Build.PL
    #######################################################################
    elif os.path.isfile('Build.PL'):
        # perl Build.PL
        command = 'perl Build.PL && ./Build distcheck && ./Build disttest && ./Build dist'
        print('I: {}'.format(command), file=sys.stderr)
        if subprocess.call(command, shell=True) != 0:
            print('E: perl Build.PL failed.', file=sys.stderr)
            exit(1)
        distdir = '.'
    #######################################################################
    # make distribution tarball using Makefile.PL
    #######################################################################
    elif os.path.isfile('Makefile.PL'):
        # perl Makefile.PL
        command = 'perl Makefile.PL && make dist'
        print('I: {}'.format(command), file=sys.stderr)
        if subprocess.call(command, shell=True) != 0:
            print('E: perl Makefile.PL failed.', file=sys.stderr)
            exit(1)
        distdir = '.'
    #######################################################################
    # make distribution tarball for other sources
    #######################################################################
    else:
        if os.path.isfile('CMakeLists.txt'):
            # CMake source tree
            print('E: CMake. Use --tar (-t).', file=sys.stderr)
        else:
            # Non standard source tree
            print('E: unsupported for --dist (-d). Use --tar (-t).', file=sys.stderr)
        exit(1)
    #######################################################################
    # set version by the tarball name
    #######################################################################
    somepackage1 = distdir + '/*.tar.xz'
    somepackage2 = distdir + '/*.tar.gz'
    somepackage3 = distdir + '/*.tar.bz2'
    files = glob.glob(somepackage1) + glob.glob(somepackage2) + glob.glob(somepackage3)
    if files:
        for file in files:
            print('I: -> {} created'.format(file), file=sys.stderr)
        para['tarball'] = files[0][len(distdir)+1:]
        print('I: {} picked for packaging'.format(para['tarball']), file=sys.stderr)
        matchtar = re.match(r'(?P<package>[^_]*)[-_](?P<version>[^-_]*)\.(?P<targz>tar\..{2,3})$', para['tarball'])
        if matchtar:
            if para['package'] == "":
                if (len(para['parent']) <= len(matchtar.group('package'))):
                    para['package'] = para['parent'].lower()
                else:
                    para['package'] = matchtar.group('package').lower()
            if para['version'] =='':
                para['version'] = matchtar.group('version')
            elif para['version'] != matchtar.group('version'):
                print('E: generated tarball version "{}".'.format(matchtar.group('version')), file=sys.stderr)
                print('E: expected version "{}" (from -u option or debian/changelog).'.format(para['version']), file=sys.stderr)
                print('E: update version number in places such as AC_INIT of configure.ac.', file=sys.stderr)
                exit(1)
            if para['targz'] =='':
                para['targz'] = matchtar.group('targz')
            elif para['targz'] != matchtar.group('targz'):
                print('W: override -z "{}" by actual value "{}".'.format(para['targz'], matchtar.group('targz')), file=sys.stderr)
                para['targz'] = matchtar.group('targz')
        else:
            print('W: {} can not be split into package-version.tar.gz style.'.format(para['tarball']), file=sys.stderr)
    else:
        print('E: {} can not be found.'.format(distpackage), file=sys.stderr)
        print('E: not even likely tarball found', file=sys.stderr)
        exit(1) 
    #######################################################################
    # copy tar to the parent directory (out of source tree)
    #######################################################################
    # cd ..
    os.chdir('..')
    print('I: pwd = "{}"'.format(os.getcwd()), file=sys.stderr)
    para['srcdir'] = para['package'] + '-' + para['version']
    return para

if __name__ == '__main__':
    print('No test program')

