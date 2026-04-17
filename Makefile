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
	@# Usage: make release [NEXT=0.2.0]
	@# VERSION is read automatically from the RST comment block in RELEASE_NOTES.rst.
	@# DATE defaults to today.  NEXT defaults to a patch-level bump.
	@python scripts/stamp_release.py $(NEXT)
	@echo "RELEASE_NOTES.rst updated.  Review, then: git add RELEASE_NOTES.rst && git commit && git tag vVERSION && git push origin main vVERSION"

test:
	pytest -q --lf ./tests
