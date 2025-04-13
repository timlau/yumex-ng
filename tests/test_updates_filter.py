from yumex.backend.dnf5daemon import create_package
from yumex.backend.dnf5daemon.filter import FilterUpdates


def get_packages_by_name(package_name: str) -> list:
    # Mock function to simulate package retrieval
    ypgk1 = create_package(
        {
            "arch": "x86_64",
            "evr": "1.0-1",
            "install_size": 257602,
            "is_installed": False,
            "name": package_name,
            "repo_id": "base",
            "summary": "This package don't exist",
        }
    )
    ypgk2 = create_package(
        {
            "arch": "x86_64",
            "evr": "1.1-1",
            "install_size": 257602,
            "is_installed": False,
            "name": package_name,
            "repo_id": "updates",
            "summary": "This package don't exist",
        }
    )
    ypgk3 = create_package(
        {
            "arch": "x86_64",
            "evr": "1.2-1",
            "install_size": 257602,
            "is_installed": False,
            "name": package_name,
            "repo_id": "epel",
            "summary": "This package don't exist",
        }
    )
    return [ypgk1, ypgk2, ypgk3]


def test_get_repo_priority():
    repo_priority = {
        "base": 1,
        "updates": 2,
        "epel": 3,
    }
    filter_updates = FilterUpdates(repo_priority, None)
    assert filter_updates._get_repo_priority("base") == 1
    assert filter_updates._get_repo_priority("updates") == 2
    assert filter_updates._get_repo_priority("epel") == 3


def test_get_package_repos():
    repo_priority = {
        "base": 1,
        "updates": 2,
        "epel": 3,
    }
    filter_updates = FilterUpdates(repo_priority, get_packages_by_name)
    repos = filter_updates._get_package_repos("test-package")
    assert set(repos) == {"base", "updates", "epel"}


def test_filter_updates():
    repo_priority = {
        "base": 1,
        "updates": 2,
        "epel": 3,
    }
    filter_updates = FilterUpdates(repo_priority, get_packages_by_name)
    updates = get_packages_by_name("test-package")
    filtered_updates = filter_updates._filter_updates(updates)
    assert len(filtered_updates) == 1
    assert filtered_updates[0].repo == "base"
    assert filtered_updates[0].evr == "1.0-1"
