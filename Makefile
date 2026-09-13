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
.PHONY: help container setup shell test status run run-all analyse quick results compare report report-preview

help:
	@echo "Setup"
	@echo "  make container         build the image and start the container (once per computer)"
	@echo "  make setup             download upstream code + datasets, build gmapping (once)"
	@echo "  make shell             open a shell inside the container"
	@echo ""
	@echo "Check"
	@echo "  make test              run the test suite"
	@echo "  make status            every experiment: runs done, to do, and made with older code  (E=E02 for one)"
	@echo ""
	@echo "Experiments  (E = experiment name or its start, e.g. E=E02; see experiments/README.md)"
	@echo "  make run E=E02         run what is missing, then build tables and figures (safe to stop and restart)"
	@echo "  make run-all           run every experiment"
	@echo "  make analyse E=E02     rebuild tables and figures only"
	@echo "  make quick             small version of every experiment into results/quick/ (a minute)"
	@echo "  make results           summary in the terminal + results/report.html"
	@echo "  make compare DIRS=\"results/A results/B\"   one table across experiments"
	@echo ""
	@echo "Report"
	@echo "  make report            build report/report.pdf"
	@echo "  make report-preview    the report with the quick results (.build/report-preview/main.pdf)"
	@echo ""
	@echo "Extra options go in ARGS, e.g.  make run E=E04 ARGS=\"--jobs 4\"   or   ARGS=--rerun"

container:
	docker build -t $(IMAGE) .devcontainer
	@docker start $(CONTAINER) 2>/dev/null || docker run -d --name $(CONTAINER) --user $$(id -u):$$(id -g) \
	  -e PFEXP_HOST=$$(hostname) -v "$(CURDIR)":/workspaces/pf-sampling -w /workspaces/pf-sampling \
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
