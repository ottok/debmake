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
import os
import sys
#######################################################################
# cat >file
def cat(file, text, end=''):
    if os.path.isfile(file) and os.stat(file).st_size != 0:
        # skip if a file exists and non-zero content
        print('I: File already exits, skipping: {}'.format(file), file=sys.stderr)
        return
    path = os.path.dirname(file)
    if path:
        os.makedirs(path, exist_ok=True)
    with open(file, 'w') as f:
        print(text, file=f, end=end)
        print('I: File written: {}'.format(file), file=sys.stderr)
    return

#######################################################################
# Test script
#######################################################################
if __name__ == '__main__':
    print('no test')

