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
import argparse
import os
import pwd
import sys
import time
###########################################################################
# undefined environment variable -> ''
def env(var):
    try:
        return os.environ[var]
    except KeyError:
        return ''
#######################################################################
# Initialize parameters
#######################################################################
def para(para):
    debmail = env('DEBEMAIL')
    if not debmail:
        debmail = os.getlogin() + '@localhost'
    debfullname = env('DEBFULLNAME')
    if not debfullname:
        debfullname = pwd.getpwnam(os.getlogin())[4].split(',')[0]

#######################################################################
# command line setting
#######################################################################
    p = argparse.ArgumentParser(
                formatter_class=argparse.RawDescriptionHelpFormatter,
                description = '''\
{0}: make Debian source package    Version: {1}
{2}

{0} builds the Debian package from the upstream source.  
Normally, this is done as follows:
 * The upstream tarball is downloaded as the packagename-version.tar.gz file.
 * The packagename_version.orig.tar.gz symlink is generated pointing to the upstream tarball.
 * It is untared to create many files under the packagename-version/ directory.  
 * {0} is invoked in the packagename-version/ directory without any arguments.
 * Files in the packagename-version/debian/ directory are manually adjusted.
 * dpkg-buildpackage is invoked in the packagename-version/ directory to make debian packages.

Argument may need to be quoted to protect from the shell.
'''.format(
                para['program_name'],
                para['program_version'],
                para['program_copyright']),
            epilog='See debmake(1) manpage for more.')
    p.add_argument(
            '-c', 
            '--copyright', 
            action = 'store_true', 
            default = False,
            help = 'scan source for copyright+license text and exit')
    sp = p.add_mutually_exclusive_group()
    sp.add_argument(
            '-n', 
            '--native', 
            action = 'store_true', 
            default = False,
            help = 'make a native source package without .orig.tar.gz')
    sp.add_argument(
            '-a',
            '--archive',
            type = str,
            action = 'store', 
            default = '',
            help = 'use the upstream source tarball directly (-p, -u, -z: overridden)',
            metavar = 'packagename-version.tar.gz')
    sp.add_argument(
            '-d', 
            '--dist',
            action = 'store_true', 
            default = False, 
            help = 'run "make dist" equivalent first to generate upstream tarball and use it')
    sp.add_argument(
            '-t', 
            '--tar',
            action = 'store_true', 
            default = False, 
            help = 'run "tar" to generate upstream tarball and use it')
    p.add_argument(
            '-p', 
            '--package', 
            action = 'store', 
            default = '',
            help = 'set the Debian package name',
            metavar = 'packagename')
    p.add_argument(
            '-u', 
            '--upstreamversion', 
            action = 'store', 
            default = '',
            help = 'set the upstream package version',
            metavar = 'version')
    p.add_argument(
            '-r', 
            '--revision', 
            action = 'store', 
            default = '',
            help = 'set the Debian package revision',
            metavar = 'revision')
    p.add_argument(
            '-z', 
            '--targz', 
            action = 'store',
            default = '',
            help = 'set the tarball type, extension=(tar.gz|tar.bz2|tar.xz)',
            metavar = 'extension')
    p.add_argument(
             '-b', 
             '--binaryspec', 
            action = 'store', 
            default = '',
            help = 'set binary package specs as comma separated list, e.g., "foo:foreign,foo-doc:all,libfoo1:same".  Here, package=(-|-doc|-dev|-common|-bin|-dbg), type=(all|any|foreign|same).',
            metavar = 'package[:type]')
    p.add_argument(
            '-e', 
            '--email', 
            action = 'store',
            default = debmail,
            help = 'set e-mail address', 
            metavar = 'foo@example.org')
    p.add_argument(
            '-f', 
            '--fullname', 
            action = 'store', 
            default = debfullname,
            help = 'set the fullname', 
            metavar = '"firstname lastname"')
#    p.add_argument(
#            '-g', 
#            '--gui',
#            action = 'store_true', 
#            default = False, 
#            help = 'run GUI configuration')
#
#   -h : used by argparse for --help
    p.add_argument(
            '-l', 
            '--license', 
            default = '',
            action = 'store', 
            help = 'add formatted license to debian/copyright',
            metavar = '"license_file"')
    p.add_argument(
            '-m', 
            '--monoarch', 
            action = 'store_true', 
            default = False,
            help = 'force packages to be non-multiarch')
    p.add_argument(
            '-q', 
            '--quitearly', 
            action = 'store_true', 
            default = False, 
            help='quit early before creating files in the debian directory')
    p.add_argument(
            '-v', 
            '--version', 
            action = 'store_true', 
            default = False, 
            help = 'show version information')
    p.add_argument(
            '-w', 
            '--with', 
            action = 'store', 
            default = '',
            dest = 'withargs',
            help = 'set additional "dh --with" option arguments',
            metavar = 'args')
    p.add_argument(
            '-x', 
            '--extra',
            default = '',
            action = 'store', 
            help = 'generate extra configuration files as templates',
            metavar = '[01234]')
    p.add_argument(
            '-y', 
            '--yes',
            action = 'store_true', 
            default = False, 
            help = 'force "yes" for all prompts')
    args = p.parse_args()
#######################################################################
# Set parameter values
#######################################################################
    ############################################# -a
    if args.archive:
        para['archive'] = True
        para['tarball'] = args.archive
    else:
        para['archive'] = False
        para['tarball'] = ''
    #############################################
    para['binaryspec']      = args.binaryspec   # -b
    para['copyright']       = args.copyright    # -c
    para['dist']            = args.dist         # -d
    para['email']           = args.email        # -e
    para['fullname']        = args.fullname     # -f
#   para['gui']             = args.gui          # -g
    ############################################# -l
    # --license: args.license -> para['license'] as set
    if args.license == '':
        para['license'] = set({'[Cc][Oo][Pp][Yy][Ii][Nn][Gg]*', 
                                 '[Ll][Ii][Cc][Ee][Nn][Ss][Ee]*'})   # default
    else:
        para['license'] = set(args.copyright.split(','))
    #############################################
    para['monoarch']        = args.monoarch     # -m
    para['native']          = args.native       # -n
    para['package']         = args.package      # -p
    para['quitearly']       = args.quitearly    # -q
    para['revision']        = args.revision     # -r
    para['tar']             = args.tar          # -t
    para['version']         = args.upstreamversion  # -u
    para['print_version']   = args.version      # -v
    ############################################# -w
    # --with: args.withargs -> para['dh_with'] as set
    if args.withargs == '':
        para['dh_with'] = set()   # default is empty set
    else:
        para['dh_with'] = set(args.withargs.split(','))
    #############################################
    para['extra']           = args.extra        # -x
    para['yes']             = args.yes          # -y
    para['targz']           = args.targz        # -z
    #######################################################################
    # return command line parameters
    #######################################################################
    return para
        
#######################################################################
# Test code
#######################################################################
if __name__ == '__main__':
    for p, v in para().items():
        print("para['{}'] = \"{}\"".format(p,v))
