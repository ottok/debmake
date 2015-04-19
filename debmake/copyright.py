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
import hashlib
import itertools
import operator
import os
import re
import subprocess
import sys
import debmake.debug
import debmake.lc
###################################################################
# Constants for sanity
###################################################################
MAX_COPYRIGHT_LINES = 256
MAX_COPYRIGHT_LENGTH = 2048
###################################################################
# Parse year within a copyright line
###################################################################
re_year_1900 = re.compile(r'''
        (?P<pre>.*?)
        (?P<n1>19\d\d)\s*[-,]\s*
        (?P<n2>\d\d)
        (?P<post>\D.*|$)''', re.IGNORECASE | re.VERBOSE)

re_year_2000 = re.compile(r'''
        (?P<pre>.*?)
        (?P<n1>20\d\d)\s*[-,]\s*
        (?P<n2>\d\d)
        (?P<post>\D.*|$)''', re.IGNORECASE | re.VERBOSE)

def normalize_year_span(line):
    # 1990-91 -> 1990-1991 etc.
    while True:
        m = re_year_1900.search(line)
        if m:
            line = m.group('pre') + m.group('n1') + '-19' + \
                    m.group('n2') + m.group('post')
        else:
            break
    # 2010-11 -> 2010-2011 etc.
    while True:
        m = re_year_2000.search(line)
        if m:
            line = m.group('pre') + m.group('n1') + '-20' + \
                    m.group('n2') + m.group('post')
        else:
            break
    return line

re_year_yn = re.compile(r'''^\s*
        (?P<year>(?:\d\d+[-,.;\s]*)+)[.,;:]?\s*
        (?P<name>\D.*\D)\s*\.?$''', re.IGNORECASE | re.VERBOSE)

re_year_ny = re.compile(r'''^\s*
        (?P<name>.*?\D)\s*
        (?P<year>(?:\d\d+[-.,;\s]*)+)[.,;:]?\s*$''', re.IGNORECASE | re.VERBOSE)

def split_year_span(line):
    # split line into years and name
    m1 = re_year_yn.search(line)
    m2 = re_year_ny.search(line)
    if m1:
        years = m1.group('year').strip()
        name = m1.group('name').strip()
    elif m2:
        years = m2.group('year').strip()
        name = m2.group('name').strip()
    elif line:
        years = 'NO_MATCH' # sign for funkey line
        name = line.strip()
    else:
        years = ''
        name = ''
    if name[:2].lower() == 'by':
        name = name[2:].strip()
    debmake.debug.debug('Dy: years="{}", name="{}" <- "{}"'.format(years, name, line), type='y')
    return (years, name)

re_year = re.compile(r'\d\d+')

def get_year_range(years):
    # year range
    year_min = 9999
    year_max = 0
    for year_string in re_year.findall(years):
        year = int(year_string)
        year_min =  min(year_min, year)
        year_max =  max(year_max, year)
    return (year_min, year_max)

###################################################################
# Parse name within a copyright line
###################################################################
re_name_drop = re.compile(r'''(?:
        All\s+Rights\s+Reserved\.?|
        originally\s+by.*$|
        (?:originally\s+)?written\s+by.*$)
        ''', re.IGNORECASE | re.VERBOSE)

re_fsf_addr = re.compile(r'^Free\s+Software\s+Foundation,\s+Inc\.',
        re.IGNORECASE)

def cleanup_name(name):
    if re_fsf_addr.search(name): # FSF without address etc.
        name = 'Free Software Foundation, Inc.'
    return name

###################################################################
# Parse (year, name) within all copyright lines
###################################################################
def analyze_copyright(copyright_lines):
    copyright_data = {}
    for line in copyright_lines:
        line = line.strip()
        line = normalize_year_span(line).strip()
        line = re_name_drop.sub('', line).strip()
        (years, name) = split_year_span(line)
        name = cleanup_name(name).strip()
        (year_min, year_max) = get_year_range(years)
        if name in copyright_data.keys():
            (year0_min, year0_max) = copyright_data[name]
            year_min =  min(year_min, year0_min)
            year_max =  max(year_max, year0_max)
        if name:
            copyright_data[name] = (year_min, year_max)
        else:
            print('W: analyze_copyright: skip name="", years="{}" <- line"{}"'.format(years, line), file=sys.stderr)
    return copyright_data

###################################################################
# A format state machine parser to extract copyright+license by format
###################################################################
fs = [
'F_BLNK  ', # blank line
'F_QUOTE ',
'F_BLKP  ',
'F_BLKPE ',
'F_BLKP0 ',
'F_BLKQ  ',
'F_BLKQE ',
'F_BLKQ0 ',
'F_BLKC  ',
'F_BLKCE ',
'F_BLKC2 ',
'F_BLKC1 ',
'F_BLKC0 ',
'F_PLAIN1',
'F_PLAIN2',
'F_PLAIN3',
'F_PLAIN4',
'F_PLAIN5',
'F_PLAIN6',
'F_PLAIN7',
'F_PLAIN8',
'F_PLAIN9',
'F_PLAIN10',
'F_PLAIN0', # always match
'F_EOF   ', # force EOF before processing the next line
]
# enum(fs)
for i, name in enumerate(fs):
    exec('{} = {}'.format(name.strip(), i))
F_EOF = -1 # override

