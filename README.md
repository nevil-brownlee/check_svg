XML parser to check SVG against [draft-brownlee-svg](http://tools.ietf.org/html/draft-iab-svg-rfc).

check-svg.py will read a .svg file and display messages about elements in the svg file that don't conform to the SVG-1.2-RFC syntax published as
draft-iab-svg-rfc-01.txt

check-svg.py -n xxx.svg  will strip out non-conforming elements and write a new file, xxx-new.svg, that does conform.  You can then display the -new file (e.g. with Firefox) to check that it looks the same.

check-svg.py is a simple (not to say 'quick and dirty') test program, it does not use the full RNC syntax set out in the draft.  Instead, word_properties.py contains a python version of the syntax, which check-svg.py uses.

check-svg.py has been tested with .svg files produced by Inkscape, LibreOffice, Dia, Graphviz and several other svg drawing programs.

In the longer term a better, production program will be developed to do these checks and transformations.

The LICENSE.md file continues to apply to check-svg.py and word_properties.py.


Nevil Brownlee, 28 Jan 2016 (NZDT)
