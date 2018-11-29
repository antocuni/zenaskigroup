# -*- encoding: utf-8 -*-

import pytest
from freezegun import freeze_time
from django.conf import settings
from trips.models import Participant
from testing.trips.test_models import trip, testuser, make_ipn

class BaseTestView(object):

    @pytest.fixture(autouse=True)
    def init(self, db, client, testuser, trip):
        self.trip = trip
        self.testuser = testuser
        self.db = db
        self.client = client

    def login(self):
        assert self.client.login(username='testuser', password='12345')

    def get(self, *args, **kwargs):
        return self.client.get(*args, **kwargs)

    def post(self, *args, **kwargs):
        return self.client.post(*args, **kwargs)

class TestNextTrip(BaseTestView):

    def test_redirect(self):
        assert self.trip.id == 1
        resp = self.get('/trip/')
        assert resp.status_code == 302 # redirect
        assert resp.url == 'http://testserver/trip/1/'


class TestPayPal(BaseTestView):

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

    def test_ipn_received(self, db, trip, testuser):
        from trips.paypal_view import ipn_received
        # this is not strictly a view test because it's a signal
        p1 = Participant(name='Mickey Mouse')
        p2 = Participant(name='Donald Duck')
        ppt = trip.add_participants(testuser, [p1, p2], paypal=True)
        assert ppt.status == ppt.Status.pending
        ipn = make_ipn(custom=ppt.id, grand_total=ppt.grand_total)
        ipn_received(ipn)
        ppt.refresh_from_db()
        assert ppt.status == ppt.Status.paid
