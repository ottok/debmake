# This directory contents are generated before packaging
# since some parts require remote http connection.
#
# all: target to export results (doc+tar) to python doc side.
# all: target to export doc to python doc side.
# tar: target to export doc to python doc side.
#
# ref: build reference data (overwrite)
# cmp: build as comparison to the ref

LIST_LOCAL := $(shell ls -1d hello*)
LIST_REMOTE := $(shell ls -1d remote*)
LIST := $(LIST_LOCAL) $(LIST_REMOTE)

all:
	$(MAKE) clean
	$(MAKE) ref
	$(MAKE) doc
	$(MAKE) clean
	$(MAKE) tar

check: check_LOCAL check_REMOTE
ref: ref_LOCAL ref_REMOTE
cmp: cmp_LOCAL cmp_REMOTE

check_LOCAL:
	@echo "$(LIST_LOCAL)"

ref_LOCAL:
	for i in $(LIST_LOCAL) ; do  $(MAKE) -C $$i ref ; echo "I: $$i done" ; done

cmp_LOCAL:
	for i in $(LIST_LOCAL) ; do  $(MAKE) -C $$i cmp ; echo "I: $$i done" ; done

check_REMOTE:
	@echo "$(LIST_REMOTE)"

ref_REMOTE:
	for i in $(LIST_REMOTE) ; do  $(MAKE) -C $$i ref ; echo "I: $$i done" ; done

cmp_REMOTE:
	for i in $(LIST_REMOTE) ; do  $(MAKE) -C $$i cmp ; echo "I: $$i done" ; done

step%.log: step%.cmd
	./$^ >$@

doc/debmake.html doc/debmake.1 doc/examples.html:
	 $(MAKE) -C doc

doc: doc/debmake.html doc/debmake.1 doc/examples.html
	cp -f doc/debmake.html ../doc/debmake.html
	cp -f doc/debmake.1 ../manpages/debmake.1
	#cp -f doc/examples.html ../doc/examples.html
tar:
	tar -cvJf ../doc/examples.tar.xz ../test

clean:
	for i in doc $(LIST) ; do  $(MAKE) -C $$i clean ; echo "I: $$i done" ; done

.PHONY: all ref cmp doc clean check tar
.PHONY: check_LOCAL check_REMOTE ref_LOCAL ref_REMOTE cmp_LOCAL cmp_REMOTE

