import pytest
from freezegun import freeze_time
from datetime import date, datetime
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from trips import models
from trips.views import RegisterForm

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

@pytest.fixture
def testuser(db):
    u = User.objects.create(username='testuser')
    u.set_password('12345')
    u.save()
    return u

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


class TestRegister(BaseTestView):

    def get_participants(self, trip):
        res = []
        for p in trip.participant_set.all():
            res.append((p.name, p.is_member, p.deposit))
        return res

    def test_login_required(self, trip):
        resp = self.get('/trip/1/register/')
        assert resp.status_code == 302
        assert resp.url == 'http://testserver/accounts/login/?next=/trip/1/register/'

    def test_registration_allowed(self):        
        with freeze_time('2018-12-24 11:59'):
            self.login()
            resp = self.get('/trip/1/register/')
        assert resp.status_code == 200
        assert resp.context['registration_allowed']

        with freeze_time('2018-12-24 12:01'):
            self.login()
            resp = self.get('/trip/1/register/')
        assert resp.status_code == 200
        assert not resp.context['registration_allowed']

    @freeze_time('2018-12-24')
    def test_register_ok(self, db, trip, testuser, client):
        testuser.member.balance = 30
        testuser.member.save()
        self.login()

        resp = self.post('/trip/1/register/', {'name': 'Pippo',
                                               'surname': 'Pluto',
                                               'is_member': '1',
                                               'deposit': '25'})
        assert resp.status_code == 200

        # check that we registered the participant
        participants = self.get_participants(self.trip)
        assert participants == [('Pluto Pippo', True, 25)]

        # that the money was taken
        testuser.member.refresh_from_db()
        assert testuser.member.balance == 5

        # and the money transfer registered
        transfers = testuser.moneytransfer_set.all()
        assert len(transfers) == 1
        t = transfers[0]
        assert t.description == 'Iscrizione di Pluto Pippo a Cervinia, 25/12/2018'
        assert t.date == date(2018, 12, 24)
        assert t.value == -25
        assert t.executed_by == testuser

        # XXX check the email
