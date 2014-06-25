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
	find . -\( -name "*.pyc" -o -name '*.pyo' -o -name "*~" -\) -delete


install:
	@python setup.py install


log:
	@(LC_ALL=C date +"* %a %b %e %Y `git config --get user.name` <`git config --get user.email`> - VERSION"; git log --pretty="format:- %s (%an)" | cat) | less


source: clean
	@python setup.py sdist

prep:
	rpmbuild -bp "$(PWD)/covscan.spec"    \
		--define "_sourcedir $(PWD)/dist" \
		--define "_rpmdir $(PWD)"         \
		--define "_specdir $(PWD)"        \
		--define "_srcrpmdir $(PWD)"

srpm: source
	rpmbuild -bs "covscan.spec"                     \
		--define "_source_filedigest_algorithm md5" \
		--define "_binary_filedigest_algorithm md5" \
		--define "_sourcedir ./dist"                \
		--define "_specdir ."                       \
		--define "_srcrpmdir ."

rpm: source
	rpmbuild -bb "covscan.spec"                     \
		--define "_source_filedigest_algorithm md5" \
		--define "_binary_filedigest_algorithm md5" \
		--define "_sourcedir $(PWD)/dist"           \
		--define "_specdir $(PWD)"                  \
		--define "hub_instance stage"               \
		--define "_rpmdir $(PWD)"

#test:
#	cd tests; ./run_tests.py
