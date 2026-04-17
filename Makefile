# Makefile to support common developer commands

# Keep pre-commit cache on local disk (avoids NFS rmdir failures on this system).
# See AGENTS.md "pre-commit on NFS home directories" for details.
export PRE_COMMIT_HOME := /tmp/pre-commit-JEMIAN

all :: style docs coverage

clean ::
	make -C docs clean

coverage:
	coverage run --concurrency=thread --parallel-mode -m pytest -q ./src
	coverage combine
	coverage report --precision 3 -m
	coverage html

docs ::
	make -C docs html

doc :: docs

isort:
	isort --sl ./src

pre:
	pre-commit run --all-files
	ruff check .

style :: isort pre

realclean :: clean
	/bin/rm -rf ./docs/build

release:
	@# Usage: make release VERSION=0.1.8 DATE=2026-04-17 NEXT=0.1.9
	@test -n "$(VERSION)" || (echo "ERROR: VERSION is required.  Usage: make release VERSION=0.1.8 DATE=2026-04-17 NEXT=0.1.9"; exit 1)
	@test -n "$(DATE)"    || (echo "ERROR: DATE is required.    Usage: make release VERSION=0.1.8 DATE=2026-04-17 NEXT=0.1.9"; exit 1)
	@test -n "$(NEXT)"    || (echo "ERROR: NEXT is required.    Usage: make release VERSION=0.1.8 DATE=2026-04-17 NEXT=0.1.9"; exit 1)
	@python scripts/stamp_release.py $(VERSION) $(DATE) $(NEXT)
	@echo "RELEASE_NOTES.rst updated for v$(VERSION).  Review, then commit and tag."

test:
	pytest -q --lf ./tests
