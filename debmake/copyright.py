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
import operator
import os
import re
import subprocess
import sys
import debmake.debug
###################################################################
# Define constants
###################################################################
MAX_FILE_SIZE = 100*1024 # 100 KB
SKIP_FILES = [
        'COPYING',
        'LICENSE',
        'INSTALL',
        'README',
        'README.txt',
        'README.Debian',
        'ChangeLog',
        'changelog',
        'Makefile.in',
        'aclocal.m4',
        'compile',
        'config.guess',
        'config.h.in',
        'config.sub',
        'configure',
        'depcomp',
        'install-sh',
        'ltconfig',
        'ltmain.sh',
        'missing',
        'mkinstalldirs',
        'py-compile'
]       # Skip these files for scanning

# First 2 are specified by --license

###################################################################
# Emulate C's enum by function enums
###################################################################
def enums(**enums):
    return type('Enum', (), enums)

###################################################################
# Define constants with enums
###################################################################
Style = enums(unknown=0, comment=1, quote=2, plain=3, irregular=4)
stylestr = ('??', '//', '/*', '__', 'XX')

Section = enums(outside=0, copyright=1, license=2)
sectionstr = ('outside ', 'copyright', 'license ')

###################################################################
# Regular expressions
###################################################################
# re.search: copyright line
re_copyright_mark = re.compile(r'''
                (Copyright|\(C\)|©|\\\(co)\s              # Copyright mark
                ''', re.IGNORECASE | re.VERBOSE)

# re.search: exclusion of C MACRO, copyright holder, ...
re_fake_copyright_mark = re.compile(r'''(
                [=?]|
                \S\(C\)|
                if\s\(C\)|
                \SCopyright|
                print.+copyright|
                copyright.+disclaimer|
                copyright\s+for\s|
                copyright.+holder|
                copyright\s+is\s|
                copyright.+interest|
                copyright.+information|
                copyright.+license|
                copyright.+line|
                copyright.+name|
                copyright.+string|
                copyright.+notice|
                copyright\slaw
                )''', re.IGNORECASE | re.VERBOSE)

###################################################################
# re.match: copyright line with comment characters
re_copy_in_comment = re.compile(r'''
                (?P<marker>\*+|/\*|\#+|//|dnl\s|--|@c|\.\\"|%|;;)
                # C, C++, Shell, m4, Lua, info, man comment, tex
                (\s|written\s+by\s+)*                        # possible comment
                (?P<copyright>(Copyright|\(C\)|©).*)        # copyright mark
                ''', re.IGNORECASE | re.VERBOSE)

# re.match: copyright line with quotes
re_copy_in_quote = re.compile(r'''
                .*(?P<q1>["'])                          # quote opening
                (\s+|\t+|written\s+by\s+)?                # possible quote 
                (?P<copyright>(Copyright|\(C\)|©)[^"']+)    # copyright text
                (?P=q1)                                     # quote closing
                ''', re.IGNORECASE | re.VERBOSE)

# re.match: copyright line with quotes (cont)
re_copy_in_quote_continue = re.compile(r'''
                .*(?P<q1>["'])                          # quote opening
                (\s+|\t+|written\s+by\s+)?                # possible plain text 
                (?P<copyright>[^"']+)                       # continued copyright text
                (?P=q1)                                     # quote closing
                ''', re.IGNORECASE | re.VERBOSE)

# re.match: copyright line in plain text
re_copy_in_plaintext = re.compile(r'''
                (\s+|\t+|written\s+by\s+)?                # possible plain text
                (?P<copyright>(Copyright|\(C\)|©|\\\(co)\s.+)  # Copyright mark
                ''', re.IGNORECASE | re.VERBOSE)

# re.match: start of license
re_license = re.compile(r'''(
                this\s+is|
                this\s+program|
                this\s+software|
                this\s+[\w.]+\s+is|
                license|
                Distributable\s+under|
                Released\s+under|
                You\s+are\s+free|
                permission\s+is|
                51\s+Franklin\s+Street|
                59\s+Temple\s+Place|
                .*redistribution|
                .*everyone.*permitted.*copy|
                .*For\s+copyright|
                .*See.+LICENSE|
                .*See.+COPYING|
                .*See.*legal\s+use|
                .*See.*distribution\s+rights)''', re.IGNORECASE | re.VERBOSE)

# re.match: move author from license to copyright
re_license_copyright = re.compile(r'''(
                written\s+by\s                         # possible leader
                )''', re.IGNORECASE | re.VERBOSE)

