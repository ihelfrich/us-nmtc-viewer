import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper"


def _read(relative_path: str) -> str:
    return (PAPER / relative_path).read_text(encoding="utf-8")


def test_title_block_has_one_author_and_names_contributors_separately():
    main = _read("main.tex")

    title_block = main[main.index(r"\wptitle") : main.index(r"\begin{abstract}")]
    assert title_block.count(r"\textsc{") == 1
    assert r"\textsc{Ian Helfrich}" in title_block
    assert "Sole author and originator" in title_block
    assert "With contributions from Katia Antunes and Elizaveta Gonchar" in title_block


def test_contribution_record_does_not_invent_roles_or_coauthor_approval():
    appendix = _read("sections/08-appendix.tex")
    normalized = " ".join(appendix.split())

    assert r"\section*{Contributors and authorship}" in appendix
    assert "Ian Helfrich is the sole author and originated the study." in normalized
    assert "Katia Antunes and Elizaveta Gonchar contributed to the project." in normalized
    assert "All authors" not in appendix
    assert "developed the blended-finance framing" not in appendix
    assert "contributed to the empirical design" not in appendix


def test_ssrn_kit_has_one_author_and_separate_contributors():
    kit = _read("SSRN_SUBMISSION.md")

    author_block = kit[kit.index("**Author:**") : kit.index("**Contributors:")]
    assert "Ian Helfrich" in author_block
    assert "Katia Antunes" not in author_block
    assert "Elizaveta Gonchar" not in author_block

    contributor_block = kit[kit.index("**Contributors:") : kit.index("**Abstract:")]
    assert "Katia Antunes" in contributor_block
    assert "Elizaveta Gonchar" in contributor_block
    assert "co-author" not in kit.lower()


def test_solo_authored_manuscript_uses_singular_authorial_voice():
    plural_voice = re.compile(r"\b(?:we|our|us)\b", flags=re.IGNORECASE)
    offenders = []

    for path in sorted((PAPER / "sections").glob("*.tex")):
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if plural_voice.search(line):
                offenders.append(f"{path.relative_to(ROOT)}:{line_number}: {line.strip()}")

    assert not offenders, "Plural authorial voice remains:\n" + "\n".join(offenders)
