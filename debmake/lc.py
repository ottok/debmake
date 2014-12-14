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
###############################################################################
# The regex of devscripts: licensecheck (version  2.14.1) was referenced.
# 85 characters needed for
#     "the Apache Group for use in the Apache HTTP server project
#      (http://www.apache.org/)"
###############################################################################
LMAX = 1200 # max junk text (head and tail)
# order rules by specific to generic
list_main = [] # main rule list = [(name, regex, [variable, ...]), ...]
list_sub = []  # substring rule list for debug
###############################################################################
re_drop = re.compile(r'("|`|‘|’|“|”|&apos;|' + r"')", re.IGNORECASE)
re_connect = re.compile(r'- ', re.IGNORECASE)
def pattern(text, tail=' '):
    text = re_drop.sub('',text) # drop quotation marks
    text = ' '.join(text.split()) # normalize white space(s) 
    text = re_connect.sub('', text) + tail # connect words
    return text # pattern normally ends with ' '
def eval_sub(sub):
    rtext = eval(sub)
    if rtext[-3:] == ' )?':
       rtext = rtext[:-1]
    return rtext # drop "?" for vanishable "(.... )?" patterns
# non greedy
rhead0=r'^(?P<head>.{0,' + '{}'.format(LMAX) + r'}?)'
rtail0=r'(?P<tail>.{0,'  + '{}'.format(LMAX) + r'}?)$'
def regex(reg, rhead=rhead0, rtail=rtail0):
    return re.compile(rhead + reg + rtail, re.IGNORECASE)
###############################################################################
# BSD Exact
###############################################################################
list_sub += ['r_BSD0']
r_BSD0 = pattern(r'''
    Redistribution and use in source and binary forms, with or without
    modification, are permitted provided that the following conditions are met:
    ''')
list_sub += ['r_BSD1']
r_BSD1 = pattern(r'''
    (?:..? )?Redistributions of source code must retain the above copyright
    notice, this list of conditions and the following disclaimer\.
    ''')
list_sub += ['r_BSD2']
r_BSD2 = pattern(r'''
    (?:..? )?Redistributions in binary form must reproduce the above copyright
    notice, this list of conditions and the following disclaimer in the
    documentation and/ or other materials provided with the distribution\.
    ''')
list_sub += ['r_BSD3']
r_BSD3 = pattern(r'''
    (?P<bsd3>(?:..? )?All advertising materials mentioning features or use of
    this software must display the following acknowledgement: This product
    includes software developed by .{2,85}\. )?
    ''', tail='')
list_sub += ['r_BSD4']
r_BSD4 = pattern(r'''
    (?P<noendorse>(?:..? )?Neither the name of .{2,85} nor the names of its
    contributors may be used to endorse or promote products derived from this
    software without specific prior written permission\. )?
    ''', tail='')
list_sub += ['r_BSDW']
r_BSDW = pattern(r'''
    (?P<nowarranty>THIS SOFTWARE IS PROVIDED BY (?P<name>.{2,85})
    &apos;&apos;AS IS&apos;&apos; AND ANY EXPRESS OR IMPLIED WARRANTIES,
    INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY
    AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL
    .{2,85} BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
    OR CONSEQUENTIAL DAMAGES \(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
    SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
    INTERRUPTION\) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
    CONTRACT, STRICT LIABILITY, OR TORT \(INCLUDING NEGLIGENCE OR OTHERWISE\)
    ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
    POSSIBILITY OF SUCH DAMAGE\. )?
    ''', tail='')
### BSD {2,3,4}-clause
list_main += [('BSD', 'EXACT', regex(r_BSD0 + r_BSD1 + r_BSD2 + r_BSD3 + r_BSD4 +
    r_BSDW[:-1]), ['bsd3', 'name', 'noendorse', 'nowarranty',
    'head', 'tail'])]
###############################################################################
# BSD Generic
###############################################################################
# list 'bsd3' before 'name'
list_sub += ['r_BSD0G']
r_BSD0G = pattern(r'''
    Redistribution and use in source and binary forms, with or without
    modification, are permitted(?P<subject> \(subject to the limitations in the
    disclaimer below\))? provided that the following conditions are met[:.]
    ''')
list_sub += ['r_BSD1G']
r_BSD1G = pattern(r'''
    (?:..? )?Redistributions of source code must retain the above copyright
    notice, this list of conditions,? and the following disclaimer\.
    ''') # ,? for XFREE86 1.1
list_sub += ['r_BSD2G']
r_BSD2G = pattern(r'''
    (?:..? )?Redistributions in binary form must reproduce the above copyright
    notice, this list of conditions and the following disclaimer in the
    documentation and(?:/ ?or)? other materials provided with the
    distribution(?:\.|, and in the same place and form as other copyright,
    license and disclaimer information\.)
    ''') # XFree86 1.1 has the last phrase
list_sub += ['r_BSD3G']
r_BSD3G = pattern(r'''
    (?P<bsd3>(?:..? )?All advertising materials mentioning features or use of
    this software must display the following acknowledge?ment. This product
    includes software developed by .{2,85}\. )?
    ''', tail='')
    # dropping "e" as variant
list_sub += ['r_BSD4G']
r_BSD4G = pattern(r'''
    (?P<noendorse>(?:..? |and that )?(?:Except as contained in this notice,
    )?.{2,85} be used (?:to endorse or promote products derived from|in
    advertising or (?:publicity pertaining to distribution of|otherwise to
    promote the sale, use or other dealings in)) (?:this|the)
    software without (?:specific,? )?(?:prior written|written prior)
    (?:permission|authorization)(?: from .{2,85}| of .{2,85})?\. )?
    ''', tail='') # Some XFree86 variant has leading clarification with shall
