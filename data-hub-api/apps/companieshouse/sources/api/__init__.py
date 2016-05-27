import slumber

from django.conf import settings

COMPANIES_HOUSE_BASE_URL = "https://api.companieshouse.gov.uk/"

api = slumber.API(
    COMPANIES_HOUSE_BASE_URL,
    auth=(
        settings.COMPANIES_HOUSE_TOKEN, ""
    ),
    append_slash=False
)
