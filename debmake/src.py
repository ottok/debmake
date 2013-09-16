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

import os, glob, pwd, sys, re, subprocess

###########################################################################
# Debhelper v7+ supported build systems are listed in:
#   /usr/share/perl5/Debian/Debhelper/Buildsystem
# with simple "dh $@ --with ..." syntax
#
# Use "grep 'this->get_sourcepath' *" to find key files
# there.
#
# GNU Coding Standards http://www.gnu.org/prep/standards/
# autoreconf http://packages.debian.org/sid/dh-autoreconf
# CMake http://www.cmake.org/ http://en.wikipedia.org/wiki/CMake
# Build.PL http://perldoc.perl.org/Module/Build/Cookbook.html
# ,, http://search.cpan.org/~leont/Module-Build-0.4004/lib/Module/Build.pm
# Makefile.PL # http://perldoc.perl.org/ExtUtils/MakeMaker/Tutorial.html
# Python distutils http://docs.python.org/2/distutils/
# Python3 distutils http://docs.python.org/3/distutils/
# qmake http://en.wikipedia.org/wiki/Qmake
# ,,    http://qt-project.org/doc/qt-4.8/qmake-manual.html
# Java ANT http://en.wikipedia.org/wiki/Apache_Ant

###########################################################################
# undefined environment variable -> ''
def env(var):
    try:
        x = os.environ[var]
    except KeyError:
        x = ''
    return x

###########################################################################
DEBEMAIL = env('DEBEMAIL')
if not DEBEMAIL:
    DEBEMAIL = os.getlogin() + '@localhost'

###########################################################################
DEBFULLNAME = env('DEBFULLNAME')
if not DEBFULLNAME:
    DEBFULLNAME = pwd.getpwnam(os.getlogin())[4].split(',')[0]

###########################################################################
def basedir(para):
    return para['package'] + '-' + para['version']

###########################################################################
def basetargz(para):
    return para['package'] + '-' + para['version'] + '.' + para['targz']

###########################################################################
def origtargz(para):
    return para['package'] + '_' + para['version'] + '.orig.' + para['targz']