list_sub += ['r_BSDWG']
r_BSDWG = pattern(r'''
    (?P<nowarranty>(?P<patent>NO EXPRESS(?:ED)? OR IMPLIED LICENSES TO ANY
    PARTYS PATENT RIGHTS ARE GRANTED BY THIS LICENSE. )?THIS SOFTWARE IS
    PROVIDED(?: BY (?P<name>.{2,85}))?  AS.IS AND ANY EXPRESS(?:ED)? OR IMPLIED
    (?:WARANTY\.|WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
    WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
    DISCLAIMED. IN NO EVENT SHALL .{2,85} BE LIABLE FOR ANY DIRECT, INDIRECT,
    INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES \(INCLUDING, BUT
    NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
    DATA, OR PROFITS; OR BUSINESS INTERRUPTION\) HOWEVER CAUSED AND ON ANY
    THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
    \(INCLUDING NEGLIGENCE OR OTHERWISE\) ARISING IN ANY WAY OUT OF THE USE OF
    THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE\.) )?
    ''', tail='') # "EXPRESSED" is what XFREE86 1.1 uses. BSD uses "EXPRESS"
### BSD {2,3,4}-clause
list_main += [('BSD', 'GENERIC', regex(r_BSD0G + r_BSD1G + r_BSD2G + r_BSD3G + r_BSD4G +
    r_BSDWG[:-1]), ['bsd3', 'name', 'subject', 'noendorse', 'nowarranty', 'patent',
    'head', 'tail'])]
###############################################################################
# Apache family (BSD0, BSD1, BSD2 are the same one)
###############################################################################
list_sub += ['r_Apache3'] # BSD3 alternative
r_Apache3 = pattern(r'''
    (?:..? )?The end-user documentation included with the redistribution, if
    any, must include the following acknowledgment: This product includes
    software developed by .{2,85}\. Alternately, this acknowledgment
    may appear in the software itself, if and wherever such third-party
    acknowledgments normally appear.
    ''')
list_sub += ['r_Apache4'] # BSD4 alternative
r_Apache4 = pattern(r'''
    (?:..? )?The names? .{2,85} must not be used to endorse or promote products
    derived from this software without prior written permission.  For written
    permission, please contact .{2,85}.
    ''')
list_sub += ['r_Apache5'] # trade mark restriction
r_Apache5 = pattern(r'''
    (?:..? )?Products derived from this software may not be called .{3,12},?
    nor may .{3,12} appear in their name. without prior written permission of
    .{2,85}\.
    ''')
list_sub += ['r_Apache6'] # BSD3 alternative
r_Apache6 = pattern(r'''
    (?:..? )?Redistributions of any form whatsoever must retain the following
    acknowledgment: This product includes software developed by .{2,85} for use
    in .{2,85}\.
    ''')
### Apache 1.0
list_main += [('Apache-1.0', 'EXACT', regex(r_BSD0G + r_BSD1G + r_BSD2G + r_BSD3G +
    r_Apache4 + r_Apache5 + r_Apache6 + r_BSDWG[:-1]), ['bsd3', 'name', 
    'subject', 'nowarranty', 'patent', 'head', 'tail'])]
### Apache 1.1
list_main += [('Apache-1.1', 'EXACT', regex(r_BSD0G + r_BSD1G + r_BSD2G + r_Apache3 +
    r_Apache4 + r_Apache5 + r_BSDWG[:-1]), ['name', 'subject', 'nowarranty',
    'patent', 'head', 'tail'])]
###############################################################################
# MIT=Expat: Exact
###############################################################################
list_sub += ['r_pemission_expat']
r_pemission_expat = pattern(r'''
    Permission is hereby granted, free of charge, to any person obtaining a
    copy of this software and associated documentation files \(the Software\),
    to deal in the Software without restriction, including without limitation
    the rights to use, copy, modify, merge, publish, distribute, sublicense,
    and/or sell copies of the Software, and to permit persons to whom the
    Software is furnished to do so, subject to the following conditions:
    ''')
list_sub += ['r_notice_expat']
r_notice_expat = pattern(r'''
    The above copyright notice and this permission notice shall be included in
    all copies or substantial portions of the Software.
    ''')
list_sub += ['r_disclaimer_expat']
r_disclaimer_expat = pattern(r'''
    (?P<nowarranty>THE SOFTWARE IS PROVIDED AS IS, WITHOUT WARRANTY OF ANY
    KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
    MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN
    NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
    OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE
    USE OR OTHER DEALINGS IN THE SOFTWARE. )
    ''', tail='')
### Expat
list_main += [('MIT', 'Expat', regex(r_pemission_expat + r_notice_expat + r_disclaimer_expat),
    ['head', 'tail', 'nowarranty'])]
###############################################################################
# MIT: Generic (trained with xorg source data)
###############################################################################
# Expat variants = r_pemission_expat with variants
list_sub += ['r_pemission_expatG']
r_pemission_expatG = pattern(r'''
    Permission is hereby granted, free of charge, to any person obtaining a
    copy of this software and associated documentation files \(the
    (?:Software|Materials)\), to deal in the Software without restriction,
    including without limitation(?: on)? the rights to use, copy, modify,
    (?:merge, )?(?:publish, )?distribute, (?:sub ?license, )?and(?:/ ?or)? sell
    copies of the Software[,.:](?: and to permit persons to whom the Software
    is furnished to do so(?:[,:]|, subject to the following conditions[.:]|,
    provided that))?
    ''')
# Expat variants = r_notice_expat with variants
list_sub += ['r_notice_expatG']
r_notice_expatG = pattern(r'''
    The above copyright notice(?:|s|\(s\)) and this permission notice
    (?P<requiredisclaimer>\(including the next paragraph\) )?(?:shall be
    included|appear) in all copies(?: or substantial portions)?(?: of the
    Software)?(?: and that both the above copyright notice(?:|s|\(s\)) and this
    permission notice appear in supporting documentation)?.
    ''')
# Expat variants = r_disclaimer_expat with variants
list_sub += ['r_disclaimer_expatG']
r_disclaimer_expatG = pattern(r'''
    (?P<nowarranty>THE SOFTWARE IS PROVIDED AS IS, WITHOUT WARRANTY OF ANY
    KIND, EXPRESS(?:ED)? OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
    WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
    NON-?INFRINGEMENT(?: OF THIRD PARTY RIGHTS)?. IN NO EVENT SHALL .{2,85} BE
    LIABLE FOR ANY CLAIM,(?: OR ANY SPECIAL INDIRECT OR CONSEQUENTIAL DAMAGES,
    OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS|
    DAMAGES,?(?: INCLUDING, BUT NOT LIMITED TO CONSEQUENTIAL OR INCIDENTAL
    DAMAGES,)? OR OTHER LIABILITY), WHETHER IN AN ACTION OF CONTRACT, (?:TORT
    OR OTHERWISE|NEGLIGENCE OR OTHER TORTIOUS ACTION), ARISING( FROM,)? OUT OF
    OR IN CONNECTION WITH(?: THE SOFTWARE OR)? THE USE OR (?:OTHER DEALINGS IN
    THE|PERFORMANCE OF THIS) SOFTWARE. )?
    ''', tail='')
