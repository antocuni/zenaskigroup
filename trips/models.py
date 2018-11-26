# -*- encoding: utf-8 -*-

from datetime import date, datetime, timedelta
from collections import Counter
from django.contrib import admin
from django.contrib.auth.models import User
from django.db import models, transaction
from annoying.fields import AutoOneToOneField

class Member(models.Model):
    user = AutoOneToOneField(User)
    balance = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Credito',
                                  default=0)
    card_no = models.CharField(max_length=5, verbose_name='Numero tessera', blank=True)
    trusted = models.BooleanField(default=False, blank=False,
                                  verbose_name='Fidato?')

    def __unicode__(self):
        return self.user.first_name or self.user.username

    def balance_class(self):
        if self.balance <= 0:
            return "text-danger"
        else:
            return ""


class TripError(Exception):
    pass


class Trip(models.Model):
    class Meta:
        verbose_name = 'Gita'
        verbose_name_plural = 'Gite'
        get_latest_by = 'date'
    
    date = models.DateField(verbose_name='Data')
    closing_date = models.DateTimeField(verbose_name='Chiusura iscrizioni')
    destination = models.CharField(max_length=200, verbose_name='Destinazione')
    seats = models.PositiveIntegerField(verbose_name='Numero di posti')
    deposit = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Caparra',
                                  default=20)
    poster = models.ImageField(verbose_name='Locandina')
    allow_extra_seats = models.BooleanField(default=False, blank=False,
                                            verbose_name='Consenti iscrizioni con riserva?')
    fb_post = models.URLField(verbose_name='Facebook post', blank=True)
    fb_album = models.URLField(verbose_name='Facebook album', blank=True)

    @property
    def seats_left(self):
        seats_busy = self.participant_set.count()
        return self.seats - seats_busy

    @property
    def seats_left_or_0(self):
        return max(self.seats_left, 0)

    @property
    def sublist_summary(self):
        count = Counter()
        for p in self.participant_set.all():
            if p.with_reservation:
                count['Riserve'] += 1
            else:
                count[p.sublist] += 1
        return sorted(count.items())

    @property
    def with_reservation(self):
        return self.seats_left <= 0 and self.allow_extra_seats

    def __unicode__(self):
        date = self.date.strftime('%d/%m/%Y')
        return u'%s, %s' % (self.destination, date)

    def poster_preview(self):
        return u'<img src="%s" width="400px" />' % self.poster.url
    poster_preview.short_description = 'Locandina'
    poster_preview.allow_tags = True

    def sublist_table(self):
        d = self.sublist_summary
        lines = []
        for key, value in d:
            lines.append('<b>%s</b>: %s<br>' % (key, value))
        return '\n'.join(lines)
    sublist_table.short_description = 'Sottoliste'
    sublist_table.allow_tags = True

    def get_participants(self, user):
        return self.participant_set.filter(registered_by=user)

    def get_paypal_participants(self, user):
        return self.get_participants(user).filter(paypal_deadline__isnull=False)

    def compute_paypal_total(self, user):
        tot = 0
        fees = 0
        for p in self.get_paypal_participants(user):
            tot += p.deposit
            fees += p.paypal_fee
        return tot, fees

    def add_participants(self, user, participants, paypal=False):
        paypal_deadline = datetime.now() + timedelta(minutes=10)
        total_deposit = 0
        for p in participants:
            # if we user is not trusted, we always use the trip deposit
            if not user.member.trusted or p.deposit is None:
                p.deposit = self.deposit
            total_deposit += p.deposit
            p.registered_by = user
            p.with_reservation = self.with_reservation
            if paypal:
                p.sublist = 'PayPal'
                p.paypal_deadline = paypal_deadline
            else:
                p.sublist = 'Online'

        with transaction.atomic():
            if (not paypal and
                user.member.balance < total_deposit and
                not user.member.trusted):
                raise TripError("Credito insufficiente")

            if self.seats_left < len(participants) and not self.with_reservation:
                if self.seats_left == 0:
                    raise TripError("Posti esauriti")
                else:
                    raise TripError(
                        'Non ci sono abbastanza posti per iscrivere '
                        'tutte le persone richieste. Numero massimo di '
                        'posti disponibili: %d' % self.seats_left)

            self.participant_set.add(*participants)

            if not paypal:
                user.member.balance -= total_deposit
                names = ', '.join([p.name for p in participants])
                descr = u'Iscrizione di %s a %s' % (names, self)
                t = MoneyTransfer(member=user.member,
                                  value=-total_deposit,
                                  executed_by=user,
                                  description=descr)
                t.save()
                user.member.save()
            self.save()



class Participant(models.Model):
    class Meta:
        verbose_name = 'Partecipante'
        verbose_name_plural = 'Partecipanti'

    trip = models.ForeignKey(Trip)
    name = models.CharField(max_length=200, verbose_name='Nome')
    deposit = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Caparra')
    is_member = models.BooleanField(default=True, blank=False,
                                    verbose_name='Socio?')
    registered_by = models.ForeignKey(User, verbose_name='Iscritto da',
                                      null=True, blank=True)
    sublist = models.CharField(max_length=20, verbose_name='Lista')
    with_reservation = models.BooleanField(default=False, blank=False,
                                           verbose_name='Con riserva?')
    paypal_deadline = models.DateTimeField(verbose_name='Scadenza Paypal',
                                           null=True, blank=True)

    def __unicode__(self):
        return self.name

    @property
    def status(self):
        t, cls = self.get_status()
        return t

    @property
    def status_class(self):
        t, cls = self.get_status()
        return cls

    @property
    def waiting_paypal(self):
        return self.paypal_deadline is not None

    @property
    def paypal_fee(self):
        return 1

    def get_status(self):
        # bah, HTML logic should not be here, but I couldn't find any other
        # simple way to do it :(
        if self.waiting_paypal:
            return 'In attesa di PayPal', 'text-danger'
        elif self.with_reservation:
            return 'Con riserva', 'text-warning'
        else:
            return 'Confermato', 'text-success'
        


class MoneyTransfer(models.Model):
    class Meta:
        verbose_name = 'Pagamento/ricarica'
        verbose_name_plural = 'Pagamenti/ricariche'

    member = models.ForeignKey(Member, verbose_name='Socio')
    date = models.DateField(verbose_name='Data', default=date.today)
    value = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Valore')
    executed_by = models.ForeignKey(User, verbose_name='Eseguito da')
    description = models.CharField(max_length=200, verbose_name='Causale',
                                   default='Ricarica')

    def __unicode__(self):
        return u'%s: %+d €, %s' % (self.member.user.get_full_name(), self.value, self.description)


class JacketSubscribe(models.Model):
    class Meta:
        verbose_name = 'Contatto'
        verbose_name_plural = 'Mailing List Giacca'

    name = models.CharField(max_length=200, verbose_name='Nome', blank=False)
    email = models.CharField(max_length=200, verbose_name='Email', blank=False)

    def __unicode__(self):
        return u'%s <%s>' % (self.name, self.email)