# entry format style id list
all_non_entry_formats = {
F_BLKPE, F_BLKP0,
F_BLKQE, F_BLKQ0,
F_BLKCE, F_BLKC2, F_BLKC1, F_BLKC0,
F_EOF}

all_entry_formats = set()
for name in fs:
    id = eval(name.strip())
    if id not in all_non_entry_formats:
        all_entry_formats.add(id)

formats = {} # dictionary
# define next format state
# formats[*][0]: regex to match
# formats[*][1]: next format state allowed
# formats[*][2]: format state allowed (persistent)

formats[F_BLNK] = (
        re.compile(r'^(?P<prefix>)(?P<text>)(?P<postfix>)$'),
        all_entry_formats,
        {F_BLNK}
        )

formats[F_QUOTE] = (
        re.compile(r'^(?P<prefix>/\*)\**(?P<text>.*?)\**(?P<postfix>\*/)$'),  # C /*...*/
        all_entry_formats,
        {F_QUOTE, F_BLKC, F_BLKCE, F_BLKC2, F_BLKC1, F_BLKC0, F_BLNK}
        )

# python block mode start with '''
formats[F_BLKP] = (
        re.compile(r'^.*?(?P<prefix>\'\'\')(?P<text>.*)(?P<postfix>)$'),  # Python
        [F_BLKPE, F_BLKP0],
        {F_BLKP, F_BLKPE, F_BLKP0, F_BLNK}
        )
formats[F_BLKPE] = (
        re.compile(r'^(?P<prefix>)(?P<text>.*?)(?P<postfix>\'\'\').*$'),  # Python
        all_entry_formats,
        {F_BLKP, F_BLKPE, F_BLKP0, F_BLNK}
        )
formats[F_BLKP0] = (
        re.compile(r'^(?P<prefix>)\s*(?P<text>.*)\s*(?P<postfix>)$'),
        [F_BLKPE, F_BLKP0],
        {F_BLKP, F_BLKPE, F_BLKP0, F_BLNK}
        )

# python block mode start with """
formats[F_BLKQ] = (
        re.compile(r'^.*?(?P<prefix>""")(?P<text>.*)(?P<postfix>)$'),  # Python
        [F_BLKQE, F_BLKQ0],
        {F_BLKQ, F_BLKQE, F_BLKQ0, F_BLNK}
        )
formats[F_BLKQE] = (
        re.compile(r'^(?P<prefix>)(?P<text>.*?)(?P<postfix>""").*$'),  # Python
        all_entry_formats,
        {F_BLKQ, F_BLKQE, F_BLKQ0, F_BLNK}
        )
formats[F_BLKQ0] = (
        re.compile(r'^(?P<prefix>)\s*(?P<text>.*)\s*(?P<postfix>)$'),
        [F_BLKQE, F_BLKQ0],
        {F_BLKQ, F_BLKQE, F_BLKQ0, F_BLNK}
        )

# C block mode start with """
formats[F_BLKC] = (
        re.compile(r'^(?P<prefix>/\*)\s*\**(?P<text>.*)(?P<postfix>)$'),  # C /*...
        [F_BLKCE, F_BLKC2, F_BLKC1, F_BLKC0],
        {F_QUOTE, F_BLKC, F_BLKCE, F_BLKC2, F_BLKC1, F_BLKC0, F_BLNK}
        )
formats[F_BLKCE] = (
        re.compile(r'^(?P<prefix>\*\s|)(?P<text>.*?)\s*\**?(?P<postfix>\*/).*$'),  # C ...*/
        all_entry_formats,
        {F_QUOTE, F_BLKC, F_BLKCE, F_BLKC2, F_BLKC1, F_BLKC0, F_BLNK}
        )
formats[F_BLKC2] = (
        re.compile(r'^(?P<prefix>\*)\**?(?P<text>.*?)\**?(?P<postfix>\*)$'),  # C *...*
        [F_BLKCE, F_BLKC2],
        {F_QUOTE, F_BLKC, F_BLKCE, F_BLKC2, F_BLKC1, F_BLKC0, F_BLNK}
        )
formats[F_BLKC1] = (
        re.compile(r'^(?P<prefix>\*)\**?(?P<text>.*)(?P<postfix>)$'),  # C *...
        [F_BLKCE, F_BLKC1],
        {F_QUOTE, F_BLKC, F_BLKCE, F_BLKC2, F_BLKC1, F_BLKC0, F_BLNK}
        )
formats[F_BLKC0] = (
        re.compile(r'^(?P<prefix>)(?P<text>.*?)(?P<postfix>)$'),
        [F_BLKCE, F_BLKC0],
        {F_QUOTE, F_BLKC, F_BLKCE, F_BLKC2, F_BLKC1, F_BLKC0, F_BLNK}
        )

# comment start with something
formats[F_PLAIN1] = (
        re.compile(r'^(?P<prefix>#)#*(?P<text>.*)(?P<postfix>)$'),   # Shell/Perl/Python
        all_entry_formats,
        {F_PLAIN1, F_BLNK}
        )

formats[F_PLAIN2] = (
        re.compile(r'^(?P<prefix>//)/*(?P<text>.*)(?P<postfix>)$'),  # C++ //
        all_entry_formats,
        {F_PLAIN2, F_BLNK}
        )

