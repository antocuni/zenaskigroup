from datetime import datetime
from django.core.urlresolvers import reverse
from django.shortcuts import render, redirect
from django.conf import settings
from django.http import Http404
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.generic import View
from paypal.standard.models import ST_PP_COMPLETED
from paypal.standard.ipn.signals import valid_ipn_received
from trips.models import (PayPalTransaction, PayPalTransactionError,
                          PendingPayPalTransactions)
from trips.register import LoginRequiredView
from trips import mails

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
        countdown = int((ppt.deadline - datetime.now()).total_seconds())
        context = {
            'ppt': ppt,
            'status': status,
            'countdown': countdown,
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
    ipn = sender
    print 'IPN received from PayPal: custom=%s' % ipn.custom
    ppt_id = int(ipn.custom)
    ppt = PayPalTransaction.objects.get(pk=ppt_id)
    try:
        ppt.mark_paid(ipn)
        print 'mark_paid done: new status: %s' % (ppt.Status(ppt.status))
        mails.registration_confirmed(ppt.user, ppt.trip,
                                     ppt.participant_set.all())
    except PayPalTransactionError as e:
        print 'mark_paid failed: %s' % e
        mails.ipn_failed(ipn, ppt)


def setup_signals():
    # this is called from apps.TripsConfig.ready()
    valid_ipn_received.connect(ipn_received)


class DeadlineMiddleware(object):
    def process_request(self, request):
        if request.path.startswith('/trip/') or request.path.startswith('/pay/'):
            for t in PendingPayPalTransactions.objects.all():
                t.ppt.cancel_maybe()
