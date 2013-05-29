.PHONY: all
all: manual.html

.PHONY: clean
clean:
	rm -f *.html

manual.html: $(wildcard *.txt)
	asciidoc -b html5 manual.txt

.PHONY: upload
upload: all
	rsync -av --delete manual.html images \
		oe-lite.org:/srv/http/doc/core/master/
