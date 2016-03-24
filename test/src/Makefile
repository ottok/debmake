# Generate template files of MIT license collection
# 1. Place "copyright" file from xorg-common package in the same directory
# 2. Run "make" to check sanity

PWD=$(shell pwd)

PYTHONPATH:=$(shell pwd)/../..
export PYTHONPATH

PATH:=$(shell pwd)/../../debmake:$(PATH)
export PATH

LC_ALL=C.UTF-8
export LC_ALL

all: test2
	# If different, next line returns non-zero(=ERROR)
	#diff -u $(PWD)/../.LICENSE.KEEP $(PWD)/../.LICENSE.LOG
	diff -u $(PWD)/../.FULL_LICENSE.KEEP $(PWD)/../.FULL_LICENSE.LOG

# Please place data from SPDX in src/dspdx/*
spdx:
	for x in dspdx/* ; do \
	y=$$(basename $$x).txt; \
	: > ../$$y ;\
	echo '#%#%#%# This is copyright analyser test data by Osamu Aoki.' >> ../$$y ;\
	echo '#%#%#%# The following lines shall not be considered copyright statement.' >> ../$$y ;\
	echo '#%#%#%# ' >> ../$$y ;\
	cat   $$x >> ../$$y ;\
	done

# Please place external data in src/dpick/*
pick:
	for x in dpick/* ; do \
	y="@$$(basename $$x).txt"; \
	: > ../$$y ;\
	echo '#%#%#%# This is copyright analyser test data by Osamu Aoki.' >> ../$$y ;\
	echo '#%#%#%# The following lines shall not be considered copyright statement.' >> ../$$y ;\
	echo '#%#%#%# ' >> ../$$y ;\
	cat   $$x >> ../$$y ;\
	done

# Please place "copyright" file from xorg-common package" in src/
mit:
	@if [ ! -f copyright ]; then \
	echo "Please place "copyright" file from xorg-common package"; \
	fi
	cd .. ; sed -n -e '1,47p' -e '53,$$p' src/copyright > copyright-clean
	cd ..; src/split copyright-clean
	rm -f ../copyright-clean

test1:
	echo $$PATH
	echo $$PYTHONPATH
	cd .. ;\
	(for x in *.txt; do \
	printf "%s\t" "$$x" ; \
	copyright.py -i $$x ; \
	echo -n '.' >&2 ;\
	done ; echo >&2 ) | sort > $(PWD)/../.LICENSE.LOG
	diff -u $(PWD)/../.LICENSE.KEEP $(PWD)/../.LICENSE.LOG > $(PWD)/../.LICENSE.DIFF \
		&& echo "SUCCESS" || echo "FAIL"

test2:
	echo $$PATH
	echo $$PYTHONPATH
	cd .. ;\
	(for x in $$(ls *.txt); do \
	copyright.py $$x ; \
	echo -n '.' >&2 ;\
	done ; echo >&2 ) > $(PWD)/../.FULL_LICENSE.LOG
	diff -u $(PWD)/../.FULL_LICENSE.KEEP $(PWD)/../.FULL_LICENSE.LOG > $(PWD)/../.FULL_LICENSE.DIFF \
		&& echo "SUCCESS" || echo "FAIL"

clean:
	rm -f $(PWD)/../.LICENSE.LOG $(PWD)/../.LICENSE.DIFF

distclean: clean

