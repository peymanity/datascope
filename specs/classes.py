from collections import OrderedDict

from django.db import models

from jsonfield import JSONField


class Individual(models.Model):
    community = models.ForeignKey('Community')
    collective = models.ForeignKey('Collective', null=True)

    properties = JSONField()
    schema = JSONField()
    spirit = models.CharField(max_length=256, db_index=True)

    def __getattr__(self, item):
        getattr(self.properties, item)

    @classmethod  # TODO: write manager instead?
    def create_from_dict(cls, dic, schema):
        """
        Create new instance of this class from a dictionary if it validates against the schema.

        :param dic:
        :param schema:the schema to validate against
        :return:
        """
        pass

    def update_from_dict(self, dic):
        """
        Override existing properties with values from dic if it validates against the schema.

        :param dic:
        :return:
        """
        pass

    @property
    def url(self, json_path=None):
        """
        TODO: Uses Django reverse
        Sets an anchor if json_path is given

        :param json_path: (optional)
        :return:
        """
        if not self.id:
            raise ValueError("Can't get path for unsaved Individual")
        return "ind/{}/".format(self.id)



class Collective(models.Model):
    community = models.ForeignKey('Community')

    schema = JSONField()
    spirit = models.CharField(max_length=256, db_index=True)

    @classmethod  # TODO: write manager instead?
    def create_from_list(cls, lst, schema, context=None):
        """
        Create new instance of this class from list if any dictionary inside validates against the schema.
        The matching dictionaries will be stored as Individual. If the context parameter is set to a dictionary.
        The Individuals get updated with the given dictionary.

        :param lst:
        :param schema:
        :param context: (optional)
        :return:
        """
        pass

    def add_from_list(self, lst, context=None):
        """
        Adds any dictionaries in list as Individual to this class if they validate against set schema.
        If the context parameter is set to a dictionary. The Individuals get updated with the given dictionary.

        :param lst:
        :param context: (optional)
        :return:
        """
        pass

    @property
    def url(self, json_path=None):
        """
        TODO: Uses Django reverse
        Sets an anchor if json_path is given

        :param json_path: (optional)
        :return:
        """
        if not self.id:
            raise ValueError("Can't get path for unsaved Collective")
        return "col/{}/".format(self.id)

    def list_json_path(self, json_path):
        """
        Returns a list consisting of values at json_path on Individuals that are members of this Collective.

        :param json_path:
        :return:
        """
        pass

    class Meta:
        unique_together = ('community_id', 'spirit')


class Community(models.Model):
    """
    NB: When fetching a community it is recommended to prefetch Individuals, Collectives and Growths with it
    """

    data = JSONField(null=True, blank=True)

    def get_collective_from_path(self, path):
        """
        Parse a path and return the collective that belongs to that path.
        If a JSON path is specified after the hash, it will return a list of values present at that path.

        :param path:
        :return:
        """
        pass

    def grow(self):
        """


        :return:

        - If data property is set: exit
        - Look for latest Growth
        - Calls Growth.progress
        - If no progress: exit
        - Fetch results
        - Create Collective or Individual from the results
        - Call Community.after_PHASE
        - If there is no new phase: exit
        - Go to next phase
        - Call Community.before_PHASE
        - Start new growth
        """
        if self.data:
            return

    @property
    def results(self):
        """
        This method is meant to be overridden. It should mangle the data attached to the community.
        And return a data structure in the correct form.

        :return: None
        """
        return None


class Growth(models.Model):
    community = models.ForeignKey(Community)
    phase_name = models.CharField(max_length=256)
    phase_properties = JSONField()
    task_id = models.CharField(max_length=256, null=True, blank=True)

    @classmethod
    def create_from_spirit_phase(cls, spirit_phase):
        """
        Creates a new Growth instance from a Community's spirit phase.

        :return:
        """
        pass

    def start(self):
        """
        Starts the Celery tasks according to the phase_properties to enable growth.

        :return:
        """
        pass

    @property
    def progress(self):
        """
        Tries to load the task_id as AsyncResult or GroupResult and indicates task progress.

        :return:
        """
        return None

    @property
    def results(self):
        """
        Returns a Storage class and all ids that were created for the growth

        :return:
        """
        return None


class ImageTranslations(Community):
    spirit = OrderedDict([
        ("translation", {
            "schema": {},
            "config": {
                "_link": "WikiTranslate"
            },
            "process": "Retrieve",
            "input": None,
            "output": "Collective"
        }),
        ("visualization", {
            "schema": {},
            "config": {},
            "process": "Retrieve",
            "input": "/col/1/#$.translation",
            "output": "Collective"
        })
    ])


class PeopleSuggestions(Community):
    spirit = OrderedDict([
        ("person", {
            "schema": {},
            "config": {
                "_link": "WikiSearch"
            },
            "process": "Retrieve",
            "input": None,
            "output": "Individual"
        }),
        ("categories", {
            "schema": {},
            "config": {
                "_link": "WikiCategories"
            },
            "process": "Retrieve",
            "input": "/ind/1/#$.title",
            "output": "Collective"
        }),
        ("members", {
            "schema": {},
            "config": {
                "_link": "WikiCategoryMembers"
            },
            "process": "Retrieve",
            "input": "/col/1/#$.title",
            "output": "Collective"
        })
    ])


class CityCelebrities(Community):
    spirit = OrderedDict([
        ("radius", {
            "schema": {},
            "config": {},
            "process": "Retrieve",
            "input": None,
            "output": "Collective"
        }),
        ("backlinks", {
            "schema": {},
            "config": {},
            "process": "Retrieve",
            "input": "/col/1/#$.title",
            "output": "Collective"
        }),
        ("people_filter", {
            "schema": {},
            "config": {},
            "process": "Submit",
            "input": "/col/2/#$.wikidata",
            "output": "Collective"
        }),
        ("people_text", {
            "schema": {},
            "config": {},
            "process": "Retrieve",
            "input": "/col/3/#$.title",
            "output": "Collective"
        }),
        ("location_text", {
            "schema": {},
            "config": {},
            "process": "Retrieve",
            "input": "/col/1/",
            "output": "Collective"
        })
    ])


class PersonProfile(Community):
    pass


class FamousFlightDeaths(Community):
    pass


class DataScopeView(object):

    @staticmethod
    def get_user_from_request(request):
        """

        :param request:
        :return:
        """
        pass


class CommunityView(DataScopeView):

    @staticmethod
    def get_community_from_request(request):
        """

        :param request:
        :return: a Community ContentModel
        """
        pass


class CollectiveView(DataScopeView):
    pass


class IndividualView(DataScopeView):
    pass
