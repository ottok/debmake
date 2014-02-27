# Debianize (initial)
CD vcsdir
cd vcsdir
L "git init"
L "git add ."
L "git commit -m \"initial commit\""
L "git checkout -b devel"
L "git branch"
L "debmake -d"
