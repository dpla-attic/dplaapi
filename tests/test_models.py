
from dplaapi import models


def test_db_can_be_instantiated():
    assert models.db


def test_account_can_be_instantiated():
    account = models.Account(
        key='08e3918eeb8bf4469924f062072459a8',
        email='x@example.org')
    assert account
