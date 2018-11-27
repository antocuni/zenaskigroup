from django.core.urlresolvers import reverse
from django.shortcuts import render
from django.conf import settings
from paypal.standard.models import ST_PP_COMPLETED
from paypal.standard.ipn.signals import valid_ipn_received
from trips.register import TripView

class PayPalView(TripView):

    def get(self, request, trip_id):
        trip = self.get_trip(trip_id)
        return self.render(trip)

    def render(self, trip):
        user = self.request.user
        participants = trip.get_paypal_participants(user)
        deadline = min([p.paypal_deadline for p in participants])
        paypal = self.make_paypal_data(trip, participants)
        paypal['notify_url'] = self.request.build_absolute_uri(
            reverse('paypal-ipn'))
        context = {
            'trip': trip,
            'user': self.request.user,
            'participants': participants,
            'paypal': paypal,
            'deadline': deadline.strftime('%Y-%m-%dT%H:%M:%S'),
        }
        return render(self.request, 'trips/paypal.html', context)

    @staticmethod
    def make_paypal_data(trip, participants):
        p_ids = []
        total_amount = 0
        fees = 0
        for p in participants:
            p_ids.append(str(p.id))
            total_amount += p.deposit
            fees += p.paypal_fee

        quantity = len(participants)
        # in theory, all participants have the same deposit, so this is just a
        # complicate way to say "amount = p.deposit". This however guarantees
        # that we charge the correct total amount even if by chance we have
        # uneven deposits (which shouldn't happen anyway)
        amount = total_amount / quantity
        item_name = 'Iscrizione gita a %s' % trip

        # pass p_ids to custom so that we know which participants we are
        # paying for
        custom = ','.join(p_ids)

        data = {
            "url": settings.PAYPAL_URL,
            "business": settings.PAYPAL_BUSINESS_ID,
            "item_name": item_name,
            "amount": amount,
            "quantity": quantity,
            "shipping": fees,
            "custom": custom,
            "total_amount": total_amount,
            "grand_total": total_amount + fees,
        }
        return data


def ipn_received(sender, **kwargs):
    ipn_obj = sender
    if ipn_obj.receiver_id != settings.PAYPAL_BUSINESS_ID:
        print 'wrong!'
        return
    print 'paypal received', ipn_obj
    # TODO

def setup_signals():
    # this is called from apps.TripsConfig.ready()
    valid_ipn_received.connect(ipn_received)
