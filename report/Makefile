# Build a version of the report inside the container:
#   docker exec pf-sampling-dev make -C report          the current version (V below)
#   docker exec pf-sampling-dev make -C report V=v1     an earlier version
#   docker exec pf-sampling-dev make -C report preview  the current version with the quick results
#
# Each version is a folder with its own main.tex, macros.tex and sections/. Intermediate files go to
# .build/report/<version>/ (safe to delete); the finished PDF is copied to report/<version>/report.pdf.
V := v2

# Paths as seen from report/ and, for latexmk, from inside the version folder.
OUT := ../.build/report/$(V)
OUT_FROM_V := ../$(OUT)
PREVIEW := ../.build/report-preview/$(V)
PREVIEW_FROM_V := ../$(PREVIEW)

# -g: always rebuild, because latexmk does not notice result files that appear after an experiment has run.
report.pdf: FORCE
	@test -f $(V)/main.tex || { echo "No report/$(V)/main.tex"; exit 2; }
	mkdir -p $(OUT)
	cd $(V) && latexmk -g -pdf -outdir=$(OUT_FROM_V) -interaction=nonstopmode -halt-on-error main.tex \
	  > $(OUT_FROM_V)/latexmk.log 2>&1 \
	  || { tail -30 $(OUT_FROM_V)/latexmk.log; echo "LaTeX failed; full log: .build/report/$(V)/main.log"; exit 1; }
	cp $(OUT)/main.pdf $(V)/report.pdf
	@echo "Built report/$(V)/report.pdf"
	@grep -h "^MISSING RESULTS" $(OUT)/main.log | sort -u | sed 's/^/  (placeholder) /' || true

preview: FORCE
	@test -f $(V)/main.tex || { echo "No report/$(V)/main.tex"; exit 2; }
	mkdir -p $(PREVIEW)
	cd $(V) && latexmk -g -pdf -outdir=$(PREVIEW_FROM_V) -interaction=nonstopmode -halt-on-error \
	  -usepretex='\def\resultsdir{../../results/quick}' main.tex > $(PREVIEW_FROM_V)/latexmk.log 2>&1 \
	  || { tail -30 $(PREVIEW_FROM_V)/latexmk.log; echo "LaTeX failed; full log: .build/report-preview/$(V)/main.log"; exit 1; }
	@echo "Built .build/report-preview/$(V)/main.pdf (with the quick results)"
	@grep -h "^MISSING RESULTS" $(PREVIEW)/main.log | sort -u | sed 's/^/  (placeholder) /' || true

clean:
	rm -rf ../.build/report ../.build/report-preview

.PHONY: FORCE clean preview
FORCE:
