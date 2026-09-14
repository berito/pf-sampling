# Short commands for everyday work. Type `make` to see them.
#
# They work from the host (each command runs inside the container pf-sampling-dev) and from a terminal
# inside the container (VS Code "Reopen in Container"). Every command is also written out in full in
# README.md and experiments/README.md, if you prefer not to use make.

CONTAINER := pf-sampling-dev
IMAGE     := pf-sampling:dev
# Inside the container, run directly; on the host, go through docker exec.
IN        := $(if $(wildcard /.dockerenv),,docker exec $(CONTAINER))
IN_TTY    := $(if $(wildcard /.dockerenv),,docker exec -it $(CONTAINER))

# make run E=E02  runs every experiment whose name starts with E02 (E03 has a localization and a SLAM part)
E ?=
EXPERIMENTS = $(if $(E),$(wildcard experiments/$(E)*.yaml),$(wildcard experiments/*.yaml))
ARGS ?=

.DEFAULT_GOAL := help
.PHONY: help container setup shell test status run run-all redo new use start start-all running log stop analyse quick results compare report report-preview

help:
	@echo "Setup"
	@echo "  make container         build the image and start the container (once per computer)"
	@echo "  make setup             download upstream code + datasets, build gmapping (once)"
	@echo "  make shell             open a shell inside the container"
	@echo ""
	@echo "Check"
	@echo "  make test              run the test suite"
	@echo "  make status            every experiment: its result set, runs done and to do, changed parameters  (E=E02 for one)"
	@echo ""
	@echo "Experiments  (E = experiment name or its start, e.g. E=E02; see experiments/README.md)"
	@echo "  make run E=E02         run what is missing, then build tables and figures (safe to stop and restart)"
	@echo "  make run-all           run every experiment"
	@echo "  make redo E=E02        the current result set is wrong (a bug, a wrong setup): delete it and run it again"
	@echo "  make new E=E02 NOTE=\"what changed\"   parameters changed on purpose: run into the next number (002, ...)"
	@echo "  make use E=E02 N=1     show result set 001 in the report and results"
	@echo "  make analyse E=E02     rebuild tables and figures only"
	@echo "  make quick             small version of every experiment into results/quick/ (a minute)"
	@echo "  make results           summary in the terminal + results/report.html"
	@echo "  make compare DIRS=\"results/A results/B\"   one table across experiments (or results/E02_.../001 .../002)"
	@echo ""
	@echo "In the background  (keeps running when VS Code, the terminal or SSH is closed)"
	@echo "  make start E=E02       like make run, in the background (ARGS=--redo or ARGS=--new NOTE=\"...\" work too)"
	@echo "  make start-all         like make run-all, in the background"
	@echo "  make running           is it still going?"
	@echo "  make log               follow its output (Ctrl+C stops following, not the run)"
	@echo "  make stop              stop it (finished runs are kept; start again to continue)"
	@echo ""
	@echo "Report"
	@echo "  make report            build report/report.pdf"
	@echo "  make report-preview    the report with the quick results (.build/report-preview/main.pdf)"
	@echo ""
	@echo "Extra options go in ARGS, e.g.  make run E=E04 ARGS=\"--jobs 4\"   or in the background  make start E=E04 ARGS=--new"

container:
	docker build -t $(IMAGE) .devcontainer
	@docker start $(CONTAINER) 2>/dev/null || docker run -d --name $(CONTAINER) --user $$(id -u):$$(id -g) \
	  --init --restart unless-stopped -e PFEXP_HOST=$$(hostname) -v "$(CURDIR)":/workspaces/pf-sampling -w /workspaces/pf-sampling \
	  $(IMAGE) sleep infinity

setup:
	$(IN) bash .devcontainer/postcreate.sh

shell:
	$(IN_TTY) bash

test:
	$(IN) python -m pytest $(ARGS)

run:
	@test -n "$(E)" || { echo "Which experiment? e.g.  make run E=E02   (or make run-all)"; exit 2; }
	@test -n "$(EXPERIMENTS)" || { echo "No experiments/$(E)*.yaml"; exit 2; }
	$(IN) python -m pfexp.run $(EXPERIMENTS) $(ARGS)

run-all:
	$(IN) python -m pfexp.run experiments/*.yaml $(ARGS)

NOTE_ARG = $(if $(NOTE),--note "$(NOTE)")

redo:
	@test -n "$(EXPERIMENTS)" -a -n "$(E)" || { echo "Which experiment? e.g.  make redo E=E02"; exit 2; }
	$(IN) python -m pfexp.run $(EXPERIMENTS) --redo $(NOTE_ARG) $(ARGS)

new:
	@test -n "$(EXPERIMENTS)" -a -n "$(E)" || { echo "Which experiment? e.g.  make new E=E02 NOTE=\"stratified resampler\""; exit 2; }
	$(IN) python -m pfexp.run $(EXPERIMENTS) --new $(NOTE_ARG) $(ARGS)

use:
	@test -n "$(EXPERIMENTS)" -a -n "$(E)" -a -n "$(N)" || { echo "Which experiment and number? e.g.  make use E=E02 N=1"; exit 2; }
	$(IN) python -m pfexp.run $(EXPERIMENTS) --use $(N) $(ARGS)

start:
	@test -n "$(E)" || { echo "Which experiment? e.g.  make start E=E02   (or make start-all)"; exit 2; }
	@test -n "$(EXPERIMENTS)" || { echo "No experiments/$(E)*.yaml"; exit 2; }
	$(IN) bash tools/background.sh start $(E) $(EXPERIMENTS) $(NOTE_ARG) $(ARGS)

start-all:
	$(IN) bash tools/background.sh start all experiments/*.yaml $(ARGS)

running:
	@$(IN) bash tools/background.sh running

log:
	@$(IN_TTY) bash tools/background.sh log

stop:
	@$(IN) bash tools/background.sh stop

status:
	$(IN) python -m pfexp.run $(EXPERIMENTS) --dry-run $(ARGS)

analyse:
	@test -n "$(EXPERIMENTS)" || { echo "No experiments/$(E)*.yaml"; exit 2; }
	$(IN) python -m pfexp.analysis $(EXPERIMENTS) $(ARGS)

quick:
	$(IN) python show_results.py --quick --no-open $(ARGS)

# Only needs Python 3 on the host, no container.
results:
	python3 show_results.py $(ARGS)

compare:
	@test -n "$(DIRS)" || { echo "Which folders? e.g.  make compare DIRS=\"results/E01_resampling_scheme_localization results/E05_resample_move\""; exit 2; }
	$(IN) python -m pfexp.compare $(DIRS) $(ARGS)

report:
	$(IN) make -C report

report-preview:
	$(IN) make -C report preview