formats[F_PLAIN3] = (
        re.compile(r'^(?P<prefix>--)-*(?P<text>.*)(?P<postfix>)$'),  # Lua --
        all_entry_formats,
        {F_PLAIN3, F_BLNK}
        )

formats[F_PLAIN4] = (
        re.compile(r'^(?P<prefix>\.\\")(?P<text>.*)(?P<postfix>)$'), # manpage
        all_entry_formats,
        {F_PLAIN4, F_BLNK}
        )

formats[F_PLAIN5] = (
        re.compile(r'^(?P<prefix>@%:@)(?P<text>.*)(?P<postfix>)$'),  # autom4te.cache
        all_entry_formats,
        {F_PLAIN5, F_BLNK}
        )

formats[F_PLAIN6] = (
        re.compile(r'^(?P<prefix>@c)\s+(?P<text>.*)(?P<postfix>)$'), # Texinfo @c
        all_entry_formats,
        {F_PLAIN6, F_BLNK}
        )

formats[F_PLAIN7] = (
        re.compile(r"^(?P<prefix>')(?P<text>.*)(?P<postfix>)$"),# Basic
        all_entry_formats,
        {F_PLAIN7, F_BLNK}
        )

formats[F_PLAIN8] = (
        re.compile(r'^(?P<prefix>;);*(?P<text>.*)(?P<postfix>)$'),# vim
        all_entry_formats,
        {F_PLAIN8, F_BLNK}
        )

formats[F_PLAIN9] = (
        re.compile(r'^(?P<prefix>dnl)\s+(?P<text>.*)(?P<postfix>)$'),# m4 dnl
        all_entry_formats,
        {F_PLAIN9, F_BLNK}
        )

formats[F_PLAIN10] = (
        re.compile(r'^(?P<prefix>%)\s+(?P<text>.*)(?P<postfix>)$'),# texinfo.tex
        all_entry_formats,
        {F_PLAIN10, F_BLNK}
        )

# This is the last rule (always match, no blank line comes here)
formats[F_PLAIN0] = (
        re.compile(r'^(?P<prefix>)(?P<text>.+)(?P<postfix>)$'),     # Text
        all_entry_formats,
        {F_PLAIN0, F_BLNK}
        )

# drop lines such as "All Rights Reserved" and treat them blank
re_dropline = re.compile(r'''(?:
        ^timestamp=|                        # timestamp line
        ^scriptversion=|                    # version line
        ^All\s+Rights\s+Reserved|           # possible leader
        ^LICENSE:|                          # 
        ^written\s+by|
        ^This\s+file\s+is\s+part\s+of\s+GNU|
        ^Last\s+update:\s|
        ^\.bp\s                             # manpage
        )''', re.IGNORECASE | re.VERBOSE)

def check_format_style(line, xformat_state):
    line = line.strip()
    if line[:1] == '+': # hack to drop patch (1 level)
        line = line[1:].strip()
    prefix = ''
    postfix = ''
    format_state = F_EOF
    formats_allowed = formats[xformat_state][1]
    for f in formats_allowed:
        regex = formats[f][0]
        m = regex.search(line)
        if m:
            line = m.group('text').strip()
            prefix = m.group('prefix') # for debug output
            postfix = m.group('postfix') # for debug output
            format_state = f
            break
    if re_dropline.match(line): # hack to drop line
        line = ''
        if format_state != F_EOF:
            format_state = F_BLNK
    debmake.debug.debug('Ds: format={}->{}, prefix="{}", postfix="{}": "{}"'.format(fs[xformat_state], fs[format_state], prefix, postfix, line), type='s')
    return (line, format_state)

###################################################################
# Clean copyright
###################################################################
# substitute: \(co or (c) or  @copyright{} -> ©
re_co = re.compile(r'(?:\\\(co|\(c\)|@copyright\{\})', re.IGNORECASE) # fake match )

# search to allow leading jank words
re_copyright_line = re.compile(r'''
        (?:(?:Copyright|Copyr\.)\s*©\s*|
        ©\s*(?:Copyright|Copyr\.)\s+|
        (?:Copyright:?|Copyr\.)\s+|
        ©\s*)(?P<copyright>[^\s].*)$
        ''', re.IGNORECASE | re.VERBOSE)

def clean_copyright(line):
    # simplify '©' handling: no (c) from C MACRO here
    line = re_co.sub('©', line)
    m = re_copyright_line.search(line)
    if m:
        line = m.group('copyright').strip()
    else:
        print("W: no match @clean_copyright line={}".format(line), file=sys.stderr)
    return line

###################################################################
# Clean license
###################################################################
def clean_license(license_lines):
    lines = license_lines
    while len(lines) > 0 and lines[0] == '':
        del lines[0]
    while len(lines) > 0 and lines[-1:][0] == '':
        del lines[-1:]
    return lines

###################################################################
# Extract copyright+license from a source file
###################################################################
# content_state
cs = [
'C_INIT',  # initial content_state
'C_COPY',  # copyright found
'C_COPYB', # blank after C_COPY
'C_AUTH',  # AUTHOR: like
'C_AUTHB', # blank after C_AUTH
'C_LICN',  # license found
'C_EOF',   # EOF found at the end of line
]
# enum(cs)
for i, name in enumerate(cs):
    exec('{} = {}'.format(name.strip(), i))
C_EOF = -1 # override

