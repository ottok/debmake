#!/usr/bin/python3
# vim:se tw=0 sts=4 ts=4 et ai:
"""
Copyright © 2013 Osamu Aoki

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

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
# Initialization constant values

import argparse, time, sys, os

from debmake import __programname__, __version__,  __copyright__, __license__
import debmake.src
import debmake.gen

#######################################################################
# Debug output
#######################################################################
def debug(msg):
    """Outputs to sys.stderr if DEBUG is non-zero."""
    if (DEBUG):
        print(msg, file=sys.stderr)
    return

def debug_para(msg, para):
    debug('{} archive="{}" package="{}" version="{}", targz="{}"'.format(msg, para['archive'], para['package'], para['version'], para['targz']))
    return

#######################################################################
# main program
#######################################################################
def main(base_path):
#######################################################################
# Initialize parameters
#######################################################################
    global DEBUG
    try:
        DEBUG = os.environ["DEBUG"]
    except KeyError:
        DEBUG = 0
    para = {}
    para['program_name'] = __programname__
    para['program_version'] = __version__
    para['program_copyright'] = __copyright__
    para['program_license'] = __license__
    para['date'] = time.strftime("%a, %d %b %Y %H:%M:%S %z")
    para['shortdate'] = time.strftime("%d %b %Y")
    para['year'] = time.strftime("%Y")
    para['standard_version'] = '3.9.4'  # Debian policy
    para['compat'] = '9'                # debhelper
    para['build_depends']   = {'debhelper (>=' + para['compat'] +')'}
    para['base_path']   = base_path
    para['cwd']   =  os.getcwd()
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
 * The upstream tarball is downloaded as the upstream-version.tar.gz file.
 * The upstream_version.orig.tar.gz symlink is generated pointing to the upstream tarball.
 * It is untared to create many files under the upstream-version/ directory.  
 * {0} is invoked in the upstream-version/ directory without any arguments.
 * Files in the upstream-version/debian/ directory are manually adjusted.
 * dpkg-buildpackage is invoked in the upstream-version/ directory to make debian packages.

Argument may need to be quoted to protect from the shell.
'''.format(
                para['program_name'],
                para['program_version'],
                para['program_copyright']),
            epilog='See debmake(1) manpage for more.')
    sp = p.add_mutually_exclusive_group()
    sp.add_argument(
            '-a',
            '--archive',
            type = str,
            action = 'store', 
            default = '',
            help = 'use the upstream source tarball directly (-p, -u, -z: overridden)',
            metavar = 'upstream-version.tar.gz')
    sp.add_argument(
            '-d', 
            '--dist',
            action = 'store_true', 
            default = False, 
            help = 'run "make dist" equivalent first to generate upstream tarball and use it')
    p.add_argument(
            '-p', 
            '--package', 
            action = 'store', 
            default = '',
            help = 'set the Debian package name',
            metavar = 'package_name')
    p.add_argument(
            '-u', 
            '--upstreamversion', 
            action = 'store', 
            default = '',
            help = 'set the upstream package version',
            metavar = 'upstream_version')
    p.add_argument(
            '-r', 
            '--revision', 
            action = 'store', 
            default = '1',
            help = 'set the Debian package revision',
            metavar = 'debian_revision')
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
            '-c', 
            '--copyright', 
            default = '',
            action = 'store', 
            help = 'add formatted license to debian/copyright',
            metavar = '"license_file"')
    p.add_argument(
            '-e', 
            '--email', 
            action = 'store',
            default = debmake.src.DEBEMAIL,
            help = 'set e-mail address', 
            metavar = 'foo@example.org')
    p.add_argument(
            '-f', 
            '--fullname', 
            action = 'store', 
            default = debmake.src.DEBFULLNAME,
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
            '-m', 
            '--monoarch', 
            action = 'store_true', 
            default = False,
            help = 'force packages to be non-multiarch')
    p.add_argument(
            '-n', 
            '--native', 
            action = 'store_true', 
            default = False,
            help = 'make a native source package without .orig.tar.gz')
    p.add_argument(
            '-o', 
            '--overwrite', 
            action = 'store_true', 
            default = False, 
            help='overwrite existing configuration files')
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
            action = 'store_true', 
            default = False, 
            help = 'generate extra configuration files as templates')
    args = p.parse_args()
#######################################################################
# -v: print version and copyright notice
#######################################################################
    if args.version:
        print('{0} (version: {1}) {2}\n\n{3}'.format(
                para['program_name'], 
                para['program_version'],
                para['program_copyright'],
                para['program_license']), file=sys.stderr)
        return
#######################################################################
# Set parameter values
#######################################################################
    para['archive']         = args.archive      # [archive]
    para['package']         = args.package      # -p
    para['version']         = args.upstreamversion  # -u
    para['revision']        = args.revision     # -r
    para['binaryspec']      = args.binaryspec   # -b
    para['dist']            = args.dist         # -d
    para['email']           = args.email        # -e
    para['fullname']        = args.fullname     # -f
#   para['gui']             = args.gui          # -g
    para['monoarch']        = args.monoarch     # -m
    para['native']          = args.native       # -n
    para['overwrite']       = args.overwrite    # -o
    para['quitearly']       = args.quitearly    # -q
    para['extra']           = args.extra        # -x
    para['targz']           = args.targz        # -z
    ############################################# -w
    # --with: args.withargs -> para['dh_with'] as set
    if args.withargs == '':
        para['dh_with'] = set([])   # default
    else:
        para['dh_with'] = set(args.withargs.split(','))
    ############################################# -c
    # --copyright: args.copyright -> para['copyright'] as set
    if args.copyright == '':
        para['copyright'] = set({'[Cc][Oo][Pp][Yy][Ii][Nn][Gg]*', 
                                 '[Ll][iI][Cc][Ee][Nn][Ss][Ee]*'})   # default
    else:
        para['copyright'] = set(args.copyright.split(','))
    ############################################# 
    debug_para('D: initial', para)
#######################################################################
# Normalize parameters without going into source tree
#######################################################################
    print('I: sanity check of parameters', file=sys.stderr)
    para                    = debmake.src.sanity(para)
    debug_para('D: post-sanitize', para)
#######################################################################
# -d: Make dist (with dist/sdist target)
#######################################################################
    if para['dist']:
        print('I: process "make dist" equivalent', file=sys.stderr)
        para                = debmake.src.dist(para)
        debug_para('D: post-dist', para)
#######################################################################
# -q: quit early
#######################################################################
    if para['quitearly']:
        print('I: quit early (-q).', file=sys.stderr)
        exit(0)
#######################################################################
# -a: extract archive (tar xvzf)
#######################################################################
    if para['archive']:
        print('I: process untar', file=sys.stderr)
        para                = debmake.src.untar(para)
        debug_para('D: post-untar', para)
#######################################################################
# Analyze source with lots of heuristics (guessing ...)
#######################################################################
    print('I: analyze source', file=sys.stderr)
    para                    = debmake.src.analyze(para)
    #debmake.gui()          # GUI setting
    #debug_para('D: post-gui', para)
#######################################################################
# Generate files in debian/*
#######################################################################
    print('I: generate debian/*', file=sys.stderr)
    debmake.gen.debian(para)
    return

#######################################################################
# Test code
#######################################################################
if __name__ == '__main__':
    base_path = os.path.dirname(
                os.path.dirname(
                os.path.realpath(__file__)))
    main(base_path) # broken for /usr/share/*