# re.match: end of copyright/license
re_end = re.compile(r'''(
                .*\*+/|                                 # no */ in line
                .*[=?_]|                                # no = ? _ in line
                """|\'\'\'|                             # python block comment
                ---|\+\+\+|@@|                          # diff block
                [{}]|                                   # perl/shell block
                \.SH|                                   # no .SH for manpage
                EOT$|EOF$|EOL$|END$|                    # shell <<EOF like lines
                TODO:|
                usage:|
                msgid\s|
                msgstr\s
                )''', re.IGNORECASE | re.VERBOSE)

###################################################################
# re.sub: drop "All Rights Reserved"
re_allrightreserved = re.compile(r'''(
                All\s+Rights\s+Reserved[.,]?                 # possible leader
                )''', re.IGNORECASE | re.VERBOSE)

# re.sub: \co -> ©
re_co = re.compile(r'\\\(co')

# re.sub: .bp -> ''
re_bp = re.compile(r'\.bp', re.IGNORECASE)

# re.sub: tailing and -> ,
re_and = re.compile(r',?\s+and$', re.IGNORECASE)

# re.sub: copyright
re_copyright = re.compile(r'''Copyright|\(C\)|©''', 
        re.IGNORECASE | re.VERBOSE)

re_year = re.compile(r'\d\d+')

re_year_section = re.compile(r'((\d\d+)[ ,-]*)')

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
# Check a line for copyright and license and
#  return (copyright_line, license_line, section, style, marker)
###################################################################
def check_line(line, section, style, marker):
    line = line.strip()
    lmarker = len(marker)
    copyright_line = ''
    license_line = ''
    debmake.debug.debug('D: {} {} {}'.format(sectionstr[section], stylestr[style], line), type='i')
    # drop useless line section       
    line = re_allrightreserved.sub('', line)

    if section == Section.outside: # if outside
       
        # if no copyright is found, skip
        if not re_copyright_mark.search(line):
            pass
       
        # if not really copyright line, skip
        elif re_fake_copyright_mark.search(line):
            pass

        else:
            section = Section.copyright
            r1 = re_copy_in_comment.match(line)
            r2 = re_copy_in_quote.match(line)
            r3 = re_copy_in_plaintext.match(line)
            if r1: # if comment
                marker = r1.group('marker')
                line = r1.group('copyright')
                style = Style.comment
            elif r2: # if quote
                line = r2.group('copyright')
                style = Style.quote
            elif r3: # if plain
                line = r3.group('copyright')
                line = re_co.sub('©', line)
                style = Style.plain
            else: # if irregular
                style = Style.irregular
           
            # normalize style (tailing "and" to ",")
            line = re_and.sub(',', line)
           
            copyright_line = line
       
    elif section == Section.copyright:
        if style == Style.comment:
            if len(line) == 0:
                pass
            elif marker[-1:] == '*' and len(line) > 1 and line[:2] == '*/':
                style = Style.unknown
                section = Section.outside
            elif len(line) >= lmarker and line[:lmarker] == marker:
                line =  line[lmarker:].strip()  # un-boxed
            elif marker == '/*' and line[0] == '*':
                line = line[1:].strip()
            else:
                style = Style.unknown
                section = Section.outside
        elif style == Style.quote:
            rx2 = re_copy_in_quote_continue.match(line)
            if rx2:
                line = rx2.group('copyright')
            else:
                style = Style.unknown
                section = Section.outside
        elif style == Style.plain:
            line = re_co.sub('©', line)
            re_bp.sub('', line)
        elif style == Style.irregular:
            line = re_co.sub('©', line)
            line = re_bp.sub('', line)
        else: # Style.unknown should not be here
            print('E: Style.unknown should not come to Section.copyright', file=sys.stderr)
            exit(1)
        #
        if section != Section.outside:
            if re_end.match(line):
                style = Style.unknown
                section = Section.outside
            elif line =='' or re_license.match(line):
                section = Section.license
                license_line = line
            else:
                copyright_line = line
       
    elif section == Section.license:
        if style == Style.comment:
            if len(line) == 0:
                pass
            elif marker[-1:] == '*' and len(line) > 1 and line[:2] == '*/':
                style = Style.unknown
                section = Section.outside
            elif len(line) >= lmarker and line[:lmarker] == marker:
                line =  line[lmarker:].lstrip()  # un-boxed
            elif marker == '/*' and line[0] == '*':
                line = line[1:].strip()
            else:
                style = Style.unknown
                section = Section.outside

        elif style == Style.quote:
            rx2 = re_copy_in_quote_continue.match(line)
            if rx2:
                line = rx2.group('copyright')
            else:
                style = Style.unknown
                section = Section.outside
        elif style == Style.plain:
            line = re_bp.sub('', line)
        elif style == Style.irregular:
            line = re_bp.sub('', line)
        else: # Style.unknown should not be here
            print('E: Style.unknown should not come to  Section.license', file=sys.stderr)
            exit(1)
        #
        if section != Section.outside:
            if re_end.match(line):
                style = Style.unknown
                section = Section.outside
            elif re_license_copyright.match(line):
                section = Section.copyright
                copyright_line = line
            else:
                license_line = line
       
    else:
        print('E: Section should be valid {}'.format(sectionstr[section]), file=sys.stderr)
        exit(1)

    if section == Section.outside:
        debmake.debug.debug('D: {} {} {}'.format(sectionstr[section], stylestr[style], line), type='o')
    elif section == Section.copyright:
        debmake.debug.debug('D: {} {} {}'.format(sectionstr[section], stylestr[style], line), type='c')
    elif section == Section.license:
        debmake.debug.debug('D: {} {} {}'.format(sectionstr[section], stylestr[style], line), type='l')
    else:
        print('E: Section invalid.', file=sys.stderr)
        exit(1)

    return (copyright_line, license_line, section, style, marker)