re_copyright_mark_maybe = re.compile(r'''
        (?:Copyright|Copyr\.|\(C\)|©|\\\(co) # fake )
        ''', re.IGNORECASE | re.VERBOSE)

# matching line is excluded to be identified as copyright.
re_copyright_mark_exclude = re.compile(r'''(?:
        [=?$]|                  # C MACRO
        [^h][-+*/_a-su-z0-9]\(C\)|  # C MACRO (but Copyright(C) is not included)
        if\s+\(C\)|             # C code
        switch\s+\(C\)|         # C code
        (?:def|if|return)\s.*\(C\)| # Python/C
        /Copyright|             # file name
        Copyright[^\s(:]|       # text or variable name
        Copyright:?$|           # text
        Copyright\s+notice|     # text
        Copyright\s+holder|     # text
        Copyright\s+section|    # text
        Copyright\s+stanza|     # text
        copyright\s+file|       # text
        copyright\s+and\s+license| # text
        of\s+copyright| # text
        their\s+copyright|    # text
        the\s+copyright|    # text
        ^This\s.*copyright      # text
        )''', re.IGNORECASE | re.VERBOSE)

re_copyright_nomark_year = re.compile(r'''
        ^[12]\d\d\d\d
        ''', re.IGNORECASE | re.VERBOSE)

re_author_init = re.compile(r'''^(?:
        authors?:?|
        maintainers?:?|
        translators?:?)
        \s*(?P<author>.*)\s*$
        ''', re.IGNORECASE | re.VERBOSE)
re_author_cont = re.compile(r'^(?:.*@.*\..*|[^ ]*(?: [^ ]*){1,4})$')

re_license_start_maybe = re.compile(r'''(
        \sare\s|
        \sis\s|
        ^Copying\s|
        ^Everyone\s|
        ^Licensed\s|
        ^License\s|
        ^Permission\s|
        ^Redistribution\s|
        ^This\s|
        ^Unless\s
        )''', re.IGNORECASE | re.VERBOSE)
re_license_start_sure = re.compile(r'''(
        ^Copying\s+and\s+distribution\s+of\s+this\s+file|       # PERMISSIVE
        ^Distributed\s+under\s+the\s+Boost\s+Software\s+License,|   # Boost
        ^Everyone\s+is\s+permitted\s+to\s+copy\s+and\s+distribute|  # GNU FULL
        ^Distribute\s+under\s[AL]?GPL\s+version|                # GPL short
        ^Licensed\s+to\s+the\s+Apache\s+Software\s+Foundation|  #Apache-2.0_var1
        ^Licensed\s+under\s+|                                   # ECL
        ^Licensed\s+under\s+the\s+Apache\s+License|             #Apache-2.0_var2
        ^License\s+Applicability.\s+Except\s+to\s+the\s+extent\s+portions|  # SGI
        ^Permission\s+is\s+granted\s+to\s+copy,\s+distribute|   # GFDL 1.1
        ^Permission\s+is\s+hereby\s+granted|                    # MIT
        ^Permission\s+to\suse,\s+copy,\s+modify|                # ISC
        ^Redistribution\s+and\s+use\s+in\s+source\s+and\s+binary\s+forms|   # Apache 1.0/BSD
        ^The\s+contents\s+of\s+this\s+file|                     # ErlPL, ...
        ^The\s+contents\s+of\s+this\s+file\s+are\s+subject\s+to| # MPL-1.0 1.1
        ^This\s+.{2,40}\s+is\s+free\s+software|                 # makefile.in etc.
        ^This\s+file\s+is\s+distributed\s+under\s+the\s+same\s+license\s+as\s+.{5,40}\.$| # same
        ^This\s+library\s+is\s+free\s+software|                 # LGPL variants
        ^This\s+license\s+is\s+a\s+modified\s+version\s+of\s+the|   # AGPL-1.0
        ^This\s+program\s+can\s+redistributed|                  # LaTeX LPPL 1.0
        ^This\s+program\s+is\s+free\s+software|                 # GPL variants
        ^This\s+program\s+may\s+be\s+redistributed|             # LaTeX LPPL 1.1 1.2
        ^This\s+software\s+is\s+furnished\s+under\s+license|    # DEC
        ^This\s+software\s+is\s+provided\s+|                    # Zlib
        ^This\s+Source\s+Code\s+Form\s+is\s+subject\s+to\s+the\s+terms\s+of| # MPL 2.0
        ^This\s+work\s+is\s+distributed\s+under|                # W3C
        ^This\s+work\s+may\s+be\s+redistributed|                # LaTeX LPPL 1.3
        ^unless\s+explicitly\s+acquired\s+and\s+licensed        # Watcom
        )''', re.IGNORECASE | re.VERBOSE)

re_license_end_start = re.compile(r'''(
        ^EOT$|^EOF$|^EOL$|^END$|        # shell <<EOF like lines
        ^msgid\s|                       # po/pot
        ^msgstr\s                       # po/pot
        )''', re.IGNORECASE | re.VERBOSE)

