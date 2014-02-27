# License list: http://spdx.org/licenses/

all: header

licenses: list.txt
	-mkdir -p licenses/
	for x in $$(cat list.txt); do \
	w3m -dump http://spdx.org/licenses/$$x > licenses/$$x; \
	done

header:
	-mkdir -p header
	for x in licenses/* ; do \
	y=`basename $$x` ; \
	sed -n -e '/^Standard License Header/,/^Who are we\?/p' <$$x  > header/$$y ; \
	done
text:
	-mkdir -p text
	for x in licenses/* ; do \
	y=`basename $$x` ; \
	sed -n -e '/^Text/,/^Standard License Header/p' <$$x  > text/$$y ; \
	done

list.txt:
	wget -O - http://spdx.org/licenses/ | \
	sed -n -e'/<table/,/<\/table/p' | \
	sed -n -e '/<code/s/^.*<code property="spdx:licenseId">\(.*\)<\/code><\/td>.*/\1/p' >list.txt

#<code property="spdx:licenseId">OSL-2.0</code></td>

clean:
	-rm -rf licenses

.PHONY: all clean licenses header text
