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
	find . -\( -name "*.pyc" -o -name '*.pyo' -o -name "*~" -\) -delete


install:
	@python setup.py install


log:
	@(LC_ALL=C date +"* %a %b %e %Y `git config --get user.name` <`git config --get user.email`> - VERSION"; git log --pretty="format:- %s (%an)" | cat) | less


source: clean
	@python setup.py sdist --formats=bztar

RPM_VER = $(shell rpmspec -q --srpm --queryformat '%{version}' covscan.spec)
GIT_VER = $(shell git describe | sed -e 's/^covscan-//' -e "s/-.*-/.$$(git log --pretty="%cd" --date=iso -1 | tr -d ':-' | tr ' ' . | cut -d. -f 1,2)./")

srpm: source
	echo "%global git_version $(GIT_VER)" > dist/covscan.spec
ifneq ($(RPM_VER),$(GIT_VER))
	cp -afv dist/covscan-$(RPM_VER).tar.bz2 dist/covscan-$(GIT_VER).tar.bz2
	sed -e 's/$(RPM_VER)$$/$(GIT_VER)/' -e 's/%{version}/$(RPM_VER)/' -e 's/^%setup -q/%setup -q -n covscan-$(RPM_VER)/' covscan.spec >> dist/covscan.spec
else
	cat covscan.spec >> dist/covscan.spec
endif
	rpmbuild -bs "dist/covscan.spec"                    \
		--define "_sourcedir ./dist"                \
		--define "_specdir ."                       \
		--define "_srcrpmdir ."						\
		--define "git_version $(GIT_VER)"

lint-all:
	pre-commit run --all-files

lint-ci:
	pre-commit run --from-ref origin/master --to-ref HEAD

prepare-env:
	rm -rf kobo
	git clone --depth 1 https://github.com/release-engineering/kobo.git

prepare-containers:
	podman pull registry-proxy.engineering.redhat.com/rh-osbs/rhel8-postgresql-12
	podman build -f containers/Dockerfile.hub -t covscanhub .
	podman build -f containers/Dockerfile.worker -t covscanworker .

start-containers:
	podman-compose up --no-start
	podman start db covscanhub

test-hub:
	podman exec -it covscanhub python3 covscanhub/manage.py test || exit 1

teardown-containers:
	podman-compose logs db
	podman-compose logs covscanhub
	podman-compose down
