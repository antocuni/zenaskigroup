# -*- encoding: utf-8 -*-

import pytest
from freezegun import freeze_time
from datetime import timedelta
from django.conf import settings
from django.core import mail
from trips.models import Participant
from trips.paypal_view import ipn_received
from testing.trips.test_views import BaseTestView
from testing.trips.test_models import trip, testuser, make_ipn


class TestPayPalView(BaseTestView):

    @staticmethod
    def P(name, deposit, trip):
        return Participant(name=name, deposit=Decimal(deposit), trip=trip)

    @freeze_time('2018-12-24 12:00')
    def test_get(self, db, trip, testuser):
        self.login()
        p1 = Participant(name='Mickey Mouse')
        p2 = Participant(name='Donald Duck')
        ppt = trip.add_participants(testuser, [p1, p2], paypal=True)
        assert ppt.id == 1
        resp = self.get('/pay/1/')
        assert resp.status_code == 200

        tags = [
            '<span id="countdown" data-deadline="2018-12-24T12:20:00">',
            '<input type="hidden" name="notify_url" value="http://testserver/paypal/">',
            '<input type="hidden" name="business" value="%s">' % settings.PAYPAL_BUSINESS_ID,
            '<input type="hidden" name="custom" value="1">']
        for tag in tags:
            assert tag in resp.content

    def test_post(self, db, trip, testuser):
        assert trip.id == 1
        p1 = Participant(name='Mickey Mouse')
        p2 = Participant(name='Donald Duck')
        p3 = Participant(name='Uncle Scrooge')
        # we want a ppt with id != 1, so that we can check that the trip/1/
        # below is the id of the trip and not of the ppt :)
        trip.add_participants(testuser, [p1], paypal=True)
        ppt = trip.add_participants(testuser, [p2, p3], paypal=True)
        assert ppt.id == 2
        assert ppt.status == ppt.Status.pending

        self.login()
        resp = self.post('/pay/2/', {'btn-cancel': ''})
        assert resp.status_code == 302 # redirect
        assert resp.url == 'http://testserver/trip/1/register/'
        ppt.refresh_from_db()
        assert ppt.status == ppt.Status.canceled

    def test_deadline(self, db, trip, testuser):
        with freeze_time('2018-12-24 12:00') as freezer:
            self.login()
            p1 = Participant(name='Mickey Mouse')
            p2 = Participant(name='Donald Duck')
            ppt = trip.add_participants(testuser, [p1, p2], paypal=True)
            assert ppt.id == 1
            resp = self.get('/pay/1/')
            assert resp.status_code == 200
            assert resp.context['status'] == 'pending'

            # move slightly before the timeout
            freezer.tick(timedelta(minutes=settings.PAYPAL_DEADLINE - 1))
            resp = self.get('/pay/1/')
            assert resp.status_code == 200
            assert resp.context['status'] == 'pending'

            # move at the timeout
            freezer.tick(timedelta(minutes=1))
            resp = self.get('/pay/1/')
            assert resp.status_code == 200
            assert resp.context['status'] == 'canceled'


class TestSignals(object):

    def test_ipn_received(self, db, trip, testuser):
        p1 = Participant(name='Mickey Mouse')
        p2 = Participant(name='Donald Duck')
        ppt = trip.add_participants(testuser, [p1, p2], paypal=True)
        assert ppt.status == ppt.Status.pending
        ipn = make_ipn(custom=ppt.id, grand_total=ppt.grand_total)
        ipn_received(ipn)
        ppt.refresh_from_db()
        assert ppt.status == ppt.Status.paid

        assert len(mail.outbox) == 1
        msg = mail.outbox[0]
        assert msg.subject == 'Zena Ski Group: conferma iscrizione'
        assert msg.to == ['test@user.com']
        assert msg.body == (u"L'iscrizione delle seguenti persone per la gita a "
                            u"Cervinia del 25/12/2018 è stata effettuata "
                            u"con successo:\n"
                            u"  - Mickey Mouse\n"
                            u"  - Donald Duck\n")

    def test_ipn_received_invalid(self, db, trip, testuser):
        from trips.paypal_view import ipn_received
        # this is not strictly a view test because it's a signal
        p1 = Participant(name='Mickey Mouse')
        p2 = Participant(name='Donald Duck')
        ppt = trip.add_participants(testuser, [p1, p2], paypal=True)
        assert ppt.status == ppt.Status.pending
        ipn = make_ipn(custom=ppt.id, grand_total=0)
        ipn.save()
        assert ipn.id == 1
        ipn_received(ipn)
        ppt.refresh_from_db()
        assert ppt.status == ppt.Status.failed

        assert len(mail.outbox) == 1
        msg = mail.outbox[0]
        assert msg.subject == 'Zena Ski Group: problemi con il pagamento'
        assert msg.to == ['test@user.com']
        assert msg.body == (
            u"C'è stato un problema con la seguente transazione PayPal:\n"
            u"Gita: Cervinia, 25/12/2018\n"
            u"Partecipanti:\n"
            u"  - Mickey Mouse\n"
            u"  - Donald Duck\n"
            u"\n"
            u"Riferimento IPN interno: 1\n"
            u"Si prega di contattare lo staff per risolvere il problema")
