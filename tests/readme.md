## unit tests

files named **test\_\*** is quick unit test there is executed by default, when running pytest

files named **dont_test\*\*** test code be running real live actions, they must be run manually
the takes time to execute and some test have requirments to packages must be available in the repos

example of manually running tests.

```
pytest tests/dont_test_service.py -v
pytest tests/dont_test_dnf5_backend_root.py -v
```
