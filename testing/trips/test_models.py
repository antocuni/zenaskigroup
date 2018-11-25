import pytest
from freezegun import freeze_time
from datetime import date, datetime
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core import mail
from trips.models import Trip, Participant, TripError

@pytest.fixture
def trip(db):
    t = Trip.objects.create(
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
    u = User.objects.create(username='testuser', email='test@user.com')
    u.set_password('12345')
    u.save()
    return u


class TestTrip(object):

    @freeze_time('2018-12-24')
    def test_add_participants(self, db, trip, testuser):
        testuser.member.balance = 70
        testuser.member.save()
        p1 = Participant(name='Mickey Mouse', is_member=True)
        p2 = Participant(name='Donald Duck', is_member=False)
        trip.add_participants(testuser, [p1, p2])

        assert list(trip.participant_set.all()) == [p1, p2]
        assert testuser.member.balance == 20
        assert p1.trip == p2.trip == trip
        assert p1.registered_by == p2.registered_by == testuser

        transfers = testuser.moneytransfer_set.all()
        assert len(transfers) == 1
        t = transfers[0]
        assert t.description == ('Iscrizione di Mickey Mouse, Donald Duck '
                                 'a Cervinia, 25/12/2018')
        assert t.date == date(2018, 12, 24)
        assert t.value == -50
        assert t.executed_by == testuser

    def test_untrusted_deposit_and_credit(self, db, trip, testuser):
        # if the user is untrusted, we always use the trip deposit and it is
        # not allowed to go negative
        testuser.member.balance = 40
        testuser.member.save()
        p1 = Participant(name='Mickey Mouse', deposit=10)
        p2 = Participant(name='Donald Duck', deposit=20)
        with pytest.raises(TripError) as exc:
            trip.add_participants(testuser, [p1, p2])
        assert exc.value.message == 'Credito insufficiente'
        assert p1.deposit == p2.deposit == 25 # note: it has been overwritten
        assert trip.participant_set.count() == 0
        assert testuser.member.balance == 40

    def test_trusted_deposit_and_credit(self, db, trip, testuser):
        # if we user is trusted, he can use the deposit he wants and go
        # negative. If the deposit is not specified, we use the default
        testuser.member.balance = 30
        testuser.member.trusted = True
        testuser.member.save()
        p1 = Participant(name='Mickey Mouse', deposit=10)
        p2 = Participant(name='Donald Duck')
        trip.add_participants(testuser, [p1, p2])
        assert p1.deposit == 10
        assert p2.deposit == 25 # the default
        assert list(trip.participant_set.all()) == [p1, p2]
        assert testuser.member.balance == -5

    def test_no_seats_left(self, db, trip, testuser):
        testuser.member.balance = 50
        trip.seats = 0
        testuser.member.save()
        trip.save()
        p1 = Participant(name='Mickey Mouse', deposit=25)
        p2 = Participant(name='Donald Duck', deposit=25)
        with pytest.raises(TripError) as exc:
            trip.add_participants(testuser, [p1])
        assert exc.value.message == 'Posti esauriti'
        assert trip.participant_set.count() == 0
        assert testuser.member.balance == 50

    def test_no_seats_left_even_with_reservation(self, db, trip, testuser):
        # if we have 2 seats left but try to register 3 people, we want to
        # reject the whole transation, even if we have "with_reservation"
        testuser.member.balance = 75
        trip.seats = 2
        trip.allow_extra_seats = True
        testuser.member.save()
        trip.save()

        p1 = Participant(name='Mickey Mouse')
        p2 = Participant(name='Donald Duck')
        p3 = Participant(name='Uncle Scrooge')
        with pytest.raises(TripError) as exc:
            trip.add_participants(testuser, [p1, p2, p3])
        assert exc.value.message == (
            'Non ci sono abbastanza posti per iscrivere tutte le persone '
            'richieste. Numero massimo di posti disponibili: 2')
        assert trip.participant_set.count() == 0
        assert testuser.member.balance == 75

    def test_with_reservation(self, db, trip, testuser):
        testuser.member.balance = 75
        trip.seats = 1
        trip.allow_extra_seats = True
        testuser.member.save()
        trip.save()

        # normal registration
        p1 = Participant(name='Mickey Mouse', deposit=25)
        trip.add_participants(testuser, [p1])
        assert list(trip.participant_set.all()) == [p1]
        assert not p1.with_reservation

        # now we go into "with_reservation" mode
        p2 = Participant(name='Donald Duck', deposit=25)
        p3 = Participant(name='Uncle Scrooge', deposit=25)
        trip.add_participants(testuser, [p2, p3])
        assert list(trip.participant_set.all()) == [p1, p2, p3]
        assert not p1.with_reservation
        assert p2.with_reservation
        assert p3.with_reservation
        assert p2.deposit == p3.deposit == 25

