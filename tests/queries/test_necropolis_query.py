"""Test dplaapi.mlt_query"""

from dplaapi.queries import necropolis_query


def test_NecropolisQuery_has_source_clause_for_fields_parameter():
    """If given an 'id' parameter, SearchQuery produces a 'terms' query with
    the ID"""
    params = {
        'id': '13283cd2bd45ef385aae962b144c7e6a',
    }
    nq = necropolis_query.NecropolisQuery(params)
    assert nq.query['query']['terms'] == {
        'id': ['13283cd2bd45ef385aae962b144c7e6a']
    }
