FIGURES=aliases_example.pdf \
	downcheck_resolve_example_1.pdf \
	downcheck_resolve_example_2.pdf \
	orthogonality.pdf \
	rule2a_example.pdf \
	rule2b_example.pdf \
	upcheck_resolve_example_1.pdf \
	upcheck_resolve_example_2.pdf

all : ${FIGURES}

%.pdf : %.tex
	pdflatex $?
	pdflatex $?  # Run again to account for any changed labels, etc.
