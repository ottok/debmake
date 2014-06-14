# Generic build script
DEBEMAIL=email.address@example.org
DEBFULLNAME="Firstname Lastname"
export DEBEMAIL DEBFULLNAME
BASEDIR=$(CURDIR)
TESTDIR=$(CURDIR)/test
REFDIR=$(CURDIR)/ref
COMMONDIR=$(abspath $(CURDIR)/..)
PATH := $(COMMONDIR)/bin:$(PATH)
PROJECT=$(shell echo $(notdir $(CURDIR))|sed -e 's/_.*$$//' -e 's/-fail-/-/' )
PROJECTDIR=$(TESTDIR)/$(PROJECT)
TERM=dumb
TREE_COLORS=
LS_COLORS=
CDPATH=
FILTER =s/\(^...........................................................................\).*$$/\1.../
export BASEDIR TESTDIR REFDIR COMMONDIR PATH PROJECT PROJECTDIR TREE_COLORS LS_COLORS TERM CDPATH

steps = $(patsubst %.cmd, %, $(shell ls *.cmd))


all: cmp

test:
	echo $(BASEDIR) > $(BASEDIR)/next.dir
	echo $(PROJECT) > $(BASEDIR)/project
	for i in $(steps) ; do \
	cd $$(cat $(BASEDIR)/next.dir) >/dev/null ; \
	export PROJECT="$$(cat $(BASEDIR)/project)" ; \
	script -e -q -c $(BASEDIR)/$$i.cmd $(BASEDIR)/$$i.raw ; \
	ERR=$$? ; \
	sed -e '1d' $(BASEDIR)/$$i.raw | col -b -x | \
	sed -e 's#$(TESTDIR)#/path/to#g' | \
	sed -e '$(FILTER)' > $(BASEDIR)/$$i.log ; \
	if [ x$$ERR != x0 ]; then exit 1 ; fi ; \
	done

# no more sed
#	-e 's#osamu#user#g' -e 's/\&/\&amp;/g' -e 's/</\&lt;/g' -e 's/>/\&gt;/g' -e 's/\\/\\\\/g' 

cmp: test
	:>result.diff
	{ for i in $(steps) ; do  if diff -u ref/$$i.log $$i.log >>result.diff; then echo "$$i: good" ; else echo "$$i: changed" ; fi ;  done } >result.log

ref: test
	rm -rf ref
	mkdir ref
	for i in $$(ls *.log) ; do  cp $$i ref/$$i ; echo "I: $$i copied" ; done

step%.log: step%.cmd
	./$^ >$@

clean:
	rm -rf $(TESTDIR)
	-rm -f *.log *.raw
	-rm -f result.diff
	-rm -f ref/result.log
	-rm -rf next.dir project

.PHONY: all test cmp ref clean
