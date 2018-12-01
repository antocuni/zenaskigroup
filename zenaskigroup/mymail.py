"""
An email backend which automatically add the admin to BCC
"""

from django.conf import settings
from django.core.mail.backends.console import EmailBackend as ConsoleBackend
from nullmailer.backend import EmailBackend as NullMailerBackend

# this is a copy&paste of this PR; once it is merged and released, we can kill
# it and use the upstream nullmailer:
# https://github.com/20tab/django-nullmailer/pull/3
import os
import threading
import rfc822
from nullmailer.backend import to_utf8

def get_email_address(s):
    """
    Extract "foo@bar.com" from "Mr. Foo <foo@bar.com>"
    """
    name, email = rfc822.parseaddr(s)
    return to_utf8(email)

class MyNullMailerBackend(NullMailerBackend):

    def send_messages(self, email_messages):
        pid = os.getpid()
        tid = threading.current_thread().ident
        num_sent = 0
        if not email_messages:
            return
        for email_message in email_messages:
            to = email_message.to
            cc = email_message.cc or []
            bcc = email_message.bcc or []
            recipients = to + cc + bcc
            #
            from_email = get_email_address(email_message.from_email)
            to_lines = '\n'.join([get_email_address(addr) for addr in recipients])
            msg = "%s\n%s\n\n%s" % ( from_email, to_lines, email_message.message().as_string())
            if self._send(msg, pid, tid):
                num_sent += 1
        return num_sent


class EmailBackend(object):

    def __init__(self, *args, **kwds):
        self.debug = getattr(settings, 'DEBUG', False)
        if self.debug:
            self.backend = ConsoleBackend(*args, **kwds)
        else:
            self.backend = MyNullMailerBackend(*args, **kwds)

    def send_messages(self, email_messages):
        for msg in email_messages:
            msg.bcc.append(settings.ADMIN_EMAIL)
        self.backend.send_messages(email_messages)
