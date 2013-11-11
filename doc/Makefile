.PHONY: all
all: autodoc manual.html

.PHONY: clean
clean:
	rm -Rf *.html auto/

autodoc: FORCE
	oe autodoc meta/core
FORCE:

manual.html: $(wildcard *.txt)
	asciidoc -b html5 manual.txt

.PHONY: upload
upload: all
	rsync -av --delete manual.html images \
		oe-lite.org:/srv/http/doc/core/
