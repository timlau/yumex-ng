# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#
# Copyright (C) 2022  Tim Lauridsen
#
#

from time import time

import dnf
import dnf.yum
import dnf.const
import dnf.conf
import dnf.subject

from yumex.backend import YumexPackage


class Packages:
    """
    Get access to packages in the dnf (hawkey) sack in an easy way
    """

    def __init__(self, base):
        self._base = base
        self._sack = base.sack
        self._inst_na = self._sack.query().installed()._na_dict()
        self._update_na = self._sack.query().upgrades()._na_dict()

    def _filter_packages(self, pkg_list, replace=True):
        """
        Filter a list of package objects and replace
        the installed ones with the installed object, instead
        of the available object
        """
        pkgs = []
        for pkg in pkg_list:
            key = (pkg.name, pkg.arch)
            inst_pkg = self._inst_na.get(key, [None])[0]
            upd_pkg = self._update_na.get(key, [None])[0]
            if inst_pkg and inst_pkg.evr == pkg.evr:
                # print(inst_pkg, pkg.reponame)
                if replace:
                    new_pkg = YumexPackage(inst_pkg)
                    new_pkg.set_installed(pkg)
                    pkgs.append(new_pkg)
            if upd_pkg and upd_pkg.evr == pkg.evr:
                new_pkg = YumexPackage(upd_pkg)
                new_pkg.set_update(inst_pkg)
                pkgs.append(new_pkg)

            else:
                new_pkg = YumexPackage(pkg)
                pkgs.append(new_pkg)
        return pkgs

    @property
    def query(self):
        """
        Get the query object from the current sack
        """
        return self._sack.query()

    @property
    def installed(self):
        """
        get installed packages
        """
        return self.query.installed().run()

    @property
    def updates(self):
        """
        get available updates
        """
        return self.query.upgrades().run()

    @property
    def all(self, showdups=False):
        """
        all packages in the repositories
        installed ones are replace with the install package objects
        """
        if showdups:
            return self._filter_packages(self.query.available().run())
        else:
            return self._filter_packages(self.query.latest().run())

    @property
    def available(self, showdups=False):
        """
        available packages there is not installed yet
        """
        if showdups:
            return self._filter_packages(self.query.available().run(), replace=False)
        else:
            return self._filter_packages(self.query.latest().run(), replace=True)

    @property
    def extras(self):
        """
        installed packages, not in current repos
        """
        # anything installed but not in a repo is an extra
        avail_dict = self.query.available().pkgtup_dict()
        inst_dict = self.query.installed().pkgtup_dict()
        pkgs = []
        for pkgtup in inst_dict:
            if pkgtup not in avail_dict:
                pkgs.extend(inst_dict[pkgtup])
        return pkgs

    @property
    def obsoletes(self):
        """
        packages there is obsoleting some installed packages
        """
        inst = self.query.installed()
        return self.query.filter(obsoletes=inst)

    @property
    def recent(self, showdups=False):
        """
        Get the recent packages
        """
        recent = []
        now = time()
        recentlimit = now - (self._base.conf.recent * 86400)
        if showdups:
            avail = self.query.available()
        else:
            avail = self.query.latest()
        for po in avail:
            if int(po.buildtime) > recentlimit:
                recent.append(po)
        return recent


class DnfBase(dnf.Base):
    """
    class to encapsulate and extend the dnf.Base API
    """

    def __init__(self, setup_sack=True):
        dnf.Base.__init__(self)
        # setup the dnf cache
        RELEASEVER = dnf.rpm.detect_releasever(self.conf.installroot)
        self.conf.substitutions["releasever"] = RELEASEVER
        # read the repository infomation
        self.read_all_repos()
        if setup_sack:
            # populate the dnf sack
            self.fill_sack()
            self._packages = Packages(self)  # Define a Packages object

    def setup_base(self):
        self.fill_sack()
        self._packages = Packages(self)  # Define a Packages object

    @property
    def packages(self):
        """property to get easy acceess to packages"""
        return self._packages

    def cachedir_fit(self):
        conf = self.conf
        subst = conf.substitutions
        # this is not public API, same procedure as dnf cli
        suffix = dnf.conf.parser.substitute(dnf.const.CACHEDIR_SUFFIX, subst)
        cli_cache = dnf.conf.CliCache(conf.cachedir, suffix)
        return cli_cache.cachedir, cli_cache.system_cachedir

    def setup_cache(self):
        """Setup the dnf cache, same as dnf cli"""
        conf = self.conf
        conf.substitutions["releasever"] = dnf.rpm.detect_releasever("/")
        conf.cachedir, self._system_cachedir = self.cachedir_fit()
        print("cachedir: %s" % conf.cachedir)


class Backend(DnfBase):
    """
    Package backend base on dnf 4.x python API
    """

    def __init__(self):
        DnfBase.__init__(self)

    def get_packages(self):
        return Packages(self).available
