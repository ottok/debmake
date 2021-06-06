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
import subprocess
import sys

import debmake.yn


def tar(tarball, targz, srcdir, parent, yes):
    """create a source tarball excluding the debian/ directory
    tar: called from debmake.main()

    tarball   = package-version.tar.gz (or package_version.orig.tar.gz)
    targz     = one of 'tar.gz', 'tar.bz2' or 'tar.xz'
    srcdir    = package-version
    parent    = parent directory name
    yes       = True if -y, False as default

    Please note that 'srcdir' and 'parent' are relative paths
    (specifically: the basename of the respective directory).

    Side-effects:
        * 'srcdir' will be deleted, if it already exists and is not the current
        * the current directory changes to 'srcdir' after successful completion
    """
    print('I: pwd = "{}"'.format(os.getcwd()), file=sys.stderr)
    if os.path.isdir(".pc"):
        print('E: .pc/ directory exists.  Stop "debmake -t ..."', file=sys.stderr)
        print(
            "E: Remove applied patches and remove .pc/ directory, first.",
            file=sys.stderr,
        )
        exit(1)
    #######################################################################
    # make distribution tarball using tar excluding debian/ directory
    # VCS tree are not copied.
    #######################################################################
    os.chdir("..")
    print('I: pwd = "{}"'.format(os.getcwd()), file=sys.stderr)
    if srcdir == parent:
        print("I: good, -t (--tar) run in the versioned directory", file=sys.stderr)
    else:
        if os.path.isdir(srcdir):
            debmake.yn.yn(
                'remove "{}" directory in tar'.format(srcdir), "rm -rf " + srcdir, yes
            )
        # copy from parent to srcdir using hardlinks (with debian/* data)
        copy_command = [
            "rsync",
            "-av",
            "--link-dest",
            os.path.join(os.getcwd(), parent),
            os.path.join(parent, os.path.curdir),
            srcdir,
        ]
        print("I: $ {}".format(" ".join(copy_command)), file=sys.stderr)
        if subprocess.call(copy_command) != 0:
            print("E: rsync -aCv failed.", file=sys.stderr)
            exit(1)
    # tar while excluding VCS and debian directories
    tar_command = [
        "tar",
        "--exclude",
        os.path.join(srcdir, "debian"),
        "--anchored",
        "--exclude-vcs",
    ]
    if targz == "tar.gz":
        tar_command.append("--gzip")
    elif targz == "tar.bz2":
        tar_command.append("--bzip2")
    elif targz == "tar.xz":
        tar_command.append("--xz")
    else:
        print('E: Wrong file format "{}".'.format(targz), file=sys.stderr)
        exit(1)
    tar_command.append("-cvf")
    tar_command.append(tarball)
    tar_command.append(srcdir)
    print("I: $ {}".format(" ".join(tar_command)), file=sys.stderr)
    if subprocess.call(tar_command) != 0:
        print("E: tar failed {}.".format(tarball), file=sys.stderr)
        exit(1)
    print("I: {} tarball made".format(tarball), file=sys.stderr)
    os.chdir(srcdir)
    print('I: pwd = "{}"'.format(os.getcwd()), file=sys.stderr)
    return


if __name__ == "__main__":
    print("No test program")