###################################################################
# Check license of a text file
###################################################################
def check_license(file, encoding='utf-8'):
# Return list of tuple: [(copyright_lines, license_lines, style, line_count), ...]

    ###################################################################
    # Start analyzing file (default encoding)
    ###################################################################
    try:
        with open(file, 'r', encoding=encoding) as fd:
   
            parts = []
            copyright_lines = []
            license_lines =   []
            section = Section.outside
            style = Style.unknown
            marker = ''
       
            ###################################################################
            # Loop over lines with (style, section) as state variables
            ###################################################################
            copyright_lines = []
            license_lines =   []
            line_count = 0
            for line in fd.readlines():
                line = line.strip()
                old_section = section
                old_style = style
                (copyright_line, license_line, section, style, marker) = \
                            check_line(line, section, style, marker)

                if copyright_line != '':
                    copyright_lines.append(copyright_line)
                if (license_lines != [] and license_lines[-1] != '' ) or license_line != '':
                    license_lines.append(license_line)
                if old_section != Section.outside and section == Section.outside:
                    if copyright_lines != [] or license_lines != []:
                        parts.append((copyright_lines, license_lines, old_style, line_count))
                        copyright_lines = []
                        license_lines =   []
                line_count += 1

    ###################################################################
    # Fall back for analyzing file (latin-1 encoding)
    ###################################################################
    except UnicodeDecodeError as e:
        print('W: Non-UTF-8 char found, using latin-1: {}'.format(file), file=sys.stderr)
        fd.close()
        with open(file, 'r', encoding='latin-1') as fd:

            parts = []
            copyright_lines = []
            license_lines =   []
            section = Section.outside
            style = Style.unknown
            marker = ''
       
            ###################################################################
            # Loop over lines with (style, section) as state variables
            ###################################################################
            copyright_lines = []
            license_lines =   []
            line_count = 0
            for line in fd.readlines():
                line = line.strip()
                old_section = section
                old_style = style
                (copyright_line, license_line, section, style, marker) = \
                            check_line(line, section, style, marker)

                if copyright_line != '':
                    copyright_lines.append(copyright_line)
                if (license_lines != [] and license_lines[-1] != '' ) or license_line != '':
                    license_lines.append(license_line)
                if old_section != Section.outside and section == Section.outside:
                    if copyright_lines != [] or license_lines != []:
                        parts.append((copyright_lines, license_lines, old_style, line_count))
                        copyright_lines = []
                        license_lines =   []
                line_count += 1

    ###################################################################
    # add the last ones if they exist and clean-up tail
    ###################################################################
    if copyright_lines != [] or license_lines != []:
        parts.append((copyright_lines, license_lines, old_style, line_count))
    parts_tailcleaned = []
    for part in parts:
        (copyright_lines, license_lines, style, line_count) = part
        if len(license_lines) > 0 and license_lines[-1] == '':
            del license_lines[-1]
        parts_tailcleaned.append((copyright_lines, license_lines, style, line_count))
    ###################################################################
    # Return parts as results
    ###################################################################
    return parts_tailcleaned