###########################################################################
def sanity(para):
    #######################################################################
    # sanity check without checking source contents
    #######################################################################
    if para['quitearly']:
        if para['archive'] == '' and not para['dist']:
            print('E: Use --quitearly (-q) only with --archive (-a) or --dist (-d).', file=sys.stderr)
            exit(1)
    #######################################################################
    # Normalize for -a
    #######################################################################
    if para['archive']:
        if not os.path.isfile(para['archive']):
            print('E: Non-existing archive name {}'.format(para['archive']), file=sys.stderr)
            exit(1)
        rebasetar = re.match(r'(.+)-([^-_]+)\.(tar\.gz|tar\.bz2|tar\.xz)$', os.path.basename(para['archive']))
        reorigtar = re.match(r'(.+)_([^-_]+)\.orig\.(tar\.gz|tar\.bz2|tar\.xz)$', os.path.basename(para['archive']))
        if reorigtar:
            # Debian upstream tar-ball (most likely downloaded with dget)
            para['package'] = reorigtar.group(1)
            para['version'] = reorigtar.group(2)
            para['targz'] = reorigtar.group(3)
            para['parchive'] = para['archive'][:-len(origtargz(para))]
            if para['parchive'] != '' and para['parchive'] != './':
                print('E: orig.tar should be in the current directory.. Remove {} from {}.'.format(para['parchive'], para['archive']), file=sys.stderr)
                exit(1)
        elif rebasetar:
            # standard upstream tar-ball
            para['package'] = rebasetar.group(1)
            para['version'] = rebasetar.group(2)
            para['targz'] = rebasetar.group(3)
            para['parchive'] = para['archive'][:-len(origtargz(para))]
            cmd = 'ln -sf ' + para['archive'] + ' ' + origtargz(para)
            print('I: {}'.format(cmd), file=sys.stderr)
            if subprocess.call(cmd, shell=True) != 0:
                print('E: failed to generate symlink.', file=sys.stderr)
                exit(1)
            else:
                print('I: symlimk to {} generated.'.format(origtargz(para)), file=sys.stderr)
    #######################################################################
    # Normalize for non -a
    #######################################################################
    else:
        if para['dist'] and (not para['version']):
            print('E: --dist (-d) needs --upstreamversion (-u)', file=sys.stderr)
            exit(1)
        # hidden feature for the lazy option argument
        if para['targz'] == '':
            para['targz'] = 'tar.gz'
        elif para['targz'][0] == 'g':
            para['targz'] = 'tar.gz'
        elif para['targz'][0] == 'b':
            para['targz'] = 'tar.bz2'
        elif para['targz'][0] == 'x':
            para['targz'] == 'tar.xz'
        elif (para['targz'] == 'tar.gz' or
                para['targz'] == 'tar.bz2' or
                para['targz'] == 'tar.xz'):
            pass
        else:
            print('E: --targz (-z) value is invalid: {}'.format(para['targz']), file=sys.stderr)
            exit(1)
        #----------------------------------------------------------------------
        # Huristics of source directory and package name and version for non -a cases
        #----------------------------------------------------------------------
        parent = os.path.basename(os.getcwd())
        para['parent'] = parent
        pkgver = re.match(r'(.+)-([^-_]+)$', parent)
        if pkgver:
            if para['package'] == '':
                if para['version'] == '':
                    para['package'] = pkgver.group(1)
                    para['version'] = pkgver.group(2)
                    para['versionedsourcedir'] = True
                else: #  para['version'] != ''
                    if para['version'] == pkgver.group(2):
                        para['package'] = pkgver.group(1)
                        para['versionedsourcedir'] = True
                    else:
                        para['package'] = parent
                        para['versionedsourcedir'] = False
            else: # para['package'] != ''
                if para['version'] == '':
                    para['version'] = pkgver.group(2)
                    if para['package'] == pkgver.group(1):
                        para['versionedsourcedir'] = True
                    elif para['package'] == parent:
                        para['versionedsourcedir'] = False
                    else:
                        print('E: Inconsistent package name {}, version {}, source directory {}.'.format(para['package'], para['version'], parent), file=sys.stderr)
                        exit(1)
                else: # para['version'] != ''
                    if para['package'] == pkgver.group(1) and para['version'] == pkgver.group(2):
                        para['versionedsourcedir'] = True
                    elif para['package'] == parent:
                        para['versionedsourcedir'] = False
                    else:
                        para['versionedsourcedir'] = False
                        print('W: Inconsistent package name {}, version {}, source directory {}.'.format(para['package'], para['version'], parent), file=sys.stderr)
        else:
            if para['version'] == '':
                print('E: Need --upstreamversion (-u) for source directory {}.'.format(parent), file=sys.stderr)
                exit(1)
            else:
                if para['package'] == '':
                    para['package'] = parent
                para['versionedsourcedir'] = False
        #----------------------------------------------------------------------
        # -d set
        #----------------------------------------------------------------------
        if para['dist'] and para['versionedsourcedir']:
            print('E: Rename the source directory {} -> {}.'.format(parent, para['package']), file=sys.stderr)
            exit(1)
    # End of "if para['archive']:"
    #######################################################################
    # Dynamic content with package name etc.
    #######################################################################
    para['section'] = 'unknown'
    para['priority'] = 'extra'
    para['homepage'] = '<insert the upstream URL, if relevant>'
    para['vcsvcs'] = 'git://anonscm.debian.org/collab-maint/' + para['package'] + '.git'
    para['vcsbrowser'] = 'http://anonscm.debian.org/gitweb/?p=collab-maint/' + para['package'] + '.git'
    #######################################################################
    # Binary package name and specification: binaryspec -> debs
    #######################################################################
    # if no binary package specs are given
    if para['binaryspec'] =='':
        para['binaryspec'] = para['package']
    # if explicit list of binary package specs are given
    # interpret it accrding to naming conventions
    r = []
    for x in para['binaryspec'].split(','):
        y = x.split(':')
        ###################################################################
        # package name
        ###################################################################
        if y[0] == '':
            p = para['package']
        elif y[0] == '-':
            p = para['package']
        elif y[0][0] == '-':
            p = para['package'] + y[0]
        else:
            p = y[0]
        # first default values and then override or update values
        a = 'any'       # arch
        t = 'unknown'   # type
        m = 'foreign'   # muiti-arch
        dp = {'${misc:Depends}'}
        pd = set([])
        # Prefix names should come first to be overriden later
        if len(y[0]) > 3 and y[0][:3] == 'lib':
            a = 'any'
            t = 'lib'
            m = 'same'
        elif len(y[0]) > 7 and y[0][:7] == 'python-':
            a = 'all'
            t = 'python'
            m = 'foreign'
        elif len(y[0]) > 8 and y[0][:8] == 'python3-':
            a = 'all'
            t = 'python3'
            m = 'foreign'
        else:
            pass
        # Suffix names override
        if len(y[0]) > 5 and y[0][-5:] == '-perl':
            a = 'all'
            t = 'perl'
            m = 'foreign'
        elif len(y[0]) > 4 and y[0][-4:] == '-dev':
            a = 'any'
            t = 'dev'
            m = 'same'
        elif len(y[0]) > 4 and y[0][-4:] == '-dbg':
            a = 'any'
            t = 'dbg'
            m = 'same'
        elif len(y[0]) > 4 and y[0][-4:] == '-bin':
            a = 'any'
            t = 'bin'
            m = 'foreign'
        elif len(y[0]) > 5 and y[0][-5:] == 'tools':
            a = 'any'
            t = 'bin'
            m = 'foreign'
        elif len(y[0]) > 5 and y[0][-5:] == 'utils':
            a = 'any'
            t = 'bin'
            m = 'foreign'
        elif len(y[0]) > 4 and y[0][-4:] == '-doc':
            a = 'all'
            t = 'doc'
            m = 'foreign'
        elif len(y[0]) > 5 and y[0][-5:] == '-html':
            a = 'all'
            t = 'doc'
            m = 'foreign'
        elif len(y[0]) > 7 and y[0][-7:] == '-manual':
            a = 'all'
            t = 'doc'
            m = 'foreign'
        elif len(y[0]) > 7 and y[0][-7:] == '-common':
            a = 'all'
            t = 'unknown'
            m = 'foreign'
        else:
            pass
        # Last prefix name overrides
        if len(y[0]) > 6 and y[0][6:] == 'fonts-':
            a = 'all'
            t = 'data'
            m = 'foreign'
        ###################################################################
        # if 2nd argument exists, e.g. all in foo:all
        ###################################################################
        if len(y) >= 2:
            if y[1] == 'a' or y[1] == 'al' or y[1] == 'all':
                a = 'all'
                m = 'foreign'
            elif y[1] == 'an' or y[1] == 'any':
                a = 'any'
                m = 'foreign'
            elif len(y[1]) >=1 and y[1][:1] == 'f':
                a = 'any'
                m = 'foreign'
            elif len(y[1]) >=1 and y[1][:1] == 's':
                a = 'any'
                m = 'same'
            elif y[1] == 'doc':
                a = 'all'
                t = 'doc'
                m = 'foreign'
            elif y[1] == 'data':
                a = 'all'
                t = 'data'
                m = 'foreign'
            elif y[1] == 'bin':
                a = 'any'
                t = 'bin'
                m = 'foreign'
            elif y[1] == 'lib':
                a = 'any'
                t = 'lib'
                m = 'same'
            elif y[1] == 'dev':
                a = 'any'
                t = 'dev'
                m = 'same'
            elif y[1] == 'dbg':
                a = 'any'
                t = 'dbg'
                m = 'same'
            elif y[1] == 'script':
                a = 'all'
                t = 'shell'
                m = 'foreign'
            elif y[1] == 'perl':
                a = 'all'
                t = 'perl'
                m = 'foreign'
            elif y[1] == 'python':
                a = 'all'
                t = 'python'
                m = 'foreign'
            elif y[1] == 'python3':
                a = 'all'
                t = 'python3'
                m = 'foreign'
            else:
                print('E: -b: {} has unknown type: {}'.format(y[0], y[1]), file=sys.stderr)
                exit(1)
        if len(y) >= 3:
            print('E: -b does not support the 3rd argument yet: {}:{}:{}'.format(y[0], y[1],y[2]), file=sys.stderr)
            exit(1)
        ###################################################################
        # template text
        ###################################################################
        desc = '<insert up to 60 chars description>'
        desc_long = '''\
 <insert long description, indented with spaces>
 <continued long description lines ...>
 .
 <continued long description line after a line break indicated by " .">
 <continued long description lines ...>
'''
        ###################################################################
        # monoarch = non-multi-arch
        ###################################################################
        if not para['monoarch']:
            pd.update({'${misc:Pre-Depends}'})
        else:
            m = ''

        ###################################################################
        # append dictionary to a list
        ###################################################################
        r.append({'package': p, 
                'arch': a, 
                'type': t, 
                'multiarch': m, 
                'desc': desc, 
                'desc_long': desc_long, 
                'depends': dp, 
                'pre-depends': pd})
    para['debs'] = r
    return para

