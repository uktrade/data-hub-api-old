from ..matcher import BaseMatcher, FindingResult
from . import api


class ChAPIMatcher(BaseMatcher):
    """
    CompaniesHouse API Matcher which uses the CH Api to find the best match.

    e.g.
        matcher = ChAPIMatcher(name, postcode)
        best_match = matcher.find()  # returns the best match, an instance of FindingResult
        matcher.findings  # if you want the full list considered internally for debug purposes
    """

    def _build_findings(self):
        results = api.search.companies.get(q=self.name)['items']

        self.findings = []
        for result in results:
            ch_name = result['title']
            ch_postcode = self._get_ch_postcode(result)
            company_number = result['company_number']
            proximity = self._get_similarity_proximity(ch_name, ch_postcode)

            self.findings.append(
                FindingResult(
                    name=ch_name, postcode=ch_postcode,
                    proximity=proximity, company_number=company_number,
                    raw=result
                )
            )