re_license_end_nostart = re.compile(r'''(
        [=?_]|                          # C MACRO code
        ^#if|                           # C CPP
        ^#include|                      # C CPP
        enum\s.*\s{|                    # C enum
        class\s.*\s{|                   # C++
        ^"""|^\'\'\'|                   # python block comment
        ^=cut|                          # perl
        ^---|^@@|                       # diff block
        ^\.TH|                          # no .TH for manpage
        ^\.SH|                          # no .SH for manpage
        ^Who\sare\swe\?$|               # The Linux Foundation License templates
        ^-----------|                   # ./configure
        ^Usage:|                        # ltmain.sh
        ^serial\s+[0-9]|                # aclocal.m4
        ^@configure_input@|             # ltversion.m4
        ^This\sfile\sis\smaintained|    # Automake files
        ^Do\sall\sthe\swork\sfor\sAutomake| # aclocal.m4 Automake
        ^Originally\s+written\s+by\+.{10,20}?\s+Please\s+send\spatches| # config.guess
        ^Please\s+note\s+that\s+the| # Makefile.in.in (gettext)
        ^Please\s+send\s+patches\s+with|   # config.sub
        ^Please\s+send\s+patches\s+to|  # config.sub, config.guess
        ^if\s+not\s+1,\s+datestamp\s+to\s+the\s+version\s+number|  # configure.ac
        ^the\s+first\s+argument\s+passed\s+to\s+this\s+file|  # config.rpath
        ^You\s+can\s+get\s+the\s+latest\s+version\s+of| # config.guess GPL3+ based
        ^@include|                      # Texinfo
        ^@end|                          # Texinfo
        ^%\*\*|                         # Texinfo
        ^Please\stry\sthe\slatest\sversion\sof # Texinfo.tex
        )''', re.IGNORECASE | re.VERBOSE)

# This should be also listed in re_license_start_sure
re_license_end_next = re.compile(r'''(
    ^This\s+file\s+is\s+distributed\s+under\s+the\s+same\s+license\s+as\s+.{5,40}\.$
        )''', re.IGNORECASE | re.VERBOSE)

