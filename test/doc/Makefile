MANUAL1 = debmake
MANUAL2 = maint-guide
GENTXT = 99-manpage.txt binary.txt caveat.txt
ALLTXT = $(wildcard *.txt) $(GENTXT)
DATE = $(shell date +%F)
VERSION = 2.0~pre1

all: man html

99-manpage.txt: manpage.txt
	sed -e 's/^= DEBMAKE(1)$$/= *debmake*(1) manpage/' -e 's/^=/==/' manpage.txt >99-manpage.txt

binary.txt: manpage.txt
	sed -n -e '/^\*-b\*/,$$p' manpage.txt | sed -e '/^\*-e\*/,$$d'>binary.txt

caveat.txt: manpage.txt
	sed -e '1,/^== CAVEAT/d' manpage.txt | sed -e '/^== DEBUG/,$$d'>caveat.txt

html: $(MANUAL1).html $(MANUAL2).html

%.html: %.txt $(GENTXT) .FORCE
	asciidoc -a toc2 -a 'newline=\n' -a "revision=$(VERSION)" -a date=$(DATE) $<

man: debmake.1

debmake.1: manpage.txt
	a2x --doctype manpage --format manpage manpage.txt

clean:
	-rm -f $(GENTXT)
	-rm -f *.html
	-rm -f debmake.1
	-rm -f *~

remote: new
	scp $(MANUAL1).html people.debian.org:~osamu/public_html/$(MANUAL1).html
	scp $(MANUAL2).html people.debian.org:~osamu/public_html/$(MANUAL2).html

list:
	echo $(ALLTXT)

new:
	$(MAKE) clean
	$(MAKE) all

.FORCE:

.PHONY: all html man clean new remote
