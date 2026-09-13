# Build the report inside the container:  docker exec pf-sampling-dev make -C report   (or `make report` from the project root)
# Intermediate files go to .build/report/ (safe to delete); the finished PDF is copied to report/report.pdf.
#
#   make -C report           report/report.pdf with the results in results/
#   make -C report preview   .build/report-preview/main.pdf with the quick results in results/quick/ (to check the
#                            layout before the full experiments have run; never copied to report/)
BUILD := ../.build/report
PREVIEW := ../.build/report-preview

# -g: always rebuild, because latexmk does not notice result files that appear after an experiment has run.
report.pdf: FORCE
	mkdir -p $(BUILD)
	latexmk -g -pdf -outdir=$(BUILD) -interaction=nonstopmode -halt-on-error main.tex > $(BUILD).latexmk.log 2>&1 \
	  || { tail -30 $(BUILD).latexmk.log; echo "LaTeX failed; full log: .build/report/main.log"; exit 1; }
	cp $(BUILD)/main.pdf report.pdf
	@echo "Built report/report.pdf"
	@grep -h "^MISSING RESULTS" $(BUILD)/main.log | sort -u | sed 's/^/  (placeholder) /' || true

preview: FORCE
	mkdir -p $(PREVIEW)
	latexmk -g -pdf -outdir=$(PREVIEW) -interaction=nonstopmode -halt-on-error \
	  -usepretex='\def\resultsdir{../results/quick}' main.tex > $(PREVIEW).latexmk.log 2>&1 \
	  || { tail -30 $(PREVIEW).latexmk.log; echo "LaTeX failed; full log: .build/report-preview/main.log"; exit 1; }
	@echo "Built .build/report-preview/main.pdf (with the quick results)"
	@grep -h "^MISSING RESULTS" $(PREVIEW)/main.log | sort -u | sed 's/^/  (placeholder) /' || true

clean:
	rm -rf $(BUILD) $(PREVIEW)

.PHONY: FORCE clean preview
FORCE:
