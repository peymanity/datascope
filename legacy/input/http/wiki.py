# TODO: split up into separate files
import json, hashlib, re

from legacy.input.http.base import JsonQueryLink, HttpJsonMixin, HttpLink
from legacy.input.helpers import sanitize_single_trueish_input
from legacy.helpers.override import override_dict
from legacy.helpers.data import extractor
from legacy.exceptions import HIFUnexpectedInput, HIFHttpError40X, HIFHttpWarning300


class WikiBaseQuery(JsonQueryLink):

    HIF_link = 'http://{}.wikipedia.org/w/api.php'  # updated at runtime
    HIF_query_parameter = 'titles'
    HIF_namespace = "wiki"

    HIF_parameters = {
        "action": "query",
        "prop": "info|pageprops",  # we fetch a lot here and filter with objectives for simplicity sake
        "format": "json",
        "redirects": "1"
    }
    HIF_wiki_results_key = 'pages'

    HIF_objective = {
        "pageid": 0,
        "ns": None,
        "title": "",
        "pageprops.wikibase_item": "",
        "pageprops.page_image": ""
    }
    HIF_translations = {
        "pageprops.wikibase_item": "wikidata",
        "pageprops.page_image": "image"
    }

    def setup(self, *args, **kwargs):
        super(WikiBaseQuery, self).setup(*args, **kwargs)
        if self.config.extracts and "extracts" not in self.HIF_parameters['prop']:
            self.HIF_parameters['prop'] = self.HIF_parameters['prop'] + '|' + 'extracts'
            self.HIF_objective['extract'] = ""
        return self

    def prepare_link(self):
        """
        Prepare link does some pre formatting by including the source_language as a sub domain.
        """
        link = super(WikiBaseQuery, self).prepare_link()
        return link.format(self.config.source_language)

    def handle_error(self):
        """
        Handles missing pages and ambiguity errors
        You can only handle these errors by parsing body :(
        """
        super(WikiBaseQuery,self).handle_error()

        # Check general response
        body = json.loads(self.body)
        if "query" not in body:
            raise HIFUnexpectedInput('Wrongly formatted Wikipedia response, missing "query"')
        response = body['query'][self.HIF_wiki_results_key]  # Wiki has response hidden under single keyed dicts :(

        # We force a 404 on missing pages
        message = "We did not find the page you were looking for. Perhaps you should create it?"
        # When searching for pages a dictionary gets returned
        if isinstance(response, dict) and "-1" in response and "missing" in response["-1"]:
            self.status = 404
            raise HIFHttpError40X(message)
        # When making lists a list is returned
        elif isinstance(response, list) and not response:
            self.status = 404
            raise HIFHttpError40X(message)

        return response

    def prepare_next(self):
        body = json.loads(self.body)
        if "query-continue" in body and self.HIF_next_parameter:
            self.next_value = body["query-continue"].values()[0][self.HIF_next_parameter]
        else:
            self.next_value = None
        return super(WikiBaseQuery, self).prepare_next()

    def extract(self, source):
        """
        We override the extract to filter out Wiki warnings that mess up clean extraction.
        :param source:
        :return:
        """
        data = json.loads(source)
        if "warnings" in data:
            del(data["warnings"])

        self._data = extractor(data, self.HIF_objective)
        return self

    def translate(self):
        super(WikiBaseQuery, self).translate()
        # Update image URL's to point to commons directly
        for page in self._data:
            if "image" in page and page['image']:
                md5 = hashlib.md5(page['image'].encode("utf-8"))
                hexhash = md5.hexdigest()
                page['image'] = u'http://upload.wikimedia.org/wikipedia/commons/{}/{}/{}'.format(
                    hexhash[:1],
                    hexhash[:2],
                    page['image']
                )
        return self


    class Meta:
        proxy = True


