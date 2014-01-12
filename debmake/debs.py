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
import sys
###########################################################################
# sanity: called from debmake.main()
###########################################################################
def debs(binaryspec, package, monoarch, dh_with):
    #######################################################################
    # parse binary package names and their specification: binaryspec -> debs
    #######################################################################
    debs = []
    for x in binaryspec.split(','):
        y = x.split(':')
        ###################################################################
        # get real binary package name: p
        ###################################################################
        if y[0] == '':
            p = package
        elif y[0] == '-':
            p = package
        elif y[0][0] == '-':
            p = package + y[0]
        else:
            p = y[0]
        # first default values and then override or update values
        a = 'any'       # arch
        m = 'foreign'   # muiti-arch
        t = 'unknown'   # type
        dp = {'${misc:Depends}'}
        pd = set([])
        # Prefix names should come first to be overriden later
        if len(y[0]) > 3 and y[0][:3] == 'lib':
            a = 'any'
            m = 'same'
            t = 'lib'
        elif len(y[0]) > 6 and y[0][6:] == 'fonts-':
            a = 'all'
            m = 'foreign'
            t = 'data'
        elif len(y[0]) > 7 and y[0][:7] == 'python-':
            a = 'all'
            m = 'foreign'
            t = 'python'
        elif len(y[0]) > 8 and y[0][:8] == 'python3-':
            a = 'all'
            m = 'foreign'
            t = 'python3'
        else:
            pass
        # Suffix names override
        if len(y[0]) > 5 and y[0][-5:] == '-perl':
            a = 'all'
            m = 'foreign'
            t = 'perl'
        elif len(y[0]) > 4 and y[0][-4:] == '-dev':
            a = 'any'
            m = 'same'
            t = 'dev'
        elif len(y[0]) > 4 and y[0][-4:] == '-dbg':
            a = 'any'
            m = 'same'
            t = 'dbg'
        elif len(y[0]) > 4 and y[0][-4:] == '-bin':
            a = 'any'
            m = 'foreign'
            t = 'bin'
        elif len(y[0]) > 5 and y[0][-5:] == 'tools':
            a = 'any'
            m = 'foreign'
            t = 'bin'
        elif len(y[0]) > 5 and y[0][-5:] == 'utils':
            a = 'any'
            m = 'foreign'
            t = 'bin'
        elif len(y[0]) > 4 and y[0][-4:] == '-doc':
            a = 'all'
            m = 'foreign'
            t = 'doc'
        elif len(y[0]) > 5 and y[0][-5:] == '-html':
            a = 'all'
            m = 'foreign'
            t = 'doc'
        elif len(y[0]) > 7 and y[0][-7:] == '-manual':
            a = 'all'
            m = 'foreign'
            t = 'doc'
        elif len(y[0]) > 7 and y[0][-7:] == '-common':
            a = 'all'
            m = 'foreign'
            t = 'unknown'
        else:
            pass
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
                m = 'foreign'
                t = 'doc'
            elif y[1] == 'data':
                a = 'all'
                m = 'foreign'
                t = 'data'
            elif y[1] == 'bin':
                a = 'any'
                m = 'foreign'
                t = 'bin'
            elif y[1] == 'lib':
                a = 'any'
                m = 'same'
                t = 'lib'
            elif y[1] == 'dev':
                a = 'any'
                m = 'same'
                t = 'dev'
            elif y[1] == 'dbg':
                a = 'any'
                m = 'same'
                t = 'dbg'
            elif y[1] == 'script':
                a = 'all'
                m = 'foreign'
                t = 'shell'
            elif y[1] == 'perl':
                a = 'all'
                m = 'foreign'
                t = 'perl'
            elif y[1] == 'python':
                a = 'all'
                m = 'foreign'
                t = 'python'
            elif y[1] == 'python3':
                a = 'all'
                m = 'foreign'
                t = 'python3'
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
 .
 package type is "{}".
'''.format(t)
        ###################################################################
        # monoarch = non-multi-arch
        ###################################################################
        if not monoarch:
            pd.update({'${misc:Pre-Depends}'})
        else:
            m = ''
        ###################################################################
        # update binary package dependency by package type etc.
        ###################################################################
        if t == 'perl':
            dp.update({'${perl:Depends}', 'perl'})
            print('W: no dh perl build support.  Maybe OK.', file=sys.stderr)
        elif t == 'python':
            dp.update({'${python:Depends}'})
        elif t == 'python3':
            dp.update({'${python3:Depends}'})
        elif t == 'unknown':
            if 'perl_build' in dh_with:
                dp.update({'${perl:Depends}', 'perl'})
            if 'perl_makemaker' in dh_with:
                dp.update({'${perl:Depends}', 'perl'})
            if 'python2' in dh_with:
                dp.update({'${python:Depends}'})
            if 'python3' in dh_with:
                dp.update({'${python3:Depends}'})
        else:
            pass
        ###################################################################
        # append dictionary to a list
        ###################################################################
        debs.append({'package': p, 
                'arch': a, 
                'multiarch': m, 
                'desc': desc, 
                'desc_long': desc_long, 
                'depends': dp, 
                'pre-depends': pd,
                'type': t})
    return debs

#######################################################################
# Test script
#######################################################################
if __name__ == '__main__':
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
    para['binaryspec'] = '-:python,-doc:doc'
    para['monoarch'] = False
    for deb in debs(para['binaryspec'], para['package'], para['monoarch'], para['dh_with']):
        for p, v in deb.items():
            print("deb['{}'] = \"{}\"".format(p,v))
        print('*****************************************')
