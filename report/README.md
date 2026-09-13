# Report

The LaTeX report. It reads each experiment's table and figure straight from `results/`, so rerunning an
experiment updates the report without copying anything.

```bash
make report             # report/report.pdf, and a list of results that are still missing
make report-preview     # the same with the quick results (results/quick/), in .build/report-preview/main.pdf
grep -rn '\\todo{' report/main.tex report/sections   # parts still to write
```
Without make, inside the container: `make -C report` and `make -C report preview`.
Build files go to `.build/report/` (safe to delete).

## Files

```
main.tex                    title, abstract, the order of the sections
macros.tex                  notation, \todo{...}, and the two commands that include results
references.bib              bibliography
sections/
  01_introduction.tex       the question and why it matters
  02_background.tex         SLAM as a dynamic Bayesian network, Rao-Blackwellization
  03_particle_filters.tex   importance sampling, proposals, resampling, MCMC moves
  04_method.tex             filters, worlds, implementation and upstream fixes, metrics
  05_experiments.tex        one subsection per experiment
  06_discussion.tex         what the results mean, limitations
  07_conclusion.tex
  A_upstream_code.tex       appendix: the upstream code and the bugs fixed
```

Each section starts with comments listing what it should cover. Every unfinished part holds a red `\todo{...}`.

## Including an experiment

```latex
\experimenttable{E02_when_to_resample}{When to resample.}
\experimentfigure{E02_when_to_resample}{metrics}{When to resample: metrics per rule.}
\experimentfigure{E02_when_to_resample}{trace_ess}{Effective sample size over time.}
```

The first argument is the config name in `experiments/`. The figure name is a file in
`results/<experiment>/figures/` without its extension: `metrics`, or `trace_<name>` for each trace listed in
the config. Until the experiment has run, a red placeholder appears and `make report` lists it.

The table shows every metric in the config's `report.metrics`. If a table is too wide for the page, list
fewer metrics there and run `make analyse E=<experiment>`. Nothing needs to rerun.

## Writing an experiment's subsection

1. `make run E=E02`, then open `results/E02_when_to_resample/summary.md`. It has the question, the setup, the
   table, and findings computed with 95% intervals (for example "the highest is ..., clearly beyond the
   seed-to-seed spread").
2. In `sections/05_experiments.tex`, replace the `\todo{...}` with: the question, the setup (what was fixed,
   what varied, how many seeds), what the table and figure show, and whether the hypothesis held. Only claim a
   difference that the summary calls clear.
3. `make report` and read the PDF.

## Before handing in

- `grep -rn '\\todo{' report/main.tex report/sections` finds nothing, and `make report` lists no missing results.
- Build from a clean copy: `rm -rf .build/report && make report`.
