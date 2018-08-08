# Debmake

This is the new debmake program written in Python.  This provides convenient
command to make a Debian package from the upstream VCS/tarball/source-tree.

This is available as the "debmake" package on Debian.

See the HTML files in the "debmake-doc" package for the introductory guide.

## Build from the git

1. Check-out devel branch
   $ git clone --branch devel https://salsa.debian.org/debian/debmake.git 

2. Make modification
3. when debmake command line interface changes:
      * update debmake-doc package
      * generate a new debmake.1 file in its source
      * copy generated debmake.1 file into manpages/debmake.1
4. Add a new entry to the debian/changelog with the new upstream version
   ("dch -i" creates entry such as 4.1.1-2 --> change to 4.1.2-1)
5. Update debmake/__init__.py with new upstream version 4.1.2
6. Update test/.LICENSE.KEEP

        $ cd test/src; make
          ... verify it is SUCCESS

   (If new test case is added and it build result is good, copy the new
   test/.LICENSE.LOG to test/.LICENSE.KEEP to make this SUCCESS)

7. Build with

        $ debmake -d -y -zx -b':py3' -i pdebuild

   or

        $ python3 setup.py deb

8. Clean source tree with

        $ python3 setup.py clean

(Under freeze for release, work on main branch)

Please follow PEP-8 as much as possible.
 * indent 4 spaces
 * 80 char/line
 *  Coding style exceptions:
   * line for debug code -> single line for eaze of "grep"
   * some regex (max 100 char/line) for readability

## Debug the source code

The source code can be tested by:
 * Set up the module loading path $PYTHONPATH and the command search path $PATH
   from the debmake source directory /path/to where setup.py is found:

          $ cd /path/to
          $ export PYTHONPATH=`pwd`
          $ export PATH=`pwd`/debmake:`pwd`/scripts:$PATH

   Now all scripts such as copyright.py and lc.py can be executed
   independently from the command line for debugging.

 * checkdep5.py [-s|-c|-t|-i|--] <file>
   
        -s	 selftest
        -c  extract copyright info as formatted text
        -t  extract license info as plain text
        -i  check license ID with extra info
        --  check license ID and extract copyright (default)

   Use "make test-dep5" and "make test-id" in test/src/Makefile to test.

 * lc.py [-][1|2|3|4|5|6] <files ...>
   check <files ...> for license ID in different mode of -c options in debmake

        1: -c       license ID
        2: -cc      license ID + license text
        3: -ccc     license ID + license text + extra
        -1: -cccc    license ID + internal ID
        -2: -ccccc   license ID + internal ID + license text
        -4: -cccccc  license ID + internal ID + license text + extra
        5: sub-string match for debug
        6: combination sub-string match for debug

Trouble shoot hints:
 * What to do for strange string contaminating license info?
     => Fix check_lines()       in debmake/checkdep5.py
 * What to do for incorrect range calculation for copyright years.
     => Fix analyze_copyright() in debmake/checkdep5.py
 * What to do for strange license type assignment?
     => Fix lc()                in debmake/lc.py

## Hints for reading the source

How copyright files are scanned by debmake in normal usage?

    -k option execution  --> debmake/kludge.py    kludge()
    -c option execution  +-> debmake/scanfiles.py scanfiles()
                         +-> debmake/checkdep5.py checkdep5()
    normal execution     --> debmake/debian.py    debian()
                          +-> debmake/copyright.py copyright()
                                 Here, copyformat() gets:
                                   para['package']
                                   para['license']
                                   para['cdata']
                                   para['xml_html_files']
                                   para['binary_files']
                                   para['huge_files']
               These are set by debmake/analyze.py analyze(para) calling:
                                   -+--> debmake/scanfiles.py scanfiles()
                                    +--> debmake/checkdep5.py checkdep5()

What does scanfiles() do?
  * Scan all files in source tree and make list of files for each category:
    nonlink_files, xml_html_files, binary_files, huge_files
  * extensions holds all file extention types

What does checkdep5() do?
  * Scan nonlink_files and return summary of copyright info as cdata
  by 3 step operations:

        adata = check_all_licenses()
        bdata = bunch_all_licenses(adata)
        cdata = format_all_licenses(bdata)
              = [(licenseid, licensetext, files, copyright_lines), ...]

What does check_all_licenses() do?

    for each file:
      (copyright_data, license_lines) = checkdep5(file, ...)
        This extract copyright iand license information section
        out of file using check_lines()
      norm_text = debmake.lc.normalize(license_lines)
        This normalize copyright info.
      (licenseid, licensetext, permissive) = debmake.lc.lc(norm_text, ...)
        This characterize license info from norm_text
        Here, md5hashkey is used to optimize operation speed

Osamu Aoki

