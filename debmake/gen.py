#!/usr/bin/python3
# vim:se tw=0 sts=4 ts=4 et ai:
import os, re, sys, glob
import debmake.copyright

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

#######################################################################
def debian(para):
    source_format(para)
    source_local_options(para)
    patches_series(para)
    compat(para)
    rules(para)
    README_Debian(para)
    changelog(para)
    copyright(para)
    control(para)
    install(para)
    installdocs(para)
    docbase(para)
    manpages(para)
    if para['extra']:
        extra(para)
    else:
        print('I: run "debmake -x" to get more template files', file=sys.stderr)
    if os.getcwd() != para['cwd']:
        print('I: upon return to the shell, current directory becomes {}'.format(para['cwd']), file=sys.stderr)
        print('I: please execute "cd {0}"'.format(os.getcwd()), file=sys.stderr)
        print('I: before building binary package with dpkg-buildpackage (or debuild, pdebuild, sbuild, ...).', file=sys.stderr)
    return

#######################################################################
# mkdir -p path
def mkdirp(path):
    return os.makedirs(path, exist_ok=True)

#######################################################################
# cat >file and cat >>file
def writefile(para, file, text, append=False, end='\n'):
    if append:
        f = open(file, 'a')
    else:
        if not para['overwrite'] and os.path.isfile(file) and os.stat(file).st_size != 0:
            # skip if a file exists and non-zero content
            print('I: File already exits, skipping: {}'.format(file), file=sys.stderr)
            return
        f = open(file, 'w')
    print(text, file=f, end=end)
    if append:
        print('I: File written: {} (append)'.format(file), file=sys.stderr)
    else:
        print('I: File written: {}'.format(file), file=sys.stderr)
    f.close()
    return

#######################################################################
# sed-like
def subst(para, text):
    subst = {
        '@PACKAGE@': para['package'],
        '@UCPACKAGE@': para['package'].upper(),
        '@YEAR@': para['year'],
        '@FULLNAME@': para['fullname'],
        '@EMAIL@': para['email'],
        '@SHORTDATE@': para['shortdate'],
    }
    for k in subst.keys():
        text = text.replace(k, subst[k])
    return text

#######################################################################
# find $(pwd) -type f
def find_files():
    matches = []
    for root, dirname, filenames in os.walk('./'):
            if dirname[:6] != 'debian':
                for filename in filenames:
                    matches.append(os.path.join(root, dirname, filename))
    return matches

#######################################################################
def source_format(para):
    mkdirp('debian/source')
    if para['native']:
        writefile(para, 'debian/source/format', '3.0 (native)')
    else:
        writefile(para, 'debian/source/format', '3.0 (quilt)')
    return

#######################################################################
def source_local_options(para):
    mkdirp('debian/source')
    msg = '''\
#### Uncomment some of the following lines if you wish :-) See dpkg-source(1)
#unapply-patches
#abort-on-upstream-changes
'''
    writefile(para, 'debian/source/local-options', msg)
    return

#######################################################################
def patches_series(para):
    mkdirp('debian/patches')
    msg = '''\
# This is manually managed by users with dquilt (quilt(1) wrapper)
# See http://www.debian.org/doc/manuals/maint-guide/modify.en.html#quiltrc
# Also this may be updated by dpkg-source(1) when making a package.
'''
    writefile(para, 'debian/patches/series', msg)
    return

#######################################################################
def compat(para):
    msg = para['compat']
    writefile(para, 'debian/compat', msg)
    return

