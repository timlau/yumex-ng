
APPNAME = yumex
APPNAME_DNF5 = yumex-dnf5
DATADIR = /usr/share
PYTHON = python3
VERSION=$(shell awk '/Version:/ { print $$2 }' ${APPNAME}.spec)
GITDATE=git$(shell date +%Y%m%d)
VER_REGEX=\(^Version:\s*[0-9]*\.[0-9]*\.\)\(.*\)
BUMPED_MINOR=${shell VN=`cat ${APPNAME}.spec | grep Version| sed  's/${VER_REGEX}/\2/'`; echo $$(($$VN + 1))}
NEW_VER=${shell cat ${APPNAME}.spec | grep Version| sed  's/\(^Version:\s*\)\([0-9]*\.[0-9]*\.\)\(.*\)/\2${BUMPED_MINOR}/'}
NEW_REL=0.1.${GITDATE}
DIST=${shell rpm --eval "%{dist}"}
GIT_MASTER=main
CURDIR = ${shell pwd}
BUILDDIR= $(CURDIR)/build
COPR_REL_DNF4 = -r fedora-39-x86_64 -r fedora-39-aarch64 -r fedora-40-x86_64 -r fedora-40-aarch64
COPR_REL_DNF5 = -r fedora-rawhide-x86_64 -r fedora-rawhide-aarch64
COPR_REL_DNF5_SUBPKG = -r fedora-39-x86_64 -r fedora-39-aarch64 -r fedora-40-x86_64 -r fedora-40-aarch64

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

# build local rpms and start a copr build
copr-release:
	@rpmbuild --define '_topdir $(BUILDDIR)' -ts ${BUILDDIR}/SOURCES/${APPNAME}-$(VERSION).tar.gz
	@copr-cli build yumex-ng $(COPR_REL_DNF4) $(BUILDDIR)/SRPMS/${APPNAME}-$(VERSION)*.src.rpm

# build local rpms and start a copr build
copr-release-dnf5:
	@$(MAKE) release-yumex-dnf5
	@copr-cli build yumex-ng $(COPR_REL_DNF5_SUBPKG) $(BUILDDIR)/SRPMS/${APPNAME_DNF5}-$(VERSION)*.src.rpm

# create a release
# commit, tag, push, build local rpm and start a copr build
release:
	@$(MAKE) clean
	@git commit -a -m "bumped release to $(VERSION)"
	@git tag -f -m "Added ${APPNAME}-${VERSION} release tag" ${APPNAME}-${VERSION}
	@git push --tags origin
	@git push origin
	@$(MAKE) archive
	@$(MAKE) copr-release

# cleanup the test branch used to create the test release
test-checkout:
	@-git stash clear
	@-git stash push -m "save local changes" -q
	@git checkout -q -b release-test

test-cleanup:
	@rm -rf ${APPNAME}-${NEW_VER}.tar.gz
	@git checkout -f
	@git checkout -q ${GIT_MASTER}
	@-git stash pop -q
	@git branch -q -D release-test

show-vars:
	@echo ${GITDATE}
	@echo ${BUMPED_MINOR}
	@echo ${NEW_VER}-${NEW_REL}
	@echo ${GIT_BRANCH}


#make a test release with the dnf5 backend
test-release-dnf5:
	@$(MAKE) test-checkout
	# +1 Minor version and add 0.1-gitYYYYMMDD release
	@cat ${APPNAME}.spec | sed  -e '3 s/DNF4/DNF5/' -e '2 s/release/debug/' -e 's/${VER_REGEX}/\1${BUMPED_MINOR}/' -e 's/\(^Release:\s*\)\([0-9]*\)\(.*\)./\10.1.${GITDATE}%{?dist}/' > ${APPNAME}-test.spec ; mv ${APPNAME}-test.spec ${APPNAME}.spec
	@git commit -a -m "bumped ${APPNAME} version ${NEW_VER}-${NEW_REL}"
	# Make archive
	@rm -rf ${APPNAME}-${NEW_VER}.tar.gz
	@git archive --format=tar --prefix=$(APPNAME)-$(NEW_VER)/ HEAD | gzip -9v >${APPNAME}-$(NEW_VER).tar.gz
	# Build RPMS
	@-rpmbuild --define '_topdir $(BUILDDIR)' -D 'app_build debug' -ta ${APPNAME}-${NEW_VER}.tar.gz
	@$(MAKE) test-cleanup

#make a test release with the dnf5 backend
test-release-yumex-dnf5:
	@$(MAKE) test-checkout
	# +1 Minor version and add 0.1-gitYYYYMMDD release
	@cat yumex.spec | sed -e "6 s/%{app_name}/%{app_name}-dnf5/" -e '3 s/DNF4/DNF5/' -e '2 s/release/debug/' -e 's/${VER_REGEX}/\1${BUMPED_MINOR}/' -e 's/\(^Release:\s*\)\([0-9]*\)\(.*\)./\10.1.${GITDATE}%{?dist}/' > ${APPNAME_DNF5}.spec
	@git add ${APPNAME_DNF5}.spec
	@git rm yumex.spec
	@git commit -a -m "bumped ${APPNAME_DNF5} version ${NEW_VER}-${NEW_REL}"
	# Make archive
	@rm -rf ${APPNAME_DNF5}-${NEW_VER}.tar.gz
	@git archive --format=tar --prefix=$(APPNAME_DNF5)-$(NEW_VER)/ HEAD | gzip -9v >${APPNAME_DNF5}-$(NEW_VER).tar.gz
	# Build RPMS
	@-rpmbuild --define '_topdir $(BUILDDIR)' -D 'app_build debug' -ta ${APPNAME_DNF5}-${NEW_VER}.tar.gz
	@ rm -d ${APPNAME_DNF5}.spec
	@$(MAKE) test-cleanup

