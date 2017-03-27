from datetime import date
from mock import Mock
from freezegun import freeze_time
from trips.utils import seats_availability

def availability(trip, left):
    trip.seats_left = left
    return seats_availability(trip)

def test_seats_availability():
    trip = Mock(seats=100)
    trip.date = date(2017, 3, 26)
    # first tuesday
    with freeze_time('2017-03-14'):
        assert availability(trip, left=100) == 'alta'
        assert availability(trip, left=76) == 'alta'
        assert availability(trip, left=75) == 'limitata'
        assert availability(trip, left=50) == 'bassa'
        assert availability(trip, left=25) == 'critica'
        assert availability(trip, left=0) == 'esauriti'
    
    # first friday, before 12:00: no change
    with freeze_time('2017-03-17 11:59'):
        assert availability(trip, left=100) == 'alta'
        assert availability(trip, left=76) == 'alta'
        assert availability(trip, left=75) == 'limitata'
        assert availability(trip, left=50) == 'bassa'
        assert availability(trip, left=25) == 'critica'
        assert availability(trip, left=0) == 'esauriti'
    
    # first friday, after 12:00: never show "alta"
    with freeze_time('2017-03-17 12:00'):
        assert availability(trip, left=100) == 'limitata'
        assert availability(trip, left=76) == 'limitata'
        assert availability(trip, left=75) == 'limitata'
        assert availability(trip, left=50) == 'bassa'
        assert availability(trip, left=25) == 'critica'
        assert availability(trip, left=0) == 'esauriti'
    #
    # second tuesday, after 12:00: never show "limitata"
    with freeze_time('2017-03-21 12:00'):
        assert availability(trip, left=100) == 'bassa'
        assert availability(trip, left=76) == 'bassa'
        assert availability(trip, left=75) == 'bassa'
        assert availability(trip, left=50) == 'bassa'
        assert availability(trip, left=25) == 'critica'
        assert availability(trip, left=0) == 'esauriti'
