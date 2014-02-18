# Debianize (initial)
CD ${PROJECT}
cd ${PROJECT}
# Need to end true to log result
L "debmake -p hello-c -u 1.5 -d -i debuild" || true
# fake output
echo 'make: *** [test] Error 1'
