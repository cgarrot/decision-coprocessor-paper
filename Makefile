.PHONY: figures paper clean

# Regenerate every figure (SVG + PDF) into paper/figures/.
# Uses uv to provision matplotlib in an ephemeral environment.
figures:
	uv run --with matplotlib --no-project python figures/make_figures.py

# Build the LaTeX paper (requires pdflatex / TeX Live).
paper: figures
	cd paper && pdflatex -interaction=nonstopmode main.tex && pdflatex -interaction=nonstopmode main.tex

clean:
	rm -f paper/*.aux paper/*.log paper/*.out paper/*.toc
