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
import subprocess
import sys
import debmake.cat
import debmake.control
import debmake.copyright
import debmake.sed
import debmake.read


#######################################################################
def debian(para):
    ###################################################################
    # set bin type deb["type"] member values
    ###################################################################
    binlist = {"bin", "perl", "python", "python3", "ruby", "script"}
    ###################################################################
    # set level for the extra file outputs
    ###################################################################
    if para["extra"] == "":  # default
        if os.path.isfile("debian/changelog"):
            print('I: found "debian/changelog"', file=sys.stderr)
            para["extra"] = "0"
        elif os.path.isfile("debian/control"):
            print('I: found "debian/control"', file=sys.stderr)
            para["extra"] = "0"
        elif os.path.isfile("debian/copyright"):
            print('I: found "debian/copyright"', file=sys.stderr)
            para["extra"] = "0"
        elif os.path.isfile("debian/rules"):
            print('I: found "debian/rules"', file=sys.stderr)
            para["extra"] = "0"
        else:
            print(
                "I: new debianization",
                file=sys.stderr,
            )
            para["extra"] = "3"
    try:
        extra = int(para["extra"])
    except ValueError:
        extra = 3  # set to normal one
    print('I: debmake -x "{}" ...'.format(extra), file=sys.stderr)
    ###################################################################
    # common variables
    ###################################################################
    package = para["debs"][0]["package"]  # the first binary package name
    substlist = {
        "@PACKAGE@": para["package"],
        "@UCPACKAGE@": para["package"].upper(),
        "@YEAR@": para["year"],
        "@FULLNAME@": para["fullname"],
        "@EMAIL@": para["email"],
        "@SHORTDATE@": para["shortdate"],
        "@DATE@": para["date"],
        "@DEBMAKEVER@": para["program_version"],
        "@BINPACKAGE@": package,
        "@COMPAT@": para["compat"],
    }
    if para["native"]:
        substlist["@PKGFORMAT@"] = "3.0 (native)"
        substlist["@VERREV@"] = para["version"]
    else:
        substlist["@PKGFORMAT@"] = "3.0 (quilt)"
        substlist["@VERREV@"] = para["version"] + "-" + para["revision"]
    ###################################################################
    # read data for required 5 configuration template files for debhelper(7) (level=0).
    #   set @EXPORT@ @OVERRIDE@ @DHWITH@ @DHBUILDSYSTEM@ strings
    ###################################################################
    export_dir = para["data_path"] + "extra0export_"
    substlist["@EXPORT@"] = ""
    if "compiler" in para["export"]:
        substlist["@EXPORT@"] += (
            debmake.read.read(export_dir + "compiler.txt").rstrip() + "\n"
        )
        if "java" in para["export"]:
            substlist["@EXPORT@"] += (
                debmake.read.read(export_dir + "java.txt").rstrip() + "\n"
            )
        if "vala" in para["export"]:
            substlist["@EXPORT@"] += (
                debmake.read.read(export_dir + "vala.txt").rstrip() + "\n"
            )
    substlist["@EXPORT@"] += (
        debmake.read.read(export_dir + "misc.txt").rstrip() + "\n\n"
    )

    override_dir = para["data_path"] + "extra0override_"
    substlist["@OVERRIDE@"] = ""
    if "autogen" in para["override"]:
        substlist["@OVERRIDE@"] += (
            debmake.read.read(override_dir + "autogen.txt").rstrip() + "\n\n"
        )
    if "autoreconf" in para["override"]:
        substlist["@OVERRIDE@"] += (
            debmake.read.read(override_dir + "autoreconf.txt").rstrip() + "\n\n"
        )
    if "cmake" in para["override"]:
        substlist["@OVERRIDE@"] += (
            debmake.read.read(override_dir + "cmake.txt").rstrip() + "\n\n"
        )
    if "java" in para["override"]:
        substlist["@OVERRIDE@"] += (
            debmake.read.read(override_dir + "java.txt").rstrip() + "\n\n"
        )
    if "judge" in para["override"]:
        substlist["@OVERRIDE@"] += (
            debmake.read.read(override_dir + "judge.txt").rstrip() + "\n\n"
        )
    if "makefile" in para["override"]:
        substlist["@OVERRIDE@"] += (
            debmake.read.read(override_dir + "makefile.txt").rstrip() + "\n\n"
        )
    if "multiarch" in para["override"]:
        substlist["@OVERRIDE@"] += (
            debmake.read.read(override_dir + "multiarch.txt").rstrip() + "\n\n"
        )
    if "pythons" in para["override"]:
        substlist["@OVERRIDE@"] += (
            debmake.read.read(override_dir + "pythons.txt").rstrip() + "\n\n"
        )

    if para["dh_with"] == set():  # no dh_with
        substlist["@DHWITH@"] = ""
    else:
        substlist["@DHWITH@"] = " --with {}".format(",".join(para["dh_with"]))

    if para["dh_buildsystem"] == "":  # no --buildsystem
        substlist["@DHBUILDSYSTEM@"] = ""
    else:
        substlist["@DHBUILDSYSTEM@"] = " --buildsystem={}".format(
            para["dh_buildsystem"]
        )

    ###################################################################
    # check which package have the documentation TODO: move to debs ?
    ###################################################################
    if para["doc"] == []:
        # if no doc package exists, set the package name of the first package as docpackage
        docpackage = para["debs"][0]["package"]  # package type of debs[0] 1st package
    else:
        docpackage = ""

    ###################################################################
    # write required 5 configuration template files for debhelper(7) (level=0).
    # (default option if any of bare minimum configuration files already exist)
    ###################################################################
    debmake.cat.cat(
        "debian/control", debmake.control.control(para), tutorial=para["tutorial"]
    )
    debmake.cat.cat(
        "debian/copyright",
        debmake.copyright.copyright(
            para["package"],
            para["license"],
            para["cdata"],
            para["xml_html_files"],
            para["binary_files"],
            para["huge_files"],
            tutorial=para["tutorial"],
        ),
        tutorial=para["tutorial"],
    )
    debmake.sed.sed(
        para["data_path"] + "extra0_",
        "debian/",
        substlist,
        package,
        tutorial=para["tutorial"],
    )  # generate changelog, rules
    os.chmod("debian/rules", 0o755)
    debmake.sed.sed(
        para["data_path"] + "extra0source_",
        "debian/source/",
        substlist,
        package,
        tutorial=para["tutorial"],
    )  # generate source/format
    ###################################################################
    # write desirable configuration template files with binary package type
    # supports for debhelper(7) (level=1).
    ###################################################################
    if extra >= 1:
        debmake.sed.sed(
            para["data_path"] + "extra1_",
            "debian/",
            substlist,
            package,
            tutorial=para["tutorial"],
        )
        debmake.sed.sed(
            para["data_path"] + "extra1tests_",
            "debian/tests/",
            substlist,
            package,
            tutorial=para["tutorial"],
        )
        debmake.sed.sed(
            para["data_path"] + "extra1upstream_",
            "debian/upstream/",
            substlist,
            package,
            tutorial=para["tutorial"],
        )
        if not para["native"] or extra >= 4:
            debmake.sed.sed(
                para["data_path"] + "extra1patches_",
                "debian/patches/",
                substlist,
                package,
                tutorial=para["tutorial"],
            )
            debmake.sed.sed(
                para["data_path"] + "extra1source.nn_",
                "debian/source/",
                substlist,
                package,
                suffix=".ex",
                tutorial=para["tutorial"],
            )
        if len(para["debs"]) == 1:  # if single binary deb
            debmake.sed.sed(
                para["data_path"] + "extra1single_",
                "debian/",
                substlist,
                package,
                tutorial=para["tutorial"],
            )  # install, links, dirs
        else:  # if multi-binary debs
            debmake.sed.sed(
                para["data_path"] + "extra1multi_",
                "debian/",
                substlist,
                package,
                tutorial=para["tutorial"],
            )  # dirs, links
            for deb in para["debs"]:
                substlist["@BINPACKAGE@"] = deb["package"]
                type = deb["type"]
                if type in binlist:
                    type = "bin"
                # type is reduced to {bin, data, dev, doc, lib}
                debmake.sed.sed(
                    para["data_path"] + "extra1" + type + "_",
                    "debian/",
                    substlist,
                    deb["package"], # use binpackage name
                    tutorial=para["tutorial"],
                )
                # TODO: dh_installdoc files if needed for the first binpackage
                if deb["package"] == docpackage:
                    type = "doc"
                    debmake.sed.sed(
                        para["data_path"] + "extra1" + type + "_",
                        "debian/",
                        substlist,
                        deb["package"], # use binpackage name
                        tutorial=para["tutorial"],
                    )
    ###################################################################
    # reset original value
    ###################################################################
    substlist["@BINPACKAGE@"] = package  # just in case
    ###################################################################
    # write normal configuration template files with maintainer script
    # supports. (normal default option) (level=2)
    ###################################################################
    # create templates only for the first binary package
    if extra >= 2:
        if len(para["debs"]) == 1:  # if single binary deb
            debmake.sed.sed(
                para["data_path"] + "extra2single.ex_",
                "debian/",
                substlist,
                package,
                suffix=".ex",
                tutorial=para["tutorial"],
            )
        else:  # if multi-binary debs
            debmake.sed.sed(
                para["data_path"] + "extra2multi.ex_",
                "debian/",
                substlist,
                package,
                suffix=".ex",
                tutorial=para["tutorial"],
            )
    ###################################################################
    # write optional configuration template files.  (level=3)
    ###################################################################
    # create templates only for the first binary package
    if extra >= 3:
        debmake.sed.sed(
            para["data_path"] + "extra3_",
            "debian/",
            substlist,
            package,
            suffix=".ex",
            tutorial=para["tutorial"],
        )
        debmake.sed.sed(
            para["data_path"] + "extra3source_",
            "debian/source/",
            substlist,
            package,
            suffix=".ex",
            tutorial=para["tutorial"],
        )
        if not para["native"] or extra >= 4:
            debmake.sed.sed(
                para["data_path"] + "extra3source.nn_",
                "debian/source/",
                substlist,
                package,
                suffix=".ex",
                tutorial=para["tutorial"],
            )
    ###################################################################
    # Deprecated optional files (level=4)
    # Provided as reminders. (files with ".ex" postfix)
    ###################################################################
    # create templates only for the first binary package
    if extra >= 4:
        debmake.sed.sed(
            para["data_path"] + "extra4_",
            "debian/",
            substlist,
            package,
            suffix=".ex",
            tutorial=para["tutorial"],
        )
    ###################################################################
    # wrap-and-sort
    # comments may be reordered to be placed after an empty line
    ###################################################################
    command = "wrap-and-sort"
    print("I: $ {}".format(command), file=sys.stderr)
    if subprocess.call(command, shell=True) != 0:
        print("E: failed to run wrap-and-sort.", file=sys.stderr)
        exit(1)
    print(
        "I: $ {} complete.  Now, debian/* may have a blank line at the top.".format(
            command
        ),
        file=sys.stderr,
    )
    return


#######################################################################
# Test script
#######################################################################
if __name__ == "__main__":
    print("no test")
