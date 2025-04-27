
APPNAME = yumex
DATADIR = /usr/share
PYTHON = python3
VERSION=$(shell awk '/Version:/ { print $$2 }' ${APPNAME}.spec)
GITDATE=git$(shell date +%Y%m%d)
NAME = $(shell git config --get user.name)
EMAIL = $(shell git config --get user.email)
PACKAGER = $(NAME) <$(EMAIL)>
NEW_REL=%autorelease -p -s $(GITDATE)
GIT_MASTER=main
RPMBUILD_OPTS = -D '_topdir $(BUILDDIR)' -D 'packager $(PACKAGER)'
CURDIR = ${shell pwd}
BUILDDIR= $(CURDIR)/build
COPR_REL_DNF5 = -r fedora-rawhide-x86_64 -r fedora-rawhide-aarch64 -r fedora-41-x86_64 -r fedora-41-aarch64 -r fedora-42-x86_64 -r fedora-42-aarch64

all:
	@echo "Nothing to do, use a specific target"

clean:
	@rm -rf *.tar.gz
	@rm -rf build/

# create a source archive for a release
archive:
	@rm -rf ${APPNAME}-${VERSION}.tar.gz
	@git archive --format=tar --prefix=$(APPNAME)-$(VERSION)/ HEAD | gzip -9v >${APPNAME}-$(VERSION).tar.gz
	@mkdir -p ${BUILDDIR}/SOURCES
	@cp ${APPNAME}-$(VERSION).tar.gz ${BUILDDIR}/SOURCES
	@rm -rf ${APPNAME}-${VERSION}.tar.gz
	@echo "The archive is in ${BUILDDIR}/SOURCES/${APPNAME}-$(VERSION).tar.gz"


# create a release
# commit, tag, push, build local rpm and start a copr build
release:
	@$(MAKE) clean
	@git commit -a -m "bumped release to $(VERSION)"
	@git tag -f -m "Added ${APPNAME}-${VERSION} release tag" ${APPNAME}-${VERSION}
	@git push --tags origin
	@git push origin
	@$(MAKE) copr-release

# build local rpms with dnf5 backend and start a copr build
copr-release:
	@$(MAKE) archive
	@-rpmbuild $(RPMBUILD_OPTS) -ta ${BUILDDIR}/SOURCES/${APPNAME}-$(VERSION).tar.gz
	@copr-cli build --nowait yumex-ng $(COPR_REL_DNF5) $(BUILDDIR)/SRPMS/${APPNAME}-$(VERSION)*.src.rpm

# cleanup the test branch used to create the test release
test-checkout:
	@-git stash clear
	@-git stash push -m "save local changes" -q
	@git checkout -q -b release-test

test-cleanup:
	@rm -rf ${APPNAME}-${VERSION}.tar.gz
	@git checkout -f
	@git checkout -q ${GIT_MASTER}
	@-git stash pop -q
	@git branch -q -D release-test

show-vars:
	@echo "GITDATE     : ${GITDATE}"
	@echo "PACKAGER    : ${PACKAGER}"

#make a test release with the dnf5 backend
test-release:
	@$(MAKE) test-checkout
	@cat ${APPNAME}.spec | sed  -e '2 s/release/debug/' -e '6 s/%autorelease/${NEW_REL}/'  > ${APPNAME}-test.spec ; mv ${APPNAME}-test.spec ${APPNAME}.spec
	@git commit -a -m "bumped ${APPNAME} release"
	# Make archive
	@rm -rf ${APPNAME}-${VERSION}.tar.gz
	@git archive --format=tar --prefix=$(APPNAME)-$(VERSION)/ HEAD | gzip -9v >${APPNAME}-$(VERSION).tar.gz
	# Build RPMS
	@-rpmbuild $(RPMBUILD_OPTS) -ta ${APPNAME}-${VERSION}.tar.gz
	@$(MAKE) test-cleanup

