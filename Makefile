all: help


help:
	@echo "Usage: make <target>"
	@echo
	@echo "Available targets are:"
	@echo " help                    show this text"
	@echo " build                   builds basic development environment"
	@echo " clean                   remove python bytecode and temp files"
	@echo " clean-dev               also cleans up development environment"
	@echo " full-dev                builds full development environment"
	@echo " install                 install program on current system"
	@echo " lint                    run pre-commit linters on branch"
	@echo " lint-all                run pre-commit linters on all files"
	@echo " source                  create source tarball"


install:
	@python3 setup.py install


build:
	@containers/scripts/deploy.sh --no-start


full-build:
	@containers/scripts/deploy.sh --no-start --full-dev


deploy:
	@containers/scripts/init-db.sh --minimal


full-deploy:
	@containers/scripts/init-db.sh --minimal --full-dev


clean-local-python:
	@python3 setup.py clean


clean-local-files:
	rm -f ./*.src.rpm
	rm -rf dist
	find . -\( -name "*.pyc" -o -name '*.pyo' -o -name "*~" -\) -delete


clean: clean-local-python clean-local-files


clean-dev: clean-local-files
	@containers/scripts/deploy.sh --clean


source: clean
	@python3 setup.py sdist --formats=gztar

# path to the distribution tarball produced by `setup.py dist`
TGZ_ORIG = $(shell echo dist/*.tar.gz)

# top-level directory in the distribution tarball used by `setup.py dist`
TGZ_DIR_ORIG = $(shell basename $(TGZ_ORIG) .tar.gz)

# version used by the RPM packaing
VERSION = $(shell scripts/get-version.sh)

# top-level directory in the distribution tarball used by the source RPM
TGZ_DIR = osh-$(VERSION)

# path to the distribution tarball used by the source RPM
TGZ = dist/$(TGZ_DIR).tar.gz

srpm: source
	tar -xzf $(TGZ_ORIG) -C dist --transform 's/$(TGZ_DIR_ORIG)/$(TGZ_DIR)/'
	tar -czf $(TGZ) -C dist --remove-files $(TGZ_DIR)
	echo "%global version $(VERSION)" > dist/osh.spec
	cat osh.spec >> dist/osh.spec
	rpmbuild -bs "dist/osh.spec"     \
	    --define "_sourcedir ./dist" \
	    --define "_specdir ."        \
	    --define "_srcrpmdir ."

REPO = origin
BRANCH = main

lint:
	pre-commit run --show-diff-on-failure --color=always --from-ref $(REPO)/$(BRANCH) --to-ref HEAD


lint-all:
	pre-commit run --show-diff-on-failure --color=always --all-files