###################################################################
# Analyze license
###################################################################
def merge_year_span(year0_min, year0_max, year1_min, year1_max):
    if year0_min > year1_min:
        year0_min = year1_min
    if year0_max < year1_max:
        year0_max = year1_max
    return (year0_min, year0_max)

def analyze_license(copyright_lines, license_lines):
    # normalize copyright
    lines = []
    line = ''
    for line_new in copyright_lines:
        line_new = line_new.strip()
        if re_copyright.match(line_new):
            if line != '':
                lines.append(line)
            line = re_copyright.sub('', line_new).strip()
        else:
            line = ' '.join([line, line_new])
    if line != '':
            lines.append(line)
    copyright_lines = lines
    copyright_data = {}
    for line in copyright_lines:
        year_min = 9999
        year_max = 0
        for year_string in re_year.findall(line):
            year = int(year_string)
            if year < year_min:
                year_min = year
            if year > year_max:
                year_max = year
        name = re_year_section.sub('', line).strip()
        if name in copyright_data.keys():
            (year0_min, year0_max) = copyright_data[name]
            copyright_data[name] = merge_year_span(year0_min, year0_max, year_min, year_max)
        else:
            copyright_data[name] = (year_min, year_max)

    # normalize license
    license_data = []
    line = ''
    for line_new in license_lines:
        line_new = line_new.strip()
        license_data.extend(line_new.split())
    license_data.insert(0, len(license_data))
    return (copyright_data, license_data)

###################################################################
# Check all appearing copyright and license texts
###################################################################
# return data which is list of tuples
# data[*][0]: license data (normalized: list with length/ID and words)
# data[*][1]: file name
# data[*][2]: copyright holder info (data=dictionary)
# data[*][3]: license text (original: list of lines)
# data[*][4]: extra copyright holder info with file and line number
###################################################################
def check_all_license(files, encoding='utf-8'):
    if len(files) == 0:
        print('E: check_all_license(files) should have files', file=sys.stderr)
        exit(1)
    data = []
    for file in files:
        debmake.debug.debug('D: section  ??     *** {} ***'.format(file), type='f')
        if os.path.isfile(file):
            parts = check_license(file, encoding=encoding)
            if len(parts) == 0:
                data.append(([-1], file, {'NO_COPYRIGHT_INFO_FOUND':(0, 0)}, [], ''))
            else:
                (copyright_lines, license_lines, style, line_count) = parts[0]
                # lazy only first one
                (copyright_data,license_data) = \
                        analyze_license(copyright_lines, license_lines)
                if len(parts) == 1:
                    data.append((license_data, file, copyright_data, license_lines, ''))
                else:
                    extra_lines = ''
                    for part in parts[1:]:
                        (xcopyright_lines, xlicense_lines, xstyle, xline_count) = part
                        if len(xlicense_lines):
                            extra_lines += (
'# NO_LICENSE_TEXT_FOUND   {}: {}, \n#\t{}\n'.format(file, xline_count, ', '.join(xcopyright_lines)))
                        else:
                            extra_lines += (
'# !!! manual check needed {}: {}, \n#\t{}\n'.format(file, xline_count, ', '.join(xcopyright_lines)))
                    data.append((license_data, file, copyright_data, license_lines, extra_lines))
        else:
            print('E: check_all_license(files) should run on existing files', file=sys.stderr)
            exit(1)
    data = sorted(data, key=operator.itemgetter(0), reverse=True)
    return data

