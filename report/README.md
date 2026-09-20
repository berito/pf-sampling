# The report

The report is kept as numbered versions, each a self-contained folder with its own `main.tex`,
`macros.tex` and `sections/`. Earlier versions stay buildable.

| Version | Shape |
|---|---|
| `v1/` | Introduction, background, particle filters, method, experiments, discussion, conclusion |
| `v2/` | Background, what the project addresses, experiments, discussion and conclusion |

`v2` is the current one.

## Build

```bash
make report              # the current version -> report/v2/report.pdf
make report V=v1         # an earlier version -> report/v1/report.pdf
make report-preview      # the current version with the quick results, not copied into report/
```

Without make: `docker exec pf-sampling-dev make -C report [V=v1] [preview]`.

Build files go to `.build/report/<version>/` (safe to delete). The build prints a line for every
table or figure whose experiment has not been run, and those appear in the PDF as red placeholders.

## Writing

Text lives in `<version>/sections/`. Tables and figures are never pasted in: they are read from
`results/` at build time, so rerunning an experiment updates the report.

```latex
\experimenttable{E04_particle_count}{Caption.}
\experimentfigure{E04_particle_count}{metrics}{Caption.}
\experimentbest{E11_estimator_resampler}{Caption.}      % the value each recording picks on its own
```

The first argument is the experiment's config name in `experiments/`, without `.yaml`. Each
experiment keeps numbered result sets and the report shows the one named in
`results/<experiment>/current.txt`; pass a number to pin one, `\experimenttable[002]{...}{...}`.

Refer to a table or figure with `\cref{tab:<experiment>}`, `\cref{fig:<experiment>-<figure>}` or
`\cref{tab:best-<experiment>}`.

## Starting a new version

Copy the current folder, rename it, and set `V` in `report/Makefile` to the new name.

## Before handing in

- `grep -rn '\todo{' report/v2` finds nothing.
- `make report` lists no missing results.
- No undefined references in `.build/report/v2/main.log`.
