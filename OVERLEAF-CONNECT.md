# Connecting this paper to Overleaf

Three routes, from least to most automatic.

## 1. One-click import (works on a free account, no setup)

Open this link and Overleaf builds a project from the committed bundle:

https://www.overleaf.com/docs?snip_uri=https%3A%2F%2Fraw.githubusercontent.com%2Fihelfrich%2Fus-nmtc-viewer%2Fmain%2Foverleaf-nmtc-paper.zip&engine=pdflatex&main_document=main.tex

The URL sets the compiler to pdfLaTeX and the root document to `main.tex`,
so it should compile on arrival.

This is an **import, not a sync**. Each click creates a new project, and
edits made in Overleaf do not travel back. Use it to get started, or to
refresh from a clean copy after regenerating tables and figures.

To refresh the source behind that link:

    bash scripts/make_overleaf_bundle.sh
    git add overleaf-nmtc-paper.zip && git commit && git push

## 2. GitHub synchronization (premium; true two-way)

A dedicated repository already exists and mirrors the paper:

    https://github.com/ihelfrich/nmtc-paper   (private)

Its contents *are* the Overleaf project: `main.tex` sits at the root beside
the style file, sections, tables, figures, and bibliography.

In Overleaf: open the project, choose **Integrations** in the left panel,
select **GitHub**, and point it at `ihelfrich/nmtc-paper`. After that,
Overleaf pushes and pulls against the repo, so edits made in either place
can be moved to the other.

To send new work from the research repo into that repository:

    bash scripts/push_paper_to_sync_repo.sh "what changed"

The script rebuilds the bundle, replaces the tracked content, and pushes.
It exits quietly when nothing has changed.

## 3. Git bridge (premium; direct)

Overleaf issues a git URL for each project under **Menu → Git**. With it:

    git clone https://git.overleaf.com/<project-id>

Then the Overleaf project is an ordinary remote and can be pushed to from
this machine. This is the most direct path and needs no GitHub in between.
Both this and route 2 require an Overleaf premium plan; route 1 does not.

## Which to use

Start with route 1 today. If a premium plan is available, spend five
minutes wiring route 2, because it keeps the manuscript, the pipeline that
generates its numbers, and the editing surface in one loop.

## One standing rule

`tables/` and `figures/` are generated. Edit them in Overleaf and the next
sync overwrites the changes, and worse, the numbers stop being traceable to
the pipeline. Change the generators in this repository, rerun, and sync.
