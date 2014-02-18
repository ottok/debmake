# Debianize (initial)
CD vcsdir
cd vcsdir
L "git init"
L "git add ."
L "git commit -m \"initial commit\""
L "git branch devel"
L "git branch upstream"
L "git branch"
L "debmake -p hello-c -u 1.5 -d"
