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
import sys
import debmake.cat
import debmake.changelog
import debmake.control
import debmake.copyright
import debmake.install
import debmake.local_options
import debmake.readme_debian
import debmake.rules
import debmake.watch
#######################################################################
def debian(para):
    ###################################################################
    # set level for the extra file outputs
    ###################################################################
    if para['extra'] == '': # default
        if os.path.isfile('debian/changelog'):
            print('I: found "debian/changelog"', file=sys.stderr)
            para['extra'] = '0'
        elif os.path.isfile('debian/control'):
            print('I: found "debian/control"', file=sys.stderr)
            para['extra'] = '0'
        elif os.path.isfile('debian/copyright'):
            print('I: found "debian/copyright"', file=sys.stderr)
            para['extra'] = '0'
        elif os.path.isfile('debian/rules'):
            print('I: found "debian/rules"', file=sys.stderr)
            para['extra'] = '0'
        elif len(para['debs']) == 1:
            print('I: single binary package', file=sys.stderr)
            para['extra'] = '1'
        else:
            print('I: multi binary packages: {}'.format(len(para['debs'])), file=sys.stderr)
            para['extra'] = '2'
    try:
        extra = int(para['extra'])
    except:
        extra = 4
    print('I: debmake -x "{}" ...'.format(extra), file=sys.stderr)
    ###################################################################
    # must have files (level=0)
    ###################################################################
    debmake.cat.cat('debian/changelog', debmake.changelog.changelog(para))
    debmake.cat.cat('debian/control', debmake.control.control(para))
    debmake.cat.cat('debian/copyright', debmake.copyright.copyright(para['package'], para['license']))
    debmake.cat.cat('debian/rules', debmake.rules.rules(para))
    os.chmod('debian/rules', 0o755)
    ###################################################################
    # optional files which are always created for new source (level=1)
    ###################################################################
    if extra >= 1:
        if para['native']:
            debmake.cat.cat('debian/source/format', '3.0 (native)')
        else:
            debmake.cat.cat('debian/source/format', '3.0 (quilt)')
        debmake.cat.cat('debian/compat', para['compat'])
        debmake.cat.cat('debian/watch', debmake.watch.watch(para))
        debmake.cat.cat('debian/source/local-options', debmake.local_options.local_options())
        debmake.cat.cat('debian/README.Debian', debmake.readme_debian.readme_debian(para))
    ###################################################################
    # popular optional files for multi-binary files (level=2)
    #     (create templates for all the binary packages)
    ###################################################################
    if extra >= 2:
        for deb in para['debs']:
            debmake.cat.cat('debian/' + deb['package'] + '.install', debmake.install.install(deb['type']))
            if deb['type'] == 'doc':
                debmake.cat.cat('debian/' + deb['package'] + '.docs', 'usr/share/doc/' + deb['package'] + '/\n')
    ###################################################################
    # rarely used optional files (level=3) dh_make compatibilities
    #     (create templates only for the first binary package)
    ###################################################################
    if extra >= 3:
        debs0 = para['debs'][0] # the first binary package
        datadir = para['base_path'] + '/share/debmake/extra/'
        ldata = len(datadir)
        substlist = {
            '@PACKAGE@': deb0['package'],
            '@UCPACKAGE@': deb0['package'].upper(),
            '@YEAR@': para['year'],
            '@FULLNAME@': para['fullname'],
            '@EMAIL@': para['email'],
            '@SHORTDATE@': para['shortdate'],
        }
        for file in glob.glob(datadir + '*.ex'):
            with open(file, 'r') as f:
                text = f.read()
            for k in substlist.keys():
                text = text.replace(k, substlist[k])
            if file[ldata:ldata+7] == 'package':
                newfile = 'debian/' + deb0['package'] + file[ldata+7:]
            else:
                newfile = 'debian/' + file[ldata:]
            debmake.cat.cat(newfile, text)
    if extra >= 4:
        datadir += 'license-examples/'
        ldata = len(datadir)
        for file in glob.glob(datadir + '*'):
            with open(file, 'r') as f:
                text = f.read()
            for k in substlist.keys():
                text = text.replace(k, substlist[k])
            newfile = 'debian/license-examples/' + file[ldata:]
            debmake.cat.cat(newfile, text)
    else:
        print('I: run "debmake -x{}" to get more template files'.format(extra + 1), file=sys.stderr)
    return

#######################################################################
# Test script
#######################################################################
if __name__ == '__main__':
    print('no test')

