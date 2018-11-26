from trips.register import TripView
from django.shortcuts import render

class PayPalView(TripView):

    def get(self, request, trip_id):
        trip = self.get_trip(trip_id)
        return self.render(trip)

    def render(self, trip):
        user = self.request.user
        participants = trip.get_paypal_participants(user)
        deposit, fees = trip.compute_paypal_total(user)
        context = {'trip': trip,
                   'user': self.request.user,
                   'participants': participants,
                   'total_deposit': deposit,
                   'paypal_fees': fees,
                   'grand_total': deposit + fees}
        return render(self.request, 'trips/paypal.html', context)
