from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordResetForm

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


# copied from here, see also urls.py:
# https://stackoverflow.com/questions/27734185/inform-user-that-email-is-invalid-using-djangos-password-reset
class EmailValidationOnForgotPassword(PasswordResetForm):
    def clean_email(self):
        email = self.cleaned_data['email']
        if not User.objects.filter(email__iexact=email, is_active=True).exists():
            raise forms.ValidationError("Non esiste nessun utente con questo indirizzo email")
        return email