#######################################################################
def rules(para):
    if len(para['debs']) == 1:
        p = para['debs'][0]['package'] # first binary package name
    else:
        p = 'tmp'
    build_dir = 'debian/' + p
    ###################################################################
    # build_mode independent portion
    msg = '''\
#!/usr/bin/make -f
# uncomment to enable verbose mode for debhelper
#DH_VERBOSE = 1
# uncomment to exclude VCS paths
#DH_ALWAYS_EXCLUDE=CVS:.svn:.git

%:
'''

    ###################################################################
    # dh $@: main build script of debhelper v9
    if para['dh_with'] == set([]):
        msg += '\tdh $@\n'   # no dh_with
    else:
        msg += '\tdh $@ --with "{}"\n'.format(','.join(para['dh_with']))

    ###################################################################
    # override build script of debhelper v9
    ###################################################################
    if 'python3' in para['dh_with']:
        # line tail // are meant to be / in debian/rule
        # make sure to keep tab code for each line (make!)
        msg += '''\

# special work around for python3 (#538978 and #597105 bugs)
PY3REQUESTED := $(shell py3versions -r)
PY3DEFAULT := $(shell py3versions -d)
PYTHON3 := $(filter-out $(PY3DEFAULT),$(PY3REQUESTED)) python3

override_dh_auto_clean:
	-rm -rf build

override_dh_auto_build:
	set -ex; for python in $(PYTHON3); do \\
	    $$python setup.py build; \\
	done

override_dh_auto_install:
	set -ex; for python in $(PYTHON3); do \\
	    $$python setup.py install \\
	        --root=''' + build_dir + '''\\
	        --install-layout=deb; \\
	done
'''
    msg += '\n# Customize by adding override scripts\n'
    ###################################################################
    # write to file
    ###################################################################
    writefile(para, 'debian/rules', msg)
    return

#######################################################################
def README_Debian(para):
    sep = '-' * (len(para['package']) + 11)
    msg = '''\
{0} for Debian
{1}

Please edit this to provide information specific information on 
this {0} Debian package.

    (Automatically generated by {2} Version {3})

 -- {4} <{5}>  {6}
'''.format(
            para['package'], 
            sep, 
            para['program_name'], 
            para['program_version'], 
            para['fullname'], 
            para['email'], 
            para['date'])
    ###################################################################
    # write to file
    writefile(para, 'debian/README.Debian', msg)
    return

#######################################################################
def changelog(para):
    if para['native']:
        msg = '''\
{0} ({1}) UNRELEASED; urgency=low

  * Initial release. Closes: #nnnn
    <nnnn is the bug number of your ITP>

 -- {2} <{3}>  {4}
'''.format(
            para['package'], 
            para['version'], 
            para['fullname'], 
            para['email'],
            para['date'])
    else:
        msg = '''\
{0} ({1}-{2}) UNRELEASED; urgency=low

  * Initial release. Closes: #nnnn
    <nnnn is the bug number of your ITP>

 -- {3} <{4}>  {5}
'''.format(
            para['package'], 
            para['version'], 
            para['revision'], 
            para['fullname'], 
            para['email'],
            para['date'])
    ###################################################################
    # write to file
    writefile(para, 'debian/changelog', msg)

#######################################################################
def control(para):
    file = 'debian/control'
    if not para['overwrite'] and os.path.isfile(file) and os.stat(file).st_size != 0:
        print('I: File already exits, skipping: {}'.format(file), file=sys.stderr)
        return
    else:
        msg = control_src(para)
        for deb in para['debs']:
            msg += control_bin(para, deb)
        writefile(para, 'debian/control', msg)
        return

#######################################################################
def control_src(para):
    msg = '''\
Source: {0}
Section: {1}
Priority: {2}
Maintainer: {3} <{4}>
Build-Depends: {5}
Standards-Version: {6}
Homepage: {7}
{8}: {9}
{10}: {11}
'''.format(
            para['package'],
            para['section'],
            para['priority'],
            para['fullname'],
            para['email'], 
            ',\n\t'.join(para['build_depends']),
            para['standard_version'],
            para['homepage'],
            guess_vcsvcs(para['vcsvcs']),
            para['vcsvcs'],
            guess_vcsbrowser(para['vcsbrowser']),
            para['vcsbrowser'])
    if 'python2' in para['dh_with']:
        msg += 'X-Python-Version: >= 2.6\n'
    if 'python3' in para['dh_with']:
        msg += 'X-Python3-Version: >= 3.2\n'
    # anythong for perl and others XXX FIXME XXX
    msg += '\n'
    ###################################################################
    return msg

