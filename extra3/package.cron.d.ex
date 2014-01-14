#
# Regular cron jobs for the @PACKAGE@ package
# See http://www.debian.org/doc/manuals/maint-guide/dother.en.html#crond
#
0 4	* * *	root	[ -x /usr/bin/@PACKAGE@_maintenance ] && /usr/bin/@PACKAGE@_maintenance