class WikiGenerator(WikiBaseQuery):

    def cleaner(self, result_instance):
        """
        We're filtering out all list pages when using generators to avoid complications.
        :param result_instance:
        :return:
        """
        # TODO: a WikiData filter would be more accurate.
        if result_instance["title"].startswith('List'):
            return False
        return True

    def handle_error(self):
        """
        Generators have a habit of leaving out the query parameter if the query returns nothing :(
        :return:
        """
        try:
            super(WikiGenerator, self).handle_error()
        # HIFUnexpectedInput should result in an empty list.
        # This indicates the generator didn't find anything under the 'query' key in body
        except HIFUnexpectedInput:
            # raise HIFHttpError40X("We did not find the page you were looking for. Perhaps you should create it?")
            pass

    class Meta:
        proxy = True


class WikiSearch(WikiBaseQuery):

    @property
    def data(self):
        """
        When we use WikiSearch we expect a single item not a list
        So we take the first item from the list that data returns here
        """
        data = super(WikiSearch, self).data
        return data[0] if len(data) else {}

    def handle_error(self):

        # Look for ambiguity when dealing with pages search
        response = super(WikiSearch, self).handle_error()
        if isinstance(response, dict):
            for page_id, page in response.iteritems():
                try:
                    if "disambiguation" in page['pageprops']:
                        self.status = 300
                        raise HIFHttpWarning300(page["title"])
                except KeyError:
                    pass

    class Meta:
        app_label = "legacy"
        proxy = True


class WikiTranslate(WikiBaseQuery):

    HIF_link = 'http://{}.wiktionary.org/w/api.php'  # updated at runtime

    HIF_parameters = override_dict(WikiBaseQuery.HIF_parameters, {
        'prop': 'info|pageprops|iwlinks',
        'iwprop': 'url',
        'iwprefix': None,  # set at runtime
    })

    HIF_objective = {
        "url": None,
        "*": None,
        "prefix": None
    }
    HIF_translations = {
        "*": "translation",
        "prefix": "language"
    }

    def prepare_params(self):
        """
        Prepare params sets the inter wiki prefix as a parameter depending on the language to translate to.
        """
        self.HIF_parameters['iwprefix'] = self.config.translate_to
        return super(WikiTranslate, self).prepare_params()

    def handle_error(self):
        super(WikiTranslate, self).handle_error()
        # TODO: re-enable this. Causes bug with extend at the moment.
        #if not "iwlinks" in self.body:
        #    self.status = 404
        #    raise HIFHttpError40X("No translations found in {} for {}".format(self.config.translate_to, self.input))

    class Meta:
        app_label = "legacy"
        proxy = True


class WikiDataClaims(HttpLink, HttpJsonMixin):

    HIF_link = "https://www.wikidata.org/wiki/Special:EntityData/{}.json"  # updated at runtime
    HIF_namespace = 'wiki'

    HIF_objective = {
        "property": "",
        "datavalue.value.numeric-id": 0
    }
    HIF_translations = {
        "datavalue.value.numeric-id": "item"
    }

    def __init__(self, *args, **kwargs):
        super(WikiDataClaims, self).__init__(*args, **kwargs)
        HttpJsonMixin.__init__(self)

    def sanitize_input(self, to_check):
        return sanitize_single_trueish_input(to_check, class_name=self.__class__.__name__)

    def prepare_link(self):
        link = super(WikiDataClaims, self).prepare_link()
        return link.format(self.input)

    def cleaner(self, result_instance):
        return result_instance['item'] and result_instance['property'] not in self.config.excluded_properties

    @property
    def rsl(self):
        claims = self.data
        unique_claims = {"{}:{}".format(claim['property'], claim['item']): claim for claim in claims}.values()
        return unique_claims

    class Meta:
        app_label = "legacy"
        proxy = True


