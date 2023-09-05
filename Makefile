all: help


help:
	@echo "Usage: make <target>"
	@echo
	@echo "Available targets are:"
	@echo " help                    show this text"
	@echo " build			builds basic development environment"
	@echo " clean                   remove python bytecode and temp files"
	@echo " clean-dev               also cleans up development environment"
	@echo " cli-test		run cli sanity tests"
	@echo " full-dev		builds full development environment"
	@echo " install                 install program on current system"
	@echo " lint			run pre-commit linters on branch"
	@echo " lint-all                run pre-commit linters on all files"
	@echo " log                     prepare changelog for spec file"
	@echo " source                  create source tarball"


install:
	@python3 setup.py install


build:
	@./containers/scripts/deploy.sh --no-start


full-build:
	@./containers/scripts/deploy.sh --no-start --full-dev


deploy:
	@./containers/scripts/deploy.sh


full-deploy:
	@./containers/scripts/deploy.sh --full-dev


IS_LINUX = $(shell source containers/scripts/utils.sh; echo $$IS_LINUX)

ifeq ($(IS_LINUX), 1)
	PREREQ =
else
	PREREQ = full-deploy
endif

cli-test: $(PREREQ)
	@[ "$(IS_LINUX)" = "1" ] && \
		./scripts/cli_sanity_test.sh || \
		docker exec -it osh-client scripts/cli_sanity_test.sh


clean-local-python:
	@python3 setup.py clean


clean-local-files:
	rm -f ./*.src.rpm
	rm -rf dist
	find . -\( -name "*.pyc" -o -name '*.pyo' -o -name "*~" -\) -delete


clean: clean-local-python clean-local-files


clean-dev: clean-local-files
	@./containers/scripts/deploy.sh --clean


log:
	@(LC_ALL=C date +"* %a %b %e %Y `git config --get user.name` <`git config --get user.email`> - VERSION"; git log --pretty="format:- %s (%an)") | less


source: clean
	@python3 setup.py sdist --formats=gztar

VERSION = $(shell echo dist/*.tar.gz | sed "s/.*osh-\(.*\).tar.gz/\1/g")

srpm: source
	echo "%global version $(VERSION)" > dist/osh.spec
	cat osh.spec >> dist/osh.spec
	rpmbuild -bs "dist/osh.spec"	\
		--define "_sourcedir ./dist"	\
		--define "_specdir ."		\
		--define "_srcrpmdir ."

REPO = origin
BRANCH = main

lint:
	pre-commit run --show-diff-on-failure --color=always --from-ref $(REPO)/$(BRANCH) --to-ref HEAD


lint-all:
	pre-commit run --show-diff-on-failure --color=always --all-files
