# -*- encoding: utf-8 -*-

from datetime import date, datetime, timedelta
from decimal import Decimal
from collections import Counter
from enum import IntEnum
from django.conf import settings
from django.contrib import admin
from django.contrib.auth.models import User
from django.db import models, transaction
from annoying.fields import AutoOneToOneField
from paypal.standard.ipn.models import PayPalIPN

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

    def add_participants(self, user, participants, paypal=False):
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

            result = None
            if paypal:
                ppt = PayPalTransaction.make(user, self, participants)
                result = ppt
            else:
                user.member.balance -= total_deposit
                names = ', '.join([p.name for p in participants])
                descr = u'Iscrizione di %s a %s' % (names, self)
                t = MoneyTransfer(member=user.member,
                                  value=-total_deposit,
                                  executed_by=user,
                                  description=descr)
                t.save()
                user.member.save()
                result = t
            self.save()
            return result


class Participant(models.Model):
    class Meta:
        verbose_name = 'Partecipante'
        verbose_name_plural = 'Partecipanti'

    trip = models.ForeignKey(Trip, null=True)
    name = models.CharField(max_length=200, verbose_name='Nome')
    deposit = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Caparra')
    is_member = models.BooleanField(default=True, blank=False,
                                    verbose_name='Socio?')
    registered_by = models.ForeignKey(User, verbose_name='Iscritto da',
                                      null=True, blank=True)
    sublist = models.CharField(max_length=20, verbose_name='Lista')
    with_reservation = models.BooleanField(default=False, blank=False,
                                           verbose_name='Con riserva?')
    paypal_transaction = models.ForeignKey('PayPalTransaction', null=True,
                                           blank=True)

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
    def paypal_pending(self):
        return (self.paypal_transaction is not None and
                self.paypal_transaction.is_pending)

    def get_status(self):
        ppt = self.paypal_transaction
        if ppt:
            st = ppt.status
            if st == ppt.Status.pending:
                return 'Da pagare', 'text-danger'
            elif st == ppt.Status.canceled:
                return 'Annullato', 'text-danger'
            elif st == ppt.Status.waiting_ipn:
                return 'In attesa di PayPal', 'text-warning'
            elif st == ppt.Status.failed:
                return 'Transazione fallita', 'text-danger'
            # elif st == paid: fallthrough
        if self.with_reservation:
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

class PayPalTransactionError(Exception):
    pass

class PayPalTransaction(models.Model):
    class Meta:
        verbose_name = 'Transazione PayPal'
        verbose_name_plural = 'Transazioni PayPal'

    class Status(IntEnum):
        pending = 0      # just created
        canceled = 1     # canceled by user or deadline
        waiting_ipn = 2  # landed after paypal but IPN not received yet
        paid = 3         # IPN received and correct
        failed = 4       # IPN received but incorrect

    user = models.ForeignKey(User)
    trip = models.ForeignKey(Trip)
    # the price of a single item in the paypal transaction
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField() # number of items
    deadline = models.DateTimeField()
    status = models.IntegerField(
        default=int(Status.pending),
        choices=[(int(tag), tag.name) for tag in Status]
    )
    ipn = models.ForeignKey(PayPalIPN, null=True)

    @classmethod
    def make(cls, user, trip, participants):
        self = cls()
        self.user = user
        self.trip = trip
        self.quantity = len(participants)
        total_amount = sum([p.deposit for p in participants])
        self.amount = total_amount / self.quantity
        self.deadline = (datetime.now() +
                         timedelta(minutes=settings.PAYPAL_DEADLINE))
        self.save()
        self.participant_set.add(*participants)
        # add self to the pending transactions
        pending_ppt = PendingPayPalTransactions(ppt=self)
        pending_ppt.save()
        return self

    def __unicode__(self):
        return '%s %s [%s]' % (self.user, self.grand_total, self.trip)

    @classmethod
    def get_pending(cls, user, trip):
        return cls.objects.filter(user=user, trip=trip,
                                  status=cls.Status.pending)

    @property
    def FEE(self):
        """
        The fee for ONE participant
        """
        return Decimal(settings.PAYPAL_FEE, 2)

    @property
    def fees(self):
        return self.quantity * self.FEE

    @property
    def total_amount(self):
        return self.amount * self.quantity

    @property
    def grand_total(self):
        return self.total_amount + self.fees

    @property
    def item_name(self):
        return 'Iscrizione gita a %s' % self.trip

    @property
    def is_pending(self):
        return self.status == self.Status.pending

    def _set_status(self, newstatus):
        """
        Set the status, save and remove self from PendingPayPalTransactions
        """
        self.status = newstatus
        if self.status != self.Status.pending:
            PendingPayPalTransactions.objects.filter(ppt=self).delete()
        self.save()

    def cancel_maybe(self):
        with transaction.atomic():
            if (self.status == self.Status.pending and
                datetime.now() >= self.deadline):
                print 'Automatic cancelation of ppt %s due to deadline: %s' % (
                    self, self.deadline)
                self.cancel()

    def cancel(self):
        with transaction.atomic():
            if self.status == self.Status.canceled:
                return
            if self.status != self.Status.pending:
                raise PayPalTransactionError(
                    u'Impossibile annullare la transazione')
            for p in self.participant_set.all():
                p.trip = None
                p.save()
            self._set_status(self.Status.canceled)

    def mark_waiting(self):
        with transaction.atomic():
            st = self.status
            if st == self.Status.canceled:
                raise PayPalTransactionError(u'Transazione già annullata')
            elif st == self.Status.pending:
                self._set_status(self.Status.waiting_ipn)
            else:
                # if the IPN already arrived, do nothing
                pass

    def mark_paid(self, ipn):
        if (ipn.receiver_email != settings.PAYPAL_BUSINESS_EMAIL or
            ipn.receiver_id != settings.PAYPAL_BUSINESS_ID or
            ipn.mc_currency != 'EUR' or
            ipn.payment_status != 'Completed' or
            ipn.custom != str(self.id) or
            ipn.mc_gross != self.grand_total):
            self._set_status(self.Status.failed)
            raise PayPalTransactionError(
                "Invalid IPN: %s; ppt: %s" % (ipn.id, self))
        elif self.status == self.Status.canceled:
            self._set_status(self.Status.failed)
            raise PayPalTransactionError(
                "Transaction already canceled: %s" % self)
        else:
            self._set_status(self.Status.paid)


class PendingPayPalTransactions(models.Model):
    """
    This is basically a self-managed index to contain all the pending
    transactions, so that they can be efficiently checked by
    DeadlineMiddleware
    """
    ppt = models.ForeignKey(PayPalTransaction, related_name='+')
