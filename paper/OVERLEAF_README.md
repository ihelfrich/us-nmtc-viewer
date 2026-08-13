# The Rural Mobilization Gap — complete project folder

Everything needed to read, compile, edit, or submit the paper.

## Read it now
`Helfrich-NMTC-working-paper.pdf` — the compiled 18-page paper.

## Edit it on Overleaf
1. Overleaf → **New Project → Upload Project** → select
   `overleaf-nmtc-paper.zip` (or drag this whole folder in).
2. Menu → **Main document:** `main.tex`.
3. Menu → **Compiler:** pdfLaTeX (XeLaTeX also compiles).
4. Recompile. If citations render as `[?]`, press Recompile once more so
   BibTeX runs.

## What each file is
| Path | Purpose |
|---|---|
| `main.tex` | Root document. Title block, abstract, section inputs, bibliography. |
| `helfrich-wp.sty` | **The house style: everything visual lives here.** Type (EB Garamond display over a Palatino text face), the four-color palette, page geometry with a working margin, section titling, captions, float tuning, the `\sidenote{}` command, and the hand-drawn TikZ pen styles. Change this file to restyle the whole paper. |
| `sections/00-08` | One file per section, in reading order. |
| `tables/*.tex` | Table bodies. **Generated** by `scripts/make_paper_tables.py` in the research repo. |
| `figures/` | The five exhibits used in the text. |
| `figures-tex/fig-mechanics.tex` | The hand-drawn program diagram, editable TikZ source. |
| `references.bib` | 21 entries, `plainnat`. |
| `DECISIONS.md` | Every analytical and editorial decision (D1–D12) with its rationale and verification. Read this before changing a number. |
| `SSRN_SUBMISSION.md` | Paste-ready submission metadata and the pre-upload checklist. |

## Two rules worth keeping
- **Do not hand-edit `tables/`.** Every number in them is written by a script
  that read it from the pipeline. Change the generator in the research repo
  (`scripts/make_paper_tables.py`), rerun, and re-copy. The same holds for
  `figures/`, which come from `make_paper_figures.py` and `make_paper_art.py`.
- **Figures are drawn at their printed width** (the 4.9in text block) so that
  `\includegraphics[width=\textwidth]` applies no scaling. If you resize a
  figure in LaTeX, its labels stop matching the body type.

## Known cosmetic warning
Under XeLaTeX you may see `Font shape T1/EBGaramond(0)/m/n undefined`. The
title still sets in EB Garamond, which resolves through the Unicode font
path; pdfLaTeX has the Type 1 files and does not warn. Output is correct on
both engines.

## Provenance
Data, pipeline, and full history: https://github.com/ihelfrich/us-nmtc-viewer
