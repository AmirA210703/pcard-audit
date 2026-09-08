DB ?= $(CURDIR)/pcards.db
PY ?= python3

T2 := $(shell seq 1 14)
T3 := $(shell seq 1 8)

.PHONY: results doc web clean

results:
	@mkdir -p results
	@for q in $(T2); do \
	  sqlite3 -header -csv "$(DB)" < sql/qry_T2_Question$$q.sql > results/T2_Q$$q.csv; \
	  echo "results/T2_Q$$q.csv"; \
	done
	@for q in $(T3); do \
	  sqlite3 -header -csv "$(DB)" < sql/qry_T3_Question$$q.sql > results/T3_Q$$q.csv; \
	  echo "results/T3_Q$$q.csv"; \
	done

DOCX ?= $(dir $(CURDIR:/=))Assignment PCARDS/Analytics_mindset_case_studies_PCard_assignment.docx

doc:
	PCARD_DOCX="$(DOCX)" $(PY) docgen/build_doc.py

web:
	cd webapp && PCARD_DB="$(DB)" $(PY) app.py

clean:
	rm -rf results/*.csv __pycache__ */__pycache__
