# -*- encoding: utf-8 -*-

from django.conf import settings
from django.core.mail import EmailMessage

def registration_confirmed(user, trip, participants):
    email = EmailMessage(subject = 'Zena Ski Group: conferma iscrizione',
                         to = [user.email])

    if trip.with_reservation:
        body = (u"L'iscrizione delle seguenti persone per la gita a "
                u"{destination} del "
                u"{date} è stata effettuata CON RISERVA.\n"
                u"In caso di conferma, verrai informato via email, oppure "
                u"puoi controllare lo stato della tua iscrizione "
                u'direttamente sul sito, nella pagina "Iscriviti online":\n'
                u"{participant_names}\n")
    else:
        body = (u"L'iscrizione delle seguenti persone per la gita a "
                u"{destination} del "
                u"{date} è stata effettuata con successo:\n"
                u"{participant_names}\n")
    #
    participant_names = ['  - %s' % p.name for p in participants]
    email.body =  body.format(
        destination = trip.destination,
        date = trip.date.strftime("%d/%m/%Y"),
        participant_names = '\n'.join(participant_names),
    )
    email.bcc = [settings.ADMIN_EMAIL]
    email.send(fail_silently=True)
