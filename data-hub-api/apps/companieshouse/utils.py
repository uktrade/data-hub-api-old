from django_countries import Countries


class CountryCleaner(object):
    """
    Used to clean countries so that they match the official ISO 3166-1 list.
    The main difference is that it ignores case sensitivity.
    """
    def __init__(self):
        self.countries = Countries()

    def clean(self, country):
        if not country:
            return None
        country = country.lower()

        for code, name in self.countries:
            if name.lower() == country:
                return code
        return None
clean_country = CountryCleaner().clean
