all: man html

list:
	echo $(wildcard *.txt)

new:
	$(MAKE) clean
	$(MAKE) all

html: debmake.html

debmake.html: $(wildcard *.txt)
	sed -e 's/^= DEBMAKE(1)$$/= *debmake*(1)/' -e 's/^=/===/' XX-manpage.txt >99-manpage.txt
	sed -n -e '/^\*-b\*/,$$p' XX-manpage.txt | sed -e '/^\*-e\*/,$$d'>binary.txt
	sed -e '1,/^== CAVEAT/d' XX-manpage.txt | sed -e '/^== DEBUG/,$$d'>caveat.txt
	asciidoc -atoc2 debmake.txt

man: debmake.1

debmake.1: XX-manpage.txt
	a2x --doctype manpage --format manpage XX-manpage.txt

clean:
	-rm -f debmake.1 *.html binary.txt caveat.txt 99-manpage.txt


.PHONY: all html man clean new
