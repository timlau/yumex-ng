class Mock:
    def __init__(self, *args, **kwargs):
        self._calls = {}

    def get_mock_call(self, method) -> list:
        return self._calls.get(method, [])

    def set_mock_call(self, method, args, kwargs):
        call_list = self._calls.get(method, [])
        call_list.append((args, kwargs))
        self._calls[method] = call_list
