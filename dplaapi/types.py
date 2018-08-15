
import apistar


class ItemsQueryType(apistar.types.Type):
    """Parameter constraints for item searches"""
    q = apistar.validators.String(
        title='Search term',
        description='Search term',
        min_length=2,
        max_length=200,
        allow_null=True)

    def is_match_all(self):
        return not self.q