# noendorse (=BSD4) is not used in Expat but used in many old MIT licenses
# MIT Xorg variants with warranty
list_main += [('MIT', 'GENERIC', regex(r_pemission_expatG + r_notice_expatG +
    r_disclaimer_expatG[:-1] + r_BSD4G), ['requiredisclaimer', 'nowarranty',
    'noendorse', 'head', 'tail']), ]
###############################################################################
# ISC: Exact
###############################################################################
list_sub += ['r_pemission_isc']
r_pemission_isc = pattern(r'''
    Permission to use, copy, modify, and/or distribute this software for any
    purpose with or without fee is hereby granted,
    ''')
list_sub += ['r_notice_isc']
r_notice_isc = pattern(r'''
    provided that the above copyright notice and this permission notice appear
    in all copies.
    ''')
list_sub += ['r_disclaimer_isc']
r_disclaimer_isc = pattern(r'''
    (?P<nowarranty>THE SOFTWARE IS PROVIDED AS IS AND ISC DISCLAIMS ALL
    WARRANTIES WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
    MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL (?P<name>.{2,85}) BE LIABLE
    FOR ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
    WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
    ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR
    IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE. )
    ''', tail='')
### ISC
list_main += [('ISC', 'EXACT', regex(r_pemission_isc + r_notice_isc + r_disclaimer_isc),
    ['head', 'tail', 'nowarranty', 'name'])]
###############################################################################
# ISC: Generic
###############################################################################
list_sub += ['r_pemission_iscG']
r_pemission_iscG = pattern(r'''
    Permission to use, copy, modify, (:?and(?:/ ?or)? distribute |distribute,
    and(?:/ ?or)? (?:sell|sublicense) )this software (:?and its documentation )?for any
    purpose (:?is hereby granted without fee,|(?:and )?(?:with or )?without fee
    is hereby granted,)
    ''')
list_sub += ['r_notice_iscG']
r_notice_iscG = pattern(r'''
    provided that the above copyright notices?(?: and this permission notice)?
    appear in all copies(:? and that both (?:that|those) copyright notices? and this
    permission notice appear in supporting documentation)?[.,]?
    ''')
list_sub += ['r_disclaimer_iscG']
r_disclaimer_iscG = pattern(r'''
    (?:No trademark license .{2,200} is hereby granted\. .{50,1000} is made\.
    )?(?:.{2,85} MAKES? NO REPRESENTATIONS .{2,80} FOR ANY PURPOSE\. 
    )?(?P<nowarranty>(?:.{2,85} make(?:|S|\(S\)) (?:no|any) representations?
    about the suitability of this software for any purpose. )?(?:(?:It|THE
    SOFTWARE) is provided as is and )?(?:.{2,85} DISCLAIM(?:|S|\(S\)) ALL
    WARRANTIES WITH REGARD TO THIS SOFTWARE,? INCLUDING ALL IMPLIED WARRANTIES
    OF MERCHANTABILITY AND FITNESS[,.] IN NO EVENT SHALL .{2,85} BE LIABLE FOR
    ANY SPECIAL,(?: DIRECT,)? INDIRECT,? OR CONSEQUENTIAL DAMAGES OR ANY
    DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN
    AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
    OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE\.|(?:It|THE
    SOFTWARE) is provided as is without express or implied warranty\.) )?
    ''', tail='') # First 2 are for Adobe Display PostScript
r_disclaimer_iscGx = pattern(r'''
    (?P<nowarranty>(?:.{2,85} make(?:|S|\(S\)) (?:no|any) representations?
    about the suitability of this software for any purpose. 
    )?(?:It|THE SOFTWARE) is provided as is(?: without express or
    implied warranty\.| 
    and .{2,85} DISCLAIM(?:|S|\(S\)) ALL WARRANTIES WITH REGARD TO THIS
    SOFTWARE,? INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND
    FITNESS[,.] IN NO EVENT SHALL .{2,85} BE LIABLE FOR ANY SPECIAL,(?:
    DIRECT,)? INDIRECT,? OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER
    RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF
    CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN
    CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.) )?
    ''', tail='')
# ISC variants with no-endorse in the middle
list_main += [('ISC', 'VARIANT_1', regex(r_pemission_iscG + r_notice_iscG +
    r_BSD4G + r_disclaimer_iscG[:-1]), ['nowarranty', 'noendorse', 'head', 'tail']), ]
# ISC variants with no-endorse at the end
list_main += [('ISC', 'VARIANT_2', regex(r_pemission_iscG + r_notice_iscG + r_notice_expatG +
    r_disclaimer_expatG[:-1] + r_BSD4G ), ['nowarranty', 'noendorse', 'head', 'tail']), ]
###############################################################################
# Zlib: Exact
###############################################################################
list_sub += ['r_disclaimer_zlib']
r_disclaimer_zlib = pattern(r'''
    (?P<nowarranty>This software is provided as.is, without any express or
    implied warranty. In no event will the authors be held liable for any
    damages arising from the use of this software. )
    ''', tail='')
list_sub += ['r_permission_zlib']
r_permission_zlib = pattern(r'''
    Permission is granted to anyone to use this software for any purpose,
    including commercial applications, and to alter it and redistribute it
    freely, subject to the following restrictions[:]
    ''')
list_sub += ['r_notice_zlib']
r_notice_zlib = pattern(r'''
    (?:..? )?The origin of this software must not be misrepresented; you must
    not claim that you wrote the original software. If you use this software in
    a product, an acknowledgment in the product documentation would be
    appreciated but is not required.
    (?:..? )?Altered source versions must be plainly marked as such, and must
    not be misrepresented as being the original software.
    (?:..? )?This notice may not be removed or altered from any source
    distribution.
    ''')
### Zlib
list_main += [('Zlib', 'EXACT', regex(r_disclaimer_zlib + r_permission_zlib + r_notice_zlib),
    ['phead', 'tail', 'nowarranty'])]
