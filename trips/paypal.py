from trips.register import TripView
from django.shortcuts import render

class PayPalView(TripView):

    def get(self, request, trip_id):
        trip = self.get_trip(trip_id)
        return self.render(trip)

    def render(self, trip):
        participants = trip.get_paypal_participants(self.request.user)
        context = {'trip': trip,
                   'user': self.request.user,
                   'participants': participants}
        context.update(**kwargs)
        return render(self.request, 'trips/paypal.html', context)
