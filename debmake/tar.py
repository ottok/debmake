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
# tar: called from debmake.main()
###########################################################################
# tarball   = package-version.tar.gz (or  package_version.orig.tar.gz)
# targz     = tar.gz
# basedir   = package-version
# parent    = parent directory name
# yes       = True if -y, False as default
###########################################################################
def tar(tarball, targz, basedir, parent, yes):
    print('I: pwd = "{}"'.format(os.getcwd()), file=sys.stderr)
    #######################################################################
    # make distribution tarball using tar excluding debian/ directory
    # VCS tree are not copied.
    #######################################################################
    os.chdir('..')
    print('I: pwd = "{}"'.format(os.getcwd()), file=sys.stderr)
    if basedir == parent:
        print('I: -t (--tar) run in the versioned directory', file=sys.stderr)
    else:
        if os.path.isdir(basedir):
            yn = input('?: remove "{}" directory? [Y/n]: '.format(basedir))
            if yes or (yn == '') or (yn[0].lower() == 'y'):
                command = 'rm -rf ' + basedir
                print('I: {}'.format(command), file=sys.stderr)
                if subprocess.call(command, shell=True) != 0:
                    print('E: rm -rf failed.', file=sys.stderr)
                    exit(1)
                print('I: removed {}.'.format(basedir), file=sys.stderr)
            else:
                exit(1)
        # copy from parent to basedir using hardlinks (with debian/* data)
        command = 'rsync -aCv --link-dest=' + os.getcwd() + '/' + parent + ' ' + parent + '/. ' + basedir
        print('I: {}'.format(command), file=sys.stderr)
        if subprocess.call(command, shell=True) != 0:
            print('E: rsync -aCv failed.', file=sys.stderr)
            exit(1)
    # tar while excluding VCS and debian directories
    command = 'tar --exclude=\'' + basedir + '/debian\' --anchored --exclude-caches --exclude-vcs '
    if targz == 'tar.gz':
        command += '-cvzf '
    elif targz == 'tar.bz2':
        command += '--bzip2 -cvf '
    elif targz == 'tar.xz':
        command += '--xz -cvf '
    else:
        print('E: Wrong file format "{}".'.format(targz), file=sys.stderr)
        exit(1)
    command += tarball + ' ' + basedir
    print('I: {}'.format(command), file=sys.stderr)
    if subprocess.call(command, shell=True) != 0:
        print('E: tar failed {}.'.format(tarball), file=sys.stderr)
        exit(1)
    print('I: {} tarball made'.format(tarball), file=sys.stderr)
    os.chdir(basedir)
    print('I: pwd = "{}"'.format(os.getcwd()), file=sys.stderr)
    return

if __name__ == '__main__':
    print('No test program')