#######################################################################
def guess_vcsvcs(vcsvcs):
    if re.search('\.git$', vcsvcs):
        return 'Vcs-Git'
    elif re.search('\.hg$', vcsvcs):
        return 'Vcs-Hg'
    elif re.search('^:pserver:', vcsvcs):
        # CVS :pserver:anonymous@anonscm.debian.org:/cvs/webwml
        return 'Vcs-Cvs'
    elif re.search('^:ext:', vcsvcs):
        # CVS :ext:username@cvs.debian.org:/cvs/webwml
        return 'Vcs-Cvs'
    elif re.search('^svn[:+]', vcsvcs):
        # SVN svn://svn.debian.org/ddp/manuals/trunk manuals
        # SVN svn+ssh://svn.debian.org/svn/ddp/manuals/trunk
        return 'Vcs-Svn'
    else:
        return '#Vcs-Git'

#######################################################################
def guess_vcsbrowser(vcsbrowser):
    if re.search('\.git$', vcsbrowser):
        return 'Vcs-Browser'
    elif re.search('\.hg$', vcsbrowser):
        return 'Vcs-Browser'
    elif re.search('^:pserver:', vcsbrowser):
        # CVS :pserver:anonymous@anonscm.debian.org:/cvs/webwml
        return 'Vcs-Browser'
    elif re.search('^:ext:', vcsbrowser):
        # CVS :ext:username@cvs.debian.org:/cvs/webwml
        return 'Vcs-Browser'
    elif re.search('^svn[:+]', vcsbrowser):
        # SVN svn://svn.debian.org/ddp/manuals/trunk manuals
        # SVN svn+ssh://svn.debian.org/svn/ddp/manuals/trunk
        return 'Vcs-Browser'
    else:
        return '#Vcs-Browser'

#######################################################################
def control_bin(para, deb):
    if para['monoarch']:
        msg = '''\
Package: {0}
Architecture: {1}
Depends: {2}
Description: {3}
{4}
'''.format(
            deb['package'],
            deb['arch'],
            ',\n\t'.join(deb['depends']),
            deb['desc'],
            deb['desc_long'])
    else:
        msg = '''\
Package: {0}
Architecture: {1}
Multi-Arch: {2}
Pre-Depends: {3}
Depends: {4}
Description: {5}
{6}
'''.format(
            deb['package'],
            deb['arch'],
            deb['multiarch'],
            ',\n\t'.join(deb['pre-depends']),
            ',\n\t'.join(deb['depends']),
            deb['desc'],
            deb['desc_long'])
    return msg

#######################################################################

###################################################################
# Write copyright and license
#  using writefile(para, file, text, append=False)
###################################################################
def copyright(para):
    if not para['overwrite'] and os.path.isfile('debian/copyright') and os.stat('debian/copyright').st_size != 0:
        print('I: File already exits, skipping: {}'.format('debian/copyright'), file=sys.stderr)
        return
    # get scan result of copyright
    (bdata, nonlink_files, binary_files, huge_files) = debmake.copyright.scan_copyright_data()
    # make text to print
    text = '''\
Format: http://www.debian.org/doc/packaging-manuals/copyright-format/1.0/
Upstream-Name: {}
Source: <url://example.com>

'''.format(para['package'])
    for bd in bdata:
        text += '#----------------------------------------------------------------------------\n'
        text += 'Files: {}\n'.format('\n\t'.join(bd[1]))
        # Copyright:
        text += 'Copyright:'
        for name in bd[2].keys():
            # name found
            if bd[2][name][0] == bd[2][name][1]:
                if bd[2][name][1] == 0: # max == 0 for binary etc.
                    text += ' {}\n'.format(name)    # XXXXX FIXME
                else:
                    text += ' {} {}\n'.format(bd[2][name][0], name)
            else:
                if bd[2][name][1] == 0: # max == 0 means not found
                    text += ' {}\n'.format(name)
                else:
                    text += ' {}-{} {}\n'.format(bd[2][name][0], bd[2][name][1], name)
        if bd[3] == []:
            text += 'License: NO_LICENSE_TEXT_FOUND\n\n'
        else:
            text += 'License:\n {}\n'.format(debmake.copyright.format_license(bd[3]))
        # add comments
        if bd[4] != '':
            text += '#............................................................................\n'
            text += '# Gray hits with matching text of "copyright":\n'
            text += bd[4]
    if binary_files != []:
        text += '#----------------------------------------------------------------------------\n'
        text += '# Binary files (skipped):\n# {}\n\n'.format('\n# '.join(binary_files))
    if huge_files != []:
        text += '#----------------------------------------------------------------------------\n'
        text += '# Huge files   (skipped):\n# {}\n\n'.format('\n# '.join(huge_files))
    text += '''\
#----------------------------------------------------------------------------
# This is meant only as a template example.
#
# Edit this accordinng to the "Machine-readable debian/copyright file" as
# http://www.debian.org/doc/packaging-manuals/copyright-format/1.0/ .
#
# Generate typical license templates with the "debmake -x" and merge them 
# into here as needed.  See "man 8 debmake" for more.
#
# Please avoid to pick license terms that are more restrictive than the
# packaged work, as it may make Debian's contributions unacceptable upstream.

'''
    for f in debmake.copyright.license_files(para):
        text += '#----------------------------------------------------------------------------\n'
        text += '# License: {}\n'.format(f)
        text += debmake.copyright.license_text(f)
        text += '\n'

    writefile(para, 'debian/copyright', text)
    return

