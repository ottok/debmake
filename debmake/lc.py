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
import re
import os

#########################################################################################
# This script referenced the devscripts: licensecheck (version  2.14.1)
# There is no line-by-line match
# Here, mostly non-greedy regular expressions are used after pre-compiled.
#########################################################################################
# ( (license_name), (compiled_regular_expression), [(variable_list)])
re_main = [
# LGPL
    ('LGPL', re.compile(r'is (free software.? you can redistribute it and/or modify it|licensed) under the terms of (version (?P<version>[^ ]+) of )?the (GNU (Library |Lesser )General Public License|LGPL)', re.IGNORECASE), ['version']),
# AGPL
    ('AGPL', re.compile(r'is (free software.? you can redistribute it and/or modify it|licensed) under the terms of the (GNU Affero General Public License|AGPL)', re.IGNORECASE), []),
# standard: GPL 2.0+/3.0+
    ('GPL', re.compile(r'is (free software.? you (can|may) redistribute it and/or modify it|licensed) under the terms of the GNU (General Public License|GPL) as published by the Free Software Foundation.? either version (?P<version>\d+(?:\.\d+)?) of the License.? or \(at your option\) any (?P<later>later version)'), ['version','later']),
# Kernel: GPL 2.0 only
    ('GPL', re.compile(r'is (free software.? you (can|may) redistribute it and/or modify it|licensed) under the terms of the GNU (General Public License|GPL) version (?P<version>\d+(?:\.\d+)?) as published by the Free Software Foundation\.'), ['version']),
# licensecheck: GPL simplified
    ('GPL', re.compile(r'version (?P<version>\d+(?:\.\d+)?)[.,]? (?:\(?only\)?.? )?(?:of the (?:GNU General Public License |GPL )?(as )?published by the Free Software Foundation)', re.IGNORECASE), ['version']),
    ('GPL', re.compile(r'GNU General Public License(?: (?:as )?published by the Free Software Foundation).? version (?P<version>\d+(?:\.\d+)?)[.,]? ', re.IGNORECASE), ['version']),
    ('GPL', re.compile(r'is distributed under the terms of the (?:GNU General Public License|GPL),', re.IGNORECASE),[]),
    ('QPL', re.compile(r'(?P<toolkit>This file is part of the .*Qt GUI Toolkit. This file )?may be distributed under the terms of the Q Public License as defined', re.IGNORECASE), ['toolkit']),
    ('MIT/X11 (BSD like)', re.compile(r'opensource\.org/licenses/mit-license\.php', re.IGNORECASE), []),
    ('MIT', re.compile(r'Permission is hereby granted, free of charge, to any person obtaining a copy of this software and(/or)? associated documentation files \(the (Software|Materials)\), to deal in the (Software|Materials)', re.IGNORECASE), []),
    ('MIT/X11 (BSD like)', re.compile(r'Permission is hereby granted, without written agreement and without license or royalty fees, to use, copy, modify, and distribute this software and its documentation for any purpose', re.IGNORECASE), []),
    ('ISC', re.compile(r'Permission to use, copy, modify, and(/or)? distribute this software for any purpose with or without fee is hereby granted, provided.*copyright notice.*permission notice.*all copies', re.IGNORECASE), []),
    ('BSD-4-Clause', re.compile(r'All advertising materials mentioning features or use of this software must display the following acknowledge?ment.*This product includes software developed by.*THIS SOFTWARE IS PROVIDED .*AS IS AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY', re.IGNORECASE), []),
    ('BSD-3-Clause', re.compile(r'(The name .*? may not|Neither the names? .*? nor the names of (its|their) contributors may) be used to endorse or promote products derived from this software.*THIS SOFTWARE IS PROVIDED .*AS IS AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY', re.IGNORECASE), []),
    ('BSD-2-Clause', re.compile(r'Redistributions of source code must retain the above copyright notice.*THIS SOFTWARE IS PROVIDED .*AS IS AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY', re.IGNORECASE), []),
    ('BSD', re.compile(r'THIS SOFTWARE IS PROVIDED .*AS IS AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY', re.IGNORECASE), []),
    ('MPL', re.compile(r'Mozilla Public License Version (?P<version>[^ ]+)', re.IGNORECASE), ['version']),
    ('Artistic', re.compile(r'Released under the terms of the Artistic License (?P<version>[^ ]+)', re.IGNORECASE), ['version']),
    ('Artistic', re.compile(r'is free software.*under .*the Artistic license', re.IGNORECASE), []),
    ('Perl', re.compile(r'This program is free software; you can redistribute it and/or modify it under the same terms as Perl itself', re.IGNORECASE), []),
    ('Apache', re.compile(r'under the Apache License, Version (?P<version>[^ ]+)', re.IGNORECASE), ['version']),
    ('Beerware', re.compile(r'(THE BEER-WARE LICENSE)', re.IGNORECASE), []),
    ('PHP', re.compile(r'This source file is subject to version (?P<version>[^ ]+) of the PHP license', re.IGNORECASE), ['version']),
    ('CeCILL', re.compile(r'under the terms of the CeCILL ', re.IGNORECASE), []),
    ('CeCILL', re.compile(r'under the terms of the CeCILL-(?P<version>[^ ]+) ', re.IGNORECASE), ['version']),
    ('SGI Free Software License B', re.compile(r'under the SGI Free Software License B', re.IGNORECASE), []),
    ('Public domain', re.compile(r'is in the public domain', re.IGNORECASE), []),
    ('CDDL', re.compile(r'terms of the Common Development and Distribution License(, Version (?P<version>[^(]+))? \(the License\)', re.IGNORECASE), ['version']),
    ('Ms-PL', re.compile(r'Microsoft Permissive License \(Ms-PL\)', re.IGNORECASE), []),
    ('BSL', re.compile(r'Permission is hereby granted, free of charge, to any person or organization obtaining a copy of the software and accompanying documentation covered by this license \(the "Software"\)', re.IGNORECASE), []),
    ('BSL', re.compile(r'Boost Software License([ ,-]+Version (?P<version>[^ ]+)?(\.))', re.IGNORECASE), ['version']),
    ('PSF', re.compile(r'PYTHON SOFTWARE FOUNDATION LICENSE (VERSION (?P<version>[^ ]+))', re.IGNORECASE), ['version']),
    ('zlib/libpng', re.compile(r'The origin of this software must not be misrepresented.*Altered source versions must be plainly marked as such.*This notice may not be removed or altered from any source distribution', re.IGNORECASE), []),
    ('zlib/libpng', re.compile(r'see copyright notice in zlib\.h', re.IGNORECASE), []),
    ('libpng', re.compile(r'This code is released under the libpng license', re.IGNORECASE), []),
    ('WTFPL', re.compile(r'Do What The Fuck You Want To Public License(, Version (?P<version>[^, ]+))?', re.IGNORECASE), ['version']),
    ('WTFPL', re.compile(r'(License WTFPL|Under (the|a) WTFPL)', re.IGNORECASE), []),
    ('FSF-MIT-like', re.compile(r'free software.? the Free Software Foundation gives unlimited permission to copy and/or distribute it, with or without modifications, as long as this notice is preserved.', re.IGNORECASE), []),
    ('UNKNOWN', re.compile(r'.', re.IGNORECASE), []), # always true
    ]

