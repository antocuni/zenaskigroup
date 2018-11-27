from decimal import Decimal
from trips.models import Participant
from trips.paypal_view import PayPalView
from testing.trips.test_models import trip, testuser

class TestPayPalLogic(object):

    def test_make_paypal_data(self, db, trip):
        def P(name, deposit):
            return Participant(name=name, deposit=Decimal(deposit), trip=trip)
        p1 = P('Mickey Mouse',  deposit=25)
        p2 = P('Donald Duck',   deposit=30)
        p1.save()
        p2.save()
        assert p1.id == 1
        assert p2.id == 2
        data = PayPalView.make_paypal_data(trip, [p1, p2])
        assert data['item_name'] == 'Iscrizione gita a Cervinia, 25/12/2018'
        assert data['amount'] == 27.5
        assert data['quantity'] == 2
        assert data['shipping'] == 2
        assert data['custom'] == '1,2'
        assert data['total_amount'] == 55
        assert data['grand_total'] == 57
    
