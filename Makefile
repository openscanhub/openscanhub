all: help


help:
	@echo "Usage: make <target>"
	@echo
	@echo "Available targets are:"
	@echo " help                    show this text"
	@echo " clean                   remove python bytecode and temp files"
	@echo " install                 install program on current system"
	@echo " log                     prepare changelog for spec file"
	@echo " source                  create source tarball"
	@echo " test                    run tests/run_tests.py"


clean:
	@python setup.py clean
	rm -f MANIFEST
	rm -f ./*.src.rpm
	find . -\( -name "*.pyc" -o -name '*.pyo' -o -name "*~" -\) -delete


install:
	@python setup.py install


log:
	@(LC_ALL=C date +"* %a %b %e %Y `git config --get user.name` <`git config --get user.email`> - VERSION"; git log --pretty="format:- %s (%an)" | cat) | less


source: clean
	@python setup.py sdist

RPM_VER = $(shell rpmspec -q --srpm --queryformat '%{version}' covscan.spec)
GIT_VER = $(shell git describe | sed -e 's/^covscan-//' -e "s/-.*-/.$$(git log --pretty="%cd" --date=iso -1 | tr -d ':-' | tr ' ' . | cut -d. -f 1,2)./")

srpm: source
ifneq ($(RPM_VER),$(GIT_VER))
	cp -afv dist/covscan-$(RPM_VER).tar.bz2 dist/covscan-$(GIT_VER).tar.bz2
	sed -e 's/$(RPM_VER)$$/$(GIT_VER)/' -e 's/%{version}/$(RPM_VER)/' -e 's/^%setup -q/%setup -q -n covscan-$(RPM_VER)/' covscan.spec > dist/covscan.spec
else
    	cp -afv covscan.spec dist/covscan.spec
endif
	rpmbuild -bs "dist/covscan.spec"                    \
		--define "_sourcedir ./dist"                \
		--define "_specdir ."                       \
		--define "_srcrpmdir ."