re_misc = [
    (' (GENERATED FILE)', re.compile(r'(All changes made in this file will be lost|DO NOT (EDIT|delete this file)|Generated (automatically|by|from)|generated.*file)', re.IGNORECASE)),
    (' (with incorrect FSF address)', re.compile(r'(?:675 Mass Ave|59 Temple Place|51 Franklin Steet|02139|02111-1307)', re.IGNORECASE)),
    ]

# remove quotation marks
re_quotes = re.compile(r'(?:"|`|‘|’|“|”|' + r"')")
#########################################################################################
def checklicense(text):
    text = re_quotes.sub('',text)
    license = ''
    version = ''
    suffix = ''
    i = ''
    for i, (license, regex, vars) in enumerate(re_main):
        r =regex.search(text)
        if r:
            for v in vars:
                if v == 'version':
                    if r.group('version'):
                        version = '-' + r.group('version')
                if v == 'later':
                    if r.group('later'):
                        suffix = '+'
            break
    try:
        DEBUG = os.environ["DEBUG"]
    except KeyError:
        pass
    else:
        if 't' in DEBUG:
            print('== {}:{}'.format(i, text))
    misc = ''
    for (t, regex) in re_misc:
        r =regex.search(text)
        if r:
            misc += t
    return (license + version + suffix + misc)

#########################################################################################
if __name__ == '__main__':
    import sys
    with open(sys.argv[1], 'r') as f:
        text = f.read()
    text = ' '.join(text.split())
    print(checklicense(text))
