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
import os
import re
import sys
import subprocess
import debmake.grep
import debmake.read
import debmake.checkdep5
import debmake.scanfiles
import debmake.yn

###########################################################################
# get master name (remove -dev)
###########################################################################
# re.sub: drop "-dev"
re_dev = re.compile(r"""(-dev$)""")


def masterdev(name):
    if re_dev.search(name):
        name = re_dev.sub("", name)
    else:
        print(
            'E: development package "{}" does not end with "-dev"'.format(name),
            file=sys.stderr,
        )
        exit(1)
    return name


###########################################################################
# popular: warn binary dependency etc. if they are top 3 popular files
###########################################################################
def popular(exttype, msg, debs, extcountlist, yes):
    n = 3  # check files with the top 3 popular extension types
    if exttype in dict(extcountlist[0:n]).keys():
        settype = False
        for deb in debs:
            type = deb["type"]  # -b (python3 also reports python)
            if type == exttype:
                settype = True
                break
            if exttype == "python3" and type == "python3":
                settype = True
                break
            if exttype == "javascript" and type == "nodejs":
                settype = True
                break
        if not settype:
            print(
                'W: many ext = "{}" type extension programs without matching -b set.'.format(
                    exttype
                ),
                file=sys.stderr,
            )
            debmake.yn.yn(msg, "", yes)
    return


