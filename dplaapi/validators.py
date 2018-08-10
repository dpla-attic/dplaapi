
from apistar import types, validators


class Search(types.Type):
    """Validation for querystring data, search()"""
    term = validators.String(
        title='Search term',
        description='Search term',
        min_length=4,
        max_length=6,
        allow_null=False)