###############################################################################
# DEC
###############################################################################
list_sub += ['r_permission_dec']
r_permission_dec = pattern(r'''
    This software is furnished under license and may be used and copied only in
    accordance with the following terms and conditions. Subject to these
    conditions, you may download, copy, install, use, modify and distribute
    this software in source and(?:/ ?or)? binary form. No title or ownership is
    transferred hereby.
    ''')
list_sub += ['r_notice_dec']
r_notice_dec = pattern(r'''
    (?:..? )?Any source code used, modified or distributed must reproduce and
    retain this copyright notice and list of conditions as they appear in the
    source file.
    ''')
list_sub += ['r_noendorse_dec']
r_noendorse_dec = pattern(r'''
    (?P<noendorse>(?:..? )?No right is granted to use any trade name,
    trademark, or logo of .{2,85}. Neither .{2,85} name nor any trademark or
    logo of .{2,85} may be used to endorse or promote products derived from
    this software without the prior written permission of .{2,85}. )?
    ''', tail='')
list_sub += ['r_disclaimer_dec']
r_disclaimer_dec = pattern(r'''
    (?P<nowarranty>(?:..? )?This software is provided AS.IS and any express or
    implied warranties, including but not limited to, any implied warranties of
    merchantability, fitness for a particular purpose, or non-infringement are
    disclaimed.  In no event shall .{2,85} be liable for any damages
    whatsoever, and in particular, .{2,85} shall not be liable for special,
    indirect, consequential, or incidental damages or damages for lost profits,
    loss of revenue or loss of use, whether such damages arise in contract,
    negligence, tort, under statute, in equity, at law or otherwise, even if
    advised of the possibility of such damage. )?
    ''', tail='')
# MIT DEC variants with warranty
list_main += [('MIT', 'DEC', regex(r_permission_dec + r_notice_dec + r_noendorse_dec +
    r_disclaimer_dec[:-1]), ['nowarranty',
    'noendorse', 'head', 'tail']), ]
###############################################################################
# ISC/X11 hybrid with waranty
###############################################################################
list_sub += ['r_BSD3A'] # BSD3 alternative
r_BSD3A = pattern(r'''
    (?:..? )?The end-user documentation included with the redistribution, if
    any, must include the following acknowledgment: This product includes
    software developed by .{2,85}(?:, in the same place and form as other
    third-party acknowledgments)?\. Alternately, this acknowledgment may appear
    in the software itself, in the same form and location as other such
    third-party acknowledgments.
    ''')
list_main += [('MIT', 'XORG+BSD', regex(r_pemission_expatG + r_BSD1G +r_BSD2G +r_BSD3A
    + r_BSD4G + r_BSDWG[:-1] ), ['nowarranty', 'noendorse', 'head', 'tail']), ]
###############################################################################
# SGI
###############################################################################
list_sub += ['r_notice_sgi']
r_notice_sgi = pattern(r'''
    The above copyright notice including the dates of first publication and
    either this permission notice or a reference to
    http://oss.sgi.com/projects/FreeB/ shall be included in all copies or
    substantial portions of the Software.
    ''')
# SGI
list_main += [('SGI-B-2.0', 'EXACT', regex(r_pemission_expatG + r_notice_sgi +
    r_disclaimer_expatG[:-1] + r_BSD4G), ['nowarranty',
    'noendorse', 'head', 'tail']), ]
###############################################################################
# Mozilla
###############################################################################
r_MPL1 = pattern(r'''
    The contents of this file are subject to the Mozilla Public License Version
    (?P<version>\d+(?:\.\d+)?) \(the License\); you may not use this file
    except in compliance with the License. You may obtain a copy of the License
    at http://www.mozilla.org/MPL/ Software distributed under the License is
    distributed on an AS IS basis, WITHOUT WARRANTY OF ANY KIND, either express
    or implied. See the License for the specific language governing rights and
    limitations under the License.
    ''')
r_MPL2 = pattern(r'''
    This Source Code Form is subject to the terms of the Mozilla Public
    License, v. (?P<version>\d+(?:\.\d+)?). If a copy of the MPL was not
    distributed with this file, You can obtain one at
    http://mozilla.org/MPL/(?:\d+(?:\.\d+)?)/.(?P<incompatible> This Source
    Code Form is Incompatible With Secondary Licenses, as defined by the
    Mozilla Public License, v. (?:\d+(?:\.\d+)?).)?
    ''')
list_main += [('MPL', 'VARIANT1', regex(r_MPL1), ['version'])]
list_main += [('MPL', 'VARIANT2', regex(r_MPL2), ['version', 'incompatible'])]
###############################################################################
# PERMISSIVE license from GNU releted sources
###############################################################################
# GNU All-Permissive License
r_PM0 = pattern(r'''
    Copying and distribution of this file, with or without modification, are
    permitted in any medium without royalty provided the copyright notice and
    this notice are preserved.(?P<nowarranty> This file is offered as.is,
    without (?:any warranty|warranty of any kind)?.)?
    ''')
# PERMISSIVE (aclocal.m4, libtool)
r_PM1 = pattern(r'''
    free software. (?:as a special exception )?the (Free Software
    Foundation|author|author\(s\)) gives unlimited permission to copy and(?:/ ?or)?
    distribute it, with or without modifications, as long as this notice is
    preserved.(?P<nowarranty> This (program|file) is distributed in the hope
    that it will be useful, but WITHOUT ANY WARRANTY, to the extent permitted
    by law; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
    A PARTICULAR PURPOSE.)?
    ''')
r_PM2 = pattern(r'''
    This file may be copied and used freely without restrictions.  It may be
    used in projects which are not available under a GNU Public License, but
    which still want to provide support for the GNU gettext functionality.
    ''')
r_PM3 = pattern(r'''
    This configure script is free software; the Free Software Foundation gives
    unlimited permission to copy, distribute and modify it.
    ''')
