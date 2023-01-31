from yumex.backend.dnf import YumexPackage
from yumex.utils.enums import PackageAction, PackageState


# fixtures is defined in conftest.py


def test_yp_init(pkg: YumexPackage):
    """should return the expected properties"""
    assert pkg.name == "mypkg"
    assert pkg.version == "1"
    assert pkg.arch == "x86_64"
    assert pkg.release == "1.0"
    assert pkg.epoch == ""
    assert pkg.repo == "repo2"
    assert pkg.description == "desc"
    assert pkg.size == 2048
    assert pkg.state == PackageState.AVAILABLE
    assert pkg.action == PackageAction.NONE


def test_yp_state_action(pkg_dict):
    """should return the expected properties, when called with state and action kwargs"""
    pkg = YumexPackage(
        **pkg_dict, state=PackageState.INSTALLED, action=PackageAction.INSTALL
    )
    assert pkg.state == PackageState.INSTALLED
    assert pkg.action == PackageAction.INSTALL
    pkg.set_state(PackageState.UPDATE)
    assert pkg.state == PackageState.UPDATE


def test_yp_installed(pkg_dict):
    """Should return the package installation state"""
    pkg = YumexPackage(
        **pkg_dict, state=PackageState.INSTALLED, action=PackageAction.INSTALL
    )
    assert pkg.is_installed
    pkg.state = PackageState.AVAILABLE
    assert pkg.is_installed is False


def test_yp_evr(pkg):
    """should return a evr string based on epoch, version and release"""
    assert pkg.evr == "1-1.0"
    pkg.epoch = "3"
    assert pkg.evr == "3:1-1.0"


def test_yp_nevra(pkg):
    """should return a nevra string based package properties"""
    assert pkg.nevra == "mypkg-1-1.0.x86_64"
    pkg.epoch = "3"
    assert pkg.nevra == "mypkg-3:1-1.0.x86_64"


def test_yp_str(pkg):
    """Should return a string representation of the package (nevra)"""
    assert str(pkg) == "mypkg-1-1.0.x86_64"


def test_yp_repr(pkg):
    assert repr(pkg) == "YumexPackage(mypkg-1-1.0.x86_64) from repo2"


def test_yp_eq(pkg_dict):
    pkg1 = YumexPackage(**pkg_dict)
    pkg2 = YumexPackage(**pkg_dict)
    assert pkg1 == pkg2


def test_yp_hash(pkg_dict):
    pkg1 = YumexPackage(**pkg_dict)
    pkg2 = YumexPackage(**pkg_dict)
    assert hash(pkg1) == hash(pkg2)


def test_yp_id(pkg):

    assert pkg.id == "mypkg,,1,1.0,x86_64,repo2"
    pkg.epoch = "3"
    pkg.repo = "@system"
    assert pkg.id == "mypkg,3,1,1.0,x86_64,system"


def test_yp_size_unit(pkg):
    assert pkg.size_with_unit == "2.0 K"
    pkg.size = 1024 * 1024
    assert pkg.size_with_unit == "1.0 M"
    pkg.size = 1024 * 1024 * 1024
    assert pkg.size_with_unit == "1.0 G"


def test_yp_ref_to(pkg, pkg_upd):
    pkg_upd.set_ref_to(pkg, PackageState.INSTALLED)
    assert pkg_upd.ref_to == pkg
    assert pkg_upd.ref_to.state == PackageState.INSTALLED
