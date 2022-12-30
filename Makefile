
APPNAME = yumex
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

all:
	@echo "Nothing to do, use a specific target"

clean:
	@rm -rf *.tar.gz

archive:
	@rm -rf ${APPNAME}-${VERSION}.tar.gz
	@git archive --format=tar --prefix=$(APPNAME)-$(VERSION)/ HEAD | gzip -9v >${APPNAME}-$(VERSION).tar.gz
	@mkdir -p ${BUILDDIR}/SOURCES
	@cp ${APPNAME}-$(VERSION).tar.gz ${BUILDDIR}/SOURCES
	@rm -rf ${APPNAME}-${VERSION}.tar.gz
	@echo "The archive is in ${BUILDDIR}/SOURCES/${APPNAME}-$(VERSION).tar.gz"

copr-release:
	@rpmbuild --define '_topdir $(BUILDDIR)' -ts ${BUILDDIR}/SOURCES/${APPNAME}-$(VERSION).tar.gz
	@copr-cli build yumex-ng $(BUILDDIR)/SRPMS/${APPNAME}-$(VERSION)*.src.rpm

release:
	@git commit -a -m "bumped release to $(VERSION)"
	@git tag -f -m "Added ${APPNAME}-${VERSION} release tag" ${APPNAME}-${VERSION}
	@git push --tags origin
	@git push origin
	@$(MAKE) archive
	@$(MAKE) copr-release

test-cleanup:
	@rm -rf ${APPNAME}-${VERSION}.test.tar.gz
	@echo "Cleanup the git release-test local branch"
	@git checkout -f
	@git checkout ${GIT_MASTER}
	@git branch -D release-test

show-vars:
	@echo ${GITDATE}
	@echo ${BUMPED_MINOR}
	@echo ${NEW_VER}-${NEW_REL}

test-release:
	@git checkout -b release-test
	# +1 Minor version and add 0.1-gitYYYYMMDD release
	@cat ${APPNAME}.spec | sed  -e '2 s/release/debug/' -e 's/${VER_REGEX}/\1${BUMPED_MINOR}/' -e 's/\(^Release:\s*\)\([0-9]*\)\(.*\)./\10.1.${GITDATE}%{?dist}/' > ${APPNAME}-test.spec ; mv ${APPNAME}-test.spec ${APPNAME}.spec
	@git commit -a -m "bumped ${APPNAME} version ${NEW_VER}-${NEW_REL}"
	# Make archive
	@rm -rf ${APPNAME}-${NEW_VER}.tar.gz
	@git archive --format=tar --prefix=$(APPNAME)-$(NEW_VER)/ HEAD | gzip -9v >${APPNAME}-$(NEW_VER).tar.gz
	# Build RPMS
	@-rpmbuild --define '_topdir $(BUILDDIR)' -D 'app_build debug' -ta ${APPNAME}-${NEW_VER}.tar.gz
	@$(MAKE) test-cleanup

rpm:
	@$(MAKE) archive
	@rpmbuild --define '_topdir $(BUILDDIR)' -ta ${BUILDDIR}/SOURCES/${APPNAME}-$(VERSION).tar.gz

test-copr:
	@$(MAKE) test-release
	copr-cli build yumex-ng $(BUILDDIR)/SRPMS/${APPNAME}-${NEW_VER}-${NEW_REL}*.src.rpm


user:
	meson setup builddir --prefix="$(shell pwd)/builddir" --buildtype=debug --wipe
	ninja -C builddir install
	ninja -C builddir run

inst-buildtools:
	sudo dnf install @fedora-packager copr-cli

inst-deps:
	sudo dnf install gtk4 libadwaita glib2 meson blueprint-compiler python3-dnf

potfiles:
	@echo "updating po/POTFILES with *.py, .in & *.blp files"
	@find yumex -iname *.py > po/POTFILES
	@find data -iname *.blp >> po/POTFILES
	@find data -iname *.in.in >> po/POTFILES

transifex-update:
	@$(MAKE) potfiles
	po/update_potfile.sh
	tx push
	git add po/*
	git commit -m "i18n: updated yumex.pot"

transifex-get:
	tx pull
	git add po/*
	git commit -m "i18n: updated translations from transifex"

