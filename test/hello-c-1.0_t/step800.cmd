# Debianize (initial)
CD hello-c
cd hello-c
VERSION=$(cat $BASEDIR/version.log)
echo " $ git-import-dsc ../hello-c_${VERSION}-1.dsc  \\"
echo '                  --pristine-tar --create-missing-branches'
git-import-dsc ../hello-c_${VERSION}-1.dsc  --pristine-tar --create-missing-branches --color=no
L "git branch"
# The following are fake user input simulation and 
# cleaning of the demonstration git repository from this test system
echo ' $ gitk --all'
rm -rf .git
cd ..
