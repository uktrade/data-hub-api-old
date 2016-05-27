from collections import namedtuple

from django.db import connection

from ..similarity import clean_name
from ..matcher import BaseMatcher, FindingResult


def namedtuplefetchall(cursor):
    "Return all rows from a cursor as a namedtuple"
    desc = cursor.description
    nt_result = namedtuple('Result', [col[0] for col in desc])
    return [nt_result(*row) for row in cursor.fetchall()]


class ChDBMatcher(BaseMatcher):
    """
    DB Matcher which uses the Database to find the best match.

    It uses the ILIKE postgres operation on 'name' and if that doesn't find anything, it tries with the
    similarity operator %.

    In oder for it to work, you must have the 'pg_trgm' extension and a 'gin_trgm_ops' index (included
    in the Django migrations).

    e.g.
        matcher = ChDBMatcher(name, postcode)
        best_match = matcher.find()  # returns the best match, an instance of FindingResult
        matcher.findings  # if you want the full list considered internally for debug purposes
    """

    def _get_similar_companies(self, name):
        cursor = connection.cursor()
        cursor.execute(
            "SELECT number, name, postcode, raw "
            "FROM companieshouse_company "
            "WHERE name ILIKE %s", ['%{}%'.format(name)]
        )
        return namedtuplefetchall(cursor)

    def _slowget_similar_companies(self, name):
        cursor = connection.cursor()
        cursor.execute(
            "SELECT number, name, postcode, raw "
            "FROM companieshouse_company "
            "WHERE name %% %s", [name]
        )
        return namedtuplefetchall(cursor)

    def _build_findings(self):
        cleaned_name = clean_name(self.name)
        results = self._get_similar_companies(cleaned_name)
        if not results:
            results = self._slowget_similar_companies(cleaned_name)

        self.findings = []
        for result in results:
            proximity = self._get_similarity_proximity(result.name, result.postcode)

            self.findings.append(
                FindingResult(
                    name=result.name, postcode=result.postcode,
                    proximity=proximity, company_number=result.number,
                    raw=result.raw
                )
            )
