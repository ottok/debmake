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
import re
import debmake.read
#######################################################################
def control(para):
    msg = control_src(para)
    if para['desc']:
        desc = para['desc'].rstrip()
    else:
        desc = debmake.read.read(para['base_path'] + '/share/debmake/extra0desc/_short').rstrip()
    if para['desc_long']:
        desc_long = para['desc_long'].rstrip() + '\n'
    else:
        desc_long = debmake.read.read(para['base_path'] + '/share/debmake/extra0desc_long/_long').rstrip() + '\n'
    for deb in para['debs']:
        deb['desc'] = desc + debmake.read.read(para['base_path'] + '/share/debmake/extra0desc/' + deb['type']).rstrip()
        deb['desc_long'] = desc_long + debmake.read.read(para['base_path'] + '/share/debmake/extra0desc_long/' + deb['type']).rstrip() + '\n'
        msg += control_bin(para, deb)
    return msg

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
    # anything for perl and others XXX FIXME XXX
    msg += '\n'
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
    # non M-A
    if para['monoarch']:
        multiarch = ''
        predepends = ''
    # M-A + lib (pre-depends line)
    elif deb['pre-depends']:
        multiarch = 'Multi-Arch: ' + deb['multiarch'] + '\n'
        predepends = 'Pre-Depends; ' + ',\n\t'.join(deb['pre-depends']) + '\n'
    # M-A + non-lib
    else:
        multiarch = 'Multi-Arch: ' + deb['multiarch'] + '\n'
        predepends = ''

    ###################################################################
    return '''\
Package: {0}
Architecture: {1}
{2}{3}Depends: {4}
Description: {5}
{6}
'''.format(
            deb['package'],
            deb['arch'],
            multiarch,
            predepends,
            ',\n\t'.join(deb['depends']),
            deb['desc'],
            deb['desc_long'])

#######################################################################
# Test script
#######################################################################
if __name__ == '__main__':
    import debmake.debs
    para = {}
    para['package'] = 'package'
    para['section'] = 'misc'
    para['priority'] = 'normal'
    para['fullname'] = 'Osamu Aoki'
    para['email'] = 'osamu@debian.org'
    para['standard_version'] = '4.0.2'
    para['build_depends'] = set()
    para['homepage'] = 'http://www.debian.org'
    para['vcsvcs'] = 'git:git.debian.org'
    para['vcsbrowser'] = 'http://anonscm.debian.org'
    para['debs'] = set()
    para['dh_with'] = set()
    print(control(para))
    print('***********************************************************')
    para['dh_with'] = set({'python3'})
    para['binaryspec'] = '-:python,-doc:doc,lib'
    para['monoarch'] = False
    para['debs'] = debmake.debs.debs(para['binaryspec'], para['package'], para['monoarch'], para['dh_with'])
    print(control(para))
