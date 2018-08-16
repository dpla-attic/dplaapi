
"""Test dplaapi.types"""

import pytest
from apistar.exceptions import ValidationError
from dplaapi import types


def test_items_query_type_can_be_instantiated():
    """ItemsQueryType can be instantiated with a dict without error"""
    assert types.ItemsQueryType({'q': 'xx'})


def test_an_items_query_type_object_is_a_dict():
    """ItemsQueryType extends dict"""
    x = types.ItemsQueryType({'q': 'xx'})
    assert isinstance(x, dict)


def test_items_query_type_flunks_bad_string_length():
    """ItemsQueryType flunks a field that is the wrong length"""
    # Just one sample field of many
    with pytest.raises(ValidationError):
        types.ItemsQueryType({'q': 'x'})  # Too few characters


def test_items_query_type_flunks_bad_string_pattern():
    """ItemsQueryType flunks a field that has the wrong pattern"""
    # In this case, the field is supposed to be a URL
    with pytest.raises(ValidationError):
        types.ItemsQueryType({'rights': "I'm free!"})


def test_items_query_type_passes_good_string_pattern():
    """ItemsQueryType passes a field that has the correct pattern"""
    # Again, the field is supposed to be a URL
    assert types.ItemsQueryType({
              'rights': "http://rightsstatements.org/vocab/InC/1.0/"})
