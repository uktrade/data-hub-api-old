from slumber.exceptions import HttpNotFoundError

from ..api import api as companieshouse_api

from ..matcher import BaseMatcher, FindingResult
from . import api


class DueDilMatcher(BaseMatcher):
    """
    DueDil API Matcher which uses the DueDil API to find the best match.

    As the free Duedil account only returns company name and number, the algorithm
    uses the Companies House dataset to get the full record.

    e.g.
        matcher = DueDilMatcher(name, postcode)
        best_match = matcher.find()  # returns the best match, an instance of FindingResult
        matcher.findings  # if you want the full list considered internally for debug purposes
    """

    def _get_ch_record(self, company_number):
        """
        Returns the CH record of company with number == `company_number` if it exists, None otherwise.
        """
        try:
            return companieshouse_api.company(company_number).get()
        except HttpNotFoundError:
            pass
        return None

    def _to_ch_raw(self, dd_record):
        """
        Translates DueDil json record into a CompaniesHouse-like json record so that we have a unified format.
        """
        return {
            'company_name': dd_record['name'],
            'company_number': dd_record['company_number']
        }

    def _build_findings(self):
        self.findings = []

        try:
            dd_results = api.search.get(q=self.name)['response']['data']
        except HttpNotFoundError as e:
            if e.response.status_code == 404:  # if not found => return empty
                return
            raise e  # otherwise it's a different problem...

        for dd_result in dd_results:
            dd_name = dd_result['name']
            company_number = dd_result['company_number']

            ch_result = self._get_ch_record(company_number)
            ch_postcode = self._get_ch_postcode(ch_result or {})

            proximity = self._get_similarity_proximity(dd_name, ch_postcode)
            raw = ch_result or self._to_ch_raw(dd_result)

            self.findings.append(
                FindingResult(
                    name=dd_name, postcode=ch_postcode,
                    proximity=proximity, company_number=company_number,
                    raw=raw
                )
            )