###########################################################################
# assume in upstream VCS, try to make tar with the (s)dist target
# para['package'] para['version'] para['targz'] were sanitized already
###########################################################################
def dist(para):
    print('I: pwd = {}'.format(os.getcwd()), file=sys.stderr)
    # -u
    #######################################################################
    # make distribution tar-ball using the Autotools
    #######################################################################
    if os.path.isfile('configure.ac') and\
            os.path.isfile('Makefile.am'):
        print('I: autotools dist', file=sys.stderr)
        if subprocess.call('autoreconf -i -v -f && ./configure && make distcheck', 
                shell=True) != 0:
            print('E: autotools failed.', file=sys.stderr)
            exit(1)
        else:
            print('I: {} tar-ball made'.format(para['archive']), file=sys.stderr)
            if para['versionedsourcedir']:
                print('E: VCS should not be in the versioned directory', file=sys.stderr)
                exit(1)
        distdir = para['parent'] + '/dist/'
    #######################################################################
    # make distribution tar-ball using setup.py
    #######################################################################
    elif os.path.isfile('setup.py'):
        # Python distutils
        f = open('setup.py', 'r')
        l = f.readline()
        if re.search('python3', l):
            print('I: setup.py (Python3): sdist', file=sys.stderr)
            # http://docs.python.org/3/distutils/
            if subprocess.call('python3 setup.py sdist', 
                    shell=True) != 0:
                print('E: setup.py (Python3) failed.', file=sys.stderr)
                exit(1)
            else:
                print('I: {} tar-ball made'.format(para['archive']), file=sys.stderr)
        else:
            print('I: setup.py (Python): sdist', file=sys.stderr)
            # http://docs.python.org/2/distutils/
            if subprocess.call('python setup.py sdist', 
                    shell=True) != 0:
                print('E: setup.py (Python) failed.', file=sys.stderr)
                exit(1)
            else:
                print('I: {} tar-ball made'.format(para['archive']), file=sys.stderr)
        if para['versionedsourcedir']:
            print('E: VCS should not be in the versioned directory', file=sys.stderr)
            exit(1)
        distdir = para['parent'] + '/dist/'
    #######################################################################
    # make distribution tar-ball using Build.PL
    #######################################################################
    elif os.path.isfile('Build.PL'):
        # perl Build.PL
        if subprocess.call('perl Build.PL', shell=True) != 0:
            print('E: perl Build.PL failed.', file=sys.stderr)
            exit(1)
        else:
            print('I: Build script made', file=sys.stderr)
        # ./Build dist
        if subprocess.call('./Build dist', shell=True) != 0:
            print('E: ./Build dist failed.', file=sys.stderr)
            exit(1)
        else:
            print('I: ./Build script run OK', file=sys.stderr)
        print('W: untested for --dist (-d) with Build.PL. patch welcomed', file=sys.stderr)
        print('E: distribution file location unknown. Please let me know.', file=sys.stderr)
        exit(1)
        distdir = para['parent'] + '/dist/'
    #######################################################################
    # make distribution tar-ball using Makefile.PL
    #######################################################################
    elif os.path.isfile('Makefile.PL'):
        # perl Makefile.PL
        if subprocess.call('perl Makefile.PL', shell=True) != 0:
            print('E: perl Makefile.PL failed.', file=sys.stderr)
            exit(1)
        else:
            print('I: Build script made', file=sys.stderr)
        # make dist
        if subprocess.call('make manifest && make disttest && make dist', shell=True) != 0:
            print('E: make dist failed.', file=sys.stderr)
            exit(1)
        else:
            print('I: "make dist" script run OK', file=sys.stderr)
        print('W: untested for --dist (-d) with Makefile.PL. patch welcomed', file=sys.stderr)
        print('E: distribution file location unknown. Please let me know.', file=sys.stderr)
        exit(1)
        distdir = para['parent'] + '/dist/'
    #######################################################################
    # make distribution tar-ball using tar
    #######################################################################
    else:
        print('W: unsupported platform for --dist (-d). Run tar to make {}'.format(basetargz(para)), file=sys.stderr)
        if os.chdir('..'):
            print('E: failed to cd to {}'.format('..'), file=sys.stderr)
            exit(1)
        else:
            print('I: pwd = {}'.format(os.getcwd()), file=sys.stderr)
        if os.path.isdir(basedir(para)):
            print('E: directory {} exists.'.format(basedir(para)), file=sys.stderr)
            exit(1)
        cmd = 'mv ' + para['parent'] + ' ' + basedir(para) + ' && '
        # tar while excluding VCS
        if para['targz'] == 'tar.gz':
            cmd += 'tar --exclude-vcs -cvzf '
        elif para['targz'] == 'tar.bz2':
            cmd += 'tar --bzip2 --exclude-vcs -cvf '
        elif para['targz'] == 'tar.xz':
            cmd += 'tar --xz --exclude-vcs -cvf '
        else:
            print('E: Should not be {}. (inisde --dist)'.format(para['targz']), file=sys.stderr)
            exit(1)
        # move directory, tar , restore directory, cd back
        cmd += basetargz(para) + ' ' + basedir(para) + '&&' + 'mv ' + basedir(para) + ' ' + para['parent']
        if subprocess.call(cmd, shell=True) != 0:
            print('E: make dist failed.', file=sys.stderr)
            exit(1)
        else:
            print('I: "make dist ..." script run OK', file=sys.stderr)
        if os.chdir(para['parent']):
            print('E: failed to cd to {}'.format('..'), file=sys.stderr)
            exit(1)
        else:
            print('I: pwd = {}'.format(os.getcwd()), file=sys.stderr)
        distdir = ''
    #######################################################################
    # make debian orig.tar
    #######################################################################
    # cd ..
    if os.chdir('..'):
        print('E: failed to cd to {}'.format('..'), file=sys.stderr)
        exit(1)
    else:
        print('I: pwd = {}'.format(os.getcwd()), file=sys.stderr)
    # ln -sf para['parent']/dist/foo-1.0.tar.gz foo_1.0.orig.tar.gz
    fn1 = distdir + basetargz(para)
    fn2 = origtargz(para)
    command = 'ln -sf ' + fn1 + ' ' + fn2
    if subprocess.call(command, shell=True) != 0:
        print('E: failed to create symlink at {} pointing to {}'.format(fn2, fn1), file=sys.stderr)
        exit(1)
    else:
        print('I: create symlink at {}/{} pointing to {}'.format(os.getcwd(), fn2, fn1), file=sys.stderr)
    para['archive'] = origtargz(para)
    return para

