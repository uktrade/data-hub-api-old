import os
import pickle
from cryptography.fernet import Fernet, InvalidToken

from django.conf import settings
from django.utils.text import slugify
from django.core.exceptions import ImproperlyConfigured


COOKIE_FILE = '/tmp/cdms_cookie_{slug}.tmp'.format(
    slug=slugify(settings.CDMS_BASE_URL)
)


class CookieStorage(object):
    """
    Stores a cookie encrypting before writing it and decrypting it after reading it.
    """
    def __init__(self):
        try:
            self.crypto = Fernet(settings.CDMS_COOKIE_KEY)
        except Exception:
            raise ImproperlyConfigured("""
settings.CDMS_COOKIE_KEY has to be a valid Fernet key.
Generate it with:

>>> ./manage.py shell
>>> from cryptography.fernet import Fernet
>>> Fernet.generate_key()
""")

    def read(self):
        """
        Returns the cookie if valid and exists, None otherwise.
        """
        if self.exists():
            with open(COOKIE_FILE, 'rb') as f:
                try:
                    ciphertext = self.crypto.decrypt(f.read())
                    return pickle.loads(ciphertext)
                except (InvalidToken, TypeError):
                    self.reset()
        return None

    def write(self, cookie):
        """
        Writes a cookie overriding any existing ones.
        """
        ciphertext = self.crypto.encrypt(pickle.dumps(cookie))
        with open(COOKIE_FILE, 'wb') as f:
            f.write(ciphertext)

    def exists(self):
        """
        Returns True if the cookie exists, False otherwise.
        """
        return os.path.exists(COOKIE_FILE)

    def reset(self):
        """
        Deletes the cookie.
        """
        if self.exists():
            os.remove(COOKIE_FILE)
