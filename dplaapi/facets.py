"""
facets.py
~~~~~~~~~

Data about facets
"""

facets = {
    'admin.contributingInstitution': ('admin.contributingInstitution',
                                      'terms'),
    'dataProvider': ('dataProvider.not_analyzed', 'terms'),
    'hasView.@id': ('hasView.@id', 'terms'),
    'hasView.format': ('hasView.format', 'terms'),
    'intermediateProvider': ('intermediateProvider.not_analyzed', 'terms'),
    'isPartOf.@id': ('isPartOf.@id', 'terms'),
    'isPartOf.name': ('isPartOf.name.not_analyzed', 'terms'),
    'provider.@id': ('provider.@id', 'terms'),
    'provider.name': ('provider.name.not_analyzed', 'terms'),
    'rights': ('rights', 'terms'),
    'rightsCategory': ('rightsCategory', 'terms'),
    'sourceResource.collection.title': ('sourceResource.collection.title'
                                        '.not_analyzed',
                                        'terms'),
    'sourceResource.contributor': ('sourceResource.contributor', 'terms'),
    'sourceResource.date.begin': ('sourceResource.date.begin',
                                  'date_histogram'),
    'sourceResource.date.begin.year': ('sourceResource.date.begin',
                                       'date_histogram'),
    'sourceResource.date.begin.month': ('sourceResource.date.begin',
                                        'date_histogram'),
    'sourceResource.date.end': ('sourceResource.date.end', 'date_histogram'),
    'sourceResource.date.end.year': ('sourceResource.date.end',
                                     'date_histogram'),
    'sourceResource.date.end.month': ('sourceResource.date.end',
                                      'date_histogram'),
    'sourceResource.format': ('sourceResource.format', 'terms'),
    'sourceResource.language.iso639_3': ('sourceResource.language.iso639_3',
                                         'terms'),
    'sourceResource.language.name': ('sourceResource.language.name', 'terms'),
    'sourceResource.publisher': ('sourceResource.publisher.not_analyzed',
                                 'terms'),
    'sourceResource.spatial.city': ('sourceResource.spatial.city.not_analyzed',
                                    'terms'),
    'sourceResource.spatial.coordinates': ('sourceResource.spatial'
                                           '.coordinates',
                                           'geo_distance'),
    'sourceResource.spatial.country': ('sourceResource.spatial.country'
                                       '.not_analyzed',
                                       'terms'),
    'sourceResource.spatial.county': ('sourceResource.spatial.county'
                                      '.not_analyzed',
                                      'terms'),
    'sourceResource.spatial.name': ('sourceResource.spatial.name.not_analyzed',
                                    'terms'),
    'sourceResource.spatial.region': ('sourceResource.spatial.region'
                                      '.not_analyzed',
                                      'terms'),
    'sourceResource.spatial.state': ('sourceResource.spatial.state'
                                     '.not_analyzed',
                                     'terms'),
    'sourceResource.subject.@id': ('sourceResource.subject.@id', 'terms'),
    'sourceResource.subject.name': ('sourceResource.subject.name.not_analyzed',
                                    'terms'),
    'sourceResource.temporal.begin': ('sourceResource.temporal.begin',
                                      'date_histogram'),
    'sourceResource.temporal.begin.year': ('sourceResource.temporal.begin',
                                           'date_histogram'),
    'sourceResource.temporal.begin.month': ('sourceResource.temporal.begin',
                                            'date_histogram'),
    'sourceResource.temporal.end': ('sourceResource.temporal.end',
                                    'date_histogram'),
    'sourceResource.temporal.end.year': ('sourceResource.temporal.end',
                                         'date_histogram'),
    'sourceResource.temporal.end.month': ('sourceResource.temporal.end',
                                          'date_histogram'),
    'sourceResource.type': ('sourceResource.type', 'terms')
}
