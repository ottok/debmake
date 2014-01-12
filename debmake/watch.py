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
def watch(para):
    if para['targz'] =='tar.gz':
        targz = 'tar\.gz'
    elif para['targz'] =='tar.bz2':
        targz = 'tar\.bz2'
    elif para['targz'] =='tar.xz':
        targz = 'tar\.xz'
    else:
        targz = para['targz']
    msg = '''\
# watch control file for uscan

# See uscan(1) for how to set this file properly
#  * uupdate(1) for upgrade a source code package
#  * gbp-import-orig(1) with --uscan for upgrade GIT repo
# Uncomment to activate the configuration. Erase unused portions.
# Line continuations are performed with the tailing \\

# Many complications around package and version strings can be worked
# around using the "opts=" prefix.  See PER-SITE OPTIONS in uscan(1).

# Compulsory line, this is a version 3 file
version=3

# Uncomment to examine a Webpage
# <Webpage URL> <string match>
#http://www.example.com/downloads.php {0}-(.*)\.{1}

# Uncomment to examine a Webserver directory
#http://www.example.com/pub/{0}-(.*)\.{1}

# Uncommment to examine a FTP server
#ftp://ftp.example.com/pub/{0}-(.*)\.{1} debian uupdate

# Uncomment to find new files on SourceForge (via qa.debian.org redirector)
#http://sf.net/{0}/{0}-src-(.+)\.{1}

# Uncomment to find new files on Google Code
#http://code.google.com/p/{0}/downloads/list?can=1 .*/{0}-(\d[\d.]*)\.{1}

# Uncomment to find new files on GitHub using the tags page:
#https://github.com/<user>/{0}/tags .*/(\d[\d\.]*)\.{1}

# Uncomment to use the cryptographic signature in a detached file with
# ".asc" suffix using the "pgpsigurlmangle" option.
# opts=<options> <Webpage URL> <string match>
#opts=pgpsigurlmangle=s/$/.asc/ http://ftp.example.org/{0}/download.html pub/{0}-([\d\.]*)\.{1}
'''.format(para['package'], targz)
    return msg

#######################################################################
# Test script
#######################################################################
if __name__ == '__main__':
    para = {}
    para['package'] = 'packagename'
    para['targz'] = 'tar.xz'
    print(watch(para))

