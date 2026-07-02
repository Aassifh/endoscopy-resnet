.PHONY: all tables clean en fr

TECTONIC ?= tectonic

all: en fr

tables:
	python3 ../../scripts/generate_paper_tables.py

en: tables
	cd en && $(TECTONIC) main.tex

fr: tables
	cd fr && $(TECTONIC) main.tex

clean:
	rm -f en/*.aux en/*.log en/*.bbl en/*.blg en/*.out en/*.pdf
	rm -f fr/*.aux fr/*.log fr/*.bbl fr/*.blg fr/*.out fr/*.pdf
