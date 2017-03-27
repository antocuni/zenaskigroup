from datetime import date
from mock import Mock
from freezegun import freeze_time
from trips.utils import seats_availability, SOLD_OUT, CRITICAL, LOW, LIMITED, HIGH

def availability(trip, left):
    trip.seats_left = left
    return seats_availability(trip)

def test_seats_availability():
    trip = Mock(seats=100)
    trip.date = date(2017, 3, 26)
    # first tuesday
    with freeze_time('2017-03-14'):
        assert availability(trip, left=100) == HIGH
        assert availability(trip, left=76) == HIGH
        assert availability(trip, left=75) == LIMITED
        assert availability(trip, left=50) == LOW
        assert availability(trip, left=25) == CRITICAL
        assert availability(trip, left=0) == SOLD_OUT
    
    # first friday, before 12:00: no change
    with freeze_time('2017-03-17 11:59'):
        assert availability(trip, left=100) == HIGH
        assert availability(trip, left=76) == HIGH
        assert availability(trip, left=75) == LIMITED
        assert availability(trip, left=50) == LOW
        assert availability(trip, left=25) == CRITICAL
        assert availability(trip, left=0) == SOLD_OUT
    
    # first friday, after 12:00: never show "alta"
    with freeze_time('2017-03-17 12:00'):
        assert availability(trip, left=100) == LIMITED
        assert availability(trip, left=76) == LIMITED
        assert availability(trip, left=75) == LIMITED
        assert availability(trip, left=50) == LOW
        assert availability(trip, left=25) == CRITICAL
        assert availability(trip, left=0) == SOLD_OUT
    #
    # second tuesday, after 12:00: never show "limitata"
    with freeze_time('2017-03-21 12:00'):
        assert availability(trip, left=100) == LOW
        assert availability(trip, left=76) == LOW
        assert availability(trip, left=75) == LOW
        assert availability(trip, left=50) == LOW
        assert availability(trip, left=25) == CRITICAL
        assert availability(trip, left=0) == SOLD_OUT
