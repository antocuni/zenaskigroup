from django.core.urlresolvers import reverse
from django.shortcuts import render, redirect
from django.conf import settings
from django.http import Http404
from trips.models import PayPalTransaction
from trips.register import LoginRequiredView
from paypal.standard.models import ST_PP_COMPLETED
from paypal.standard.ipn.signals import valid_ipn_received

class PayPalView(LoginRequiredView):

    def get(self, request, transaction_id):
        ppt = self.get_ppt(transaction_id)
        return self.render(ppt)

    def post(self, request, transaction_id):
        ppt = self.get_ppt(transaction_id)
        if 'btn-cancel' in request.POST:
            ppt.cancel()
            url = reverse('trips-register', args=[ppt.trip.id])
            return redirect(url)
        # this should never happen!
        return self.render(ppt)

    def get_ppt(self, transaction_id):
        try:
            return PayPalTransaction.objects.get(pk=transaction_id)
        except PayPalTransaction.DoesNotExist:
            raise Http404

    def render(self, ppt):
        notify_url = self.request.build_absolute_uri(reverse('paypal-ipn'))
        context = {
            'ppt': ppt,
            'notify_url': notify_url,
            'paypal_url': settings.PAYPAL_URL,
            'paypal_business_id': settings.PAYPAL_BUSINESS_ID,
        }
        return render(self.request, 'trips/paypal.html', context)


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
