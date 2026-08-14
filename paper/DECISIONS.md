# Decision log — NMTC working paper, referee-fix round (2026-08-13)

Standard for this document: every analytical choice made in this round is
recorded with its rationale; nothing in the manuscript asserts a quantity
that was not computed in this repository; validation checks that could be
automated are hard assertions inside the scripts and the run fails if they
fail. No observation in the data was added, dropped, or edited in this
round; every change below is a change of analysis or of claim, not of data.

## D1. Gelbach decomposition replaces the sequential story as primary

**Decision.** Report the Gelbach (2016) full-model-reference decomposition
of the raw rural gap alongside the layered table, and treat it as the
primary decomposition when attributing the gap to covariate blocks.

**Rationale.** Sequential FE addition is path-dependent: the "QALICB type
explains about a quarter" reading from M1 to M2 depends on the order the
blocks enter. The Gelbach decomposition is invariant to listing order.
Computed result: of the raw-to-full movement of -0.216, the CDE block
contributes -0.185 (85.6%), QALICB type -0.041 (19.2%), year +0.010
(-4.8%). The V1 text's "roughly a quarter from type" was an artifact of
sequencing and is corrected in the revision.

**Validation.** The identity (beta_M0 - beta_full = sum of block
contributions) is a hard assertion at 1e-8; observed residual 4.8e-15.
The hand-built design matrix reproduces the formula-API M4 coefficient to
1e-6 (asserted).

## D2. The headline ratio is demoted; the level component is promoted

**Decision.** Stop headlining "82.2% of the gap is selection" as a
precisely-known quantity. Report instead: the CDE component of the raw gap
is -0.185, CDE-cluster bootstrap 95% CI [-0.347, -0.023]; the selection
share point estimate is 82% with bootstrap CI [25%, 255%], reported with
that interval.

**Rationale.** The share is a ratio of two estimated coefficients whose
denominator resamples; its bootstrap distribution is wide and crosses 100%.
Honest inference lives at the level of the component (which excludes zero),
not the ratio. Claims sized to what the data can bear.

## D3. The mean null is reported as underpowered; the median carries the null

**Decision.** State explicitly that the mean specification's cluster-robust
CI is [-0.245, +0.151] and that a one-sided 5% test can only reject
within-CDE penalties larger than 0.213 - nearly the raw gap - so the mean
regression alone is weak evidence of a zero. The median regression
(beta = -0.001, SE 0.008, rejectable bound 0.013) carries the precision.

**Rationale.** "Statistically insignificant" was previously allowed to
imply "zero." Equivalence logic is the honest frame: report the smallest
penalty the design can reject, for both estimators.

**Caveat recorded.** The median SE is the quantreg asymptotic (kernel) SE,
not CDE-clustered; a clustered bootstrap of the median with ~600 fixed
effects was judged computationally disproportionate for V1 and is listed as
an outstanding item. The mean-vs-median SE gap (0.101 vs 0.008) also
reflects the outcome's long right tail, which inflates mean-regression
variance; this is stated in the text.

## D4. Extensive/intensive margins added