list_main += [('PERMISSIVE', 'VARIANT0', regex(r_PM0), ['nowarranty'])]
list_main += [('PERMISSIVE', 'VARIANT1', regex(r_PM1), ['nowarranty'])]
list_main += [('PERMISSIVE', 'VARIANT2', regex(r_PM2), [])]
list_main += [('PERMISSIVE', 'VARIANT3', regex(r_PM3), [])]
###############################################################################
# Reference to license name (Generic style)
###############################################################################
# Permission clause
# under the terms of the <GNU General Public License >
list_sub += ['r_under']
r_under = pattern(r'''
    (?:you (?:can|may) redistribute it and(?:/ ?or)? modify .{2,85} under
    |Permission(?: is granted)? to copy, distribute,? and(?:/ ?or)? modify this
        document under
    |Permission(?: is granted)? to use, copy, modify,? (?:merge, )?(?:publish,
        )?distribute,? (?:sublicense,? )and(?:/ ?or)? sell .{2,85} under
    |Permission(?: is granted)? to use, copy, modify,? (?:merge,?
        )?(?:publish,? )?and(?:/ ?or)? distribute .{2,85} under
    |.{2,85} (?:is|are) licensed under
    |distribute under
    |subject to
    |Released under
    |free software .{2,85} under )
    ''', tail='') + r'(?:the (?:terms of the )?)?'
###############################################################################
# GNU version
list_sub += ['r_version1']
r_version1 = pattern(r'''
    (?:(?:as )?published by the Free Software Foundation[,;:.]? 
    )?(?:either )?versions? 
    (?P<version>\d+(?:\.\d+)?)(?: of the License)?[,.]?(?: \(?only\)?\.? 
    | or (?:\(at your option\)? )?(?:any )?(?P<later>later)(?: versions?)?\.?|)
    (?:published by the Free Software Foundation[,;:.]? )?''', tail='')
    # wrong additional "s" is used in some software
    # GNU Free Documentation License, Version 1.1 or any later version published 
# XXXXX FIXME XXXXX r_version2 not tested
list_sub += ['r_version2']
r_version2 = pattern(r'''
    (?:either )?versions? 
    (?P<version>\d+(?:\.\d+)?)(?: of the License)?(?:\.| 
    \(?only\)\.?|, 
    or (?:\(at your option\) )?(?:any )?(?P<later>later)(?: versions?)?\.)?
    ''') + r'(?: of the\s)?'
    # wrong additional "s" is used in some software
###############################################################################
list_sub += ['r_LGPL']
r_LGPL = r'(?:GNU (?:Library|Lesser) General Public License|(?:GNU )?LGPL).? '
list_main += [('LGPL', 'VARIANT1', regex(r_under + r_LGPL + r_version1), ['head',
    'version', 'later', 'tail'])]
list_main += [ ('LGPL', 'VARIANT2', regex(r_under + r_version2 + r_LGPL), ['head',
    'version', 'later', 'tail'])]

list_sub += ['r_AGPL']
r_AGPL = r'(?:GNU Affero General Public License|(?:GNU )?AGPL).? '
list_main += [('AGPL', 'VARIANT1', regex(r_under + r_AGPL + r_version1), ['head',
    'version', 'later', 'tail'])]
list_main += [ ('AGPL', 'VARIANT2', regex(r_under + r_version2 + r_AGPL), ['head',
    'version', 'later', 'tail']) ]

list_sub += ['r_GFDL']
r_GFDL = r'(?:GNU Free Documentation License|(?:GNU )?GFDL|GNU FDL).? '
list_main += [ ('GFDL', 'VARIANT1', regex(r_under + r_GFDL + r_version1), ['head',
    'version', 'later', 'tail']), ]
list_main += [ ('GFDL', 'VARIANT2', regex(r_under + r_version2 + r_GFDL), ['head',
    'version', 'later', 'tail']), ]

list_sub += ['r_GPL']
r_GPL = r'(?:GNU General Public License|(?:GNU )?GPL).? '
list_main += [ ('GPL', 'VARIANT1', regex(r_under + r_GPL + r_version1), ['head',
    'version', 'later', 'tail']), ]
list_main += [ ('GPL', 'VARIANT2', regex(r_under + r_version2 + r_GPL), ['head',
    'version', 'later', 'tail']), ]

list_sub += ['r_MPL']
r_MPL = r'Mozilla Public License.? '
list_main += [ ('MPL', 'VARIANT1', regex(r_under + r_MPL + r_version1), ['head',
    'version', 'later', 'tail']), ]
list_main += [ ('MPL', 'VARIANT2', regex(r_under + r_version2 + r_MPL), ['head',
    'version', 'later', 'tail']), ]

list_sub += ['r_Artistic']
r_Artistic = r'Artistic License.? '
list_main += [ ('Artistic', 'VARIANT1', regex(r_under + r_Artistic + r_version1),
    ['head', 'version', 'later', 'tail']), ]
list_main += [ ('Artistic', 'VARIANT2', regex(r_under + r_version2 + r_Artistic),
    ['head', 'version', 'later', 'tail']), ]
###############################################################################
# Reference to the package license
###############################################################################
r_SM0 = pattern(r'''
    This file is distributed under the same license as .{5,40}\.
    ''')
