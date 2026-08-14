#!/usr/bin/env bash
# Assemble a self-contained Overleaf bundle from paper/ + figures/.
# Usage: bash scripts/make_overleaf_bundle.sh   (run from the repo root)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# Gate the bundle on the numbers audit. A manuscript number that has drifted
# from the pipeline output that produced it must not reach Overleaf, where
# it becomes something a referee finds rather than something we do.
echo "auditing manuscript numbers against pipeline outputs..."
if ! python3 scripts/audit_paper_numbers.py; then
  echo "ABORT: the manuscript disagrees with the pipeline. Fix before bundling." >&2
  exit 1
fi
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
[ -f paper/main.pdf ] && cp paper/main.pdf "overleaf/Helfrich-NMTC-working-paper.pdf"
cp paper/DECISIONS.md overleaf/DECISIONS.md
cp paper/SSRN_SUBMISSION.md overleaf/SSRN_SUBMISSION.md
python3 - <<'PY'
p = "overleaf/main.tex"; s = open(p).read()
s = s.replace("\\graphicspath{{../figures/}}", "\\graphicspath{{figures/}}")
open(p, "w").write(s)
PY
[ -f overleaf/README.md ] || cp paper/OVERLEAF_README.md overleaf/README.md 2>/dev/null || true
(cd overleaf && zip -qr ../overleaf-nmtc-paper.zip .)
echo "wrote overleaf/ and overleaf-nmtc-paper.zip"