#        [{}]|                           # perl/shell block
def check_lines(lines):
    copyright_found = False
    license_found = False
    format_state = F_BLNK
    content_state = C_INIT
    copyright_lines = []
    license_lines = []
    author_lines = []
    ##########################################################################
    # main loop for lines (start)
    ##########################################################################
    for line in lines:
        line = line.strip()
        if line == '.': # empty line only with . as empty
            line = ''
        # set previous values
        xformat_state = format_state
        xcontent_state = content_state
        debmake.debug.debug('Db: begin xformat={}, xcontent={}, copyright={}, license={}: "{}"'.format(fs[xformat_state], cs[xcontent_state], copyright_found, license_found, line), type='b')
        if xcontent_state == C_EOF:
            break
        if xformat_state == F_EOF:
            break
        ######################################################################
        (line, format_state) = check_format_style(line, xformat_state)
        ######################################################################
        if xcontent_state == C_INIT:
            persistent_format = [] # unset
        else: # xcontent_state != C_INIT
            if persistent_format == []:
                persistent_format = formats[xformat_state][2] # set
            elif format_state not in persistent_format:
                break
            else:
                pass
        ######################################################################
        match_author_init = re_author_init.search(line)
        ######################################################################
        if re_license_end_start.search(line): # end no matter what
            debmake.debug.debug('Dm: license_end_start: "{}"'.format(line), type='m')
            break
        elif xcontent_state != C_INIT and \
                re_license_end_nostart.search(line):
            debmake.debug.debug('Dm: xcontent_state != C_INIT and license_end_nostart: "{}"'.format(line), type='m')
            break
        elif xcontent_state in [C_INIT, C_COPY, C_COPYB, C_AUTH, C_AUTHB] and \
                re_copyright_mark_maybe.search(line) and \
                (not re_copyright_mark_exclude.search(line)): # copyright_start_sure
            debmake.debug.debug('Dm: xcontent_state in [C_INIT, C_COPY, C_COPYB, C_AUTH, C_AUTHB] and copyright_start_sure: "{}"'.format(line), type='m')
            line = clean_copyright(line)
            copyright_lines.append(line)
            copyright_found = True
            content_state = C_COPY
        elif xcontent_state == C_COPY and \
                re_copyright_nomark_year.search(line):
            debmake.debug.debug('Dm: copyright_nomark_year: "{}"'.format(line), type='m')
            copyright_lines.append(line)
            copyright_found = True
            content_state = C_COPY
        elif xcontent_state in [C_INIT, C_COPY, C_COPYB, C_AUTH, C_AUTHB] and \
                re_license_start_sure.search(line):
            debmake.debug.debug('Dm: xcontent_state in [C_INIT, C_COPY, C_COPYB, C_AUTH, C_AUTHB] and license_start_sure: "{}"'.format(line), type='m')
            license_lines.append(line)
            license_found = True
            if re_license_end_next.search(line):
                content_state = C_EOF
            else:
                content_state = C_LICN
        elif xcontent_state in [C_INIT, C_COPY, C_COPYB, C_LICN, C_AUTH, C_AUTHB] and \
                match_author_init:
            debmake.debug.debug('Dm: xcontent_state in [C_INIT, C_COPY, C_COPYB, C_LICN, C_AUTH, C_AUTHB] and author_init: "{}"'.format(line), type='m')
            content_state = C_AUTH
            author_lines.append(match_author_init.group('author'))
        elif xcontent_state == C_INIT:
            debmake.debug.debug('Dm: xcontent_state == C_INIT: "{}"'.format(line), type='m')
            content_state = C_INIT
        elif xcontent_state in [C_AUTH, C_AUTHB] and \
                re_author_cont.search(line):
            debmake.debug.debug('Dm: xcontent_state in [C_AUTH, C_AUTHB] and author_cont: "{}"'.format(line), type='m')
            author_lines.append(line)
            content_state = C_AUTH
        elif xcontent_state in [C_COPY, C_AUTH] and \
                re_license_start_maybe.search(line):
            debmake.debug.debug('Dm: xcontent_state in [C_COPY, C_AUTH] and license_start_maybe: "{}"'.format(line), type='m')
            license_lines.append(line)
            license_found = True
            content_state = C_LICN
        elif xcontent_state == C_COPY and line == '':
            debmake.debug.debug('Dm: C_COPY + blank line', type='m')
            content_state = C_COPYB
        elif xcontent_state == C_COPY: # line != ''
            debmake.debug.debug('Dm: C_COPY + non-blank line: "{}"'.format(line), type='m')
            last = len(copyright_lines) -1
            if copyright_lines[last][-1:] == '-':
                copyright_lines[last] = (copyright_lines[last][:-1] + line).strip()
            else:
                copyright_lines[last] = (copyright_lines[last] + ' ' + line).strip()
            content_state = C_COPY
        elif xcontent_state == C_COPYB and line == '':
            debmake.debug.debug('Dm: C_COPYB + blank line', type='m')
            content_state = C_COPYB
        elif xcontent_state == C_COPYB: # line != ''
            debmake.debug.debug('Dm: C_COPYB + non-blank line: "{}"'.format(line), type='m')
            license_lines.append(line)
            license_found = True
            content_state = C_LICN
        elif xcontent_state == C_LICN:
            debmake.debug.debug('Dm: xcontent_state == C_LICN: "{}"'.format(line), type='m')
            license_lines.append(line)
            license_found = True
            content_state = C_LICN
        elif xcontent_state == C_AUTH:
            debmake.debug.debug('Dm: xcontent_state == C_AUTH: "{}"'.format(line), type='m')
            author_lines.append(line)
            content_state = C_AUTH
        elif xcontent_state == C_AUTHB and license_found:
            debmake.debug.debug('Dm: xcontent_state == C_AUTHB and license_found, copyright={}, license={}: "{}"'.format(copyright_found, license_found, line), type='m')
            content_state = C_EOF
        elif xcontent_state == C_AUTHB and copyright_found:
            debmake.debug.debug('Dm: xcontent_state == C_AUTHB and copyright_found, copyright={}, license={}: "{}"'.format(copyright_found, license_found, line), type='m')
            license_lines.append(line)
            license_found = True
            content_state = C_LICN
        elif xcontent_state == C_AUTHB:
            debmake.debug.debug('Dm: xcontent_state == C_AUTHB, copyright={}, license={}: "{}"'.format(copyright_found, license_found, line), type='m')
            author_lines.append(line)
            content_state = C_AUTH
        else: # should not be here
            print('W: !!!!! format={}->{}, content={}->{}, copyright={}, license={}: "{}"'.format(fs[xformat_state], fs[format_state], cs[xcontent_state], cs[content_state], copyright_found, license_found, line), file=sys.stderr)
            print('W: !!!!! assertion error, exit loop !!!!!', file=sys.stderr)
            break
        debmake.debug.debug('De: *end* format={}->{}, content={}->{}, copyright={}, license={}: "{}"'.format(fs[xformat_state], fs[format_state], cs[xcontent_state], cs[content_state], copyright_found, license_found, line), type='e')
    ##########################################################################
    # main loop for lines (end)
    # sanitize copyright_lines
    ##########################################################################
    if len(copyright_lines) > MAX_COPYRIGHT_LINES:
        print('W: !!!!! too many copyright lines !!!!!', file=sys.stderr)
        print('W: starting with {}'.format(copyright_lines[0]), file=sys.stderr)
        copyright_lines = copyright_lines[:MAX_COPYRIGHT_LINES]
    for (i, line) in enumerate(copyright_lines):
        if len(line) > MAX_COPYRIGHT_LENGTH:
            copyright_lines[i] = line[:MAX_COPYRIGHT_LENGTH]
            print('W: !!!!! too long copyright line !!!!!', file=sys.stderr)
            print('W: starting with {}'.format(copyright_lines[i]), file=sys.stderr)
    ##########################################################################
    # analyze copyright
    ##########################################################################
    copyright_data = analyze_copyright(copyright_lines)
    license_lines = clean_license(license_lines)
    debmake.debug.debug('Da: AUTHOR(s)/TRANSLATOR(s):', type='a')
    for line in author_lines:
        debmake.debug.debug('Da: {}'.format(line), type='a')
    if copyright_data == {} and license_lines == []:
        # no copyright and no license
        copyright_data = {'__NO_COPYRIGHT_NOR_LICENSE__':(9999, 0)}
    elif copyright_data == {}:
        # no copyright and but with license (Maybe __UNKNOWN__ license)
        copyright_data = {'__NO_COPYRIGHT__':(9999, 0)}
    return (copyright_data, license_lines)

