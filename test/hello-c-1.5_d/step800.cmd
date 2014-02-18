# Debianize (initial)
CD vcsdir
cd vcsdir
L "git-import-dsc --color=no --pristine-tar ../hello-c_1.5-1.dsc"
L "git branch"
# The following are fake user input simulation and 
# cleaning of the demonstration git repository from this test system
echo ' $ gitk --all'
rm -rf .git
cd ..