list_main += [('_SAME_', 'VARIANT0', regex(r_SM0), [])]
###############################################################################
# Reference to license name (specific style)
###############################################################################
list_main += [
    ('Apache', 'EXTRA', regex(pattern(r'''
        (?:.{2,85} licenses? this file to you|licensed) under the Apache
        License, Version (?P<version>[^ ]+) \(the LICENSE\).
        ''')), ['version','head', 'tail']),
    ('QPL', 'EXTRA', regex(pattern(r'''
        (?P<toolkit>This file is part of the .*Qt GUI Toolkit.  This file )?may
        be distributed under the terms of the Q Public License as defined.
        ''')), ['toolkit', 'head', 'tail']),
    ('Perl', 'EXTRA', regex(pattern(r'''
        This program is free software; you can redistribute it and/or modify it
        under the same terms as Perl itself.
        ''')), []),
    ('Beerware', 'EXTRA', regex(r'\(THE BEER-WARE LICENSE\).' 
        ), []),
    ('PHP', 'EXTRA', regex(pattern(r'''
        This source file is subject to version (?P<version>[^ ]+) of the PHP
        license.
        ''')), ['version']),
    ('CeCILL', 'EXTRA', regex(pattern(r'''
        under the terms of the CeCILL(?:-(?P<version>[^ ]+))?.
        ''')), ['version']),
    ('SGI-B', 'EXTRA', regex(pattern(r'''
        (?:permitted in|under) the SGI Free Software License B, Version (?P<version>[^ ]+) \(the License\).
        ''')), ['version']),
    ('Public domain', 'EXTRA', regex(pattern(r'''
        is in the public domain.
        ''')), []),
    ('CDDL', 'EXTRA', regex(pattern(r''''
        terms of the Common Development and Distribution License (?:, Version
        (?P<version>[^ ]+)? \(the License\)).
        ''')), ['version']),
    ('Ms-PL', 'EXTRA', regex(pattern(r'''
        Microsoft Permissive License \(Ms-PL\).
        ''')), []),
    ('BSL', 'EXTRA', regex(pattern(r'''
        Distributed under the Boost Software License, Version (?P<version>[^ ]+)\.
        ''')), ['version']),
    ('PSF', 'EXTRA', regex(pattern(r'''
        PYTHON SOFTWARE FOUNDATION LICENSE (VERSION (?P<version>[^ ]+))?.
        ''')), ['version']),
    ('libpng', 'EXTRA', regex(pattern(r'''
        This code is released under the libpng license.
        ''')), []),
    ('APSL', 'EXTRA', regex(pattern(r'''
        subject to the Apple Public
        Source License Version (?P<version>[^ ]+) \(the License\).
        ''')), ['version']),
    ('LPPL', 'EXTRA', regex(pattern(r'''
        (?:under the conditions of the LaTeX Project Public License,
        |under the terms of the LaTeX Project Public License Distributed from
        CTAN archives in directory macros/latex/base/lppl.txt; )either 
        version (?P<version>[^ ]+) of (?:this|the) license,? or \(at your
        option\) any later version.
        ''')), ['version']),
    ('W3C', 'EXTRA', regex(pattern(r'''
        distributed under the W3C..? Software License in
        ''')), []), # W3C(R)
    ('WTFPL', 'EXTRA', regex(pattern(r'''
        Do What The Fuck You Want To Public License (?:, Version
        (?P<version>[^, ]+))?.
        ''')), ['version']),
    ('WTFPL', 'EXTRA', regex(pattern(r'''
        (?:License WTFPL|Under (?:the|a) WTFPL).
        ''')), []),
    ('__UNKNOWN__', '', regex(r'.*'), []), # always true
]
###############################################################################
# exception clause
###############################################################################
r_autoconf1 = pattern(r'''
    As a special exception to the GNU General Public License, if you distribute
    this file as part of a program that contains a configuration script
    generated by Autoconf, you may include it under the same distribution terms
    that you use for the rest of that program.''', tail='')
r_autoconf2 = pattern(r'''
    As a special exception to the GNU General Public License, if you
    distribute this file as part of a program that contains a
    configuration script generated by Autoconf, you may include it under
    the same distribution terms that you use for the rest of that
    program.  This Exception is an additional permission under section 7
    of the GNU General Public License, version 3 \(.?GPLv3.?\).''', tail='')
r_autoconf3 = pattern(r'''
    As a special exception to the GNU General Public License,
    this file may be distributed as part of a program that
    contains a configuration script generated by Autoconf, under
    the same distribution terms as the rest of that program.''', tail='')
r_autoconf4 = pattern(r'''
    Additional permission under section 7 of the GNU General Public License,
    version 3 \(.?GPLv3.?\): If you convey this file as part of a work that
    contains a configuration script generated by Autoconf, you may do so under
    terms of your choice.''', tail='')
r_libtool = pattern(r'''
    As a special exception to the GNU General Public License, if you distribute
    this file as part of a program or library that is built using GNU Libtool,
    you may include this file under the same distribution terms that you use
    for the rest of that program.''', tail='')
r_bison = pattern(r'''
    As a special exception, you may create a larger work that contains part or
    all of the Bison parser skeleton and distribute that work under terms of
    your choice, so long as that work isn.t itself a parser generator
    using the skeleton or a modified version thereof as a parser skeleton.
    Alternatively, if you modify or redistribute the parser skeleton itself,
    you may \(at your option\) remove this special exception, which will cause
    the skeleton and the resulting Bison output files to be licensed under the
    GNU General Public License without this special exception.''', tail='')
r_font = pattern(r'''
    As a special exception, if you create a document which uses this font, and
    embed this font or unaltered portions of this font into the document, this
    font does not by itself cause the resulting document to be covered by the
    GNU General Public License. This exception does not however invalidate any
    other reasons why the document might be covered by the GNU General Public
    License. If you modify this font, you may extend this exception to your
    version of the font, but you are not obligated to do so. If you do not wish
    to do so, delete this exception statement from your version.''', tail='')
list_exceptions = [
    ('autoconf', regex(r_autoconf1), True),
    ('autoconf', regex(r_autoconf2), True),
    ('autoconf', regex(r_autoconf3), True),
    ('autoconf', regex(r_autoconf4), True),
    ('libtool', regex(r_libtool), True),
    ('bison', regex(r_bison), True),
    ('font', regex(r_font), False),
]
regex_exception = regex(r'exception')
list_attribs = [
    ('The FSF address in the above text is the old one.', 
    regex(r'(?:675 Mass Ave|59 Temple Place|51 Franklin Steet|02139|02111-1307)')),
]
list_permissive = [
    'PERMISSIVE',
    'MIT',
    'ISC',
    'Zlib',
    'BSD-2-Clause',
    'BSD-3-Clause',
]
###############################################################################
# GNU License text
# 300 BYTES:   Most license headers included in the source
# 10000 BYTES: Full license text for GPL like license
# "Definitions": not present in normal license headers
re_FULL = re.compile(r'definition', re.IGNORECASE)
size_FULL = 500
re_LICENSE_HEADER = regex(pattern(r'''
    Standard License Header COPYRIGHT'''), 
    rhead=r'^(?P<head>.*?)', rtail='(?P<tail>.*?)$')
re_LICENSE_AFFERO = regex(pattern(r'''
    software over a computer network.*Affero General Public License
    '''),
    rhead=r'^(?P<head>.*?)', rtail='(?P<tail>.*?)$')