###################################################################
# Check license of a text file
###################################################################
def check_license(file, encoding='utf-8'):
    ###################################################################
    # Start analyzing file (default encoding)
    ###################################################################
    try:
        with open(file, 'r', encoding=encoding) as fd:
            (copyright_data, license_lines) = check_lines(fd.readlines())
    ###################################################################
    # Fall back for analyzing file (latin-1 encoding)
    ###################################################################
    except UnicodeDecodeError as e:
        print('W: Non-UTF-8 char found, using latin-1: {}'.format(file), file=sys.stderr)
        fd.close()
        with open(file, 'r', encoding='latin-1') as fd:
            (copyright_data, license_lines) = check_lines(fd.readlines())
    return (copyright_data, license_lines)

###################################################################
# Check autogenerated files
###################################################################
re_autofiles = re.compile(r'''(
        ^Makefile.in$| # Autotools
        ^.*/Makefile\.in$| # Autotools
        ^aclocal.m4$| # Autotools
        ^build-aux/.*$| # Autotools
        ^compile$| # Autotools
        ^config\.guess$| # Autotools
        ^config\.status$| # Autotools
        ^config\.sub$| # Autotools
        ^config\.rpath$| # Autotools
        ^configure$| # Autotools
        ^depcomp$| # Autotools
        ^install-sh$| # Autotools
        ^libltdl/.*$| # Autotools
        ^libtool$| # Autotools
        ^ltmain.sh$| # Autotools
        ^missing$| # Autotools
        ^py-compile$| # Autotools
        ^test-driver$| # Autotools
        ^po/Makefile$| # Autotools (getttext)
        ^po/Makefile\.in$| # Autotools (gettext)
        ^po/Makefile\.in\.in$| # Autotools (gettext)
        ^po/Makevars$| # Autotools (gettext)
        ^m4/.*$        # Autotools (no | at the end)
        )''', re.IGNORECASE | re.VERBOSE)

###################################################################
# Check all appearing copyright and license texts
###################################################################
# data[*][0]: license name ID: licenseid
# data[*][1]: file name (bunched, list): files
# data[*][2]: copyright holder info (data=dictionary): copyright_lines
# data[*][3]: license text (original: list of lines): license_lines
###################################################################
def check_all_licenses(files, encoding='utf-8', mode=0, pedantic=False):
    adata = []
    license_cache = {} # hashtable for quicker license scan
    md5hash = hashlib.md5()
    licensetext0 = '\n Auto-generated file under the permissive license.'
    md5hash.update(licensetext0.encode())
    md5hashkey0 = md5hash.hexdigest()
    license_cache[md5hashkey0] = ('__AUTO_PERMISSIVE__', licensetext0, True)
    if len(files) == 0:
        print('W: check_all_licenses(files) should have files', file=sys.stderr)
    if sys.hexversion >= 0x03030000: # Python 3.3 ...
        print('I: ', file=sys.stderr, end='', flush=True)
    for file in files:
        debmake.debug.debug('Df: check_all_licenses file={}'.format(file), type='f')
        if os.path.isfile(file):
            if sys.hexversion >= 0x03030000: # Python 3.3 ...
                print('.', file=sys.stderr, end='', flush=True)
            (copyright_data, license_lines) = check_license(file, encoding=encoding)
            debmake.debug.debug('Dc: copyright_data  = {}'.format(copyright_data), type='c')
            norm_text = debmake.lc.normalize(license_lines)
            md5hash = hashlib.md5()
            md5hash.update(norm_text.encode())
            md5hashkey = md5hash.hexdigest()
            if md5hashkey in license_cache.keys():
                (licenseid, licensetext, permissive) = license_cache[md5hashkey]
            else:
                (licenseid, licensetext, permissive) = debmake.lc.lc(norm_text, license_lines, mode)
                license_cache[md5hashkey] = (licenseid, licensetext, permissive)
            if not pedantic and permissive and re_autofiles.search(file):
                debmake.debug.debug('Dl: LICENSE ID = __AUTO_PERMISSIVE__ from {}'.format(licenseid), type='l')
                licenseid = '__AUTO_PERMISSIVE__'
                licensetext = licensetext0
                md5hashkey = md5hashkey0
            else:
                debmake.debug.debug('Dl: LICENSE ID = {}'.format(licenseid), type='l')
            adata.append((md5hashkey, copyright_data, licenseid, licensetext, file))
        else:
            print('W: check_all_licenses on non-existing file: {}'.format(file), file=sys.stderr)
        for c in copyright_data.keys():
            debmake.debug.debug('Dc: {}-{}: {}'.format(copyright_data[c][0], copyright_data[c][1], c), type='c')
        for l in license_lines:
            debmake.debug.debug('Dl: {}'.format(l), type='l')
    print('\nI: check_all_licenses completed for {} files.'.format(len(files)), file=sys.stderr)
    return adata