class WikiDataClaimers(HttpLink, HttpJsonMixin):

    # TODO: add an exact operator to reach() to solve issue with similarly named keys

    HIF_link = "http://wdq.wmflabs.org/api?q={}"
    HIF_objective = {
        "status.items": 0,
        "items": []
    }

    def __init__(self, *args, **kwargs):
        super(WikiDataClaimers, self).__init__(*args, **kwargs)
        HttpJsonMixin.__init__(self)

    def sanitize_input(self, to_check):
        if not isinstance(to_check, (list, tuple,)):
            return False, "WikiDataClaimers expects a list or tuple"
        # TODO write a sanitize function that checks for existence of keys
        for claim_input in to_check:
            if not "property" in claim_input or not "item" in claim_input:
                return False, "Found input without 'property' and 'item' keys: {}".format(to_check)
        return True, to_check

    def prepare_link(self):

        query_expression = "CLAIM[{}:{}] AND "
        query = ''
        for claim in self.input:
            property = claim['property'][1:]  # strips 'P'
            item = claim['item']
            query += query_expression.format(property, item)

        link = super(WikiDataClaimers, self).prepare_link()
        return link.format(query)[:-5]  # strips last AND

    @property
    def data(self):
        data = super(WikiDataClaimers, self).data
        return data[0]['items']

    @property  # TODO: how to implement these things correctly with mixins instead of having to add it all the time
    def rsl(self):
        return self.data

    class Meta:
        app_label = "legacy"
        proxy = True


class WikiBacklinks(WikiGenerator):

    HIF_parameters = override_dict(WikiGenerator.HIF_parameters, {
        "action": "query",
        "generator": "backlinks",
        "gbllimit": 500,
        "gbltitle": "",
        "gblnamespace": 0,
    })

    HIF_query_parameter = "gbltitle"

    class Meta:
        app_label = "legacy"
        proxy = True


class WikiLinks(WikiGenerator):

    HIF_parameters = override_dict(WikiGenerator.HIF_parameters, {
        "generator": "links",
        "gpllimit": 500,
        "gplnamespace": 0
    })

    class Meta:
        app_label = "legacy"
        proxy = True


class WikiCategories(WikiGenerator):

    HIF_parameters = override_dict(WikiGenerator.HIF_parameters, {
        "generator": "categories",
        "gcllimit": 500,
        "gclshow": "!hidden"
    })

    HIF_next_parameter = 'gclcontinue'

    def cleaner(self,result_instance):
        if result_instance["title"].startswith('Category:Living people'):
            return False
        if re.match(r'Category:\d\d\d\d (births|deaths)', result_instance['title']):
            return False
        return True


    class Meta:
        app_label = "legacy"
        proxy = True


class WikiCategoryMembers(WikiGenerator):

    HIF_parameters = override_dict(WikiGenerator.HIF_parameters, {
        "gcmtitle": "",
        "generator": "categorymembers",
        "gcmlimit": 500,
        "gcmnamespace": 0
    })

    HIF_next_parameter = 'gcmcontinue'

    HIF_query_parameter = "gcmtitle"

    class Meta:
        app_label = "legacy"
        proxy = True


class WikiGeo(WikiBaseQuery):

    HIF_wiki_results_key = "geosearch"

    HIF_parameters = override_dict(WikiBaseQuery.HIF_parameters, {
        "list": "geosearch",
        "gscoord": "",
        "gsradius": 0,  # gets set through config
        "gslimit": 500,
        "gsnamespace": 0,
        "gsprop": "type|dim",
    })

    HIF_objective = {
        "lat": 0,
        "lon": 0,
        "type": None,
        "dim": None,
        "title": "",
        "dist": 0,
    }

    HIF_query_parameter = "gscoord"

    def prepare_params(self):
        self.HIF_parameters['gsradius'] = self.config.radius
        return super(WikiGeo, self).prepare_params()

    def cleaner(self,result_instance):
        if result_instance["title"].startswith('List'):
            return False
        return True

    class Meta:
        app_label = "legacy"
        proxy = True