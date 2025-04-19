from yumex.utils import get_distro_release


def test_get_distro_release():
    release = get_distro_release()
    assert release == "42"
