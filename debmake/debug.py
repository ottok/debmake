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
# Debug output
#######################################################################
def debug(msg, type=''):
    """Outputs to sys.stderr if DEBUG is set."""
    try:
        DEBUG = os.environ["DEBUG"]
    except KeyError:
        pass
    else:
        if type =='':
            print(msg, file=sys.stderr)
        elif type in DEBUG:
            print(msg, file=sys.stderr)
    return

def debug_para(msg, para):
    debug('{}: "{}_{}.{}"'.format(
            msg, 
            para['package'], 
            para['version'], 
            para['targz']))
    return


#######################################################################
# Test code
#######################################################################
if __name__ == '__main__':
    debug('DEBUG ON!')
    para = {}
    para['package'] = 'package'
    para['version'] = '1.0'
    para['targz'] = 'tar.gz'
    debug_para('debug_para', para)

