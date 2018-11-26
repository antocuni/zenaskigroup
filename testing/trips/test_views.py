# -*- encoding: utf-8 -*-

import pytest
from testing.trips.test_models import trip, testuser

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
