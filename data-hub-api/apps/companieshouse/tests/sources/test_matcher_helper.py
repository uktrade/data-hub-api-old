from django.test.testcases import TestCase
from django.conf import settings

from companieshouse.sources.matcher import MatcherHelper, BaseMatcher, FindingResult


class BestTestMatcher(BaseMatcher):
    proximity = 0

    def _build_findings(self):
        self.findings = [
            FindingResult(
                company_number=str(self.proximity),
                name='company {}'.format(self.proximity),
                postcode='SW1A1AA',
                proximity=self.proximity,
                raw={'company_number': '0'}
            )
        ]


class JustPassMatcher(BestTestMatcher):
    proximity = settings.MATCHER_ACCEPTANCE_PROXIMITY


class JustFailMatcher(BestTestMatcher):
    proximity = (settings.MATCHER_ACCEPTANCE_PROXIMITY) - 0.01


class AlwaysFailMatcher(BestTestMatcher):
    proximity = 0


class AlwaysPassMatcher(BestTestMatcher):
    proximity = 1.


class MatcherHelperTestCase(TestCase):
    def test_finding_just_passes_acceptance_level(self):
        with self.settings(MATCHER_CLASSES=[
            'companieshouse.tests.sources.test_matcher_helper.JustPassMatcher',
            'companieshouse.tests.sources.test_matcher_helper.AlwaysPassMatcher',
        ]):
            helper = MatcherHelper()
            best_match = helper.find_match('company name', 'SW1A 1AA')
            self.assertEqual(best_match.proximity, settings.MATCHER_ACCEPTANCE_PROXIMITY)

    def test_no_findings_pass_acceptance_level(self):
        with self.settings(MATCHER_CLASSES=[
            'companieshouse.tests.sources.test_matcher_helper.AlwaysFailMatcher',
            'companieshouse.tests.sources.test_matcher_helper.JustFailMatcher',
        ]):
            helper = MatcherHelper()
            best_match = helper.find_match('company name', 'SW1A 1AA')
            self.assertEqual(best_match, None)

    def test_override_acceptance_level(self):
        overriding_acceptance_level = JustFailMatcher.proximity
        with self.settings(
            MATCHER_CLASSES=[
                'companieshouse.tests.sources.test_matcher_helper.AlwaysFailMatcher',
                'companieshouse.tests.sources.test_matcher_helper.JustFailMatcher',
            ],
            MATCHER_ACCEPTANCE_PROXIMITY=overriding_acceptance_level
        ):
            helper = MatcherHelper()
            best_match = helper.find_match('company name', 'SW1A 1AA')
            self.assertEqual(best_match.proximity, overriding_acceptance_level)