test-reinstall:
	@$(MAKE) clean
	@$(MAKE) test-release
	@-sudo dnf5 reinstall  build/RPMS/noarch/*.rpm

test-update:
	@$(MAKE) clean
	@$(MAKE) test-release
	@-sudo dnf5 update build/RPMS/noarch/*.rpm

test-install:
	@$(MAKE) clean
	@$(MAKE) test-release
	@-sudo dnf5 install build/RPMS/noarch/*.rpm

# build release rpms
rpm:
	@$(MAKE) archive
	@rpmbuild --define '_topdir $(BUILDDIR)' -ta ${BUILDDIR}/SOURCES/${APPNAME}-$(VERSION).tar.gz

test-copr:
	@$(MAKE) clean
	@$(MAKE) test-release
	@copr-cli build --nowait yumex-ng-dev $(COPR_REL_DNF5) $(BUILDDIR)/SRPMS/${APPNAME}-$(VERSION)*.src.rpm

# Make a local build and run it
localbuild:
	meson setup builddir --prefix="$(shell pwd)/builddir" --buildtype=debug --wipe
	ninja -C builddir install

# install tools needed for unit testing
inst-test-tools:
	sudo dnf5 install python3-pytest python3-pytest-cov python3-pytest-mock

# install tools needed for local/copr rpm building
inst-build-tools:
	sudo dnf5 install @fedora-packager copr-cli

# install packages needed running and building
inst-deps:
	@-sudo dnf5 builddep yumex.spec -y
	@-sudo dnf5 install python3-dbus  -y
	@-sudo dnf5 install dnf5daemon-server -y

# generate the POTFILES from available source files with translations
# POTFILES is source for what fies is used to generate the .POT file.
potfiles:
	@echo "updating po/POTFILES with *.py, .in & *.blp files"
	@find yumex -iname *.py > po/POTFILES
	@find yumex -iname yumex_updater_systray >> po/POTFILES
	@find data -iname *.blp >> po/POTFILES
	@find data -iname *.in.in >> po/POTFILES

# update .pot file from source files and push to transifex and commit to git
transifex-update:
	@$(MAKE) potfiles
	po/update_potfile.sh
	tx push
	git add po/*
	git commit -m "i18n: updated yumex.pot"

# fetct .po files from transifex and commit to git
transifex-get:
	tx pull -f
	git add po/*
	git commit -m "i18n: updated translations from transifex"

# run unit tests
run-tests:
	pytest

# Run live envrionment pytest
run-tests-live:
	pytest tests/dont_test_*.py -s -v

# run unit tests and generate html coverage report
run-test-report:
	pytest --cov --cov-report html


run-updater:
	@systemctl --user stop yumex-updater.service
	@$(MAKE) localbuild
	@-./builddir/bin/yumex_updater

# dnf5 install python3-memray
memray-updater:
	@systemctl --user stop yumex-updater.service
	@$(MAKE) localbuild
	@-mkdir -p profile
	@-rm profile/output.bin
	@-rm profile/memray-flamegraph-output.html
	@-python3 -m memray run -o profile/output.bin ./builddir/bin/yumex_updater_systray
	@-python3 -m memray flamegraph profile/output.bin

# dnf5 install python3-memray
memray-updater-live:
	@-systemctl --user stop yumex-updater.service
	@$(MAKE) localbuild
	@-mkdir -p profile
	@-python3 -m memray run --live ./builddir/bin/yumex_updater_systray


run-gui-test: localbuild
	@python tests/guitest/main.py

upstream_rpms: clean
	@mkdir -p $(BUILDDIR)/SOURCES
	@spectool -g -C $(BUILDDIR)/SOURCES -S yumex.spec
	@rpmbuild $(RPMBUILD_OPTS) -ba yumex.spec
	@echo "RPMS Build:"
	@tree -P *.rpm -I *.src.rpm  $(BUILDDIR)/RPMS/noarch/
