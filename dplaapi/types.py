
import apistar


sr = 'SourceResource (Cultural Heritage Object)'
url_match_pat = r'^https?://[-a-zA-Z0-9:%_\+.~#?&/=]+$'

items_params = {
    'q': apistar.validators.String(
            title='Search term',
            description='Search term',
            min_length=2,
            max_length=200,
            allow_null=True),
    'id': apistar.validators.String(
            title='ID',
            description='DPLA Record ID',
            min_length=32,
            max_length=32,
            pattern=r'^[a-f0-9]{32}$',
            allow_null=True),
    'sourceResource.title': apistar.validators.String(
            title='Title',
            description='Primary name given to ' + sr,
            min_length=2,
            max_length=200,
            allow_null=True),
    'sourceResource.description': apistar.validators.String(
            title='Description',
            description='Includes, but is not limited to an abstract, a table '
                        'of contents, or a free-text account of ' + sr,
            min_length=2,
            max_length=200,
            allow_null=True),
    'sourceResource.collection.title': apistar.validators.String(
            title='Collection Title',
            description='Name of the collection or aggregation of which '
                        "%s is a part" % sr,
            min_length=2,
            max_length=200,
            allow_null=True),
    'sourceResource.collection.description': apistar.validators.String(
            title='Collection Description',
            description='Free-text account of collection, for example an '
                        'abstract or content scope note',
            min_length=2,
            max_length=200,
            allow_null=True),
    'sourceResource.collection': apistar.validators.String(
            title='Collection',
            description="Entity or collection of which %s is a part" % sr,
            min_length=2,
            max_length=200,
            allow_null=True),
    'sourceResource.collection.id': apistar.validators.String(
            title='Collection ID',
            description=sr + ' Collection ID',
            min_length=2,
            max_length=200,
            allow_null=True),
    'sourceResource.collection.@id': apistar.validators.String(
            title='Collection @id',
            description=sr + ' Collection URI',
            min_length=2,
            max_length=200,
            pattern=url_match_pat,
            allow_null=True),
    'sourceResource.contributor': apistar.validators.String(
            title='Contributor',
            description='Entity responsible for making contributions to ' + sr,
            min_length=2,
            max_length=200,
            allow_null=True),
    'sourceResource.creator': apistar.validators.String(
            title='Creator',
            description='Entity primarily responsible for making ' + sr,
            min_length=2,
            max_length=200,
            allow_null=True),
    'sourceResource.extent': apistar.validators.String(
            title='Extent',
            description='Size or duration of ' + sr,
            min_length=2,
            max_length=200,
            allow_null=True),
    'sourceResource.format': apistar.validators.String(
            title='Format',
            description='File format, physical medium, or dimensions of ' + sr,
            min_length=2,
            max_length=200,
            allow_null=True),
    'sourceResource.language.name': apistar.validators.String(
            title='Subject Name',
            description='Source Resource Subject Name',
            min_length=2,
            max_length=200,
            allow_null=True),
    'sourceResource.language': apistar.validators.String(
            title='Language',
            description='Language of ' + sr,
            min_length=2,
            max_length=200,
            allow_null=True),
    'sourceResource.language.iso639_3': apistar.validators.String(
            title='Language ISO Code',
            description='Language ISO-639-3 code of ' + sr,
            min_length=2,
            max_length=200,
            allow_null=True),
    'sourceResource.publisher': apistar.validators.String(
            title='Publisher',
            description="Entity responsible for making the %s available, "
                        "typically the publisher of a text" % sr,
            min_length=2,
            max_length=200,
            allow_null=True),
    'sourceResource.relation': apistar.validators.String(
            title='Relation',
            description='Resource related to ' + sr,
            min_length=2,
            max_length=200,
            allow_null=True),
    'sourceResource.spatial.name': apistar.validators.String(
            title='Place Name',
            description="Name of place related to %s" % sr,
            min_length=2,
            max_length=200,
            allow_null=True),
    'sourceResource.spatial.country': apistar.validators.String(
            title='Country',
            description="Name of country related to %s" % sr,
            min_length=2,
            max_length=200,
            allow_null=True),
    'sourceResource.spatial.state': apistar.validators.String(
            title='State, Province, or Administrative Region',
            description='Name of state, province, or other administrative '
                        "region related to %s" % sr,
            min_length=2,
            max_length=200,
            allow_null=True),
    'sourceResource.spatial.county': apistar.validators.String(
            title='U.S. County',
            description="Name of U.S. county related to %s" % sr,
            min_length=2,
            max_length=200,
            allow_null=True),
    'sourceResource.spatial.region': apistar.validators.String(
            title='Region',
            description="A region of arbitrary scope related to %s" % sr,
            min_length=2,
            max_length=200,
            allow_null=True),
    'sourceResource.spatial.coordinates': apistar.validators.String(
            title='Coordinates',
            description="Decimal geographic coordinates related to %s" % sr,
            min_length=2,
            max_length=200,
            allow_null=True),
    'sourceResource.specType': apistar.validators.String(
            title='Genre',
            description='edm:isRelatedTo. Captures categories of objects in '
                        'a given field',
            min_length=2,
            max_length=200,
            allow_null=True),
    'sourceResource.subject': apistar.validators.String(
            title='Subject',
            description='Topic of ' + sr,
            min_length=2,
            max_length=200,
            allow_null=True),
    'sourceResource.subject.name': apistar.validators.String(
            title='Subject Name',
            description="Name of subject of %s. Maps to skos:prefLabel." % sr,
            min_length=2,
            max_length=200,
            allow_null=True),
    'sourceResource.type': apistar.validators.String(
            title='Subject Name',
            description='Source Resource Subject Name',
            min_length=2,
            max_length=200,
            allow_null=True),
    'dataProvider': apistar.validators.String(
            title='Subject Name',
            description='Source Resource Subject Name',
            min_length=2,
            max_length=200,
            allow_null=True),
    'intermediateProvider': apistar.validators.String(
            title='Intermediate Provider',
            description='An intermediate organization that selects, collates, '
                        'or curates data from a Data Provider that is then '
                        'aggregated by a Provider from which DPLA harvests. '
                        'The organization must be distinct from both the Data '
                        'Provider and the Provider in the data supply chain.',
            min_length=2,
            max_length=200,
            allow_null=True),
    'provider.name': apistar.validators.String(
            title='Provider Name',
            description='A Service or Content Hub providing access to the '
                        'Data Provider’s content. May contain the same value '
                        'as Data Provider.',
            min_length=2,
            max_length=200,
            allow_null=True),
    'hasView': apistar.validators.String(
            title='Web Resource',
            description='Relates an ore:Aggregation about a '
                        'dpla:SourceResource with an edm:WebResource',
            min_length=2,
            max_length=200,
            allow_null=True),
    'hasView.@id': apistar.validators.String(
            title='Web Resource URL',
            description='URL of the Web Resource that is related to the DPLA '
                        'ore:Aggregation (record)',
            min_length=2,
            max_length=200,
            pattern=url_match_pat,
            allow_null=True),
    'hasView.format': apistar.validators.String(
            title='Web Resource MIME type',
            description='The MIME type of the resource indicated by '
                        'hasView.@id',
            min_length=8,
            max_length=20,
            pattern=r'^[a-z]+/[a-z]$',
            allow_null=True),
    'hasView.rights': apistar.validators.String(
            title='Web Resource Rights',
            description='Rights statement for the Web Resource, as given by '
                        'its provider.  Usually not a standardized rights '
                        'statement.',
            min_length=2,
            max_length=200,
            allow_null=True),
    'isShownAt': apistar.validators.String(
            title='Digital Object Web Resource',
            description="Unambiguous URL reference to the digital "
                        "representation of the %s in its "
                        "full information context." % sr,
            min_length=2,
            max_length=200,
            pattern=url_match_pat,
            allow_null=True),
    'object': apistar.validators.String(
            title='Thumbnail Image',
            description='An unambiguous URL reference to the DPLA digital '
                        'content preview of the Digital Object Web Resource',
            min_length=2,
            max_length=200,
            allow_null=True),
    'provider': apistar.validators.String(
            title='Provider',
            description='Service or content hub providing access to the Data '
                        'Provider’s content. May contain the same value as '
                        'Data Provider.',
            min_length=2,
            max_length=200,
            allow_null=True),
    'provider.@id': apistar.validators.String(
            title='Provider URI',
            description="The DPLA's URI for the provider",
            min_length=2,
            max_length=200,
            pattern=url_match_pat,
            allow_null=True),
    'sourceResource.identifier': apistar.validators.String(
            title='Identifier',
            description="Original identifier of the %s as given by "
                        "its provider" % sr,
            min_length=2,
            max_length=200,
            allow_null=True),
    'sourceResource.rights': apistar.validators.String(
            title='SourceResource Rights',
            description="Rights statement for the %s as given by its "
                        "provider. Usually not a standardized rights "
                        "statement." % sr,
            min_length=2,
            max_length=200,
            allow_null=True),
    'rights': apistar.validators.String(
            title='Standardized Rights Statement (edm:Rights)',
            description='The value given here should be the rights statement '
                        'that applies to the digital representation as given '
                        'in object or isShownAt, when these resources are '
                        'not provided with their own edm:rights. ',
            min_length=2,
            max_length=200,
            pattern=url_match_pat,
            allow_null=True)
}


class ItemsQueryType(dict):
    def __init__(self, *args):
        super(ItemsQueryType, self).__init__(*args)
        for k, v in self.items():
            if k in items_params:
                items_params[k].validate(v)
            else:
                raise apistar.exceptions.ValidationError(
                    "%s is not a valid parameter" % k)
