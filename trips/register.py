# -*- encoding: utf-8 -*-

from datetime import datetime
from django import forms
from django.conf import settings
from django.core.urlresolvers import reverse
from django.views.generic import View
from django.http import Http404
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from trips import models
from trips.views import compute_availability
from trips import mails

class RegisterForm(forms.Form):

    name = forms.CharField(label='Nome',
                           max_length=200,
                           widget=forms.TextInput(
                               attrs={'placeholder': 'Nome',
                                      'class': 'form-control input-sm'}
                           ))

    surname = forms.CharField(label='Cognome',
                              max_length=200,
                              widget=forms.TextInput(
                                  attrs={'placeholder': 'Cognome',
                                         'class': 'form-control input-sm'}
                              ))
    is_member = forms.BooleanField(label='Socio?', initial=False, required=False)
    deposit = forms.DecimalField(label='Caparra',
                                 required=False,
                                 widget=forms.TextInput(
                                     attrs={'class': 'form-control input-sm',
                                            'size': 5}
                                 ))

    def as_participant(self):
        assert self.is_valid()
        name = '%s %s' % (self.cleaned_data['surname'],
                          self.cleaned_data['name'])
        name = name.strip()
        return models.Participant(
            name=name,
            deposit=self.cleaned_data['deposit'],
            is_member=self.cleaned_data['is_member'])

RegisterFormSet = forms.formset_factory(RegisterForm, extra=0)


class LoginRequiredView(View):
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(LoginRequiredView, self).dispatch(*args, **kwargs)

class TripView(LoginRequiredView):

    def get_trip(self, trip_id):
        try:
            return models.Trip.objects.get(pk=self.kwargs['trip_id'])
        except models.Trip.DoesNotExist:
            raise Http404


class RegisterView(TripView):

    def get(self, request, trip_id):
        trip = self.get_trip(trip_id)
        # if we have a pending paypal transaction, we redirect to the
        # appropriate page
        ppts = models.PayPalTransaction.get_pending(self.request.user, trip)
        if ppts:
            url = reverse('trips-paypal-pay', args=[ppts[0].id])
            return redirect(url)
        return self.render(trip)

    def post(self, request, trip_id):
        trip = self.get_trip(trip_id)
        formset = RegisterFormSet(request.POST)
        if not formset.is_valid():
            # pass form to render so that it can show the errors and
            # pre-populate the already compiled fields
            error = "Correggere gli errori evidenziati"
            return self.render(trip, formset=formset, error=error)

        try:
            return self.on_form_validated(trip, formset)
        except models.TripError as exc:
            return self.render(trip, formset=formset, error=str(exc))

    def on_form_validated(self, trip, formset):
        user = self.request.user
        participants = [form.as_participant() for form in formset]
        paypal = 'btn-paypal' in self.request.POST
        trip.add_participants(user, participants, paypal=paypal)
        if not paypal:
            mails.registration_confirmed(user, trip, participants)
        message = (u"L'iscrizione è andata a buon fine. Credito residuo: %s €" %
                   user.member.balance)
        return self.render(trip, message=message)

    # ---------------------

    def compute_total_deposit(self, trip, formset):
        total = 0
        for form in formset:
            total += self.compute_one_deposit(trip, form)
        return total

    def compute_one_deposit(self, trip, form):
        if self.request.user.member.trusted and form.is_valid():
            return form.cleaned_data['deposit']
        return trip.deposit

    def new_formset(self, trip):
        deposit = trip.deposit
        if trip.with_reservation and trip.seats_left <= 0:
            deposit = 0 # default 0 deposit for registrations with reservation
        formset = RegisterFormSet(initial=[{'deposit': deposit}])
        return formset

    def render(self, trip, formset=None, **kwargs):
        if formset is None:
            formset = self.new_formset(trip)
        registration_allowed = trip.closing_date >= datetime.now()
        participants = trip.get_participants(self.request.user)
        empty_form = formset.empty_form
        empty_form.initial['deposit'] = trip.deposit
        context = {'trip': trip,
                   'user': self.request.user,
                   'participants': participants,
                   'formset': formset,
                   'allforms': list(formset) + [empty_form],
                   'registration_allowed': registration_allowed}
        context.update(**kwargs)
        compute_availability(self.request.user, context)
        return render(self.request, 'trips/register.html', context)
