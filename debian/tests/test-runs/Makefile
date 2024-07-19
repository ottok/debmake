#
# This is used for manual testing
#
#DEBUG = w
#export DEBUG

all:
	mkdir foo10 ; cd foo10 ; debmake -p debhello -u 1.0 -n -T -x0
	mkdir foo11 ; cd foo11 ; debmake -p debhello -u 1.1 -n -T -x1
	mkdir foo12 ; cd foo12 ; debmake -p debhello -u 1.2 -n -T -x2
	mkdir foo13 ; cd foo13 ; debmake -p debhello -u 1.3 -n -T -x3
	mkdir foo14 ; cd foo14 ; debmake -p debhello -u 1.4 -n -T -x4
	mkdir foo20 ; cd foo20 ; debmake -p debhello -u 2.0 -r 1 -t -T -x0
	mkdir foo21 ; cd foo21 ; debmake -p debhello -u 2.1 -r 1 -t -T -x1
	mkdir foo22 ; cd foo22 ; debmake -p debhello -u 2.2 -r 1 -t -T -x2
	mkdir foo23 ; cd foo23 ; debmake -p debhello -u 2.3 -r 1 -t -T -x3
	mkdir foo24 ; cd foo24 ; debmake -p debhello -u 2.4 -r 1 -t -T -x4
	mkdir foo32 ; cd foo32 ; debmake -p debhello -u 3.2 -r 1 -t -T -x2 -b"-,-doc,libdebhello1,libdebhello1-dev"

clean:
	rm -rf foo*
	rm -rf debhello*
