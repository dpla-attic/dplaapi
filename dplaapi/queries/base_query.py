"""
base_query
~~~~~~~~~~

Base class that other query classes extend
"""
from dplaapi.field_or_subfield import field_or_subfield


class BaseQuery():

    def add_sort_clause(self, params):
        actual_field = field_or_subfield[params['sort_by']]
        if actual_field == 'sourceResource.spatial.coordinates':
            pin = params['sort_by_pin']
            self.query['sort'] = [
                {
                    '_geo_distance': {
                        'sourceResource.spatial.coordinates': pin,
                        'order': 'asc',
                        'unit': 'mi'
                    }
                }
            ]
        else:
            self.query['sort'] = [
                {actual_field: {'order': params['sort_order']}},
                {'_score': {'order': 'desc'}}]