def bunch_all_licenses(adata):
    # group scan result by license
    group_by_license = []
    adata = sorted(adata, key=operator.itemgetter(0)) # sort by md5hashkey
    for k, g in itertools.groupby(adata, operator.itemgetter(0)):
        group_by_license.append(list(g))      # Store group iterator as a list
    # bunch the same license for reporting
    bdata = []
    for data_by_license in group_by_license:
        bunched_files = []
        bunched_copyright_data = {}
        for (md5hashkey, copyright_data, licenseid, licensetext, file) in data_by_license:
            bunched_files.append(file)
            for name, (year_min, year_max) in copyright_data.items():
                if name in bunched_copyright_data.keys():
                    (year_min0, year_max0) = bunched_copyright_data[name]
                    bunched_copyright_data[name] = (min(year_min0, year_min), max(year_max0, year_max))
                else:
                    bunched_copyright_data[name] = (year_min, year_max)
        sortkey = '{0:03} {1:02} {2} {3}'.format(max(0, 1000 - len(bunched_files)), min(99, len(licenseid)), licenseid, md5hashkey)
        bunched_files = sorted(bunched_files)
        copyright_list = []
        for name, (year_min, year_max) in bunched_copyright_data.items():
            copyright_list.append((year_min, year_max, name))
        copyright_list = sorted(copyright_list)
        bdata.append((sortkey, bunched_files, copyright_list, licenseid, licensetext))
        debmake.debug.debug('Dk: sortkey="{}", files={}'.format(sortkey, bunched_files), type='k')
    return bdata

def format_all_licenses(bdata):
    spaces = '           ' # 11 spaces
    # sort for printer ready order
    group_by_license = []
    bdata = sorted(bdata, key=operator.itemgetter(0)) # sort by sortkey (more files comes early)
    for k, g in itertools.groupby(bdata, operator.itemgetter(0)):
        group_by_license.append(list(g))      # Store group iterator as a list
    cdata = []
    for data_by_sortkey in group_by_license:
        for (sortkey, bunched_files, copyright_list, licenseid, licensetext) in data_by_sortkey:
            copyright_lines = ''
            for (year_min, year_max, name) in copyright_list:
                if year_max == 0: # not found
                    copyright_lines += '{}{}\n'.format(spaces, name)
                elif year_min == year_max:
                    copyright_lines += '{}{} {}\n'.format(spaces, year_min, name)
                else:
                    copyright_lines += '{}{}-{} {}\n'.format(spaces, year_min, year_max, name)
            cdata.append((licenseid, licensetext, bunched_files, copyright_lines))
    return cdata

def check_copyright(files, mode=0, encoding='utf-8', pedantic=False):
    print('I: check_all_licenses', file=sys.stderr)
    adata = check_all_licenses(files, encoding=encoding, mode=mode, pedantic=pedantic)
    print('I: bunch_all_licenses', file=sys.stderr)
    bdata = bunch_all_licenses(adata)
    print('I: format_all_licenses', file=sys.stderr)
    cdata = format_all_licenses(bdata)
    return cdata


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
def copyright(package_name, license_file_masks, data, xml_html_files, binary_files, huge_files, mode=0, tutorial=False):
    # mode: 0: not -c, 1: -c simple, 2: -cc normal, 3: -ccc extensive
    #      -1: -cccc debug simple, -2 -ccccc debug normal -3 -cccccc debug extensive
    # make text to print
    text = '''\
Format: http://www.debian.org/doc/packaging-manuals/copyright-format/1.0/
Upstream-Name: {}
Source: <url://example.com>
'''.format(package_name)
    if tutorial:
        text += '''###
### Uncomment the following 2 lines to enable uscan to exclude non-DFSG components 
### Files-Excluded: command/non-dfsg.exe
###   docs/source/javascripts/jquery-1.7.1.min.js
###
### This is a autogenerated template for debian/copyright.
###
### Edit this accordinng to the "Machine-readable debian/copyright file" as
### http://www.debian.org/doc/packaging-manuals/copyright-format/1.0/ .
###
### Generate updated license templates with the "debmake -cc" to STDOUT
### and merge them into debian/copyright as needed.
###
### Please avoid to pick license terms that are more restrictive than the
### packaged work, as it may make Debian's contributions unacceptable upstream.

'''
    else:
        text += '\n'
    for (licenseid, licensetext, files, copyright_lines) in data:
        # Files:
        text +=             'Files:     {}\n'.format('\n           '.join(files))
        # Copyright:
        text +=             'Copyright: ' + copyright_lines[11:]
        # License:
        text +=             'License:   {}{}\n\n'.format(licenseid, licensetext)
    if xml_html_files != []:
        text += '#----------------------------------------------------------------------------\n'
        text += '# xml and html files (skipped):\n#         {}\n\n'.format('\n#         '.join(xml_html_files))
    if binary_files != []:
        text += '#----------------------------------------------------------------------------\n'
        text += '# binary files (skipped):\n#         {}\n\n'.format('\n#         '.join(binary_files))
    if huge_files != []:
        text += '#----------------------------------------------------------------------------\n'
        text += '# huge files   (skipped):\n#         {}\n\n'.format('\n#         '.join(huge_files))
    if mode == 0: # not for -c
        text += '''\
#----------------------------------------------------------------------------
# Files marked as NO_LICENSE_TEXT_FOUND may be covered by the following
# license/copyright files.

'''
        # get list of files to attach
        license_files = set()
        for fx in license_file_masks:
            license_files.update(set(glob.glob(fx)))
        for f in license_files:
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
    check_lines(['#!/bin/sh', 'COPYRIGHT FOO_BAR 1890', '', 'License', 'END'])
    print(analyze_copyright(["1987-90 FOO bar","boo foo wooo 2001-12", "1994, 1995, 1996, 1997, 1998, 1999, 2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009  Free Software Foundation, Inc." ]))
    X = 'Free Software Foundation, Inc. HHHHHHH'
    print(cleanup_name(X))

