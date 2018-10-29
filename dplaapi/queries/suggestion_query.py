"""
dplaapi.suggestion_query
~~~~~~~~~~~~~~~~~~~~~~~~

Elasticsearch Phrase Suggester Query
"""

query_skel = {'suggest': {}}
fields = ['sourceResource.title', 'sourceResource.description']


def field_clause(field):
    return {

        'term': {
            'field': "%s.suggestion" % field
        }
    }


class SuggestionQuery():
    """Elasticsearch Phrase Suggester Query

    Representing the JSON request body of the _search POST request.
    The `query' attribute is a dict that represents the JSON of the
    Elasticsearch query.

    Instance attributes:
    - query: The dict that will be serialized to JSON for the query.
    """
    def __init__(self, params: dict):
        """Initialize the query

        Arguments:
        - params: The request's path and querystring parameters
        """
        self.query = query_skel.copy()
        self.query['suggest']['text'] = params['text']
        for field in fields:
            self.query['suggest'][field] = field_clause(field)
