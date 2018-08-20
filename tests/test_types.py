
"""Test dplaapi.types"""

import pytest
from apistar.exceptions import ValidationError
from dplaapi import types


def test_ItemsQueryType_can_be_instantiated():
    """ItemsQueryType can be instantiated with a dict without error"""
    assert types.ItemsQueryType({'q': 'xx'})


def test_an_ItemsQueryType_object_is_a_dict():
    """ItemsQueryType extends dict"""
    x = types.ItemsQueryType({'q': 'xx'})
    assert isinstance(x, dict)


def test_ItemsQueryType_flunks_bad_string_length():
    """ItemsQueryType flunks a field that is the wrong length"""
    # Just one sample field of many
    with pytest.raises(ValidationError):
        types.ItemsQueryType({'q': 'x'})  # Too few characters


def test_ItemsQueryType_flunks_bad_string_pattern():
    """ItemsQueryType flunks a field that has the wrong pattern"""
    # In this case, the field is supposed to be a URL
    with pytest.raises(ValidationError):
        types.ItemsQueryType({'rights': "I'm free!"})


def test_ItemsQueryType_passes_good_string_pattern():
    """ItemsQueryType passes a field that has the correct pattern"""
    # Again, the field is supposed to be a URL
    assert types.ItemsQueryType({
              'rights': "http://rightsstatements.org/vocab/InC/1.0/"})


def test_ItemsQueryType_flunks_bad_param_name():
    """ItemsQueryType flunks a bad querystring parameter name"""
    with pytest.raises(ValidationError):
        types.ItemsQueryType({'not_a_valid_param': 'x'})


def test_ItemsQueryType_sets_default_page():
    """ItemsQueryType sets default page number 1 if it is not provided"""
    x = types.ItemsQueryType()
    assert x['page'] == 1


def test_ItemsQueryType_sets_default_page_size():
    """ItemsQueryType sets default page size 10 if it is not provided"""
    x = types.ItemsQueryType()
    assert x['page_size'] == 10


def test_ItemsQueryType_validates_offset():
    """ItemsQueryType validates that page and page size are within limits"""
    types.ItemsQueryType({'page_size': '500', 'page': '100'})  # OK
    types.ItemsQueryType({'page_size': '1', 'page': '50499'})  # OK
    types.ItemsQueryType({'page_size': '10', 'page': '5049'})  # OK
    with pytest.raises(ValidationError):
        types.ItemsQueryType({'page_size': '500', 'page': '101'})
    with pytest.raises(ValidationError):
        types.ItemsQueryType({'page_size': '10', 'page': '5050'})
