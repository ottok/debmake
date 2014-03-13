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
import operator
import os
import re
import sys
import debmake.copyright

###################################################################
# Define constants
###################################################################
MAX_FILE_SIZE = 1024*1024 # 1 MiB
SKIP_FILES = [
        'COPYING',
        'LICENSE',
        'ChangeLog',
        'changelog',
]       # Skip these files for scanning
#        'INSTALL',
#        'README',
#        'README.txt',
#        'README.Debian',
#        'Makefile.in',
#        'aclocal.m4',
#        'compile',
#        'config.guess',
#        'config.h.in',
#        'config.sub',
#        'configure',
#        'depcomp',
#        'install-sh',
#        'ltconfig',
#        'ltmain.sh',
#        'missing',
#        'mkinstalldirs',
#        'py-compile'

# First 2 are specified by --license

extequiv = {'pl': 'perl',
            'PL': 'perl',
            'pm': 'perl',
            'py': 'python',
            'pyc': 'python',
            'rb': 'ruby',
            'javac': 'java',
            'js': 'javascript',
            'ml': 'ocml',
            'vala': 'vala',
            'h' : 'c',
            'cpp': 'c',
            'CPP': 'c',
            'cc': 'c',
            'C': 'c',
            'cxx': 'c',
            'CXX': 'c',
            'c++': 'c',
            'hh': 'c',
            'H': 'c',
            'hxx': 'c',
            'Hxx': 'c',
            'HXX': 'c',
            'hpp': 'c',
            'h++': 'c',
            'asm': 'c',
            's': 'c',
            'S': 'c',
            'TXT': 'text',
            'txt': 'text',
            'doc': 'text',
            'html': 'text',
            'htm': 'text',
            'xml': 'text',
            'dbk': 'text',
            'dtd': 'text',
            'odt': 'text',
            'sda': 'text',
            'sdb': 'text',
            'sdc': 'text',
            'sdd': 'text',
            'sds': 'text',
            'sdw': 'text',
            'a': 'binary',
            'class': 'binary',
            'jar': 'binary',
            'exe': 'binary',
            'com': 'binary',
            'dll': 'binary',
            'obj': 'binary',
            'zip': 'archive',
            'tar': 'archive',
            'cpio': 'archive',
            'afio': 'archive',
            'jpeg': 'media',
            'jpg': 'media',
            'm4a': 'media',
            'png': 'media',
            'gif': 'media',
            'GIF': 'media',
            'svg': 'media',
            'ico': 'media',
            'mp3': 'media',
            'ogg': 'media',
            'wav': 'media',
            'ttf': 'media',
            'TTF': 'media',
            'otf': 'media',
            'OTF': 'media',
            'wav': 'media'
            }
###################################################################
# re.search file name extension

re_ext = re.compile(r'\.(?P<ext>[^.]+)(?:\.in|\.gz|\.bz2|\.xz|\.Z\|.z|~)*$')

###################################################################
# Check if binary file
###################################################################
def istextfile(file, blocksize=4048):
    buff = open(file, 'rb').read(blocksize)
    if b'\x00' in buff:
        return False
    else:
        return True

###################################################################
# Get all files to be analyzed under dir
###################################################################
def get_all_files(dir):
    nonlink_files = []
    binary_files = []
    huge_files = []
    extensions = []
    # extensions : representative code type
    # binary means possible non-DFSG component
    if not os.path.isdir(dir):
        print('E: get_all_files(dir) should have existing dir', file=sys.stderr)
        exit(1)
    for dir, subdirs, files in os.walk(dir):
        for file in files:
            filepath = os.path.join(dir, file)
            if os.path.islink(filepath):
                pass # skip symlink (both for file and dir)
            elif file in SKIP_FILES:
                pass # skip automatically generated files
            else:
                re_ext_match = re_ext.search(file)
                if re_ext_match:
                    ext = re_ext_match.group('ext')
                    if ext in extequiv.keys():
                        extrep = extequiv[ext]
                    else:
                        extrep = ext
                    extensions.append(extrep)
                if os.path.getsize(filepath) > MAX_FILE_SIZE:
                    huge_files.append(filepath)
                elif istextfile(filepath):
                    nonlink_files.append(filepath)
                else:
                    binary_files.append(filepath)
        # do not decend to VCS dirs
        for vcs in ['CVS', '.svn', '.pc', '.git', '.hg', '.bzr']:
            if vcs in subdirs:
                subdirs.remove(vcs)  # skip VCS
        # do not decend to symlink dirs
        symlinks = []
        for subdir in subdirs:
            dirpath = os.path.join(dir, subdir)
            if os.path.islink(dirpath):
                symlinks.append(subdir)
        # do not change subdirs inside looping over subdirs
        for symlink in symlinks:
            subdirs.remove(symlink)  # skip symlinks
            print('W: get_all_files(dir) skip symlink dir', file=sys.stderr)
    return (nonlink_files, binary_files, huge_files, extensions)

#######################################################################
# complete scanfiles
#######################################################################
def scanfiles(mode=0, check=True):
    (nonlink_files, binary_files, huge_files, extensions) = get_all_files('.')
    # copyright license checks
    if check:
        data = debmake.copyright.check_all_license(nonlink_files)
        bdata = debmake.copyright.bunch_licence(data, mode)
    else:
        bdata = []
    # filename extensions
    n = len(extensions)
    count = {}
    for ext in extensions:
        if ext in count.keys():
            count[ext] += 100.0 / n
        else:
            count[ext] = 100.0 / n
    extcount = sorted(count.items(), key=operator.itemgetter(1), reverse=True)
    for ext, freq in extcount:
        if ext == 'binary' or ext == 'archive':
            print('W: {} type exists.  Maybe non-DFSG!'.format(ext), file=sys.stderr)
        print('I: {1:3.0f} %, ext = {0}'.format(ext, freq), file=sys.stderr)
    return (bdata, binary_files, huge_files, extcount)

#######################################################################
# Test script
#######################################################################
if __name__ == '__main__':
    (bdata, binary_files, huge_files, extcount) = scanfiles(mode=1, check=False)
    print('Number of bunched license data: {}'.format(len(bdata)))
    print('I: frequency of file extensions', file=sys.stderr)
    for ext, freq in extcount:
        print('{1:3.0f} %, ext = {0}'.format(ext, freq))