re_LICENSE = regex(pattern(r'''
    (?:(?P<agpl>AFFERO GENERAL PUBLIC LICENSE.*)
    |(?P<gfdl>GNU Free Documentation License.*)
    |(?P<lgpl>GNU (?:Library|Lesser) General Public License.*)
    |(?P<gpl>GNU General Public License.*) )version 
    (?P<version>\d+(?:\.\d+)?),? o.*later'''), 
    rhead=r'^(?P<head>.*?)', rtail='(?P<tail>.*?)$')
###############################################################################
# license name: file name, licence full name
licensefiles = {
    'Apache-2.0'    : ('Apache-2.0','Apache License Version 2.0\n '),
    'Artistic'      : ('Artistic',  '"Artistic License"\n '),
    'BSD-3-Clause'  : ('BSD',       'BSD 3-clause "New" or "Revised"\n License'),
    'GFDL-1.2'      : ('GFDL-1.2',  'GNU Free Documentation License\n Version 1.2'),
    'GFDL-1.2+'     : ('GFDL-1.2',  'GNU Free Documentation License\n Version 1.2'),
    'GFDL-1.3'      : ('GFDL-1.3',  'GNU Free Documentation License\n Version 1.3'),
    'GFDL-1.3+'     : ('GFDL-1.3',  'GNU Free Documentation License\n Version 1.3'),
    'GPL-1.0'       : ('GPL-1',     'GNU General Public License\n Version 1'),
    'GPL-1.0+'      : ('GPL-1',     'GNU General Public License\n Version 1'),
    'GPL-2.0'       : ('GPL-2',     'GNU General Public License\n Version 2'),
    'GPL-2.0+'      : ('GPL-2',     'GNU General Public License\n Version 2'),
    'GPL-3.0'       : ('GPL-3',     'GNU General Public License\n Version 3'),
    'GPL-3.0+'      : ('GPL-3',     'GNU General Public License\n Version 3'),
    'LGPL-2.0'      : ('LGPL-2',    'GNU Library General Public License\n Version 2'),
    'LGPL-2.0+'     : ('LGPL-2',    'GNU Library General Public License\n Version 2'),
    'LGPL-2.1'      : ('LGPL-2.1',  'GNU Lesser General Public License\n Version 2.1'),
    'LGPL-2.1+'     : ('LGPL-2.1',  'GNU Lesser General Public License\n Version 2.1'),
    'LGPL-3.0'      : ('LGPL-3',    'GNU Lesser General Public License\n Version 3'),
    'LGPL-3.0+'     : ('LGPL-3',    'GNU Lesser General Public License\n Version 3')}
#########################################################################################
def normalize(license_lines):
    # normalize license to a single normalized line with single space
    license_data = []
    for line in license_lines:
        line = line.strip()
        license_data.extend(line.split())
    try:
        license_data.remove('') # remove empty words
    except ValueError:
        pass
    return pattern(' '.join(license_data))
