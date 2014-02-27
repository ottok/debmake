# Git repo
L "tar -xzmf ${PROJECT}.tar.gz"
CD ${PROJECT}
cd ${PROJECT} >/dev/null
L "git init"
L "git add ."
L "git commit -m 'initial import of ${PROJECT}.tar.gz'"
L "git branch upstream"
L "git tag upstream/0.3.2"
L "pristine-tar commit ../${PROJECT}.tar.gz"
