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
#######################################################################
def install(deb):
    if 'type' not in deb:
        text = ''
    elif deb['type'] == 'lib':
        text = 'lib/\nusr/lib/\n'
    elif deb['type'] == 'bin' or deb['type'] == 'script':
        text = 'bin/\nusr/bin/\nsbin/\nusr/sbin/\n'
    elif deb['type'] == 'data':
        text = 'usr/share/' + para['package'] + '/\n'
    else:
        text = ''
    return text

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
    para['dh_with'] = set({'python3'})
    para['binaryspec'] = '-:python3,-doc:doc,libpackage,-dbg'
    para['monoarch'] = False
    para['debs'] = debmake.debs.debs(para['binaryspec'], para['package'], para['monoarch'], para['dh_with'])
    for deb in  para['debs']:
        print(install(deb))
        print('*****')

