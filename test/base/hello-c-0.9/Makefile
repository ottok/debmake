all: hello

hello: hello.c
	gcc -Wall -o hello hello.c

install: hello
	install -D hello /usr/local/bin/hello

clean:
	-rm -f hello

distclean: clean

.PHONY: all install clean distclean
