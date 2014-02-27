# Debianize (initial)
CD vcsdir
cd vcsdir
echo ' $ git-import-dsc ../hello-c_1.5-1.dsc  \'
echo '                  --pristine-tar --create-missing-branches'
git-import-dsc ../hello-c_1.5-1.dsc  --pristine-tar --create-missing-branches --color=no
L "git branch"
# The following are fake user input simulation and 
# cleaning of the demonstration git repository from this test system
echo ' $ gitk --all'
rm -rf .git
cd ..
