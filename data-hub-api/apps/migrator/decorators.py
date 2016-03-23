def only_with_cdms_skip(func):
    def wrapper(self, *args, **kwargs):
        if not self.cdms_skip:
            raise NotImplementedError(
                '{method} not implemented yet'.format(method=func.__name__)
            )

        return func(self, *args, **kwargs)
    return wrapper
