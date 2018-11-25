import pytest
from freezegun import freeze_time
from datetime import date, datetime
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core import mail
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

@pytest.fixture
def testuser(db):
    u = User.objects.create(username='testuser', email='test@user.com')
    u.set_password('12345')
    u.save()
    return u


class TestTrip(object):

    @freeze_time('2018-12-24')
    def test_add_participants(self, db, trip, testuser):
        testuser.member.balance = 50
        testuser.member.save()
        p1 = models.Participant(name='Mickey Mouse', deposit=10, is_member=True)
        p2 = models.Participant(name='Donald Duck', deposit=20, is_member=False)
        trip.add_participants(testuser, [p1, p2])

        assert list(trip.participant_set.all()) == [p1, p2]
        assert testuser.member.balance == 20

        assert p1.registered_by == testuser
        assert p2.registered_by == testuser

        transfers = testuser.moneytransfer_set.all()
        assert len(transfers) == 1
        t = transfers[0]
        assert t.description == ('Iscrizione di Mickey Mouse, Donald Duck '
                                 'a Cervinia, 25/12/2018')
        assert t.date == date(2018, 12, 24)
        assert t.value == -30
        assert t.executed_by == testuser

    def test_no_credit(self, db, trip, testuser):
        testuser.member.balance = 25
        testuser.member.save()
        p1 = models.Participant(name='Mickey Mouse', deposit=10)
        p2 = models.Participant(name='Donald Duck', deposit=20)
        with pytest.raises(models.TripError) as exc:
            trip.add_participants(testuser, [p1, p2])
        assert exc.value.message == 'Credito insufficiente'
        #
        testuser.member.trusted = True
        testuser.member.save()
        trip.add_participants(testuser, [p1, p2])
        assert list(trip.participant_set.all()) == [p1, p2]
        assert testuser.member.balance == -5
