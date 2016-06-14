import re

EXCLUDE_NAME_PARTS = re.compile(r"(?i)\bltd\b|\blimited\b|\binc\b|\bllc\b|\bthe\b|\.")


def clean_postcode(postcode):
    """
    Returns `postcode` lowercase without spaces so that it can be used for comparisons.
    """
    if not postcode:
        return postcode
    return postcode.lower().replace(' ', '').strip()


def clean_name(name):
    """
    Returns `name` lowercase without common parts and extra spaces so that it can be used for comparisons.
    """
    if not name:
        return name

    cleaned_name = name.lower()  # lowercase
    cleaned_name = EXCLUDE_NAME_PARTS.sub('', cleaned_name)  # remove words
    return ' '.join(cleaned_name.split())  # remove unnecessary spaces


class SimilarityCalculator(object):
    """
    Used to calculate the similarity proximity between 2 records.
    It works by analysing different steps where 'name' and 'postcode' are mandatory.
    Each step has a weight (between 0 and 1) expressing its importance (eg. name is more important than postcode)

    e.g.

        calc = SimilarityCalculator()
        calc.analyse_names(name1, name2)
        calc.analyse_postcodes(postcode1, postcode2)

        proximity = calc.get_proximity()

    If you want to add an extra step:

        calc = SimilarityCalculator()
        calc.analyse_names(name1, name2)
        calc.analyse_postcodes(postcode1, postcode2)
        calc.analyse(what, weight, part1, part2, func)

        proximity = calc.get_proximity()
    """
    NAME_WEIGHT = 1
    NAME_STEP_NAME = 'name'

    POSTCODE_WEIGHT = 0.9
    POSTCODE_STEP_NAME = 'postcode'

    def __init__(self):
        self.data = {}

    def analyse(self, what, weight, part1, part2, func):
        """
        Analyses the step 'what'.
        For names and postcodes, it's easier to use `analyse_names` and `analyse_postcodes`.

        what: string expressing the step you are analysing
        weight: the weight (importance) of the step (between 0 and 1)
        part1 and part2: the two objects to compare
        func: a function taking part1 and part2 and returning a proximity value between 0 and 1
        """
        assert what not in self.data, '{} has already been analysed'.format(what)

        proximity = func(part1, part2)
        self.data[what] = {
            'weight': weight,
            'proximity': proximity
        }

    def analyse_names(self, name1, name2):
        return self.analyse(
            self.NAME_STEP_NAME, self.NAME_WEIGHT,
            name1, name2, self._get_names_proximity
        )

    def analyse_postcodes(self, postcode1, postcode2):
        return self.analyse(
            self.POSTCODE_STEP_NAME, self.POSTCODE_WEIGHT,
            postcode1, postcode2, self._get_postcode_proximity
        )

    def get_proximity(self):
        assert (
            self.NAME_STEP_NAME in self.data and self.POSTCODE_STEP_NAME in self.data
        ), (
            'You need to analyse at least some names and postcodes '
            'by calling `.analyse_names(name1, name2)` and `.analyse_postcodes(postcode1, postcode1)`'
        )

        tot_weights = sum([step_data['weight'] for step_data in self.data.values()])
        proximity = 0
        for what, step_data in self.data.items():
            booster = (1 * step_data['weight']) / tot_weights
            proximity += step_data['proximity'] * booster

        return round(proximity, 2)

    def _get_names_proximity(self, name1, name2):
        """
        Quite basic comparison function returning 1 if the names are exactly the same and 0.5 if they are somewhat
        similar. Could be improved but not needed atm so we're trying to keep things simple.
        """
        cleaned_name1 = clean_name(name1)
        cleaned_name2 = clean_name(name2)

        if cleaned_name1 == cleaned_name2:
            return 1

        # if at least one of the parts between the 2 strings are the same...
        if set(cleaned_name1.split()).intersection(set(cleaned_name2.split())):
            return 0.5

        return 0

    def _get_postcode_proximity(self, postcode1, postcode2):
        """
        Quite basic comparison function returning 1 if the postcodes are exactly the same and 0.5 if they are somewhat
        similar. Could be improved but not needed atm so we're trying to keep things simple.
        """
        cleaned_postcode1 = clean_postcode(postcode1) or ''
        cleaned_postcode2 = clean_postcode(postcode2) or ''

        if cleaned_postcode1 and cleaned_postcode1 == cleaned_postcode2:
            return 1

        if cleaned_postcode1 and cleaned_postcode1[:3] == cleaned_postcode2[:3]:
            return 0.5

        return 0
