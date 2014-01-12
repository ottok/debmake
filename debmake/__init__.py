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
import sys
import time
import debmake.analyze
import debmake.copyright
import debmake.debian
import debmake.debs
import debmake.debug
import debmake.dist
import debmake.origtar
import debmake.para
import debmake.sanity
import debmake.tar
import debmake.untar
#######################################################################
# Basic package information
#######################################################################

__programname__     = 'debmake'
__version__         = '4.0.2'
__copyright__       = 'Copyright © 2014 Osamu Aoki <osamu@debian.org>'
__license__         = '''\
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
'''

__debian_policy__   = '3.9.5'   # debian policy version
__debian_compat__   = '9'       # dpkg compatibility level in debian/comapt

#######################################################################
# main program
#######################################################################
def main():
#######################################################################
# set parameters from commandline etc.
#######################################################################
    debmake.debug.debug('D: {} started'.format(sys.argv[0]))
    debmake.debug.debug('D: PYTHONPATH = {} '.format(':'.join(sys.path)))
    print('I: set parameters', file=sys.stderr)
    para = {}
    para['cwd'] = os.getcwd()
    para['program_name'] = __programname__
    para['program_version'] = __version__
    para['program_copyright'] = __copyright__
    para['program_license'] = __license__
    para['date'] = time.strftime("%a, %d %b %Y %H:%M:%S %z")
    para['shortdate'] = time.strftime("%d %b %Y")
    para['year'] = time.strftime("%Y")
    para['standard_version'] = __debian_policy__    # Debian policy_
    para['compat'] = __debian_compat__              # debhelper
    para['build_depends']   = {'debhelper (>=' + para['compat'] +')'}
    # get prefix for install --user/ ,, --prefix/ ,, --home
    fullparent = os.path.dirname(sys.argv[0])
    if fullparent == '.':
        para['base_path'] = '..'
    else:
        para['base_path'] = os.path.dirname(fullparent)
    para = debmake.para.para(para)
    debmake.debug.debug_para('D: post para', para)
#######################################################################
# -v: print version and copyright notice and exit
#######################################################################
    if para['print_version']:
        print('{0} (version: {1}) {2}\n\n{3}'.format(
                para['program_name'], 
                para['program_version'],
                para['program_copyright'],
                para['program_license']), file=sys.stderr)
        return
#######################################################################
# -c: scan source for copyright+ license text, print and exit
#######################################################################
    if para['copyright']:
        print('I: scan source for copyright+license text', file=sys.stderr)
        print(debmake.copyright.copyright('packagename',set()))
        return
#######################################################################
# sanity check parameters without digging deep into source tree
#######################################################################
    print('I: sanity check of parameters', file=sys.stderr)
    para = debmake.sanity.sanity(para)
    debmake.debug.debug_para('D: post-sanity', para)
    print('I: pkg="{}", ver="{}", rev="{}"'.format(para['package'], para['version'], para['revision']), file=sys.stderr)
#######################################################################
# -d: make dist (with upstream buildsystem dist/sdist target)
#######################################################################
    if para['dist']:
        print('I: make the upstream tarball with "make dist" equivalents', file=sys.stderr)
        version = debmake.dist.dist(para['package'], para['targz'], para['parent'])
        if para['version'] == version:
            pass
        elif para['version'] == '': # differed until now
            para['version'] = version
        else:
            print('E: (version(upstream build system)="{}") != (version(debian/changelog)="{}")'.format(version, para['version']), file=sys.stderr)
            exit(1)
        para['basedir'] = para['package'] + '-' + para['version']
        para['tarball'] = para['package'] + '-' + para['version'] + '.' + para['targz']
        debmake.debug.debug_para('D: post-dist', para)
#######################################################################
# -t: make tar (with "tar --exclude=debian" command)
#######################################################################
    elif para['tar']:
        print('I: make the upstream tarball with "tar --exclude=debian"', file=sys.stderr)
        debmake.tar.tar(para['tarball'], para['targz'], para['basedir'], para['parent'], para['yes'])
        debmake.debug.debug_para('D: post-tar', para)
#######################################################################
# -a, -d: extract archive from tarball (tar -xvzf)
#######################################################################
    if para['archive'] or para['dist']:
        print('I: untar the upstream tarball', file=sys.stderr)
        debmake.untar.untar(para['tarball'], para['targz'], para['basedir'], para['dist'], para['tar'], para['parent'], para['yes'])
        debmake.debug.debug_para('D: post-untar', para)
#######################################################################
# always: generate orig tarball if missing and non-native package
#######################################################################
    para['parent'] = os.path.basename(os.getcwd()) # update !!!
    print('I: *** start packaging in "{}". ***'.format(para['parent']), file=sys.stderr)
    if para['parent'] != para['basedir']:
        print('E: parent dirtectory must be "{}"'.format(para['basedir']), file=sys.stderr)
        exit(1)
    if not para['native']:
        print('I: provide {}_{}.orig.tar.gz for non-native Debian package'.format(para['package'], para['version']), file=sys.stderr)
        debmake.origtar.origtar(para['package'], para['version'], para['targz'], para['tarball'], para['basedir'])
#######################################################################
# -q: quit here before generating template debian/* package files
#######################################################################
    if para['quitearly']:
        print('I: quit early after making the upstream tarball.', file=sys.stderr)
        exit(0)
#######################################################################
# Prep to create debian/* package files
#######################################################################
    print('I: parse binary package settings', file=sys.stderr)
    para['debs'] = debmake.debs.debs(para['binaryspec'], para['package'], para['monoarch'], para['dh_with'])
    print('I: analyze the source tree', file=sys.stderr)
    para = debmake.analyze.analyze(para)
    #debmake.gui()          # GUI setting
    #debmake.debug.debug_para('D: post-gui', para)
#######################################################################
# Make debian/* package files
#######################################################################
    print('I: make debian/* template files', file=sys.stderr)
    debmake.debian.debian(para)
    if os.getcwd() != para['cwd']:
        print('I: upon return to the shell, current directory becomes {}'.format(para['cwd']), file=sys.stderr)
        print('I: please execute "cd {0}"'.format(os.getcwd()), file=sys.stderr)
        print('I: before building binary package with dpkg-buildpackage (or debuild, pdebuild, sbuild, ...).', file=sys.stderr)
    return

#######################################################################
# Test code
#######################################################################
if __name__ == '__main__':
    main()