###########################################################################
def untar(para):
    p = basedir(para)
    # the target directory should not exist
    if os.path.isdir(p):
        print('E: the target "{}" directory already exist.'.format(p), file=sys.stderr)
        exit(1)
    if para['targz'] == 'tar.bz2':
        tar = 'tar --bzip2 -xvf '
    elif para['targz'] == 'tar.xz':
        tar = 'tar --xz -xvf '
    elif para['targz'] == 'tar.gz':
        tar = 'tar -xvzf '
    else:
        print('E: the extension "{}" not supported.'.format(para['targz']), file=sys.stderr)
        exit(1)
    tar += para['archive']
    if os.path.isfile(para['archive']):
        print('I: run "{}".'.format(tar), file=sys.stderr)
        if subprocess.call(tar, shell=True) == 1:
            print('E: failed to untar.', file=sys.stderr)
            exit(1)
        else:
            print('I: untared.', file=sys.stderr)
    else:
        print('E: missing the "{}" file.'.format(para['archive']), file=sys.stderr)
        exit(1)
    # cd package-version
    if os.chdir(p):
        print('E: failed to cd to {}'.format(p), file=sys.stderr)
        exit(1)
    else:
        print('I: pwd = {}'.format(os.getcwd()), file=sys.stderr)
    return para

