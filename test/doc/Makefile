all: man html

list:
	echo $(wildcard *.txt)

new:
	$(MAKE) clean
	$(MAKE) all

html: debmake.html

debmake.html: $(wildcard *.txt)
	sed -e 's/^= DEBMAKE(1)$$/= The *debmake*(1) manpage/' -e 's/^=/===/' debmake.1.txt >99-debmake-man.txt
	sed -n -e '/^\*-b\*/,$$p' debmake.1.txt | sed -e '/^\*-e\*/,$$d'>binary.txt
	sed -e '1,/^== CAVEAT/d' debmake.1.txt | sed -e '/^== DEBUG/,$$d'>caveat.txt
	asciidoc -atoc2 debmake.txt

man: debmake.1

debmake.1: debmake.1.txt
	a2x --doctype manpage --format manpage debmake.1.txt

clean:
	-rm -f debmake.1 debmake.html 99-debmake-man.txt binary.txt caveat.txt examples.html


.PHONY: all html man clean new
