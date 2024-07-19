# see: dh_installdeb(1), dpkg-maintscript-helper(1)
###      https://www.debian.org/doc/debian-policy/ch-maintainerscripts.html
###      https://www.debian.org/doc/debian-policy/ap-flowcharts.html
###
### For removing a conffile, you are advised to create a debian/package.conffiles
### with "remove-on-upgrade conffile" line in debian/package.conffiles, instead.
### See dh_installdeb(1) and deb-conffiles(5).
###
# For renaming a conffile, you are advised to uncomment and edit the following
#dpkg-maintscript-helper mv_conffile old-conffile new-conffile prior-version package
###
# For switching a symlink to directory, you are advised to uncomment and edit the following
#dpkg-maintscript-helper symlink_to_dir pathname old-target prior-version package
###
# For switching a directory to symlink, you are advised to uncomment and edit the following
#dpkg-maintscript-helper dir_to_symlink pathname new-target prior-version package
