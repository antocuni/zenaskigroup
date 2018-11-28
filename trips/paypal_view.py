from django.core.urlresolvers import reverse
from django.shortcuts import render, redirect
from django.conf import settings
from django.http import Http404
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.generic import View
from paypal.standard.models import ST_PP_COMPLETED
from paypal.standard.ipn.signals import valid_ipn_received
from trips.models import PayPalTransaction
from trips.register import LoginRequiredView

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
        request = self.request
        notify_url = request.build_absolute_uri(reverse('paypal-ipn'))
        return_url = request.build_absolute_uri(
            reverse('trips-paypal-return', args=[ppt.id]))
        cancel_url = request.build_absolute_uri(
            reverse('trips-paypal-pay', args=[ppt.id]))

        status = ppt.Status(ppt.status).name
        context = {
            'ppt': ppt,
            'status': status,
            'notify_url': notify_url,
            'return_url': return_url,
            'cancel_url': cancel_url,
            'paypal_url': settings.PAYPAL_URL,
            'paypal_business_id': settings.PAYPAL_BUSINESS_ID,
        }
        return render(request, 'trips/paypal.html', context)


class PayPalReturn(View):

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(PayPalReturn, self).dispatch(request, *args, **kwargs)

    def post(self, request, transaction_id):
        assert request.POST['business'] == settings.PAYPAL_BUSINESS_EMAIL
        assert request.POST['custom'] == str(transaction_id)
        ppt = PayPalTransaction.objects.get(pk=transaction_id)
        ppt.mark_waiting()
        url = reverse('trips-paypal-pay', args=[transaction_id])
        return redirect(url)

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