###################################################################
# Bunch licence
###################################################################
# return data which is list of tuples
# bdata[*][0]: license data (normalized: length and list of words)
#              [-1]: NO_COPYRIGHT_INFO_FOUND
#              [0] : NO LICENSE TEXT found
# bdata[*][1]: file name (bunched, list)
# bdata[*][2]: copyright holder info (data=dictionary)
# bdata[*][3]: license text (original: list of lines)
# bdata[*][4]: extra copyright holder info with file and line number (bunched)
def bunch_licence(data):
    if len(data) == 0:
        print('E: bunch_licence(data) should have data', file=sys.stderr)
        exit(1)
    d0 = data[0][0] # license data
    d1 = [ data[0][1] ] # a file name (list)
    d2 = data[0][2] # copyright holder info (dictionary)
    d3 = data[0][3] # license text (original: list of lines)
    d4 = data[0][4] # extra text (text line)
    bdata = []
    if len(data) > 1:
        for dx in data[1:]:
            if d0 ==dx[0]:
                d1.append(dx[1])
                for name in dx[2].keys():
                    (year0_min, year0_max) = dx[2][name]
                    if name in d2.keys():
                        (year1_min, year1_max) =d2[name]
                        d2[name] = merge_year_span(year0_min, year0_max, year1_min, year1_max)
                    else:
                        d2[name] = (year0_min, year0_max)
                d4 += dx[4]
            else:
                bdata.append((d0, d1, d2, d3, d4))
                d0 = dx[0] # license data
                d1 = [ dx[1] ] # a file name (list)
                d2 = dx[2] # copyright holder info (dictionary)
                d3 = dx[3] # license text (original: list of lines)
                d4 = dx[4] # extra text (text line)
    bdata.append((d0, d1, d2, d3, d4))
    return bdata

###################################################################
# Format licence
###################################################################
def format_license(lines):
    # RFC-822 compliant empty lines with "."
    xlines = []
    for line in lines:
        line = line.rstrip()
        if line == '':
            xlines.append(' .\n')
        else:
            xlines.append(' ' + line + '\n')
    return ''.join(xlines)

###################################################################
# Get all files to be analyzed under dir
###################################################################
def get_all_files(dir):
    nonlink_files = []
    binary_files = []
    huge_files = []
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
            elif os.path.getsize(filepath) > MAX_FILE_SIZE:
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
    return (nonlink_files, binary_files, huge_files)

#######################################################################
# complete scan_copyright_data
#######################################################################
def scan_copyright_data():
    (nonlink_files, binary_files, huge_files) = get_all_files('.')
    data = check_all_license(nonlink_files)
    bdata = bunch_licence(data)
    return (bdata, nonlink_files, binary_files, huge_files)

#######################################################################
# license text files (glob files specified by --license)
#######################################################################
def license_files(files): 
    f = set()
    for fx in files:
        f.update(set(glob.glob(fx)))
    return f

#######################################################################
# license text file conversion
#######################################################################
def license_text(file, encoding='utf-8'): 
    lines = []
    try:
        with open(file, 'r', encoding=encoding) as fd:
            for line in fd.readlines():
                lines.append(line.rstrip())
    except UnicodeDecodeError as e:
        print('W: Non-UTF-8 char found, using latin-1: {}'.format(file), file=sys.stderr)
        fd.close()
        lines = []
        with open(file, 'r', encoding='latin-1') as fd:
            for line in fd.readlines():
                lines.append(line.rstrip())
    return format_license(lines)

#######################################################################
# main program
#######################################################################
def copyright(package_name, license_file_masks):
    # get scan result of copyright
    (bdata, nonlink_files, binary_files, huge_files) = scan_copyright_data()
    # make text to print
    text = '''\
Format: http://www.debian.org/doc/packaging-manuals/copyright-format/1.0/
Upstream-Name: {}
Source: <url://example.com>

'''.format(package_name)
    for bd in bdata:
        text += '#----------------------------------------------------------------------------\n'
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
        # Files:
        text += 'Files: {}\n'.format('\n\t'.join(bd[1]))
        # licensecheck(1):
        command = 'licensecheck '+ bd[1][0]
        p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        for line in p.stdout.readlines():
            text += '# licensecheck(1): ' + line.decode('utf-8').strip() + '\n'
        if p.wait() != 0:
            print('E: "{}" returns "{}"'.format(command, retval), file=sys.stderr)
            exit(1)
        # License:
        if bd[3] == []:
            text += 'License: NO_LICENSE_TEXT_FOUND\n\n'
        else:
            text += 'License:\n {}\n'.format(format_license(bd[3]))
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
# Generate typical license templates with the "debmake -c" to STDOUT
# and merge them into here as needed.  See "man 8 debmake" for more.
#
# licensecheck(1) from the devscripts package is used here to determin
# the name of the license that applies.
#
# Please avoid to pick license terms that are more restrictive than the
# packaged work, as it may make Debian's contributions unacceptable upstream.

'''
    for f in license_files(license_file_masks):
        text += '#----------------------------------------------------------------------------\n'
        text += '# License: {}\n'.format(f)
        text += license_text(f)
        text += '\n'

    return text

#######################################################################
# Test script
#######################################################################
if __name__ == '__main__':
    print(copyright('foo', {'LICENSE*', 'COPYRIGHT'}))
