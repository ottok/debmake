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
NORMAL_LINE_LENGTH = 64         # chars
MAX_COPYRIGHT_LINE_LENGTH = 256 # chars
MAX_COPYRIGHT_LINES = 256       # lines
NORMAL_LICENSE_LINES = 32       # lines
MAX_LICENSE_LINE_LENGTH = 1024  # chars
MAX_LICENSE_LINES = 1024        # lines

###################################################################
# check_lines() uses following state parameters to scan and extract
# in its MAIN-LOOP to generate:
#  * copyright_lines
#  * license_lines as list of string
###################################################################
#------------------------------------------------------------------
# format state lists
#------------------------------------------------------------------
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

#------------------------------------------------------------------
# content_state
#------------------------------------------------------------------
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

#------------------------------------------------------------------
# format rule definitions
#------------------------------------------------------------------
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

# C block mode start with /*
formats[F_BLKC] = (
        re.compile(r'^(?P<prefix>/\*)\s*\**(?P<text>.*)(?P<postfix>)$'),  # C /*...
        [F_BLKCE, F_BLKC2, F_BLKC1, F_BLKC0],
        {F_QUOTE, F_BLKC, F_BLKCE, F_BLKC2, F_BLKC1, F_BLKC0, F_BLNK}
        )
formats[F_BLKCE] = (
        re.compile(r'^(?P<prefix>\*|)(?P<text>.*?)\s*\**?(?P<postfix>\*/).*$'),  # C ...*/
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

###################################################################
# check_lines() uses regex to change state in its MAIN-LOOP:
###################################################################
#------------------------------------------------------------------
# Extract copyright+license from a source file
#------------------------------------------------------------------
# pre-process line
re_dropwords = re.compile(r'''(?:
        ^[:!;"'#%*\s]*timestamp=.*$|            # timestamp line
        ^[:!;"'#%*\s]*scriptversion=.*$|        # version line
        ^[:!;"'#%*\s]*\$Id:.*\$|                # CVS/RCS version
        ^[:!;"'#%*\s]*-\*-\s+coding:.*-\*-.*$|  # EMACS
        ^[:!;"'#%*\s]*vim?:.*$|                 # VIM/VI
        ^\.bp|                                  # manpage
        All\s+Rights?\s+Reserved.?|             # remove
        <BR>                                    # HTML
        )''', re.IGNORECASE | re.VERBOSE)

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

re_author_init_exclude = re.compile(r'''(
        ^authorization\s|
        ^authors?\sbe\s|
        ^authors?\sor\s
        )''', re.IGNORECASE | re.VERBOSE)

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
        ^GNU\s+General\s+Public\s+License\s+|                   # 1 liner GPL
        ^GPL|                                                   # 1 liner GPL
        ^LGPL|                                                  # 1 liner GPL
        ^BSD|                                                   # 1 liner BSD
        ^MIT|                                                   # 1 liner MIT
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
        ^This\s+program\s+and\s+the\+accompanying\s+materials|  # INTEL
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
        ^static\s+.*=|                  # C
        ^const\s+.*=|                   # C
        ^struct\s+.*=|                  # C
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
        ^Basic\sInstallation\s          # INSTALL
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
        ^Module Name:|                  # ASM
        ^Please\s+try\s+the\s+latest\s+version\s+of # Texinfo.tex
        )''', re.IGNORECASE | re.VERBOSE)

# This should be also listed in re_license_start_sure
re_license_end_next = re.compile(r'''(
    ^This\s+file\s+is\s+distributed\s+under\s+the\s+same\s+license\s+as\s+.{5,40}\.$
        )''', re.IGNORECASE | re.VERBOSE)

###################################################################
# check_lines() uses following to process line in its MAIN-LOOP:
###################################################################
#------------------------------------------------------------------
# process line to identify new state based on above definitions
#------------------------------------------------------------------
def check_format_style(line, xformat_state):
    # main process loop
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
    debmake.debug.debug('Ds: format={}->{}, prefix="{}", postfix="{}": "{}"'.format(fs[xformat_state], fs[format_state], prefix, postfix, line), type='s')
    return (line, format_state)

#------------------------------------------------------------------
# Normalize line starting copyright_line
#------------------------------------------------------------------
# substitute: \(co or (c) or  @copyright{} -> ©
re_co = re.compile(r'(?:\\\(co|\(c\)|@copyright\{\})', re.IGNORECASE) # fake match )

# search to allow leading jank words
re_copyright_mark = re.compile(r'''
        (?:(?:Copyright|Copyr\.)\s*©\s*|
        ©\s*(?:Copyright|Copyr\.)\s+|
        (?:Copyright:?|Copyr\.)\s+|
        ©\s*)(?P<copyright>[^\s].*)$
        ''', re.IGNORECASE | re.VERBOSE)

def normalize_copyright_mark(copyright_line):
    # simplify '©' handling: no (c) from C MACRO here
    copyright_line = re_co.sub('©', copyright_line)
    # output after © or equivalents as copyright data
    m = re_copyright_mark.search(copyright_line)
    if m:
        copyright_line = m.group('copyright').strip()
    else:
        print("W: no match @normalize_copyright_mark copyright_line={}".format(copyright_line), file=sys.stderr)
    return copyright_line

###################################################################
# check_lines() uses followings in its POST-PROCESS to generate:
#  * copyright_data (dictionary holding tuple)
#  * license_lines  (cleaned-up strings)
###################################################################
#------------------------------------------------------------------
# split copyright line into years and name
#------------------------------------------------------------------
re_ascii = re.compile('[\s!-~]')

re_year_yn = re.compile(r'''^
        (?P<year>\d\d[-,.;\s\d]*):?\s*
        (?P<name>\D.*)$''', re.IGNORECASE | re.VERBOSE)

re_year_ny = re.compile(r'''^
        (?P<name>.*?\D)\s*
        (?P<year>\d\d[-.,;\s\d]*)$''', re.IGNORECASE | re.VERBOSE)
def split_years_name(copyright_line):
    # copyright_line: leading "Copyright (c)" is removed in MAIN-LOOP
    copyright_line = copyright_line.strip()
    # split copyright_line into years and name
    m1 = re_year_yn.search(copyright_line)
    m2 = re_year_ny.search(copyright_line)
    if m1:
        years = m1.group('year').strip()
        name = m1.group('name').strip()
    elif m2:
        years = m2.group('year').strip()
        name = m2.group('name').strip()
    elif copyright_line:
        years = 'NO_MATCH' # sign for funkey copyright_line
        name = copyright_line.strip()
    else:
        years = ''
        name = ''
    debmake.debug.debug('Dy: years="{}", name="{}" <- "{}"'.format(years, name, copyright_line), type='y')
    return (years, name)

#------------------------------------------------------------------
# Parse years into tuple (year_min, year_max)
#------------------------------------------------------------------
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

re_year = re.compile(r'\d\d+')

def get_year_range(years):
    # 1990-91 -> 1990-1991 etc.
    while True:
        m = re_year_1900.search(years)
        if m:
            years = m.group('pre') + m.group('n1') + '-19' + \
                    m.group('n2') + m.group('post')
        else:
            break
    # 2010-11 -> 2010-2011 etc.
    while True:
        m = re_year_2000.search(years)
        if m:
            years = m.group('pre') + m.group('n1') + '-20' + \
                    m.group('n2') + m.group('post')
        else:
            break
    # year range
    year_min = 9999
    year_max = 0
    for year_string in re_year.findall(years):
        year = int(year_string)
        year_min =  min(year_min, year)
        year_max =  max(year_max, year)
    return (year_min, year_max)

#------------------------------------------------------------------
# Parse name to remove junks
#------------------------------------------------------------------
re_name_drop = re.compile(r'''
        by|
        originally\s+by|
        written\s+by|
        (?:originally\s+)?written\s+by
        ''', re.IGNORECASE | re.VERBOSE)

re_fsf_addr = re.compile(r'^Free\s+Software\s+Foundation,\s+Inc\.',
        re.IGNORECASE)

def normalize_name(name):
    name = name.strip()
    name = re_name_drop.sub('', name).strip()
    if re_fsf_addr.search(name): # If FSF, strip address etc.
        name = 'Free Software Foundation, Inc.' 
    return name

#------------------------------------------------------------------
# Analyze all copyright_lines into copyright_data
#------------------------------------------------------------------
def analyze_copyright(copyright_lines):
    #------------------------------------------------------------------
    # sanitize copyright_lines
    #------------------------------------------------------------------
    n_copyright_lines = len(copyright_lines)
    if n_copyright_lines > MAX_COPYRIGHT_LINES:
        copyright_lines = [ "_TOO_MANY_LINES_({}lines) starting with: {}".format(n_copyright_lines, copyright_lines[0][0:NORMAL_LINE_LENGTH]) ]
    for (i, copyright_line) in enumerate(copyright_lines):
        copyright_line = copyright_line.strip()
        n_copyright = len(copyright_line)
        if n_copyright > MAX_COPYRIGHT_LINE_LENGTH:
            copyright_line = "_TOO_LONG_LINE_({}chars.) starting with: {}".format(n_copyright, copyright_line[0:NORMAL_LINE_LENGTH])
        non_ascii = re_ascii.sub('', copyright_line)
        if non_ascii:
            n_non_ascii = len(non_ascii)
        else:
            n_non_ascii = 0
        if n_copyright < (n_non_ascii * 4) and n_copyright > NORMAL_LINE_LENGTH:
            copyright_line = "_TOO_MANY_NON_ASCII_({}chars. over {}chars. in one of lines) starting with: {}".format(n_non_ascii, n_copyright, copyright_line[0:NORMAL_LINE_LENGTH])
    copyright_data = {}
    for copyright_line in copyright_lines:
        (years, name) = split_years_name(copyright_line)
        name = normalize_name(name).strip()
        (year_min, year_max) = get_year_range(years)
        if name in copyright_data.keys():
            (year0_min, year0_max) = copyright_data[name]
            year_min =  min(year_min, year0_min)
            year_max =  max(year_max, year0_max)
        if name:
            copyright_data[name] = (year_min, year_max)
        else:
            print('W: analyze_copyright: skip name="", years={}-{}'.format(year_min, year_max), file=sys.stderr)
    return copyright_data

#------------------------------------------------------------------
# Clean license
#------------------------------------------------------------------
def clean_license(license_lines, file):
    #------------------------------------------------------------------
    # sanitize license_lines
    #------------------------------------------------------------------
    n_license_lines = len(license_lines)
    if n_license_lines > MAX_LICENSE_LINES:
        license_lines = [ "_TOO_MANY_LINES_({}lines) starting with: {}".format(n_license_lines, license_lines[0][0:NORMAL_LINE_LENGTH]) ]
    for (i, license_line) in enumerate(license_lines):
        license_line = license_line.strip()
        n_license = len(license_line)
        if n_license > MAX_LICENSE_LINE_LENGTH:
            license_line = [ "_TOO_LONG_LINE_({}chars.) starting with: {}".format(n_license, license_line[0:NORMAL_LINE_LENGTH]) ]
        non_ascii = re_ascii.sub('', license_line)
        if non_ascii:
            n_non_ascii = len(non_ascii)
        else:
            n_non_ascii = 0
        if n_license < (n_non_ascii * 4) and n_license > NORMAL_LINE_LENGTH:
            license_lines = "_TOO_MANY_NON_ASCII_({}chars. over {}chars. in one of lines) starting with: {}".format(n_non_ascii, n_license, license_line[0:NORMAL_LINE_LENGTH])
    lines = license_lines
    license_lines = []
    for line in lines:
        if line[0:len(file) + 1] == (file + ':'):
            license_lines.append('')
        else:
            license_lines.append(line.strip())
    while len(license_lines) > 0 and license_lines[0] == '':
        del license_lines[0]
    while len(license_lines) > 0 and license_lines[-1] == '':
        del license_lines[-1]
    return license_lines

##########################################################################
# Main text process loop over lines
##########################################################################
def check_lines(lines, file):
    copyright_found = False
    license_found = False
    format_state = F_BLNK
    content_state = C_INIT
    copyright_lines = []
    license_lines = []
    author_lines = []
    ##########################################################################
    # MAIN-LOOP for lines (start)
    ##########################################################################
    for line in lines:
        # set previous values
        xformat_state = format_state
        xcontent_state = content_state
        debmake.debug.debug('Db: begin xformat={}, xcontent={}, copyright={}, license={}: "{}"'.format(fs[xformat_state], cs[xcontent_state], copyright_found, license_found, line), type='b')
        if xcontent_state == C_EOF:
            break
        if xformat_state == F_EOF:
            break
        #------------------------------------------------------------------
        # pre-process line
        #------------------------------------------------------------------
        line = line.strip()
        if line[:1] == '+': # hack to drop patch (1 level)
            line = line[1:]
        if line == '.':     # empty line only with . as empty
            line = ''
        if line[:len(file)] == file:
            line = ""
        line = re_dropwords.sub('', line)
        line = line.strip()
        #------------------------------------------------------------------
        # procss line
        #------------------------------------------------------------------
        (line, format_state) = check_format_style(line, xformat_state)
        if xcontent_state == C_INIT:
            persistent_format = [] # unset
        else: # xcontent_state != C_INIT
            if persistent_format == []:
                persistent_format = formats[xformat_state][2] # set
            elif format_state not in persistent_format:
                break
            else:
                pass
        #------------------------------------------------------------------
        match_author_init = re_author_init.search(line)
        match_author_init_exclude = re_author_init_exclude.search(line)
        #------------------------------------------------------------------
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
            # copyright marked line
            line = normalize_copyright_mark(line)
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
        elif xcontent_state in [C_COPY, C_COPYB, C_AUTH, C_AUTHB] and \
                match_author_init:
            debmake.debug.debug('Dm: xcontent_state in [C_COPY, C_COPYB, C_AUTH, C_AUTHB] and author_init: "{}"'.format(line), type='m')
            content_state = C_AUTH
            author_lines.append(match_author_init.group('author'))
        elif xcontent_state in [C_INIT, C_LICN] and (not match_author_init_exclude) and \
                match_author_init:
            debmake.debug.debug('Dm: xcontent_state in [C_INIT, C_LICN] and author_init: "{}"'.format(line), type='m')
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
    # MAIN-LOOP (end)
    ##########################################################################

    ##########################################################################
    # POST-PROCESS
    ##########################################################################
    #------------------------------------------------------------------
    # analyze_copyright and clean_license
    #------------------------------------------------------------------
    copyright_data = analyze_copyright(copyright_lines)
    license_lines = clean_license(license_lines, file)
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
            (copyright_data, license_lines) = check_lines(fd.readlines(), file)
    ###################################################################
    # Fall back for analyzing file (latin-1 encoding)
    ###################################################################
    except UnicodeDecodeError as e:
        print('W: Non-UTF-8 char found, using latin-1: {}'.format(file), file=sys.stderr)
        fd.close()
        with open(file, 'r', encoding='latin-1') as fd:
            (copyright_data, license_lines) = check_lines(fd.readlines(), file)
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
re_permissive = re.compile('''(
        ^PERMISSIVE$|
        ^Expat$|
        ^MIT$|
        ^ISC$|
        ^Zlib$|
        ^BSD-2-Clause$|
        ^BSD-3-Clause$|
        ^BSD-4-Clause-UC$|
        ^GFDL[123]?(?:\.[01])? with (autoconf|libtool|bison) exception$|
        ^[AL]?GPL[123]?(?:\.[01])? with (autoconf|libtool|bison) exception$
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
                (licenseid, licensetext) = license_cache[md5hashkey]
            else:
                (licenseid, licensetext) = debmake.lc.lc(norm_text, license_lines, mode)
                license_cache[md5hashkey] = (licenseid, licensetext)
            if not pedantic and re_permissive.search(licenseid) and re_autofiles.search(file):
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
        for name, (year_min, year_max) in sorted(bunched_copyright_data.items()):
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
            if os.path.isfile(f): # if only a real file
                text += '#----------------------------------------------------------------------------\n'
                text += '# License file: {}\n'.format(f)
                text += license_text(f)
                text += '\n'
    return text

#######################################################################
# Test script
#######################################################################
if __name__ == '__main__':
    # parse command line
    if (sys.argv[1] == '-s'):
        mode = 'selftest'
    elif (sys.argv[1] == '-c'):
        # extract copyright
        mode = "copyright"
        file = sys.argv[2]
    elif (sys.argv[1] == '-t'):
        # extract license text
        mode = "text"
        file = sys.argv[2]
    elif (sys.argv[1] == '-i'):
        # get license ID (mode=-1)
        mode = "id"
        file = sys.argv[2]
    else:
        mode = "parse"
        if sys.argv[1] == '--':
            file = sys.argv[2]
        else:
            file = sys.argv[1]
    # main routine
    if mode == 'selftest':
        print ("self-test: copyright.py")
        print ("-- copyright:")
        print(copyright('foo', {'LICENSE*', 'COPYRIGHT'}, [], ['xml1.file', 'xml2.file'], ['binary1.file', 'binary2.file'], ['huge.file1', 'huge.file2']))
        (copyright_data, license_lines) = check_lines(['#!/bin/sh', '# COPYRIGHT (C) 2015 FOO_BAR', '', '# this is license text 1', '#  this is 2nd line', '', 'REAL CODE'], 'filename')
        print ("-- copyright_data:")
        print (copyright_data)
        print ("-- license_lines:")
        print (license_lines)
        print ("-- analyze_copyright:")
        print(analyze_copyright(["1987-90 FOO bar","boo foo wooo 2001-12", "1994, 1995, 1996, 1997, 1998, 1999, 2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009  Free Software Foundation, Inc." ]))
        print ("-- Free Software Foundation, Inc.:")
        X = 'Free Software Foundation, Inc. HHHHHHH'
        print(parse_name(X))
    else:
        with open(file, 'r') as fd:
            lines = fd.readlines()
            while(lines[0][:5] == '#%#%#'):
                # Skip header lines
                del lines[0]
            (copyright_data, license_lines) = check_lines(lines, file)
        copyright_lines = ''
        for name, (year_min, year_max) in sorted(dict.items(copyright_data)):
            if year_max == 0: # not found
                copyright_lines += '{}\n'.format(name)
            elif year_min == year_max:
                copyright_lines += '{} {}\n'.format(year_min, name)
            else:
                copyright_lines += '{}-{} {}\n'.format(year_min, year_max, name)
    if mode == 'copyright':
        print(copyright_lines)
    if mode == 'text':
        print('\n'.join(license_lines))
    if mode == 'id':
        norm_text = debmake.lc.normalize(license_lines)
        (licenseid, text) = debmake.lc.lc(norm_text, license_lines, -1)
        print(licenseid)
    if mode == 'parse':
        norm_text = debmake.lc.normalize(license_lines)
        (licenseid, text) = debmake.lc.lc(norm_text, license_lines, -2)
        print('== file ==')
        print(file)
        print('== copyright ==')
        print(copyright_lines, end='')
        print('== ID ==')
        print(licenseid)
        print('== license_lines ==', end='')
        print(text)
        print() # empty line

