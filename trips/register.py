# -*- encoding: utf-8 -*-

from datetime import datetime
from django import forms
from django.conf import settings
from django.core.mail import EmailMessage
from django.views.generic import View
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from trips import models
from trips.views import compute_availability

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
            self.send_confirmation_email(trip, participants)
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

    def send_confirmation_email(self, trip, participants):
        user = self.request.user
        email = EmailMessage(subject = 'Zena Ski Group: conferma iscrizione',
                             to = [user.email])

        if trip.with_reservation:
            body = (u"L'iscrizione delle seguenti persone per la gita a "
                    u"{destination} del "
                    u"{date} è stata effettuata CON RISERVA.\n"
                    u"In caso di conferma, verrai informato via email, oppure "
                    u"puoi controllare lo stato della tua iscrizione "
                    u'direttamente sul sito, nella pagina "Iscriviti online":\n'
                    u"{participant_names}\n")
        else:
            body = (u"L'iscrizione delle seguenti persone per la gita a "
                    u"{destination} del "
                    u"{date} è stata effettuata con successo:\n"
                    u"{participant_names}\n")
        #
        participant_names = ['  - %s' % p.name for p in participants]
        email.body =  body.format(
            destination = trip.destination,
            date = trip.date.strftime("%d/%m/%Y"),
            participant_names = '\n'.join(participant_names),
        )
        email.bcc = [settings.ADMIN_EMAIL]
        email.send(fail_silently=True)