###########################################################################
def analyze(para):
    #######################################################################
    # analize source (preparation)
    #######################################################################
    # check if '*.pro' exist? set pro
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
        f = open('setup.py', 'r')
        l = f.readline()
        if re.search('python3', l):
            # http://docs.python.org/3/distutils/
            para['dh_with'].update({'python3'})
            para['build_type']      = 'Python3 distutils'
            para['build_depends'].update({'python3-all'})
        elif re.search('python', l):
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
    # Binary package dependency needs to be updated
    #######################################################################
    rn = []
    for r in para['debs']:
        p = r['package']
        a = r['arch']
        t = r['type']
        m = r['multiarch']
        desc = r['desc']
        desc_long = r['desc_long']
        dp = r['depends']
        pd = r['pre-depends']

        if t == 'unknown':
            if 'perl_build' in para['dh_with']:
                dp.update({'${perl:Depends}', 'perl'})
            if 'perl_makemaker' in para['dh_with']:
                dp.update({'${perl:Depends}', 'perl'})
            if 'python2' in para['dh_with']:
                dp.update({'${python:Depends}'})
            if 'python3' in para['dh_with']:
                dp.update({'${python3:Depends}'})

        if t == 'perl':
            dp.update({'${perl:Depends}', 'perl'})
            #para['dh_with'].update({'perl'})
            print('W: no dh perl build support.  Maybe OK.', file=sys.stderr)
        if t == 'python':
            dp.update({'${python:Depends}'})
            para['dh_with'].update({'python2'})
        if t == 'python3':
            dp.update({'${python3:Depends}'})
            para['dh_with'].update({'python3'})

        rn.append({'package': p, 
                'arch': a, 
                'type': t, 
                'multiarch': m, 
                'desc': desc, 
                'desc_long': desc_long, 
                'depends': dp, 
                'pre-depends': pd})
    para['debs'] = rn
    #######################################################################
    # Autotools may need extra support tools if requested via --with
    #######################################################################
    if para['build_type'][:9] == 'Autotools':
        if 'python2' in para['dh_with']:
            para['build_depends'].update({'python-all'})
        if 'python3' in para['dh_with']:
            para['build_depends'].update({'python3-all'})
        if 'perl_build' in para['dh_with']:
            para['build_depends'].update({'perl'})
        if 'perl_makemaker' in para['dh_with']:
            para['build_depends'].update({'perl'})

    return para

if __name__ == '__main__':
    para['dh_with'] = set([])
    para = analyze(para)
    print('para =', para)

