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
def changelog(para):
    if para['native']:
        msg = '''\
{0} ({1}) UNRELEASED; urgency=low

  * Initial release. Closes: #nnnn
    <nnnn is the bug number of your ITP>

 -- {2} <{3}>  {4}
'''.format(
            para['package'], 
            para['version'], 
            para['fullname'], 
            para['email'],
            para['date'])
    else:
        msg = '''\
{0} ({1}-{2}) UNRELEASED; urgency=low

  * Initial release. Closes: #nnnn
    <nnnn is the bug number of your ITP>

 -- {3} <{4}>  {5}
'''.format(
            para['package'], 
            para['version'], 
            para['revision'], 
            para['fullname'], 
            para['email'],
            para['date'])
    return msg

#######################################################################
# Test script
#######################################################################
if __name__ == '__main__':
    para = {}
    para['native'] = False
    para['package'] = 'package'
    para['version'] = '1.0.0'
    para['revision'] = '1'
    para['fullname'] = 'fullname'
    para['email'] = 'foo@example.org'
    para['date'] = 'Sat, 04 Jan 2014 18:11:08 +0900'
    print(changelog(para))
    print('***********************************************************')
    para['native'] = True
    print(changelog(para))

