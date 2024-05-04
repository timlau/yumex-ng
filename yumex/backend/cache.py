from typing import Generator
from yumex.backend.dnf import YumexPackage
from yumex.backend.interface import PackageBackend
from yumex.utils import log
from yumex.utils.enums import PackageFilter, PackageState


class YumexPackageCache:
    """A cache for storing YumexPackages, so the state is preserved when getting packages
    from the PackageBackend.

    Implement the PackageCache protocol class
    """

    def __init__(self, backend: PackageBackend) -> None:
        self._packages = {}
        self.backend: PackageBackend = backend
        self._package_dict = {}

    def get_packages_by_filter(self, pkgfilter: PackageFilter, reset=False) -> list[YumexPackage]:
        if not isinstance(pkgfilter, PackageFilter):
            raise KeyError(f"{pkgfilter} is not a valid PackageFilter")
        if pkgfilter not in self._packages or reset:
            pkgs = self.get_packages(self.backend.get_packages(pkgfilter))
            self._packages[pkgfilter] = list(pkgs)
        return self._packages[pkgfilter]

    def get_packages(self, pkgs: list[YumexPackage]) -> Generator[YumexPackage, None, None]:
        for pkg in pkgs:
            yield self.get_package(pkg)

    def get_package(self, pkg: YumexPackage) -> YumexPackage:
        """cache a new package or return the already cached one"""
        if pkg not in self._package_dict:
            self._package_dict[pkg] = pkg
            return pkg
        else:
            cached_pkg = self._package_dict[pkg]
            if pkg.state != cached_pkg.state:
                log(f" update state : {cached_pkg}{cached_pkg.state} {pkg}{pkg.state}")
                self._update_state(cached_pkg, pkg)
            # use the action from the newest pkg,
            # to get queued deps, sorted the right way
            cached_pkg.action = pkg.action
            return cached_pkg

    def _update_state(self, current, new) -> None:
        """update the state of the cached pkg"""
        match (current.state, new.state):
            case (PackageState.AVAILABLE, PackageState.UPDATE):
                current.state = PackageState.UPDATE
            case (PackageState.INSTALLED, PackageState.UPDATE):
                current.state = PackageState.UPDATE
            case (PackageState.AVAILABLE, PackageState.INSTALLED):
                current.state = PackageState.INSTALLED
