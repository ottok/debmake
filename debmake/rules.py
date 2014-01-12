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
#export DEB_BUILD_MAINT_OPTIONS = hardening=+all
export DEB_CFLAGS_MAINT_APPEND  = -Wall -pedantic
export DEB_LDFLAGS_MAINT_APPEND = -Wl,--as-needed

%:
'''

    ###################################################################
    # dh $@: main build script of debhelper v9
    if para['dh_with'] == set():
        msg += '\tdh $@\n'   # no dh_with
    else:
        msg += '\tdh $@ --with "{}"\n'.format(','.join(para['dh_with']))

    ###################################################################
    # override build script of debhelper v9
    ###################################################################
    if 'python3' in para['dh_with']:
        # line tail inv-// are meant to be inv-/ in debian/rule
        # make sure to keep tab code for each line (make!)
        msg += '''\

# special work around for python3 (#538978 and #597105 bugs)
PY3REQUESTED := $(shell py3versions -r)
PY3DEFAULT := $(shell py3versions -d)
PYTHON3 := $(filter-out $(PY3DEFAULT),$(PY3REQUESTED)) python3

override_dh_auto_clean:
\t-rm -rf build

override_dh_auto_build:
\tset -ex; for python in $(PYTHON3); do \\
	    $$python setup.py build; \\
	done

override_dh_auto_install:
\tset -ex; for python in $(PYTHON3); do \\
	    $$python setup.py install \\
	        --root={}\\
	        --force\\
	        --install-layout=deb; \\
	done
'''.format(build_dir)
    msg += '\n# Customize this by adding more override scripts'
    return msg

#######################################################################
# Test script
#######################################################################
if __name__ == '__main__':
    import debmake.debs
    para = {}
    para['package'] = 'package'
    para['debs'] = set()
    para['dh_with'] = set()
    print(rules(para))
    print('***********************************************************')
    para['dh_with'] = set({'python3'})
    para['binaryspec'] = '-:python,-doc:doc'
    para['monoarch'] = False
    para['debs'] = debmake.debs.debs(para['binaryspec'], para['package'], para['monoarch'], para['dh_with'])
    print(rules(para))


