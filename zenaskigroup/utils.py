class UserTracebackMiddleware(object):
    """
    Adds user to request context during request processing, so that they
    show up in the error emails.
    """
    def process_exception(self, request, exception):
        if request.user.is_authenticated():
            request.META['AUTH_USER'] = unicode(request.user.username)
        else:
            request.META['AUTH_USER'] = "Anonymous User"
