# Overleaf bundle — The Rural Mobilization Gap (Helfrich 2026)

Self-contained. Nothing outside this folder is required.

## Uploading
1. Overleaf → New Project → **Upload Project** → drop `overleaf-nmtc-paper.zip`
   (or upload this folder).
2. Menu → **Main document**: `main.tex`.
3. Menu → **Compiler**: pdfLaTeX (XeLaTeX also compiles).
4. Recompile. BibTeX runs automatically; if citations show as `[?]`, hit
   Recompile once more.

## What is here
| Path | What it is |
|---|---|
| `main.tex` | root document: title block, abstract, `\input`s, bibliography |
| `helfrich-wp.sty` | the house style. Type, color, geometry, section titling, captions, the `\sidenote{}` command, and the hand-drawn TikZ pen styles all live here. Edit this to restyle the whole paper. |
| `sections/00-08` | one file per section, in reading order |
| `tables/*.tex` | table bodies, **generated** by `scripts/make_paper_tables.py` in the research repo. Editing them by hand breaks the guarantee that every number traces to the pipeline; change the generator instead and re-copy. |
| `figures/` | the five raster/vector figures used in the text |
| `figures-tex/fig-mechanics.tex` | the hand-drawn program diagram, as TikZ source you can edit directly |
| `references.bib` | BibTeX, `plainnat` style |

## Editing notes
- **Restyle:** everything visual is in `helfrich-wp.sty`. The palette is four
  colors (`inkblack`, `inkblue`, `penblue`, `pencil`); the accent is used only
  for structure.
- **Margin notes:** `\sidenote{...}` puts an italic note in the outer margin.
  The geometry already reserves 1.7in for it.
- **The sketch:** `figures-tex/fig-mechanics.tex` is plain TikZ using the
  `fineliner`, `fountain`, and `pencilline` styles defined in the `.sty`.
- **Regenerating numbers:** tables and the switchboard figure come from
  `github.com/ihelfrich/us-nmtc-viewer` (`scripts/make_paper_tables.py`,
  `scripts/make_paper_art.py`). Re-run those, then copy `paper/tables/*.tex`
  and `figures/7_switcher_spines.pdf` back into this bundle.

## Provenance
`DECISIONS.md` in the research repo logs every analytical and editorial
decision (D1–D11) with its rationale and verification.
