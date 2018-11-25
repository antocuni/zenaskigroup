# -*- encoding: utf-8 -*-

import pytest
from freezegun import freeze_time
from datetime import date, datetime
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core import mail
from trips import models
from trips.views import RegisterForm, RegisterFormSet
from testing.trips.test_models import trip, testuser


def encode_formset(formset_class, formsdata):
    prefix = formset_class().prefix
    data = {
        '%s-INITIAL_FORMS' % prefix: '0',
        '%s-TOTAL_FORMS' % prefix: str(len(formsdata))
        }
    for i, formdata in enumerate(formsdata):
        for key, value in formdata.iteritems():
            new_key = '%s-%d-%s' % (prefix, i, key)
            data[new_key] = value
    return data

def test_encode_formset():
    data = [{'a': 'aaa', 'b': 'bbb'},
            {'a': 'xxx', 'b': 'yyy'}]
    encoded = encode_formset(RegisterFormSet, data)
    assert encoded == {
        'form-INITIAL_FORMS': '0',
        'form-TOTAL_FORMS': '2',
        'form-0-a': 'aaa',
        'form-0-b': 'bbb',
        'form-1-a': 'xxx',
        'form-1-b': 'yyy'
        }

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


class TestRegisterForm(object):

    def test_as_participant(self):
        form = RegisterForm(data=dict(surname='Mickey',
                                      name='Mouse',
                                      is_member='1',
                                      deposit='10'))
        p = form.as_participant()
        assert p.name == 'Mickey Mouse'
        assert p.is_member
        assert p.deposit == 10


class TestRegister(BaseTestView):

    def submit(self, url, data):
        encoded = encode_formset(RegisterFormSet, data)
        return self.post(url, encoded)

    def get_participants(self, trip):
        res = []
        for p in trip.participant_set.all():
            res.append((p.name, p.is_member, p.deposit, p.with_reservation))
        return res

    def test_login_required(self):
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
    def test_register_ok(self, testuser):
        testuser.member.balance = 30
        testuser.member.save()
        self.login()

        # note: we INTENTIONALLY use a deposit which is different than the one
        # on the trip: since this is not a trusted user, the field is ignored
        resp = self.submit('/trip/1/register/', [{'name': 'Pippo',
                                                 'surname': 'Pluto',
                                                 'is_member': '1',
                                                 'deposit': '42'}])
        assert resp.status_code == 200

        # check that we registered the participant
        participants = self.get_participants(self.trip)
        assert participants == [('Pluto Pippo', True, 25, False)]

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

        assert resp.context['message'] == (u"L'iscrizione è andata a buon fine. "
                                           u"Credito residuo: 5.00 €")

        # check the email which has been sent
        assert len(mail.outbox) == 1
        msg = mail.outbox[0]
        assert msg.subject == 'Zena Ski Group: conferma iscrizione'
        assert msg.to == ['test@user.com']
        assert msg.body == (u"L'iscrizione delle seguenti persone per la gita a "
                            u"Cervinia del 25/12/2018 è stata effettuata "
                            u"con successo:\n"
                            u"  - Pluto Pippo\n")


    @freeze_time('2018-12-24')
    def test_register_many(self, testuser):
        testuser.member.balance = 60
        testuser.member.save()
        self.login()

        # note: we INTENTIONALLY use a deposit which is different than the one
        # on the trip: since this is not a trusted user, the field is ignored
        data = [{'name': 'Pippo', 'surname': 'Pluto',
                 'is_member': '1', 'deposit': '42'},
                {'name': 'Mickey', 'surname': 'Mouse',
                 'deposit': '42'}]
        resp = self.submit('/trip/1/register/', data)
        assert resp.status_code == 200

        participants = self.get_participants(self.trip)
        assert participants == [('Pluto Pippo', True, 25, False),
                                ('Mouse Mickey', False, 25, False)]

        testuser.member.refresh_from_db()
        assert testuser.member.balance == 10

        # check the money transfer
        transfers = testuser.moneytransfer_set.all()
        assert len(transfers) == 1
        t = transfers[0]
        assert t.description == ('Iscrizione di Pluto Pippo, Mouse Mickey '
                                 'a Cervinia, 25/12/2018')
        assert t.date == date(2018, 12, 24)
        assert t.value == -50
        assert t.executed_by == testuser

        assert len(mail.outbox) == 1
        msg = mail.outbox[0]
        assert msg.subject == 'Zena Ski Group: conferma iscrizione'
        assert msg.to == ['test@user.com']
        assert msg.body == (u"L'iscrizione delle seguenti persone per la gita a "
                            u"Cervinia del 25/12/2018 è stata effettuata "
                            u"con successo:\n"
                            u"  - Pluto Pippo\n"
                            u"  - Mouse Mickey\n")


    @freeze_time('2018-12-24')
    def test_trusted_deposit(self, testuser):
        testuser.member.trusted = True
        testuser.member.save()
        self.login()

        # since the user is trusted, we use the deposit which was actually
        # specified in the form
        data = [{'name': 'Pippo', 'surname': 'Pluto',
                 'is_member': '1', 'deposit': '10'},
                {'name': 'Mickey', 'surname': 'Mouse',
                 'is_member': '1', 'deposit': '12'}]
        resp = self.submit('/trip/1/register/', data)
        assert resp.status_code == 200
        participants = self.get_participants(self.trip)
        assert participants == [('Pluto Pippo', True, 10, False),
                                ('Mouse Mickey', True, 12, False)]
        testuser.member.refresh_from_db()
        assert testuser.member.balance == -22

    @freeze_time('2018-12-24')
    def test_TripError(self):
        # test that when we raise TripError we do the correct thing
        self.login()
        p1 = {'name': 'Pippo', 'surname': 'Pluto', 'deposit': '10'}
        resp = self.submit('/trip/1/register/', [p1])
        assert resp.status_code == 200
        participants = self.get_participants(self.trip)
        assert not participants
        assert resp.context['error'] == 'Credito insufficiente'

    @freeze_time('2018-12-24')
    def test_with_reservation(self, trip, testuser):
        testuser.member.balance = 50
        trip.seats = 0
        trip.allow_extra_seats = True
        testuser.member.save()
        trip.save()
        self.login()
        data = [
            {'name': 'Mickey', 'surname': 'Mouse', 'deposit': '25'},
            {'name': 'Donald', 'surname': 'Duck', 'deposit': '25'}
        ]
        resp = self.submit('/trip/1/register/', data)
        assert resp.status_code == 200
        participants = self.get_participants(self.trip)
        assert participants == [('Mouse Mickey', False, 25, True),
                                ('Duck Donald', False, 25, True)]
        msg = mail.outbox[0]
        assert 'CON RISERVA' in msg.body
        assert 'Mouse Mickey' in msg.body
        assert 'Duck Donald' in msg.body

    @freeze_time('2018-12-24')
    def test_form_invalid(self, testuser):
        testuser.member.balance = 25
        testuser.member.save()
        self.login()
        resp = self.submit('/trip/1/register/',
                           [{'name': 'Pippo', 'surname': ''}])
        assert resp.status_code == 200
        participants = self.get_participants(self.trip)
        assert not participants

        formset = resp.context['formset']
        assert not formset.is_valid()

        assert 'Pippo' in resp.content # check that the invalid form is
                                       # pre-populated
