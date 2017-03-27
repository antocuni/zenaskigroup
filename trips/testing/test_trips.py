from mock import Mock
from trips.utils import seats_availability

def test_seats_availability():
    trip = Mock(seats=100)
    trip.seats_left = 100
    assert seats_availability(trip) == 'alta'
    #
    trip.seats_left = 76
    assert seats_availability(trip) == 'alta'
    #
    trip.seats_left = 75
    assert seats_availability(trip) == 'limitata'
    #
    trip.seats_left = 50
    assert seats_availability(trip) == 'bassa'
    #
    trip.seats_left = 25
    assert seats_availability(trip) == 'critica'
