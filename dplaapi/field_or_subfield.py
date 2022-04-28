"""
dplaapi.field_or_subfield
~~~~~~~~~~~~~~~~~~~~~~~~~

A dictionary of mappings between given field name and the actual field in the
Elasticsearch mapping that we want to use for the field.

This is used by dplaapi.search_query.SearchQuery and dplaapi.mlt_query.MLTQuery
for the purpose of constructing "sort" and "fields" clauses in queries.
"""

# Dictionary of {field: actual field to use} for a sort or an
# "exact_field_match" query
field_or_subfield = {
    'dataProvider': 'dataProvider.name.not_analyzed',
    'dataProvider.name': 'dataProvider.name.not_analyzed',
    'dataProvider.@id': 'dataProvider.@id',
    'dataProvider.exactMatch': 'dataProvider.exactMatch.not_analyzed',
    '@id': '@id',
    'hasView.@id': 'hasView.@id',
    'hasView.format': 'hasView.format',
    'id': 'id',
    'isPartOf.@id': 'isPartOf.@id',
    'isPartOf.name': 'isPartOf.name.not_analyzed',
    'isShownAt': 'isShownAt',
    'object': 'object',
    'provider.@id': 'provider.@id',
    'provider.name': 'provider.name.not_analyzed',
    'sourceResource.contributor': 'sourceResource.contributor',
    'sourceResource.date.begin': 'sourceResource.date.begin.not_analyzed',
    'sourceResource.date.end': 'sourceResource.date.end.not_analyzed',
    'sourceResource.extent': 'sourceResource.extent',
    'sourceResource.format': 'sourceResource.format',
    'sourceResource.language.iso639_3': 'sourceResource.language.iso639_3',
    'sourceResource.language.name': 'sourceResource.language.name',
    'sourceResource.publisher': 'sourceResource.publisher.not_analyzed',
    'sourceResource.spatial': 'sourceResource.spatial.name.not_analyzed',
    'sourceResource.spatial.city': 'sourceResource.spatial.city.not_analyzed',
    'sourceResource.spatial.coordinates': 'sourceResource.spatial.coordinates',
    'sourceResource.spatial.country': 'sourceResource.spatial.country'
                                      '.not_analyzed',
    'sourceResource.spatial.county': 'sourceResource.spatial.county'
                                     '.not_analyzed',
    'sourceResource.spatial.name': 'sourceResource.spatial.name.not_analyzed',
    'sourceResource.spatial.region': 'sourceResource.spatial.region'
                                     '.not_analyzed',
    'sourceResource.spatial.state': 'sourceResource.spatial.state'
                                    '.not_analyzed',
    'sourceResource.subject.@id': 'sourceResource.subject.@id',
    'sourceResource.subject.name': 'sourceResource.subject.name.not_analyzed',
    'sourceResource.subject.scheme': 'sourceResource.subject.scheme.not_analyzed',
    'sourceResource.temporal.begin': 'sourceResource.temporal.begin'
                                     '.not_analyzed',
    'sourceResource.temporal.end': 'sourceResource.temporal.end.not_analyzed',
    'sourceResource.title': 'sourceResource.title.not_analyzed',
    'sourceResource.type': 'sourceResource.type'
}
