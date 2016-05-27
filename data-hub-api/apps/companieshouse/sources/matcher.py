from django.utils.module_loading import import_string
from django.utils.functional import cached_property
from django.conf import settings

from collections import namedtuple

from .similarity import SimilarityCalculator


FindingResult = namedtuple(
    'FindingResult',
    ['company_number', 'name', 'postcode', 'proximity', 'raw']
)


class BaseMatcher(object):
    """
    Base Matcher class to be subclassed to add actual logic.

    e.g.
        matcher = MyMatcher(name, postcode)
        best_match = matcher.find()  # returns the best match, an instance of FindingResult
        matcher.findings  # if you want the full list considered internally for debug purposes
    """
    def __init__(self, name, postcode):
        super(BaseMatcher, self).__init__()
        self.name = name
        self.postcode = postcode
        self.findings = None

    def _get_similarity_proximity(self, other_name, other_postcode):
        similarity_calc = SimilarityCalculator()
        similarity_calc.analyse_names(self.name, other_name)
        similarity_calc.analyse_postcodes(self.postcode, other_postcode)
        return similarity_calc.get_proximity()

    def _choose_best_finding(self):
        assert self.findings != None  # noqa

        if not self.findings:
            return None

        return max(self.findings, key=lambda x: x.proximity)

    def _get_ch_postcode(self, ch_data):
        for prop in ['registered_office_address', 'address']:
            if prop in ch_data:
                return ch_data.get(prop, {}).get('postal_code')
        return None

    def _build_findings(self):
        """
        To be overridden when subclassing.
        """
        pass

    def find(self):
        """
        Builds the findings and returns the best match which is an instance of FindingResult.
        """
        self._build_findings()
        return self._choose_best_finding()


class MatcherHelper(object):
    """
    Helper that can be used to get the Companies House matches.
    """
    @cached_property
    def matcher_classes(self):
        _matcher_classes = []
        for matcher_path in settings.MATCHER_CLASSES:
            _matcher_classes.append(import_string(matcher_path))
        return _matcher_classes

    def find_match(self, company_name, company_postcode):
        """
        Returns the first match (not the best one as that can be time/computational expensive) if found or None
        otherwise. The match is of type `FindingResult`.

        It goes through the list of MATCHER_CLASSES in order and uses the matcher classes one by one
        until one acceptable match is found.

        The acceptance level can be set using the settings `MATCHER_ACCEPTANCE_PROXIMITY`.
        """
        for matcher_class in self.matcher_classes:
            matcher = matcher_class(company_name, company_postcode)
            best_match = matcher.find()
            if best_match and best_match.proximity >= settings.MATCHER_ACCEPTANCE_PROXIMITY:
                return best_match
        return None
matcher_helper = MatcherHelper()
