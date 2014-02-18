# Debianize (initial)
CD vcsdir
cd vcsdir
L "git init"
L "git add ."
L "git commit -m \"initial commit\""
L "git branch devel"
L "git branch upstream"
L "git branch"
L "debmake -s -b':python3' -p hello-py -u 1.0 -d -i debuild"
L "git clean -d -f"
