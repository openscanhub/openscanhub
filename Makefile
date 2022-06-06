all: help


help:
	@echo "Usage: make <target>"
	@echo
	@echo "Available targets are:"
	@echo " help                    show this text"
	@echo " clean                   remove python bytecode and temp files"
	@echo " install                 install program on current system"
	@echo " lint-all                run pre-commit linters on all files"
	@echo " log                     prepare changelog for spec file"
	@echo " source                  create source tarball"


clean:
	@python setup.py clean
	rm -f MANIFEST
	rm -f ./*.src.rpm
	rm -rf dist
	find . -\( -name "*.pyc" -o -name '*.pyo' -o -name "*~" -\) -delete


install:
	@python setup.py install


log:
	@(LC_ALL=C date +"* %a %b %e %Y `git config --get user.name` <`git config --get user.email`> - VERSION"; git log --pretty="format:- %s (%an)" | cat) | less


source: clean
	@python setup.py sdist --formats=bztar

VERSION = $(shell echo dist/*.tar.bz2 | sed "s/.*covscan-\(.*\).tar.bz2/\1/g")

srpm: source
	echo "%global version $(VERSION)" > dist/covscan.spec
	cat covscan.spec >> dist/covscan.spec
	rpmbuild -bs "dist/covscan.spec"                    \
		--define "_sourcedir ./dist"                \
		--define "_specdir ."                       \
		--define "_srcrpmdir ."

lint-all:
	pre-commit run --all-files
