from requests.exceptions import RequestException

# all request exceptions extend requests RequestException


class LoginErrorException(RequestException):
    """
    Used when there's a known login error like invalid credentials etc.
    The message will say what the validation error is.
    """
    pass


class UnexpectedResponseException(RequestException):
    """
    Used when there's an unexpected response.
    The message will have the status_code and the content will be the response body.
    """
    def __init__(self, message, content=None):
        super(UnexpectedResponseException, self).__init__(message)
        self.message = message
        self.content = content


# all api related exceptions extend CDMSException

class CDMSException(Exception):
    def __init__(self, message, status_code=None):
        super(CDMSException, self).__init__(message)
        self.message = message
        self.status_code = status_code


class CDMSNotFoundException(CDMSException):
    pass


class CDMSUnauthorizedException(CDMSException):
    pass
