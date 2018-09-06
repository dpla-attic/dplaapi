import pytest


@pytest.fixture(scope='function', autouse=True)
def disable_env_vars(monkeypatch):
    monkeypatch.delenv('ES_BASE', raising=False)
    monkeypatch.delenv('APP_LOG_LEVEL', raising=False)
    monkeypatch.delenv('DISABLE_AUTH', raising=False)
    monkeypatch.delenv('EMAIL_FROM', raising=False)
    monkeypatch.delenv('POSTGRES_DATABASE', raising=False)
    monkeypatch.delenv('POSTGRES_HOST', raising=False)
    monkeypatch.delenv('POSTGRES_USER', raising=False)
    monkeypatch.delenv('POSTGRES_PASSWORD', raising=False)
    monkeypatch.delenv('POSTGRES_MAX_CONN', raising=False)
    monkeypatch.delenv('POSTGRES_TIMEOUT', raising=False)
    monkeypatch.delenv('POSTGRES_STALE_TIMEOUT', raising=False)
    monkeypatch.delenv('AWS_ACCESS_KEY_ID', raising=False)
    monkeypatch.delenv('AWS_SECRET_ACCESS_KEY', raising=False)
