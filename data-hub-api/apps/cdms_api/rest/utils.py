import re
import time
import datetime


DATETIME_RE = re.compile('/Date\(([-+]?\d+)\)/')


def cdms_datetime_to_datetime(value):
    """
    Parses a cdms datetime as string and returns the equivalent datetime value.
    Dates in CDMS are always UTC.
    """
    match = DATETIME_RE.match(value or '')
    if match:
        parsed_val = int(match.group(1))
        parsed_val = datetime.datetime.fromtimestamp(parsed_val / 1000)
        return parsed_val.replace(tzinfo=datetime.timezone.utc)


def datetime_to_cdms_datetime(value):
    """
    Returns the cdms string equivalent of the datetime value.
    """
    if not value:
        return value
    return '/Date({0})/'.format(
        int(time.mktime(value.timetuple()) * 1000)
    )
