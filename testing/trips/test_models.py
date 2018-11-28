import pytest
from freezegun import freeze_time
from datetime import date, datetime
from decimal import Decimal
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core import mail
from trips.models import Trip, Participant, TripError, PayPalTransaction

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

class TestParticipant(object):

    def test_status(self):
        p = Participant('Mickey Mouse')
        assert p.status == 'Confermato'
        assert p.status_class == 'text-success'

        p.with_reservation = True
        assert p.status == 'Con riserva'
        assert p.status_class == 'text-warning'


class TestTrip(object):

    def test_get_participants(self, db, trip, testuser):
        p1 = Participant(name='Mickey Mouse', deposit=0, registered_by=testuser)
        p2 = Participant(name='Donald Duck', deposit=0, registered_by=None)
        p3 = Participant(name='Uncle Scrooge', deposit=0, registered_by=testuser)
        trip.participant_set.add(p1, p2, p3)
        participants = trip.get_participants(testuser)
        assert list(participants) == [p1, p3]

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
        assert p1.sublist == p2.sublist == 'Online'

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


class TestPayPal(object):

    @staticmethod
    def P(name, deposit, trip):
        return Participant(name=name, deposit=Decimal(deposit), trip=trip)

    @freeze_time('2018-12-24 12:00')
    def test_transaction_make(self, db, trip, testuser):
        p1 = self.P('Mickey Mouse', 25, trip)
        p2 = self.P('Donald Duck', 30, trip)
        ppt = PayPalTransaction.make(testuser, trip, [p1, p2])
        assert ppt.user == testuser
        assert ppt.trip == trip
        assert ppt.amount == 27.5
        assert ppt.quantity == 2
        assert ppt.deadline == datetime(2018, 12, 24, 12, 20, 0)
        assert ppt.ipn is None
        assert ppt.is_pending
        assert not ppt.is_paid
        assert list(ppt.participant_set.all()) == [p1, p2]
        assert ppt.fees == 2
        assert ppt.total_amount == 55
        assert ppt.grand_total == 57
        assert ppt.item_name == 'Iscrizione gita a Cervinia, 25/12/2018'

    @freeze_time('2018-12-24 12:00')
    def test_pay_with_paypal(self, db, trip, testuser):
        p1 = Participant(name='Mickey Mouse')
        p2 = Participant(name='Donald Duck')
        trip.add_participants(testuser, [p1, p2], paypal=True)
        assert list(trip.participant_set.all()) == [p1, p2]
        assert testuser.member.balance == 0
        assert p1.waiting_paypal
        assert p2.waiting_paypal
        assert p1.sublist == p2.sublist == 'PayPal'
        transactions = trip.paypaltransaction_set.all()
        assert len(transactions) == 1
        ppt = transactions[0]
        assert list(ppt.participant_set.all()) == [p1, p2]
        assert ppt.total_amount == trip.deposit * 2

    def test_participant_status(self, db, trip, testuser):
        p1 = self.P('Mickey Mouse', 25, trip)
        assert p1.status == 'Confermato'
        ppt = PayPalTransaction.make(testuser, trip, [p1])
        assert p1.status == 'In attesa di PayPal'
        assert p1.status_class == 'text-danger'

    def test_paypal_pending(self, db, trip, testuser):
        p1 = Participant(name='Mickey Mouse')
        p2 = Participant(name='Donald Duck')
        trip.add_participants(testuser, [p1, p2], paypal=True)
        qs = PayPalTransaction.get_pending(testuser, trip)
        assert len(qs) == 1
        ppt = qs[0]
        assert ppt.total_amount == 50
        assert ppt.trip == trip
        ppt.is_pending = False
        ppt.save()
        assert not PayPalTransaction.get_pending(testuser, trip)
