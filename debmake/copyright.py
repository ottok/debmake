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
style = {
    'unknown' : '??',
    'comment' : '//',
    'quote' : '/*',
    'plain' : '__',
    'irregular' : 'XX'}

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
                copyright\slaw|
                \(c\)\sall\s
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

###################################################################
# re.match: start of license
re_license = re.compile(r'''(
                this\s.*is|
                this\s.*program|
                this\s.*software|
                this\s.*script|
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

###################################################################
# re.match: move author from license to copyright
re_license_copyright = re.compile(r'''(
                written\s+by\s                         # possible leader
                )''', re.IGNORECASE | re.VERBOSE)

###################################################################
# re.match: end of copyright/license
re_end = re.compile(r'''(
                .*\*+/|                                 # no */ in line
                .*[=?_]|                                # no = ? _ in line
                """|\'\'\'|                             # python block comment
                ---|\+\+\+|@@|                          # diff block
                [{}]|                                   # perl/shell block
                ^\.SH|                                   # no .SH for manpage
                ^EOT$|EOF$|EOL$|END$|                    # shell <<EOF like lines
                ^You\scan\sget\sthe\slatest\sversion|
                ^From\shttp|
                ^Please\ssend\spatches|
                ^The\snames\sof\sthe\stagged\sconfigurations|
                ^This\sfile\sis\smaintained\sin|
                ^force\sinclude|
                ^Basic\sInstallation|
                ^[#]\s-----------*\s[#]|
                ^serial|
                ^TODO:|
                ^usage:|
                ^msgid\s|
                ^msgstr\s
                )''', re.IGNORECASE | re.VERBOSE)

###################################################################
# re.sub: drop "All Rights Reserved" etc.
re_dropline = re.compile(r'''(
                ^timestamp=.*|                          # timestamp line
                ^scriptversion=.*|                      # version line
                All\s+Rights\s+Reserved.*|              # possible leader
                This\s+file\s+is\s+part\s+of\s+GNU.*
                )''', re.IGNORECASE | re.VERBOSE)

###################################################################
# manpage and text substitution
# re.sub: \co -> ©
re_co = re.compile(r'\\\(co')

# re.sub: .bp -> ''
re_bp = re.compile(r'\.bp', re.IGNORECASE)

# re.sub: tailing and -> ,
re_and = re.compile(r',?\s+and$', re.IGNORECASE)

# re.sub: copyright
re_copyright = re.compile(r'''Copyright|\(C\)|©''', 
        re.IGNORECASE | re.VERBOSE)

###################################################################
# copyright year
re_year = re.compile(r'\d\d+')

re_year_section = re.compile(r'((\d\d+)[ ,-]*)')

###################################################################
# Check a line for copyright and license and
#  return (copyright_line, license_line, section, style, marker)
###################################################################
def check_line(line, section, style, marker):
    line = line.strip()
    lmarker = len(marker)
    copyright_line = ''
    license_line = ''
    debmake.debug.debug('D: {} {} {}'.format(section, style, line), type='i')
    # drop useless line section       
    line = re_dropline.sub('', line).strip()

    if section == 'outside': # if outside
       
        # if no copyright is found, skip
        if not re_copyright_mark.search(line):
            pass
       
        # if not really copyright line, skip
        elif re_fake_copyright_mark.search(line):
            pass

        else:
            section = 'copyright'
            r1 = re_copy_in_comment.match(line)
            r2 = re_copy_in_quote.match(line)
            r3 = re_copy_in_plaintext.match(line)
            if r1: # if comment
                marker = r1.group('marker')
                line = r1.group('copyright')
                style = 'comment'
            elif r2: # if quote
                line = r2.group('copyright')
                style = 'quote'
            elif r3: # if plain
                line = r3.group('copyright')
                line = re_co.sub('©', line)
                style = 'plain'
            else: # if irregular
                style = 'irregular'
           
            # normalize style (tailing "and" to ",")
            line = re_and.sub(',', line)
           
            copyright_line = line.strip()
       
    elif section == 'copyright':
        if style == 'comment':
            if len(line) == 0:
                pass
            elif marker[-1:] == '*' and len(line) > 1 and line[:2] == '*/':
                style = 'unknown'
                section = 'outside'
            elif len(line) >= lmarker and line[:lmarker] == marker:
                line =  line[lmarker:].strip()  # un-boxed
            elif marker == '/*' and line[0] == '*':
                line = line[1:].strip()
            else:
                style = 'unknown'
                section = 'outside'
        elif style == 'quote':
            rx2 = re_copy_in_quote_continue.match(line)
            if rx2:
                line = rx2.group('copyright')
            else:
                style = 'unknown'
                section = 'outside'
        elif style == 'plain':
            line = re_co.sub('©', line)
            re_bp.sub('', line)
        elif style == 'irregular':
            line = re_co.sub('©', line)
            line = re_bp.sub('', line)
        else: # 'unknown' should not be here
            print("E: 'unknown' should not come to 'copyright'", file=sys.stderr)
            exit(1)
        #
        if section != 'outside':
            if re_end.match(line):
                style = 'unknown'
                section = 'outside'
            elif line =='' or re_license.match(line):
                section = 'license'
                license_line = line.strip()
            else:
                copyright_line = line.strip()
       
    elif section == 'license':
        if style == 'comment':
            if len(line) == 0:
                pass
            elif marker[-1:] == '*' and len(line) > 1 and line[:2] == '*/':
                style = 'unknown'
                section = 'outside'
            elif len(line) >= lmarker and line[:lmarker] == marker:
                line =  line[lmarker:].lstrip()  # un-boxed
            elif marker == '/*' and line[0] == '*':
                line = line[1:].strip()
            else:
                style = 'unknown'
                section = 'outside'

        elif style == 'quote':
            rx2 = re_copy_in_quote_continue.match(line)
            if rx2:
                line = rx2.group('copyright')
            else:
                style = 'unknown'
                section = 'outside'
        elif style == 'plain':
            line = re_bp.sub('', line)
        elif style == 'irregular':
            line = re_bp.sub('', line)
        else: # 'unknown' should not be here
            print("E: 'unknown' should not come to  'license'", file=sys.stderr)
            exit(1)
        #
        if section != 'outside':
            if re_end.match(line):
                style = 'unknown'
                section = 'outside'
            elif re_license_copyright.match(line):
                section = 'copyright'
                copyright_line = line.strip()
            else:
                license_line = line.strip()
       
    else:
        print('E: Section should be valid {}'.format(section), file=sys.stderr)
        exit(1)

    if section == 'outside':
        debmake.debug.debug('D: {} {} {}'.format(section, style, line), type='o')
    elif section == 'copyright':
        debmake.debug.debug('D: {} {} {}'.format(section, style, line), type='c')
    elif section == 'license':
        debmake.debug.debug('D: {} {} {}'.format(section, style, line), type='l')
    else:
        print('E: Section invalid.', file=sys.stderr)
        exit(1)

    return (copyright_line, license_line, section, style, marker)

###################################################################
# Check license of a text file (internal, no encoding error)
###################################################################
def check_license_fd(fd):
# Return list of tuple: [(copyright_lines, license_lines, style, line_count), ...]
    parts = []
    copyright_lines = []
    license_lines =   []
    section = 'outside'
    style = 'unknown'
    marker = ''
    ###################################################################
    # Loop over lines with (style, section) as state variables
    ###################################################################
    copyright_lines = []
    license_lines =   []
    line_count = 0
    for line in fd.readlines():
        if line[:1] == '+': # drop patch (1 level)
            line = line[1:]
        line = line.strip()
        old_section = section
        old_style = style
        (copyright_line, license_line, section, style, marker) = \
                    check_line(line, section, style, marker)

        if copyright_line != '':
            copyright_lines.append(copyright_line)
        if (license_lines != [] and license_lines[-1] != '' ) or license_line != '':
            license_lines.append(license_line)
        if old_section != 'outside' and section == 'outside':
            if copyright_lines != [] or license_lines != []:
                parts.append((copyright_lines, license_lines, old_style, line_count))
                copyright_lines = []
                license_lines =   []
        line_count += 1
    ###################################################################
    # add the last ones if they exist
    ###################################################################
    if copyright_lines != [] or license_lines != []:
        parts.append((copyright_lines, license_lines, old_style, line_count))
    ###################################################################
    # clean-up empty line tails of license text for each part
    ###################################################################
    parts_tailcleaned = []
    for copyright_lines, license_lines, style, line_count in parts:
        while len(license_lines) > 0 and license_lines[-1] == '':
            del license_lines[-1]
        parts_tailcleaned.append((copyright_lines, license_lines, style, line_count))
    ###################################################################
    # Return parts as results
    ###################################################################
    return parts_tailcleaned

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
            parts = check_license_fd(fd)
    ###################################################################
    # Fall back for analyzing file (latin-1 encoding)
    ###################################################################
    except UnicodeDecodeError as e:
        print('W: Non-UTF-8 char found, using latin-1: {}'.format(file), file=sys.stderr)
        fd.close()
        with open(file, 'r', encoding='latin-1') as fd:
            parts = check_license_fd(fd)

    ###################################################################
    # Return parts as results
    ###################################################################
    return parts

###################################################################
# Analyze copyright
###################################################################
def merge_year_span(year0_min, year0_max, year1_min, year1_max):
    if year0_min > year1_min:
        year0_min = year1_min
    if year0_max < year1_max:
        year0_max = year1_max
    return (year0_min, year0_max)

def analyze_copyright(copyright_lines):
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
    return copyright_data

###################################################################
# Analyze license
###################################################################
def analyze_license(license_lines):
    # normalize license
    license_data = []
    for line in license_lines:
        line = line.strip()
        license_data.extend(line.split())
    try:
        license_data.remove('') # remove empty words
    except ValueError:
        pass
    license = ' '.join(license_data)
    return license

###################################################################
# Check all appearing copyright and license texts
###################################################################
# return data which is list of tuples
# data[*][0]: license data (normalized)
# data[*][1]: file name
# data[*][2]: copyright holder info (data=dictionary)
# data[*][3]: license text (original: list of lines)
# data[*][4]: extra copyright holder info with file and line number
###################################################################
def check_all_license(files, encoding='utf-8'):
    data = []
    if len(files) == 0:
        print('W: check_all_license(files) should have files', file=sys.stderr)
    for file in files:
        debmake.debug.debug('D: section  ??     *** {} ***'.format(file), type='f')
        if os.path.isfile(file):
            parts = check_license(file, encoding=encoding)
            license = ''
            copyright_data = {}
            license_lines_rep = []
            extra_lines = ''
            for i, (copyright_lines, license_lines, style, line_count) in enumerate(parts):
                if i == 0:
                    copyright_data = analyze_copyright(copyright_lines)
                    license = analyze_license(license_lines)
                    license_lines_rep = license_lines
                else:
                    extra_lines += '### !!! F: file = {} @ {} ==========\n'.format(file, line_count)
                    for line in copyright_lines:
                        extra_lines += '### !!! C: {}\n'.format(line)
                    for line in license_lines:
                        extra_lines += '### !!! L: {}\n'.format(line)
                    extra_lines += '### !!!\n'
            if copyright_data == {}:
                copyright_data = {'NO_COPYRIGHT_INFO_FOUND':(0, 0)}
        else:
            print('W: check_all_license on non-existing file: {}'.format(file), file=sys.stderr)
        data.append((license, file, copyright_data, license_lines_rep, extra_lines))
    data = sorted(data, key=operator.itemgetter(0), reverse=True) # sort by license
    return data

###################################################################
# Bunch licence
###################################################################
# return data which is list of tuples
# No. of files
# bdata[*][0]: license data (normalized)
# bdata[*][1]: file name (bunched, list)
# bdata[*][2]: copyright holder info (data=dictionary)
# bdata[*][3]: license text (original: list of lines)
# bdata[*][4]: extra copyright holder lines with file and line number (bunched)
def bunch_licence(data):
    bdata = []
    if len(data) == 0:
        print('W: bunch_licence(data) should have data', file=sys.stderr)
    xlicense = ''
    xfile = []
    xcopyright_data = {}
    xlicense_lines_rep = []
    xextra_lines = ''
    for i, (license, file, copyright_data, license_lines_rep, extra_lines) in enumerate(data):
        if i == 0:
            xlicense = license
            xfile = [file]
            xcopyright_data = copyright_data
            xlicense_lines_rep = license_lines_rep
            xextra_lines += extra_lines
        else:
            if xlicense == license:
                xfile += [file]
                for name, (year_min, year_max) in copyright_data.items():
                    if name in xcopyright_data.keys():
                        (xyear_min, xyear_max) = xcopyright_data[name]
                        xcopyright_data[name] = merge_year_span(xyear_min, xyear_max, year_min, year_max)
                    else:
                        xcopyright_data[name] = (year_min, year_max)
                xextra_lines += extra_lines
            else:
                bdata.append((len(xfile) + min(0.999,len(xlicense)/1000000), xlicense, xfile, xcopyright_data, xlicense_lines_rep, xextra_lines))
                xlicense = license
                xfile = [file]
                xcopyright_data = copyright_data
                xlicense_lines_rep = license_lines_rep
                xextra_lines += extra_lines
    bdata.append((len(xfile) + min(0.999,len(xlicense)/1000000), xlicense, xfile, xcopyright_data, xlicense_lines_rep, xextra_lines))
    bdata = sorted(bdata, key=operator.itemgetter(0), reverse=True) # sort by No. of files
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
def copyright(package_name, license_file_masks, bdata, binary_files, huge_files):
    # make text to print
    text = '''\
Format: http://www.debian.org/doc/packaging-manuals/copyright-format/1.0/
Upstream-Name: {}
Source: <url://example.com>
# This is a autogenerated template for debian/copyright.
#
# Edit this accordinng to the "Machine-readable debian/copyright file" as
# http://www.debian.org/doc/packaging-manuals/copyright-format/1.0/ .
#
# Generate updated license templates with the "debmake -c" to STDOUT
# and merge them into debian/copyright as needed.
#
# licensecheck(1) from the devscripts package is used here to determin
# the name of the license that applies.
#
# Please avoid to pick license terms that are more restrictive than the
# packaged work, as it may make Debian's contributions unacceptable upstream.

'''.format(package_name)
    for (index, license, file, copyright_data, license_lines_rep, extra_lines) in bdata:
        # Files:
        text += 'Files: {}\n'.format('\n       '.join(file))
        # Copyright:
        copy = ''
        for name in copyright_data.keys():
            # name found
            if copyright_data[name][0] == copyright_data[name][1]:
                if copyright_data[name][1] == 0: # max == 0 for binary etc.
                    copy += '           {}\n'.format(name)
                else:
                    copy += '           {} {}\n'.format(copyright_data[name][0], name)
            else:
                if copyright_data[name][1] == 0: # max == 0 means not found
                    copy += '           {}\n'.format(name)
                else:
                    copy += '           {}-{} {}\n'.format(copyright_data[name][0], copyright_data[name][1], name)
        text += 'Copyright:' + copy[10:]
        # licensecheck(1):
        command = 'licensecheck '+ file[0] + ' | sed -e "s/^[^:]*://"'
        p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        licensecheck = p.stdout.read().decode('utf-8').strip()
        if p.wait() != 0:
            print('E: "{}" returns "{}"'.format(command, p.returncode), file=sys.stderr)
            exit(1)
        # License:
        if license_lines_rep == []:
            text += 'License: {} NO_LICENSE_TEXT_FOUND\n\n'.format(licensecheck)
        else:
            text += 'License: {}\n'.format(licensecheck)
            text += '{}\n'.format(format_license(license_lines_rep))
        try:
            DEBUG = os.environ["DEBUG"]
        except KeyError:
            pass
        else:
            if 'g' in DEBUG:
                # add comments
                if extra_lines != '':
                    text += '### !!! ......................................................................\n'
                    text += '### !!! gray hits with matching text of "copyright":\n'
                    text += extra_lines.rstrip() + '\n'
    if binary_files != []:
        text += '#----------------------------------------------------------------------------\n'
        text += '# binary files (skipped):\n#       {}\n\n'.format('\n#       '.join(binary_files))
    if huge_files != []:
        text += '#----------------------------------------------------------------------------\n'
        text += '# huge files   (skipped):\n#       {}\n\n'.format('\n#       '.join(huge_files))
    text += '''\
#----------------------------------------------------------------------------
# Files marked as NO_LICENSE_TEXT_FOUND may be covered by the following 
# license/copyright files.

'''
    for f in license_files(license_file_masks):
        text += '#----------------------------------------------------------------------------\n'
        text += '# License file: {}\n'.format(f)
        text += license_text(f)
        text += '\n'

    return text

#######################################################################
# Test script
#######################################################################
if __name__ == '__main__':
    print(copyright('foo', {'LICENSE*', 'COPYRIGHT'}, [], ['binary1.file', 'binary2.file'], ['huge.file1', 'huge.file2']))
