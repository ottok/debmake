# Menu template (edit and rename to debian/menu to activate)
# See dh_installmenu(1)
#     /usr/share/doc/menu/html/*
#     http://www.debian.org/doc/manuals/maint-guide/dother.en.html#menu
#
?package(@PACKAGE@):needs="X11|text|vc|wm" section="Applications/see-menu-manual"\
  title="@PACKAGE@" command="/usr/bin/@PACKAGE@"