test-reinstall:
	@$(MAKE) clean
	@$(MAKE) test-release-yumex-dnf5
	@-sudo dnf5 reinstall  build/RPMS/noarch/*.rpm

test-update:
	@$(MAKE) clean
	@$(MAKE) test-release-yumex-dnf5
	@-sudo dnf5 update build/RPMS/noarch/*.rpm

release-yumex-dnf5:
	@$(MAKE) test-checkout
	@cat yumex.spec | sed -e "6 s/%{app_name}/%{app_name}-dnf5/" -e '3 s/DNF4/DNF5/' > ${APPNAME_DNF5}.spec
	@git add ${APPNAME_DNF5}.spec
	@git rm yumex.spec
	@git commit -a -m "bumped ${APPNAME_DNF5} to $(VERSION)"
	# Make archive
	@rm -rf ${APPNAME_DNF5}-${VERSION}.tar.gz
	@git archive --format=tar --prefix=$(APPNAME_DNF5)-$(VERSION)/ HEAD | gzip -9v >${APPNAME_DNF5}-$(VERSION).tar.gz
	# Build RPMS
	@-rpmbuild --define '_topdir $(BUILDDIR)' -ta ${APPNAME_DNF5}-${VERSION}.tar.gz
	@ rm -d ${APPNAME_DNF5}.spec
	@$(MAKE) test-cleanup

# make a test release and build rpms
test-release:
	@$(MAKE) test-checkout
	# +1 Minor version and add 0.1-gitYYYYMMDD release
	@cat ${APPNAME}.spec | sed  -e '2 s/release/debug/' -e 's/${VER_REGEX}/\1${BUMPED_MINOR}/' -e 's/\(^Release:\s*\)\([0-9]*\)\(.*\)./\10.1.${GITDATE}%{?dist}/' > ${APPNAME}-test.spec ; mv ${APPNAME}-test.spec ${APPNAME}.spec
	@git commit -a -m "bumped ${APPNAME} version ${NEW_VER}-${NEW_REL}"
	# Make archive
	@rm -rf ${APPNAME}-${NEW_VER}.tar.gz
	@git archive --format=tar --prefix=$(APPNAME)-$(NEW_VER)/ HEAD | gzip -9v >${APPNAME}-$(NEW_VER).tar.gz
	# Build RPMS
	@-rpmbuild --define '_topdir $(BUILDDIR)' -D 'app_build debug' -ta ${APPNAME}-${NEW_VER}.tar.gz
	@$(MAKE) test-cleanup

# build release rpms
rpm:
	@$(MAKE) archive
	@rpmbuild --define '_topdir $(BUILDDIR)' -ta ${BUILDDIR}/SOURCES/${APPNAME}-$(VERSION).tar.gz

# make a test-releases and build it in fedora copr
test-copr:
	@$(MAKE) test-release
	copr-cli build --nowait yumex-ng $(COPR_REL_DNF4) $(BUILDDIR)/SRPMS/${APPNAME}-${NEW_VER}-${NEW_REL}*.src.rpm

test-copr-dnf5:
	@$(MAKE) test-release-dnf5
	copr-cli build --nowait yumex-ng $(COPR_REL_DNF5) $(BUILDDIR)/SRPMS/${APPNAME}-${NEW_VER}-${NEW_REL}*.src.rpm

test-copr-yumex-dnf5:
	@$(MAKE) test-release-yumex-dnf5
	copr-cli build --nowait yumex-ng $(COPR_REL_DNF5_SUBPKG) $(BUILDDIR)/SRPMS/${APPNAME_DNF5}-${NEW_VER}-${NEW_REL}*.src.rpm

all-test-copr:
	@$(MAKE) test-copr
	@$(MAKE) test-copr-dnf5
	@$(MAKE) test-copr-yumex-dnf5

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

# install packages needed for running with the dnf5 backend
inst-deps-dnf5:
	sudo dnf5 python3-libdnf5 dnf5daemon-server python3-dasbus

# install packages needed running and building
inst-deps:
	sudo dnf5 install gtk4 libadwaita glib2 meson blueprint-compiler python3-dnf gtk4-devel libadwaita-devel python3-dnfdaemon

# generate the POTFILES from available source files with translations
# POTFILES is source for what fies is used to generate the .POT file.
potfiles:
	@echo "updating po/POTFILES with *.py, .in & *.blp files"
	@find yumex -iname *.py > po/POTFILES
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
	tx pull
	git add po/*
	git commit -m "i18n: updated translations from transifex"

# run unit tests
run-tests:
	pytest

# run unit tests and generate html coverage report
run-test-report:
	pytest --cov --cov-report html

# dnf5 install python3-memray
memray-updater:
	@systemctl --user stop yumex-updater-systray.service
	@$(MAKE) localbuild
	@-mkdir -p profile
	@-rm profile/output.bin
	@-rm profile/memray-flamegraph-output.html
	@-python3 -m memray run -o profile/output.bin ./builddir/bin/yumex_updater_systray
	@-python3 -m memray flamegraph profile/output.bin

# dnf5 install python3-memray
memray-updater-live:
	@-systemctl --user stop yumex-updater-systray.service
	@$(MAKE) localbuild
	@-mkdir -p profile
	@-python3 -m memray run --live ./builddir/bin/yumex_updater_systray



