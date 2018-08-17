import os
import logging

def test_dplaapi_warns_if_ES_BASE_not_set(monkeypatch):

    def mock_warning(self, message):
        assert message.startswith('ES_BASE env var is not defined')

    os.putenv('ES_BASE', '')
    monkeypatch.setattr(logging.Logger, 'warning', mock_warning)
    import dplaapi
