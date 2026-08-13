#!/usr/bin/env bash
# Assemble a self-contained Overleaf bundle from paper/ + figures/.
# Usage: bash scripts/make_overleaf_bundle.sh   (run from the repo root)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
# Figures actually referenced by the manuscript. Derived from the sections
# so this list cannot silently drift out of sync again.
FIGS=$(grep -rho 'includegraphics\[[^]]*\]{[^}]*}' paper/sections/ \
  | sed 's/.*{//; s/}//' | sort -u)
rm -rf overleaf overleaf-nmtc-paper.zip
mkdir -p overleaf/{sections,tables,figures,figures-tex}
cp paper/main.tex paper/helfrich-wp.sty paper/references.bib overleaf/
cp paper/sections/*.tex overleaf/sections/
cp paper/tables/*.tex   overleaf/tables/
cp paper/figures-tex/*.tex overleaf/figures-tex/
for f in $FIGS; do
  if [ ! -f "figures/$f" ]; then echo "MISSING figure: $f" >&2; exit 1; fi
  cp "figures/$f" overleaf/figures/
done
[ -f paper/main.pdf ] && cp paper/main.pdf overleaf/main-preview.pdf
python3 - <<'PY'
p = "overleaf/main.tex"; s = open(p).read()
s = s.replace("\\graphicspath{{../figures/}}", "\\graphicspath{{figures/}}")
open(p, "w").write(s)
PY
[ -f overleaf/README.md ] || cp paper/OVERLEAF_README.md overleaf/README.md 2>/dev/null || true
(cd overleaf && zip -qr ../overleaf-nmtc-paper.zip .)
echo "wrote overleaf/ and overleaf-nmtc-paper.zip"