###########################################################################
# description: read from the upstream packaging system
###########################################################################
def description(type, data_path):
    text = ""
    command = data_path + type + ".short.sh"
    p = subprocess.Popen(
        command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    if p.stdout is not None:
        for line in p.stdout.readlines():
            text += line.decode("utf-8").strip() + " "
    if p.wait() != 0:
        print('E: "{}" returns "{}"'.format(command, p.returncode), file=sys.stderr)
        exit(1)
    return text.strip()


###########################################################################
# description_long: read from the upstream packaging system
###########################################################################
def description_long(type, data_path):
    text = ""
    command = data_path + type + ".long.sh"
    p = subprocess.Popen(
        command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    if p.stdout is not None:
        for line in p.stdout.readlines():
            l_chomp = line.decode("utf-8").rstrip()
            if l_chomp:
                text += " " + l_chomp + "\n"
            else:
                text += " .\n"
    if p.wait() != 0:
        print('E: "{}" returns "{}"'.format(command, p.returncode), file=sys.stderr)
        exit(1)
    if text == " .\n":
        text = ""
    return text


###########################################################################
# analyze: called from debmake.main()
###########################################################################
def analyze(para):
    ###################################################################
    # package list by types (first pass)
    ###################################################################
    para["bin"] = []
    para["lib"] = []
    para["dev"] = []
    para["data"] = []
    para["doc"] = []
    para["scripts"] = []
    for i, deb in enumerate(para["debs"]):
        if deb["type"] == "bin":
            para["bin"].append(deb["package"])
        elif deb["type"] == "lib":
            para["lib"].append(deb["package"])
        elif deb["type"] == "dev":
            para["dev"].append(deb["package"])
        elif deb["type"] == "doc":
            para["doc"].append(deb["package"])
        elif deb["type"] == "data":
            para["data"].append(deb["package"])
        else:
            para["scripts"].append(deb["package"])
    if len(para["debs"]) != 1 and len(para["dev"]) != len(para["lib"]):
        print(
            'E: # of "dev":{} != # of "lib": {}.'.format(
                len(para["dev"]), len(para["lib"])
            ),
            file=sys.stderr,
        )
        exit(1)
    if para["lib"] != []:
        setmultiarch = True
    elif para["bin"] != [] and len(para["debs"]) == 1:
        setmultiarch = True
    else:
        setmultiarch = False  # for override
    if para["monoarch"]:
        setmultiarch = False
    ###################################################################
    # package list by types (second pass)
    ###################################################################
    for i, deb in enumerate(para["debs"]):
        if deb["type"] == "bin":
            para["export"].update({"compiler"})
            for libpkg in para["lib"]:
                para["debs"][i]["depends"].update({libpkg + " (= ${binary:Version})"})
        elif deb["type"] == "lib":
            para["export"].update({"compiler"})
        elif deb["type"] == "dev":
            pkg = masterdev(deb["package"])
            match = False
            for libpkg in para["lib"]:
                if libpkg[: len(pkg)] == pkg:
                    para["debs"][i]["depends"].update(
                        {libpkg + " (= ${binary:Version})"}
                    )
                    match = True
                    break
            if not match:
                print(
                    'E: {} does not have matching library in "{}".'.format(
                        deb["package"], ", ".join(para["lib"])
                    ),
                    file=sys.stderr,
                )
                exit(1)
        elif deb["type"] == "perl":
            for libpkg in para["lib"]:
                para["debs"][i]["depends"].update(
                    {
                        libpkg
                        + " (>= ${source:Version}), "
                        + libpkg
                        + " (<< ${source:Upstream-Version}.0~)"
                    }
                )
        elif deb["type"] == "python3":
            para["dh_with"].update({"python3"})
            para["build_depends"].update({"python3-all", "dh-python"})
            for libpkg in para["lib"]:
                para["debs"][i]["depends"].update(
                    {
                        libpkg
                        + " (>= ${source:Version}), "
                        + libpkg
                        + " (<< ${source:Upstream-Version}.0~)"
                    }
                )
        elif deb["type"] == "ruby":
            para["dh_with"].update({"ruby"})  # may not be needed
            para["build_depends"].update({"ruby"})
            for libpkg in para["lib"]:
                para["debs"][i]["depends"].update(
                    {
                        libpkg
                        + " (>= ${source:Version}), "
                        + libpkg
                        + " (<< ${source:Upstream-Version}.0~)"
                    }
                )
        elif deb["type"] == "nodejs":
            para["dh_with"].update({"nodejs"})
            para["build_depends"].update({"pkg-js-tools"})
            for libpkg in para["lib"]:
                para["debs"][i]["depends"].update(
                    {
                        libpkg
                        + " (>= ${source:Version}), "
                        + libpkg
                        + " (<< ${source:Upstream-Version}.0~)"
                    }
                )
        elif deb["type"] == "script":
            for libpkg in para["lib"]:
                para["debs"][i]["depends"].update(
                    {
                        libpkg
                        + " (>= ${source:Version}), "
                        + libpkg
                        + " (<< ${source:Upstream-Version}.0~)"
                    }
                )
        else:
            pass
    #######################################################################
    # auto-set build system by files in the base directory
    #   update para["dh_with"] -- debian build component dh_*
    #   para["build_type"] -- upstrean build type
    #   para["build_depends"] -- build dependency packages
    #   para["export"] -- exported build environment variable type
    #   para["override"] -- set override_dh_* setting type
    #######################################################################
    para["build_type"] = ""  # reset value
    para["dh_buildsystem"] = ""  # normally not needed
    # check if '*.pro' for Qmake project exist in advance.
    pro = glob.glob("*.pro")
    if pro:
        pro = pro[0]
    else:
        pro = ""
    # check if '*.spec.in' for RPM
    specs = glob.glob("*.spec.in")
    if specs:
        spec = specs[0]
    else:
        spec = ""
    # GNU coding standard with autotools = autoconf+automake
    if (
        os.path.isfile("configure.ac")
        and os.path.isfile("Makefile.am")
        and ("autotools-dev" not in para["dh_with"])
    ):
        para["dh_with"].update({"autoreconf"})
        para["build_type"] = "Autotools with autoreconf"
        para["build_depends"].update({"dh-autoreconf"})
        para["export"].update({"autotools"})
        if os.path.isfile("autogen.sh"):
            para["override"].update({"autogen"})
        else:
            para["override"].update({"autoreconf"})
    elif (
        os.path.isfile("configure.in")
        and os.path.isfile("Makefile.am")
        and ("autotools-dev" not in para["dh_with"])
    ):
        para["dh_with"].update({"autoreconf"})
        para["build_type"] = "Autotools with autoreconf (old)"
        para["build_depends"].update({"dh-autoreconf"})
        para["export"].update({"autotools"})
        if os.path.isfile("autogen.sh"):
            para["override"].update({"autogen"})
        else:
            para["override"].update({"autoreconf"})
        print("W: Use of configure.in has been deprecated since 2001.", file=sys.stderr)
    elif (
        os.path.isfile("configure.ac")
        and os.path.isfile("Makefile.am")
        and os.path.isfile("configure")
    ):
        para["dh_with"].update({"autotools-dev"})
        para["build_type"] = "Autotools"
        para["build_depends"].update({"autotools-dev"})
        para["export"].update({"autotools"})
    elif (
        os.path.isfile("configure.in")
        and os.path.isfile("Makefile.am")
        and os.path.isfile("configure")
    ):
        para["dh_with"].update({"autotools-dev"})
        para["build_type"] = "Autotools (old)"
        para["build_depends"].update({"autotools-dev"})
        para["export"].update({"autotools"})
        print("W: Use of configure.in has been deprecated since 2001.", file=sys.stderr)
    elif "autoreconf" in para["dh_with"]:
        print(
            'E: missing configure.ac or Makefile.am required for "dh $@ --with autoreconf".',
            file=sys.stderr,
        )
        exit(1)
    elif "autotools-dev" in para["dh_with"]:
        print(
            'E: missing configure.ac or Makefile.am or configure required for "dh $@ --with autotools-dev".',
            file=sys.stderr,
        )
        exit(1)
    # GNU coding standard with configure
    elif os.path.isfile("configure"):
        para["build_type"] = "configure"
        if setmultiarch:
            para["override"].update({"multiarch"})
    # GNU coding standard with Cmake
    elif os.path.isfile("CMakeLists.txt"):
        para["build_type"] = "Cmake"
        para["build_depends"].update({"cmake"})
        para["override"].update({"cmake"})
        if setmultiarch:
            para["override"].update({"multiarch"})
    # GNU coding standard with make
    elif os.path.isfile("Makefile"):
        para["build_type"] = "make"
        para["override"].update({"makefile"})
        if setmultiarch:
            para["override"].update({"multiarch"})
    # Python setuptools
    elif os.path.isfile("setup.py"):
        para["dh_with"].update({"python3"})
        para["build_type"] = "Python setuptools (setup.py)"
        para["dh_buildsystem"] = "pybuild"
        # dh-python and python3-build are pulled in by pybuild-plugin-pyproject"
        para["build_depends"].update({"python3-all", "pybuild-plugin-pyproject"})
        if para["spec"]:
            if para["desc"] == "":
                para["desc"] = description("python3", para["data_path"])
            if para["desc_long"] == "":
                para["desc_long"] = description_long("python3", para["data_path"])
        if debmake.grep.grep("setup.py", "python3", 0, 1) or debmake.grep.grep(
            "setup.py", "python", 0, 1
        ):
            # http://docs.python.org/3/distutils/
            if debmake.grep.grep(
                "setup.py", r"from\s+setuptools\s+import\s+setup", 0, -1
            ):
                # TODO: this needs verification
                para["build_depends"].update({"python3-setuptools"})
            else:
                # non-setuptools (pure distutil?) may not be supported
                print(
                    "W: no setuptools. (distutils?)  check setup.py.",
                    file=sys.stderr,
                )
        else:
            print("W: unknown python system.  check setup.py.", file=sys.stderr)
    elif os.path.isfile("setup.cnf"):
        para["dh_with"].update({"python3"})
        para["build_type"] = "Python setuptools (setup.cnf)"
        para["dh_buildsystem"] = "pybuild"
        # dh-python and python3-build are pulled in by pybuild-plugin-pyproject"
        para["build_depends"].update({"python3-all", "pybuild-plugin-pyproject"})
        # TODO: check if this is good idea
        para["build_depends"].update({"python3-setuptools"})
    elif os.path.isfile("pyproject.toml"):
        para["dh_with"].update({"python3"})
        para["build_type"] = "Python (pyproject.toml: PEP-518, PEP-621, PEP-660)"
        para["dh_buildsystem"] = "pybuild"
        # dh-python and python3-build are pulled in by pybuild-plugin-pyproject"
        para["build_depends"].update({"python3-all", "pybuild-plugin-pyproject"})
        if debmake.grep.grep("pyproject.toml", r"setuptools", 0, -1):
            # TODO: check if this is good idea
            para["build_depends"].update({"python3-setuptools"})
            # para["build_depends"].update({"python3-setuptools-whl"})
            print("W: setuptools build system.", file=sys.stderr)
        elif debmake.grep.grep("pyproject.toml", r"hatchling", 0, -1):
            # TODO: check if this is good idea
            para["build_depends"].update({"python3-hatchling"})
            print("W: Hatchling build system.", file=sys.stderr)
        elif debmake.grep.grep("pyproject.toml", r"flit_core", 0, -1):
            # TODO: check if this is good idea
            para["build_depends"].update({"flit"})
            print("W: Flit build system.", file=sys.stderr)
        elif debmake.grep.grep("pyproject.toml", r"pdm-backend", 0, -1):
            # TODO: check if this is good idea
            para["build_depends"].update({"python3-pdm"})
            # para["build_depends"].update({"python3-pdm-pep517"})
            print("W: PDM build system.", file=sys.stderr)
        else:
            # TODO: check if this is good idea
            print("W: unknown python build system.", file=sys.stderr)
    # Perl
    elif os.path.isfile("Build.PL"):
        # Preferred over Makefile.PL after debhelper v8
        para["build_type"] = "Perl Module::Build"
        para["build_depends"].update({"perl"})
    elif os.path.isfile("Makefile.PL"):
        para["build_type"] = "Perl ExtUtils::MakeMaker"
        para["build_depends"].update({"perl"})
    # Ruby
    elif os.path.isfile("setup.rb"):
        print(
            "W: dh-make-ruby(1) (gem2deb package) may provide better packaging results.",
            file=sys.stderr,
        )
        para["build_type"] = "Ruby setup.rb"
        para["build_depends"].update({"ruby", "gem2deb"})
    # Javascript nodejs
    elif os.path.isfile("package.json"):
        para["build_type"] = "nodejs"
        para["dh_with"].update({"nodejs"})
        para["build_depends"].update({"dh-nodejs"})
    # Java
    elif os.path.isfile("build.xml"):
        para["build_type"] = "Java ant"
        para["dh_with"].update({"javahelper"})
        # XXX FIXME XXX which compiler to use?
        para["build_depends"].update({"javahelper", "gcj"})
        para["export"].update({"java", "compiler"})
        para["override"].update({"java"})
        if setmultiarch:
            para["override"].update({"multiarch"})
    # Qmake
    elif os.path.isfile(pro):
        # XXX FIXME XXX Is this right?
        para["build_type"] = "QMake"
        para["build_depends"].update({"qt4-qmake"})
        if setmultiarch:
            para["override"].update({"multiarch"})
    else:
        para["build_type"] = "Unknown"
        if setmultiarch:
            para["override"].update({"multiarch"})
    print("I: build_type = {}".format(para["build_type"]), file=sys.stderr)
    #######################################################################
    # high priority spec source, first
    if para["spec"]:
        if para["desc"] == "" and os.path.isfile("META.yml"):
            para["desc"] = description("META.yml", para["data_path"])
        if para["desc"] == "" and os.path.isfile("Rakefile"):
            para["desc"] = description("Rakefile", para["data_path"])
        if para["desc"] == "" and spec:
            para["desc"] = description("spec", para["data_path"])
        if para["desc_long"] == "" and spec:
            para["desc_long"] = description_long("spec", para["data_path"])
    #######################################################################
    # analyze copyright+license content + file extensions
    # copyright, control: build/binary dependency, rules export/override
    #######################################################################
    print(
        "I: scan source for copyright+license text and file extensions", file=sys.stderr
    )
    (
        para["nonlink_files"],
        para["xml_html_files"],
        para["binary_files"],
        para["huge_files"],
        para["extcount"],
        para["extcountlist"],
    ) = debmake.scanfiles.scanfiles()
    # skip slow license+copyright check if debian/copyright exists
    if os.path.isfile("debian/copyright"):
        para["cdata"] = []
    else:
        para["cdata"] = debmake.checkdep5.checkdep5(
            para["nonlink_files"], mode=2, pedantic=para["pedantic"]
        )
    #######################################################################
    # compiler: set build dependency etc. if they are used
    if "c" in para["extcount"].keys():
        para["export"].update({"compiler"})
        if setmultiarch and para["build_type"][0:9] != "Autotools":
            para["override"].update({"multiarch"})
    if "java" in para["extcount"].keys():
        if para["build_type"][0:4] != "Java":
            # Non-ant build system
            if para["build_type"]:
                para["build_type"] = "Java + " + para["build_type"]
            else:
                para["build_type"] = "Java"
            para["dh_with"].update({"javahelper"})
            para["build_depends"].update({"javahelper", "gcj"})
            para["export"].update({"java", "compiler"})
            para["override"].update({"java"})
            if setmultiarch and para["build_type"][0:9] != "Autotools":
                para["override"].update({"multiarch"})
    if para["build_type"][0:4] == "Java":
        print(
            "W: Java support is not perfect. (/usr/share/doc/javahelper/tutorials.html)",
            file=sys.stderr,
        )
    if "vala" in para["extcount"].keys():
        para["build_type"] = "Vala"
        para["build_depends"].update({"valac"})
        para["export"].update({"vala", "compiler"})
        if setmultiarch and para["build_type"][0:9] != "Autotools":
            para["override"].update({"multiarch"})
    #######################################################################
    # set build dependency and override if --with python3
    #######################################################################
    if "python3" in para["dh_with"]:
        para["build_depends"].update({"python3-all", "dh-python"})
        para["override"].update({"pythons"})
    #######################################################################
    # interpreter: warn binary dependency etc. if they are top 3 popular files
    #######################################################################
    popular(
        "perl",
        '-b":perl, ..." missing. Continue?',
        para["debs"],
        para["extcountlist"],
        para["yes"],
    )
    popular(
        "python3",
        '-b":python3" is missing. Continue?',
        para["debs"],
        para["extcountlist"],
        para["yes"],
    )
    popular(
        "ruby",
        '-b":ruby, ..." missing. Continue?',
        para["debs"],
        para["extcountlist"],
        para["yes"],
    )
    popular(
        "javascript",
        '-b":nodejs, ..." missing. Continue?',
        para["debs"],
        para["extcountlist"],
        para["yes"],
    )
    #######################################################################
    return para


if __name__ == "__main__":
    print("no test")