**Decision.** Add an LPM for P(leverage > floor) and an OLS on leverage
among mobilizing projects, both with the M4 fixed effects and CDE
clustering; floors 1.001 (the data's exact-floor mass) and 1.05
(sensitivity).

**Rationale.** 27.4% of projects sit at the leverage floor (zero private
mobilization); a mean effect could hide offsetting margins. Computed: both
margins are null within CDE (extensive -0.018, p=0.34; intensive -0.039,
p=0.77; stable at the 1.05 floor). The floor values are analysis choices,
not data edits; both are reported.

## D5. Switcher diagnostics reported

**Decision.** Report that 163 of 343 CDEs operate on both sides of the
rural line and hold 93.9% of rural projects.

**Rationale.** With CDE fixed effects, the rural coefficient is identified
only by such switchers; a referee should be shown that the identifying set
is broad, not a sliver. (The 343 differs from the bunching test's 310
because the bunching sample conditions on >= 5 transactions; both bases are
stated where used.)

## D6. Remaining robustness rows filled

**Decision.** Add the top-50-CDE subsample (beta -0.100, SE 0.148, n=4,229)
and two-way clustered SEs by CDE and tract via Cameron-Gelbach-Miller
inclusion-exclusion (SE 0.105 vs one-way 0.101).

**Rationale.** These were the two unrun rows from the paper outline's own
robustness plan (5.3.5, 5.3.6). CGM positivity is asserted in code; the
one-way CDE piece is asserted to reproduce the headline M4 fit exactly.

## D7. The interpretation caveat is moved into the paper's front matter

**Decision.** State in the empirical-strategy and discussion sections that
the between-CDE component is a composition fact, and that its "selection"
reading is an interpretation: rural market conditions could in principle
*cause* the specialization of low-leverage intermediaries into rural
deployment, in which case part of the between-CDE component is market
structure operating through intermediary business models. The within-CDE
null (precise at the median, both margins) is the paper's secure claim.

**Rationale.** This is the strongest referee objection to the paper's
framing and it is better raised by the paper than by a referee.

## D8. Sample notes

The analysis sample for the referee-fix round is the same 8,024 projects as
the main pipeline (requiring tract_fips removed zero rows). No winsorization
or trimming choices changed in this round. The bunching analysis is
unchanged. Bootstrap: 499 CDE-cluster resamples, seed 20260813, zero failed
replications; resampled duplicate CDEs are treated as distinct clusters
(standard cluster-bootstrap practice).

## D9. SSRN pass (2026-08-13, second round)

**Decision.** Before submission, every institutional claim inherited from
the outline was recomputed against the release. Three were false and are
corrected in the text: (a) "roughly 600 CDEs" -> the release names 345
distinct CDEs in the transaction ledger (343 at the project level); (b)
"top twenty CDEs account for more than half of dollars" -> computed 23.9%
of QLICI dollars, described as moderate concentration; (c) "shares range
0% to 80%+" -> the computed range is 0% to 100%, with 39% of >=5-tx CDEs
never deploying non-metro and 6.5% at 80%+. The outline's figures likely
referred to certified allocatees program-wide; the paper now claims only
what its own ledger shows.

**Also in this pass.** Deployment figures (annual QLICI, non-metro share
vs the 20% line) added to the data section; the Gelbach table moved after
the main table so numbering follows the narrative; eleven bibliography
entries added and cited in text (program-evaluation and place-based
literatures). Compile verified: zero undefined references, zero warnings.

## D10. Overleaf restructure, house style, and artwork (2026-08-13)

**Decision.** The manuscript becomes a multi-file Overleaf project:
main.tex + helfrich-wp.sty + sections/00-08 + references.bib (BibTeX,
plainnat) + figures-tex/ (TikZ) + generated tables/. The style commits to
Palatino text and math, a narrow book measure with a wide working margin,
one fountain-ink accent reserved for structure, small-caps hairline
captions, and a sidenote command for the margin.

**Artwork decisions.** Two registers, per the author's direction. (a) A
hand-drawn institutional sketch of the program's mechanics, built as TikZ
with random-step path decoration in fineliner/fountain/pencil weights, so
the drawing stays vector-exact while reading as a working sketch. (b) The
switchboard figure: each dual-market CDE as a spine from urban-book mean
to rural-book mean, ordered by pooled mean, with a marginal distribution
of within-CDE gaps against zero. Sample rule: at least three projects per
side (104 CDEs qualify); the rule, the medians, and the ranges displayed
are recorded in figures/7_switcher_spines.json, and the pooled-mean
between-books identity is asserted in the generator. The figure's second
annotation was revised before inclusion because its first draft ("books
sit nearly on top of each other") overstated what the spines show; the
accurate claim is that gaps center on zero and are an order of magnitude
smaller than the between-CDE range. Statistics quoted in Section 5.2's
new paragraph (104, median -0.12, IQR [-0.46, +0.36], levels 1.0-4.0)
come from that sidecar.

**Prose decision.** Paragraph-opening single-clause sentences were
expanded in four places (introduction, results twice, discussion) per the
author's stylistic direction; content unchanged.

## D11. Cross-model review round (2026-08-13)

Two reviewers worked the paper independently: this session's own pass and
Codex (gpt-5.6-sol, xhigh), whose report is preserved as
paper/CODEX-PAPER-REVIEW.md. I verified every claim from that report
computationally or against primary sources before acting on it; the
verification script is scripts/run_review_round2.py and its outputs are in
data/processed/regressions/review_round2.json. Both reviewers independently
flagged the loose "order of magnitude" quantifier, which was wrong: the
ratio of the raw to the within-CDE coefficient is 5.6.

**D11.1 The workhorse was not nested (structural).** The published M4 adds
CDE effects while dropping the state effects of M3, so the layered
narrative describing an addition was inaccurate. I estimated the strictly
nested model carrying year, type, state, and CDE effects: the rural
coefficient is -0.0602 (SE 0.0991, p = 0.54), and its R-squared weakly
exceeds both restricted models, which is asserted in code. The nested model
now appears as column 7 of Table 2 and the text states the substitution
plainly. The paper's conclusion is unchanged and better supported.

**D11.2 QLICI principal is not a federal dollar (substantive).** The draft
called the QLICI a public or federal dollar and read leverage minus one as
private capital mobilized per federal dollar. That is wrong: the federal
cost is the 39% credit claimed against the qualified equity investment, so
a dollar of QLICI corresponds to roughly thirty-nine cents of tax
expenditure. The abstract and data section now describe leverage as a
financing multiple on subsidized investment and report both denominators
($0.82 of other capital per dollar of subsidized investment; about $2.09
per dollar of implied tax expenditure). No estimate changes, because a
constant rescaling of the denominator leaves every coefficient's sign,
relative magnitude, and test unchanged.

**D11.3 The mandate citation was wrong and the period was wrong.** The
draft attributed the non-metropolitan proportionality rule to the 2000
authorizing act. Verified against the U.S. Code: the instruction is IRC
Sec. 45D(i)(6), added by the Tax Relief and Health Care Act of 2006
(P.L. 109-432, Sec. 102(b)), so it does not govern the early sample. The
statute names no percentage; the 20% figure is the CDFI Fund's
administrative implementation, and the paper now says so and carries a
footnote directing readers to primary sources. The excess-mass test is
additionally reported for origination years from 2007 onward, where the
rule applies: -0.003 in counts and +0.001 in dollars, both intervals
containing zero across 291 CDEs.

**D11.4 The mandate is described in investment terms, so the test now uses
dollars.** The published test used deal counts. Dollar shares give excess
mass of +0.005 with interval [-0.008, +0.020]; the two share measures
correlate at 0.98. Both are reported. The word "notch" is removed, since
no discontinuity in the CDE budget set at 20% is established.

**D11.5 Numeric corrections.** CI upper endpoint 0.151 to 0.152 (three
places, matching the sidecar's rounding of 0.1515); unwinsorized within-CDE
coefficient -0.215 to -0.216 (exact value -0.215500); "roughly six hundred
fixed effects" to 343, the count in the estimation sample; "27.4% sit
exactly at the leverage floor" restated as measured at the 1.001 threshold;
"eight directions" replaced with the list of dimensions; the Table 2 caption
corrected, since column 6 reports an unclustered quantile-regression
standard error and had been described as CDE-clustered.

**D11.6 Claims qualified.** The two novelty claims now carry the caveat
that a negative about a literature this size cannot be proven from a
reference list.

**D11.7 Project hygiene.** The appendix now precedes the bibliography;
main.tex documents that compilation happens from paper/; a duplicate
sec:bunching label was removed. Compile is clean: no undefined references,
no multiply-defined labels.

**Reviewer objections recorded and not yet resolved.** Codex's third
referee point stands as a limitation rather than a fix: with a discrete,
bimodal share distribution and a polynomial counterfactual, the excess-mass
test has limited power near 20%, so its null cannot establish that the
target fails to bind. The paper should not, and now does not, claim more
than the absence of detectable bunching.

## D12. Second Codex round: figures rebuilt, prose humanized (2026-08-13)

**Graphics.** scripts/make_paper_figures.py regenerates the four legacy
matplotlib exhibits as paper_*.pdf/.png in the house design: serif type,
ink and pencil with the accent reserved for the focal element, hairline
spines, direct labels in place of framed legends, and no baked-in titles
duplicating the LaTeX captions. The originals are untouched, since the
viewer site uses them. The bunching estimator is reproduced exactly from
run_regressions.py rather than reimplemented, and each figure prints a
provenance line: 19,907 transactions and $66.6B QLICI; 22 years at a 19.6%
overall non-metro share; 8,024 projects with medians of 1.19x and 1.07x;
310 CDEs with B = -0.0006. All four match the manuscript.

I overrode one choice. The first pass painted the entire bunching
histogram in signal blue, which puts the accent on the distribution
instead of on the target the figure is about; bars are now ink at 62%
opacity and the accent marks the 20% line and its test window.

**Prose.** The section files were rewritten to remove the standard
machine-written tells: self-congratulatory meta-commentary ("This paper is
deliberate about...", "the paper reports it where it lives", "is the
paper's central exhibit"), throat-clearing openers, rule-of-three padding,
paragraph-ending restatements, and over-balanced clause pairs. Word count
fell from 4,536 to 3,948, about 13%, with no claim added, weakened, or
strengthened.

**Verification.** scripts/verify_prose_edit.py extracts every numeric
token, citation key, and cross-reference from the section files at two
revisions and diffs them. Against the pre-edit baseline (2d97430):
citations identical at 21, labels and references identical at 41, and the
single reported numeric difference is an artifact of the regex reading the
em dash in "---82\%" as part of the number when that dash became a comma.
No statistic moved. Compile is clean, and the two figure tests pass.

**Two edits restored.** The rewrite dropped "and cannot" from the sentence
describing what the mean regression can rule out, which removes the
concession that carries the paragraph's honesty, and it dropped the
two-word answer ("It does not.") to the question the margins paragraph
poses. Both are back. One further word choice was corrected: "outcomes"
was used to mean "estimates" in the introduction, which collides with the
term's technical sense in this paper.

## D13. Design and legibility pass (2026-08-13)

**The opening pages.** A separate title page left two thirds of a sheet
blank, which reads as an unfinished draft, and the abstract then filled a
second page as an unbroken block of three hundred words. Title, abstract,
and keywords now share the opening page, the abstract is set in a flowing
indented measure that can break across pages rather than a minipage that
cannot, and it is divided into three paragraphs at its natural joints.
Section 1 follows on the same page as the keywords.

**Type.** EB Garamond is loaded first only so its family name can be
captured, after which newpxtext is loaded and wins the body. The title,
section headings, running heads, and the author line therefore set in a
classical display face while the reading text keeps Palatino's larger
x-height. Under XeLaTeX this raises a benign warning about a T1 shape,
since the display face resolves through the Unicode path; pdfLaTeX has the
Type 1 files and does not warn. Output is correct on both engines and the
README says so.

**Figures were illegible and are now drawn at the size they print.** The
exhibits were generated 6.5 to 10.6 inches wide and then scaled into a 4.9
inch measure, which shrank their labels to roughly five points. Every
figure is now drawn at 4.9 inches with type set for that size, and included
at width=\textwidth so no scaling occurs. The two deployment panels are
stacked rather than placed side by side at 0.48 width each, and the caption
was corrected from left and right to above and below. The switchboard lost
its internal title and subtitle, which duplicated the caption and collided
with each other at the smaller size, and its annotations were shortened and
moved into empty quadrants.

**Layout faults fixed.** Section headings were stranded at the feet of
pages with their rules carried to the next; every heading now reserves
seven lines for itself. Float thresholds were loosened, since LaTeX's
defaults are tuned for a wider measure and were leaving thirds of pages
blank. The section rule now sits against its heading instead of floating
below it. The two tables that overflowed the measure by 97 and 75 points
are set in footnotesize with tightened column separation, and one sentence
was rewrapped; the worst remaining overhang is 18 points, which is ordinary
in justified text.

**A defect this pass introduced and caught.** Wrapping the main table in a
size group added an opening brace whose closing brace landed in the wrong
branch of the generator, so the table was unbalanced and the document
stopped compiling. The clean-room bundle check caught it. Both the
generator and the bundle script now fail loudly instead of producing
output that does not build.

**Harness correction.** verify_prose_edit.py counted figure widths and
spacing lengths as evidence, so a design pass looked like a change to the
numbers. Layout arguments are now stripped before comparison. Against the
pre-design revision the section files carry 241 numeric tokens, 21
citations, and 41 references, all identical.

## D14. Second author added (2026-08-14)

Katia Antunes joins the byline at the author's instruction. Both ORCIDs
were verified against the ORCID public API rather than trusted as
transcribed: 0000-0002-4105-1635 resolves to Ian Helfrich and
0009-0003-1901-0137 resolves to Katia Antunes, both public records. Hers
arrived by text on 12 May 2026, typed out because a screenshot failed to
send; she wrote "orchid," which is why keyword searches of email never
surfaced it.

**Consequential edits.** A two-author paper cannot narrate in the first
person singular, so fifteen instances of "I" were conjugated to the plural
by hand, one at a time, since the verbs do not all take the same form.

**An affiliation I got wrong and corrected.** I first listed Katia at
Universidade de Trás-os-Montes e Alto Douro, inferring it from a funding
email that discusses CETRAD at UTAD. Reading the message properly shows the
opposite: it recommends she *contact* that group. The same email places her
at American University as a graduating senior, which is what the title
block now says, and the checklist asks her to confirm it.

**Author contributions.** The appendix opens with a contributions
statement, drafted from the project record and marked in the source for
both authors to confirm. It exists because the work grew out of an advising
relationship, and the honest remedy for that is to say plainly who did
what. The larger question of whether the division stated there is the right
one remains with the authors; the statement is a placeholder until they
confirm it.

**SSRN.** Her SSRN author ID is not on record. Messages contain only
abstract links from her literature sweep. SSRN requires each co-author to
hold an account before a paper posts under both names, so the kit records
that she must register, or that the paper posts and adds her afterwards.

## D15. Elizaveta Gonchar's ORCID, confirmed (2026-08-14)

The record 0000-0002-5372-9669 was held back in D14 because its education
section reproduced five of Ian Helfrich's six degrees with identical end
dates, including the MS in Geographic Information Science and Technology
housed in City and Regional Planning. That pattern is what a record
populated from the wrong CV looks like, and an incorrect ORCID on a
submission attributes the work to a stranger.

It resolves in her favour. The ORCID record carries a researcher URL to
elizaveta-gonchar.com. That site is hers: it gives elizaveta.gonchar@gmail.com,
the address that appears in her correspondence with the first author, and it
states a Georgia Tech PhD in Economics completed 2024 together with an MS in
Geographic Information Science and Technology completed 2022. The GIS&T
degree is the entry that raised the doubt, and her own site confirms she
holds it. The record's keywords, GIS, economics, and international trade,
match her stated fields. Independent corroboration sits in the first
author's July 2024 correspondence describing her as his coauthor on Trade in
the Spotlight and as defending in the same period. The overlap is a shared
path through the same programs, not a copied record.

The ORCID is now on the title block. Her affiliation reads "independent
researcher" because her own site places the Carnegie Mellon Block Center
role in the past tense and names no current institution; the checklist asks
her to confirm the wording. Her contribution line remains a placeholder
written without a record to draw on, and still needs her own words.

## D16. The education overlap, explained by the authors (2026-08-14)

The first author confirms directly that the overlap D15 investigated is a
shared path rather than a records error. The two authors have attended
Barcelona School of Economics, Indiana University Bloomington, and Georgia
Tech together, and every graduate degree is the same except Barcelona,
where Gonchar earned an MSc in Economics and Finance and Helfrich an MSc in
Specialized Economic Analysis: Public Policy. D15's inference from her
website was correct, and the question is now closed on the authors' own
statement rather than on inference.

Two small inaccuracies surfaced in the process and are recorded here rather
than changed unilaterally, since both belong to their owners. The first
author's public CV renders the Barcelona degree as "Economics & Public
Policy", which may be a deliberate simplification of its official name. Her
ORCID record renders hers as "MSc in Economics" rather than Economics and
Finance.

## D17. Author lines settled (2026-08-14)

Gonchar's line now reads "Applied economist", taken verbatim from how she
introduces herself on her own site ("Applied Economist | PhD in Economics +
MS in GIS-T"), at the first author's instruction to follow her record as
she puts it. This replaces "independent researcher", which was my
inference from the absence of a current employer rather than anything she
had written. Her ORCID record lists no employment, and her people page
withholds affiliation at her preference, so her own words are the only
faithful source available.

Separately, the first author's public CV rendered his Barcelona degree as
"Economics & Public Policy". The programme is Specialized Economic
Analysis with a public policy track, which is what a transcript shows, and
the shorthand would not survive verification. The site now leads with the
official name and carries the track in parentheses, in the CV list, the CV
trajectory label, the about-page ladder, and the people record.

## D18. The ladder, and a broken table caught by reading the proof (2026-08-14)

**A new exhibit.** The paper's central movement, a coefficient collapsing
as fixed effects enter, existed only as a seven-column table, which asks a
reader to hold seven numbers in mind to see one thing. Figure 4 draws each
specification's estimate with its 95 percent interval on one axis: the
interval crosses zero exactly when intermediary identity enters and stays
there in the strictly nested model. A second panel carries the
order-invariant decomposition, so the reader sees where the gap went rather
than only that it went. Every value is read from the same pipeline outputs
that build Tables 2 and 3; nothing is typed in.

**Table 2 was silently broken and is now fixed.** Adding a size wrapper
above the table in D13 shifted every row by one, while the code that
appends the nested column addressed rows by position. Column 7 was
scattered into the wrong rows: its header landed on the top rule, its
coefficient on a midrule, its sample size in the R-squared row. The
compiled table looked wrong in the proof and nowhere else, since LaTeX
raised no error. The append now locates rows by content and asserts that
each pattern matches exactly one row, so the same class of drift fails
loudly instead of rendering.

**Two sentences began with a lowercase "we"**, an artifact of the D14
conversion from singular to plural where a mid-sentence replacement landed
at a sentence start. Both corrected.

## D19. The mandate figure now shows what the text claims (2026-08-14)

Section 5.5 reports the excess-mass test three ways: deal counts over the
full period, QLICI dollars, and dollars from 2007 onward once the
proportionality instruction was in the code. The figure showed only the
first, which left the other two asserted and unillustrated, and the second
pair is the more institutionally faithful test, since the requirement is
written in investment terms and did not govern the early years.

Figure 6 is now two panels: deal counts across the full period, and QLICI
dollars from 2007 onward, each carrying its own excess mass with a
CDE-cluster bootstrap interval, both containing zero. Panel statistics are
read from review_round2.json rather than recomputed for the figure, so the
figure cannot drift from the text. The single-panel exhibit remains in
figures/ for the viewer site; the bundle no longer ships it, since the
bundle derives its figure list from the manuscript.

## D20. Section 5.5, where the residual lives (2026-08-14)

The paper outline listed a residual analysis that had never been built, and
it answers the natural referee question: is the within-CDE null uniform, or
does an average conceal a subpopulation where rural deployment really does
mobilize less. scripts/run_residual_analysis.py re-estimates the workhorse
specification inside eighteen subgroups (quartiles of intermediary size,
three origination eras, four census regions, four project types, three
bands of the intermediary's own rural orientation), keeping the same fixed
effects and CDE-clustered errors, and reports rather than drops cells too
small to identify the comparison.

Seventeen cells estimate. Two reach p < 0.05 uncorrected, real estate at
-0.395 and the third size quartile at +0.349, pointing in opposite
directions, against roughly one rejection expected by chance across
seventeen tests. Neither survives Benjamini-Hochberg, and the smallest
p-value in the whole scan is 0.043. The scan is reported with that
correction rather than as a list of suggestive cells, because scanning
without it is how spurious subgroup findings enter papers.

The real-estate cell is flagged in the text rather than buried: it is the
largest negative estimate, it matches the descriptive pattern in the
type interaction, and it is where private debt-stacking makes a genuine
penalty most plausible. The honest statement is that the data cannot
separate that reading from chance.

**A bug caught by reading the output.** The first run returned four empty
region cells. The state column carries full names, not postal
abbreviations, which the region map assumed, so every project fell through
to "Other". The map now uses full names and the script asserts that at
least 95 percent of projects map to a census region, so the same silent
failure cannot recur.

## D21. The manuscript's numbers are now audited by machine (2026-08-14)

The standing rule on this project is that every displayed number originates
in the repository pipeline. Until now that rule was enforced by care, which
is the same as not being enforced. A number can be right when written and
become stale the instant an upstream script is re-run, and nothing in the
build would notice.

`scripts/audit_paper_numbers.py` names 28 load-bearing numbers, each as the
literal string it appears as in a `.tex` source, paired with the JSON field
that produced it. A claim passes when the source value, rounded half-up to
the precision the manuscript actually prints, equals the printed number
exactly. Comparing on rounding rather than on a tolerance is the right
convention: a printed $-0.185$ is a claim about what $-0.1845$ rounds to,
and a tolerance of $5\times10^{-4}$ rejects that pair on a floating-point
technicality. Python's built-in `round` is also wrong here, giving
`round(0.815, 2) == 0.81`; the audit uses `Decimal` with `ROUND_HALF_UP`.

All 28 pass. `scripts/make_overleaf_bundle.sh` now refuses to build if any
fail, so a drifted number cannot reach Overleaf. `tests/test_audit_paper_numbers.py`
confirms the audit fires when a value is perturbed, since a guard never
observed to fire is indistinguishable from one that cannot.

Excluded by design, because no pipeline output backs them: statutory facts
(the 39% credit rate, the 20% target), dates, and citation years.

Building the manifest was itself a check on the paper, and the paper came
through clean. Every claim traced to a real field with the expected value.
