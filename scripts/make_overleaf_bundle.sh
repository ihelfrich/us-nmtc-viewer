#!/usr/bin/env bash
# Assemble a self-contained Overleaf bundle from paper/ + figures/.
# Usage: bash scripts/make_overleaf_bundle.sh   (run from the repo root)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
FIGS=(1_allocation_timeseries.png 2_non_metro_share_timeseries.png
      3_leverage_distribution.png 6_bunching_diagnostic.png
      7_switcher_spines.pdf)
rm -rf overleaf overleaf-nmtc-paper.zip
mkdir -p overleaf/{sections,tables,figures,figures-tex}
cp paper/main.tex paper/helfrich-wp.sty paper/references.bib overleaf/
cp paper/sections/*.tex overleaf/sections/
cp paper/tables/*.tex   overleaf/tables/
cp paper/figures-tex/*.tex overleaf/figures-tex/
for f in "${FIGS[@]}"; do cp "figures/$f" overleaf/figures/; done
[ -f paper/main.pdf ] && cp paper/main.pdf overleaf/main-preview.pdf
python3 - <<'PY'
p = "overleaf/main.tex"; s = open(p).read()
s = s.replace("\\graphicspath{{../figures/}}", "\\graphicspath{{figures/}}")
open(p, "w").write(s)
PY
[ -f overleaf/README.md ] || cp paper/OVERLEAF_README.md overleaf/README.md 2>/dev/null || true
(cd overleaf && zip -qr ../overleaf-nmtc-paper.zip .)
echo "wrote overleaf/ and overleaf-nmtc-paper.zip"
