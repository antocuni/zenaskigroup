import pytest
from freezegun import freeze_time
from datetime import date, datetime
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from trips import models

@pytest.fixture
def trip(db):
    t = models.Trip.objects.create(
        date=date(2018, 12, 25),
        closing_date=datetime(2018, 12, 24, 12, 0, 0),
        destination='Cervinia',
        seats=50,
        deposit=25,
        poster=SimpleUploadedFile(name='test.jpg',
                                  content='',
                                  content_type='image/jpeg'))
    return t

@pytest.fixture(autouse=True)
def testuser(db):
    u = User.objects.create(username='testuser')
    u.set_password('12345')
    u.save()
    return u

def test_next_trip(db, client, trip):
    assert trip.id == 1
    resp = client.get('/trip/')
    assert resp.status_code == 302 # redirect
    assert resp.url == 'http://testserver/trip/1/'


class TestRegister(object):

    def test_login_required(self, db, trip, client):
        resp = client.get('/trip/1/register/')
        assert resp.status_code == 302
        assert resp.url == 'http://testserver/accounts/login/?next=/trip/1/register/'

    def test_registration_allowed(self, db, trip, client):        
        with freeze_time('2018-12-24 11:59'):
            client.login(username='testuser', password='12345')
            resp = client.get('/trip/1/register/')
        assert resp.status_code == 200
        assert resp.context['registration_allowed']

        with freeze_time('2018-12-24 12:01'):
            client.login(username='testuser', password='12345')
            resp = client.get('/trip/1/register/')
        assert resp.status_code == 200
        assert not resp.context['registration_allowed']
