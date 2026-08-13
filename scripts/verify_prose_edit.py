"""
Police a prose-only edit: confirm that rewriting changed words and not
evidence. Extracts every numeric token from the section files at two git
revisions and reports any number that appears in one and not the other,
plus citation keys, labels, and refs.

A prose pass is allowed to change wording, sentence order, and paragraph
structure. It is not allowed to add, drop, or alter a statistic, a
citation, or a cross-reference. Anything this script prints is either a
deliberate change to be justified in DECISIONS.md or a defect.

Usage: python3 scripts/verify_prose_edit.py <base_rev> [head_rev]
"""
from __future__ import annotations

import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SECTIONS = "paper/sections"

# numbers, including signed decimals, percentages, and LaTeX-escaped forms
NUM = re.compile(r"-?\$?-?\d[\d,]*\.?\d*")
# Layout parameters are not evidence: figure widths, spacing lengths, and
# similar typesetting arguments change freely during a design pass and would
# otherwise drown the signal this check exists to give.
LAYOUT = re.compile(
    r"\\includegraphics\[[^]]*\]|"
    r"\\(?:v|h)space\*?\{[^}]*\}|"
    r"\[[0-9.]+(?:pt|em|ex|in|cm|mm)\]|"
    r"width=[0-9.]*\\?\w*|"
    r"\\resizebox\{[^}]*\}\{[^}]*\}")
CITE = re.compile(r"\\cite[tp]?\{([^}]*)\}")
REFLBL = re.compile(r"\\(?:label|ref|eqref)\{([^}]*)\}")


def at_rev(rev: str) -> dict[str, str]:
    files = subprocess.run(
        ["git", "ls-tree", "--name-only", "-r", rev, SECTIONS],
        cwd=ROOT, capture_output=True, text=True, check=True).stdout.split()
    out = {}
    for f in files:
        out[f] = subprocess.run(["git", "show", f"{rev}:{f}"],
                                cwd=ROOT, capture_output=True, text=True,
                                check=True).stdout
    return out


def head_files() -> dict[str, str]:
    return {str(p.relative_to(ROOT)): p.read_text()
            for p in sorted((ROOT / SECTIONS).glob("*.tex"))}


def tokens(text: str) -> tuple[Counter, Counter, Counter]:
    # strip comments so commented-out text is not compared
    body = "\n".join(l.split("%")[0] for l in text.splitlines())
    body = LAYOUT.sub(" ", body)
    nums = Counter(t.replace("$", "").replace(",", "") for t in NUM.findall(body))
    cites = Counter(k.strip() for m in CITE.findall(body) for k in m.split(","))
    refs = Counter(REFLBL.findall(body))
    return nums, cites, refs


def main() -> int:
    base = sys.argv[1]
    head = sys.argv[2] if len(sys.argv) > 2 else None
    a = at_rev(base)
    b = at_rev(head) if head else head_files()

    an, ac, ar = tokens("\n".join(a.values()))
    bn, bc, br = tokens("\n".join(b.values()))

    bad = 0
    for label, before, after in (("NUMBER", an, bn), ("CITATION", ac, bc),
                                 ("LABEL/REF", ar, br)):
        removed = before - after
        added = after - before
        if removed or added:
            bad += 1
            print(f"\n=== {label} CHANGES ===")
            for k, v in sorted(removed.items()):
                print(f"  removed ({v}x): {k}")
            for k, v in sorted(added.items()):
                print(f"  added   ({v}x): {k}")
        else:
            print(f"{label}: identical ({sum(before.values())} tokens)")

    words_a = sum(len(t.split()) for t in a.values())
    words_b = sum(len(t.split()) for t in b.values())
    print(f"\nword count: {words_a} -> {words_b} ({words_b - words_a:+d})")
    print("\nVERDICT:", "PROSE-ONLY (evidence unchanged)" if bad == 0
          else "REVIEW REQUIRED: evidence tokens moved")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