#######################################################################
def extra(para):
    for file in glob.glob(para['base_path'] + '/share/debmake/extra/*'):
        with open(file, 'r') as f:
            text = f.read()
        writefile(para, 
            'debian/' + os.path.basename(file), 
            subst(para, text))
    return

#######################################################################
#debs =[{'package': p,
#        'arch': a,
#        'type': t,
#        'multiarch': m,
#        'desc': desc,
#        'desc_long': desc_long,
#        'depends': dp,
#        'pre-depends': pd}, ...}
#######################################################################
def install(para):
    #text = '# see dh_install'
    for deb in para['debs']:
        if deb['type'] == 'lib':
            text = 'lib/\nusr/lib/\n'
        elif deb['type'] == 'bin' or deb['type'] == 'script':
            text = 'bin/\nusr/bin/\nsbin/\nusr/sbin/\n'
        elif deb['type'] == 'data':
            text = 'usr/share/' + para['package'] + '/\n'
        else:
            text = ''
        writefile(para, 
            'debian/' + deb['package'] +'.install', 
            text)
    return

#######################################################################
def installdocs(para):
    #text = '# see dh_install'
    for deb in para['debs']:
        if deb['type'] == 'doc':
            text = 'usr/share/doc/' + deb['package'] + '/\n'
            writefile(para, 
                'debian/' + deb['package'] +'.docs', 
                text)
    return

#######################################################################
def docbase(para):
    for deb in para['debs']:
        if deb['type'] == 'doc':
            text = '''\
Document: {0}
Title: Debian {1} Manual
Author: <insert document author here>
Abstract: This manual describes what {1} is
 and how it can be used to
 manage online manuals on Debian systems.
Section: unknown

Format: PDF
Files: /usr/share/doc/{0}/{1}.pdf.gz

Format: text
Files: /usr/share/doc/{0}/{1}.text.gz

Format: HTML
Index: /usr/share/doc/{0}/html/index.html
Files: /usr/share/doc/{0}/html/*.html
'''.format(deb['package'], para['package'])
            writefile(para, 
                'debian/' + deb['package'] +'.doc-base', 
                text)
    return

#######################################################################
def manpages(para):
    for deb in para['debs']:
        if deb['type'] == 'bin':
            text = '# See dh_installman(1)\n'
            writefile(para, 
                'debian/' + deb['package'] +'.manpages', 
                text)
    return

#######################################################################
# Test script
#######################################################################
if __name__ == '__main__':
    para = {}
    para['package'] = 'package'
    para['year'] = '9999'
    para['fullname'] = 'fullname'
    para['email'] = 'foo@example.org'
    para['shortdate'] = '1919-12-19'
    text = '@PACKAGE@ @UCPACKAGE@ @YEAR@ @USERNAME@ @EMAIL@ @SHORTDATE@'
    print(subst(para, text))