#########################################################################################
def lc(norm_text, license_lines, mode):
    # norm_text: normalized license lines to be analized
    # license_lines: original license lines for output
    # mode: license check mode
    # mode = 0: mode for copyright file generation; same as mode == 2 for lc.py
    if mode == 0:
        mode = 2
    # abs(mode) = 1: mode for the license scan (1 line output; -c, -cccc)
    # abs(mode) = 2: mode for the license scan (mode = 1 + license text; -cc, -ccccc)
    # abs(mode) = 3: mode for the license scan (mode = 2 + comments; -ccc, -cccccc)
    # abs(mode) = 4: mode for the license scan (mode = 3 + match text; debug only)
    # mode < 0: add pattern index id (for -cccc, -ccccc, -cccccc)
    # return: text to be placed after "License: "
    # return: flag for permissive license
    #####################################################################################
    # 1st-line part
    license = '' # License type: GPL   BSD
    id = ''      # "FULL_LICENSE" or   ""
    version = '' #               3     -3-Clause
    suffix = ''  #               +     ""
    with_exception = ''   #  ' with ' + ... + ' exception'
    permissive = False
    # not in the 1st-line part
    set_exceptions = set() # add exceptions found in the copyright text
    set_attribs = set() # add attribute found in the copyright text
    set_subtypes = set() # add invisible subtype to the normal license type="license + id + version + suffix" such as "BSD-3-Clause"
    match_text = '' # mode == 4 used by debug
    if len(norm_text) == 0:
        license = '__NO_LICENSE_TEXT__'
        text = ''
    elif len(norm_text) > size_FULL and re_FULL.search(norm_text):
        # full license text (very rough guess)
        lh = re_LICENSE_HEADER.search(norm_text)
        la = re_LICENSE_AFFERO.search(norm_text)
        if la:
            license = 'AGPL'
            version =  '-1.0'
            suffix = '+'
            id = 'FULL_LICENSE'
        elif lh:
            norm_text = lh.group('tail').strip()
            #print('~~~>>> : {}'.format(norm_text))
            l = re_LICENSE.search(norm_text)
            if l:
                if l.group('agpl'):
                    license = 'AGPL'
                    version =  l.group('version')
                    id = 'FULL_LICENSE'
                elif l.group('lgpl'):
                    license = 'LGPL'
                    version =  l.group('version')
                    id = 'FULL_LICENSE'
                elif l.group('gfdl'):
                    license = 'GFDL'
                    version =  l.group('version')
                    id = 'FULL_LICENSE'
                elif l.group('gpl'):
                    license = 'GPL'
                    version =  l.group('version')
                    id = 'FULL_LICENSE'
                else:
                    license = '__TOO_LONG_TYPE1__'
                if (len(version) == 1) and (version in '1234567890'):
                    version = version + '.0'
                if version:
                    version = '-' + version
                    suffix = '+'
            else:
                license = '__TOO_LONG_TYPE2__'
        else:
            license = '__TOO_LONG_TYPE3__'
    else:
        if norm_text:
            for (license, id, regex, vars) in list_main:
                #print('>> {}:{}'.format(license, id))
                if license == 'BSD':
                    version = '-2-Clause'
                else:
                    version = ''
                r0 =regex.search(norm_text)
                if r0:
                    match_text = r0.group()
                    for v in vars:
                        try:
                            if v == 'version':
                                if r0.group(v):
                                    version = r0.group('version')
                                    if (len(version) == 1) and (version in '1234567890'):
                                        version = version + '.0'
                                    if version:
                                        version = '-' + version
                            elif v == 'later':
                                if r0.group(v):
                                    suffix = '+'
                            elif v == 'bsd3':
                                if r0.group(v):
                                    if license == 'BSD':
                                        version = '-4-Clause'
                            elif v == 'noendorse':
                                if license == 'BSD':
                                    if r0.group(v) and (version != '-4-Clause'):
                                        version = '-3-Clause'
                                elif license[:3] == 'MIT' or license[:3] == 'ISC': 
                                    # MIT variants with optional noendorse
                                    if r0.group(v):
                                        set_subtypes.update({'no-endorsement clause'})
                                else: # SGI-B, DEC incorporating BSD's no-endorsement clause
                                    if not r0.group(v):
                                        set_subtypes.update({'no-endorsement clause'})
                            elif v == 'incompatible':
                                if r0.group(v):
                                    set_subtypes.update({'copyleft incompatibility concern'})
                            elif v == 'nowarranty':
                                if not r0.group(v):
                                    set_subtypes.update({'nowarranty disclaimer'})
                            elif v == 'requiredisclaimer':
                                if r0.group(v):
                                    set_subtypes.update({'requiring nowarranty disclaimer'})
                            elif v == 'name':
                                if r0.group(v):
                                    name = r0.group('name')
                                    if name[4:11] == 'FREEBSD':
                                        suffix += '-FreeBSD'
                                    elif name[4:10] == 'NETBSD':
                                        suffix += '-NETBSD'
                                    elif name[4:11] == 'REGENTS':
                                        if version == '-4-Clause':
                                            suffix += '-UC'
                            elif v == 'patent' or v == 'subject':
                                if r0.group(v):
                                    suffix = '-Clear'
                            #elif v == 'name1':
                            #    if r0.group('name1'):
                            #        name3 = r0.group('name1')
                            #        suffix += '<1:' + name1 + '>'
                        except IndexError:
                            print('ERROR: {} missing: {} {}'.format(v, license, id))
                    # find only first match
                    break
            for (type_attribs, re_attribs) in list_attribs:
                r2 = re_attribs.search(norm_text)
                if r2:
                    set_attribs.update({type_attribs})
            # exception handling
            for (type_exceptions, re_exceptions, perm) in list_exceptions:
                r2 = re_exceptions.search(norm_text)
                if r2:
                    set_exceptions.update(type_exceptions)
                    permissive |= perm
            if len(set_exceptions) == 1:
                with_exception = ' with ' + set_exceptions.pop() + ' exception'
            elif len(set_exceptions) == 0:
                r2 = regex_exception.search(norm_text)
                if r2:
                    with_exception = ' with unknown exception XXX FIXME XXX'
            else:
                with_exception = ' with multiple exceptions XXX FIXME XXX'
            if with_exception == '':
                if license + version in list_permissive:
                    permissive = True
        else:
            license = '' # NO LICENSE TEXT
    if mode <= -1 and id !='':
        id = ':' + id
    else:
        id = ''
    licenseid = license + version + suffix + id + with_exception
    text = ''
    if abs(mode) >= 3: # output comments
        if set_subtypes:
            text += '\n### !!! C: {}'.format('\n### !!! C: '.join(list(set_subtypes)))
    if abs(mode) >= 2: # Skip if simple
        # RFC-822 complian and empty lines replaced with " ."
        for line in license_lines:
            line = line.rstrip()
            if line == '':
                text += '\n .'
            else:
                text += '\n {}'.format(line)
        if set_attribs:
            text += '\n .\n {}'.format('\n '.join(list(set_attribs)))
        if license + version + suffix in licensefiles.keys():
            (filename, licensename) = licensefiles[license + version + suffix]
            text += "\n .\n On Debian systems, the complete text of the " + licensename + \
                " can be found in `/usr/share/common-licenses/{}'.".format(filename)
    if abs(mode) >= 4: # output debug outputs
        if match_text:
            text += '\n### !!! M: {}'.format(match_text)
        if norm_text:
            text += '\n### !!! T: {}'.format(norm_text)
    return (licenseid, text, permissive)

#########################################################################################
def lc_sub(norm_text, mode):
    # check license for debug regex pattern
    # license_lines: license lines to be checked (list)
    # mode: license check mode
    # abs(mode) = 5 (single)
    # abs(mode) = 6 (combination)
    #####################################################################################
    text = ''
    for subx in list_sub:
        r = re.compile(eval_sub(subx), re.IGNORECASE)
        if r.search(norm_text):
            # match with regx
            text += '>>>>>>>> {} -> "{}"\n'.format(subx, r.search(norm_text).group())
            if abs(mode) >= 6:
                for suby in list_sub:
                    if subx != suby:
                        try:
                            r = re.compile(eval_sub(subx) + eval_sub(suby), re.IGNORECASE)
                            if r.search(norm_text):
                                # match with combination of subx + suby
                                text += '==== {} + {} => "{}"\n'.format(subx, suby, r.search(norm_text).group())
                        except:
                            pass
    return text
#########################################################################################
if __name__ == '__main__':
    import sys
    import os
    mode = 1
    argc = len(sys.argv)
    if argc == 1:
        print('Syntax: ' + argv[0] + ' [-][123456] file1 file2 ...')
    elif argc == 2:
        files = sys.argv[1:]
    elif argc >= 3:
        try:
            mode = int(sys.argv[1])
        except ValueError:
            files = sys.argv[1:]
        else:
            files = sys.argv[2:]
    else:
        print('lc.py file ...')
    for file in files:
        if os.path.isfile(file):
            with open(file, 'r') as f:
                license_lines = f.readlines()
            while(license_lines[0].strip() == ''):
                del license_lines[0]
            while(license_lines[-1].strip() == ''):
                del license_lines[-1]
            norm_text = normalize(license_lines)
            if abs(mode) <= 1: # like debmake -c etc.
                (licenseid, text) = lc(norm_text, license_lines, mode)
                print('{}\t=> {}'.format(file, licenseid))
            elif abs(mode) <= 4: # like debmake -c etc.
                print('File:    {}'.format(file))
                (licenseid, text) = lc(norm_text, license_lines, mode)
                print('License: {}{}\n'.format(licenseid, text))
            else: # abs(mode> => 5 for sunstring match to debug list_sub regex
                print('File:    {}'.format(file))
                print(lc_sub(norm_text, mode))

