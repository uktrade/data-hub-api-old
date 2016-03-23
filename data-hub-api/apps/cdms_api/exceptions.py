class CDMSException(Exception):
    def __init__(self, message, status_code=None):
        super(CDMSException, self).__init__(message)
        self.message = message
        self.status_code = status_code


class CDMSNotFoundException(CDMSException):
    pass


class CDMSUnauthorizedException(CDMSException):
    pass
