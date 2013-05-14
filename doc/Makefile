.PHONY: all
all: manual.html

.PHONY: clean
clean:
	rm -f *.html

%.html: %.doc
	a2x -f chunked -d book $< -v
	a2x -f text -d book $< -v
	a2x -f xhtml -d book $< -v

.PHONY: upload
upload: manual.html
	scp docbook-xsl.css $< oe-lite.org:/srv/http/download/manual/current
