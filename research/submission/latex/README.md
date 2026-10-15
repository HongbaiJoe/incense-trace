# Complete paper package

The main `.tex` file and supplementary source are generated from the reviewed Markdown manuscript by:

```bash
uv run python -m xiangji.export_latex
```

The complete paper uses the standard `article` class, numerical citations, 29 numbered equations, eight `booktabs` tables and six vector figures in the body. TeX Gyre Termes and Latin Modern Math provide a portable Times-style text and mathematics pairing. The copied BibTeX database is supplied for reference management; compilation does not depend on it.

Compile from this directory with a current XeLaTeX-compatible engine. The release PDFs were verified with Tectonic 0.17.0:

```bash
tectonic -X compile xiangji_cgir_complete_paper.tex
tectonic -X compile xiangji_cgir_supplementary.tex
```

The DOCX paper uses black Times New Roman throughout and native editable Word equations. The compiled LaTeX PDF is the typographic reference copy.
