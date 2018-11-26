from django.shortcuts import render
from django.conf import settings
from paypal.standard.forms import PayPalPaymentsForm
from trips.register import TripView

class PayPalView(TripView):

    def get(self, request, trip_id):
        trip = self.get_trip(trip_id)
        return self.render(trip)

    def render(self, trip):
        user = self.request.user
        participants = trip.get_paypal_participants(user)
        n = len(participants)
        deposit, fees = trip.compute_paypal_total(user)
        context = {
            'trip': trip,
            'user': self.request.user,
            'participants': participants,
            'total_deposit': deposit,
            'paypal_fees': fees,
            'grand_total': deposit + fees,
            'paypal_form': self.make_paypal_form(n, deposit, fees),
        }
        return render(self.request, 'trips/paypal.html', context)

    def make_paypal_form(self, n, deposit, fees):
        import pdb;pdb.set_trace()
        paypal_dict = {
            "business": settings.PAYPAL_BUSINESS_ID,
            "lc": "IT",
            "amount": str(deposit),
            "item_name": "%d Caparre" % n,
            "shipping0": str(fees),
            ## "notify_url": request.build_absolute_uri(reverse('paypal-ipn')),
            ## "return": request.build_absolute_uri(reverse('your-return-view')),
            ## "cancel_return": request.build_absolute_uri(reverse('your-cancel-view')),
            "custom": "premium_plan",
    }
