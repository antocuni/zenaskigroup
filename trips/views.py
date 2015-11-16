# -*- encoding: utf-8 -*-

from datetime import date, datetime
from django.core.mail import send_mail, EmailMessage
from django.conf import settings
from django.shortcuts import render, redirect
from django.http import HttpResponse, Http404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
import django.contrib.auth.models as auth_models
from django.db import transaction
from django import forms
from trips import models

# ----------------------------------
# show trip
# ----------------------------------

def next_trip(request):
    trip = models.Trip.objects.latest()
    return redirect('/trip/%d/' % trip.id)

def next_trip_register(request):
    trip = models.Trip.objects.latest()
    return redirect('/trip/%d/register' % trip.id)

def latest_poster(request):
    trip = models.Trip.objects.latest()
    return redirect(trip.poster.url)

class TripForm(forms.Form):
    sublist = forms.CharField(label='Lista', max_length=20)
    count = forms.IntegerField(label='Posti', min_value=0)

    def __init__(self, *args, **kwargs):
        super(TripForm, self).__init__(*args, **kwargs)
        self.fields['sublist'].widget.attrs['placeholder'] = 'Sottolista'
        self.fields['sublist'].widget.attrs['class'] = 'form-control input-sm'
        self.fields['count'].widget.attrs['placeholder'] = 'Posti'
        self.fields['count'].widget.attrs['class'] = 'form-control input-sm'

def trip(request, trip_id):
    try:
        trip = models.Trip.objects.get(pk=trip_id)
    except models.Trip.DoesNotExist:
        raise Http404

    registration_allowed = trip.closing_date >= datetime.now()
    
    if request.method == 'POST':
        form = TripForm(request.POST)
        if form.is_valid():
            data = form.clean()
            for i in range(data['count']):
                p = models.Participant(name='<Riservato>', deposit=0, is_member=False,
                                       registered_by=None, sublist=data['sublist'])
                trip.participant_set.add(p)

    form = TripForm()
    context = {
        'trip': trip,
        'registration_allowed': registration_allowed,
        'form': form
    }
    return render(request, 'trips/trip.html', context)


# ----------------------------------
# faq
# ----------------------------------

def faq(request):
    return render(request, 'trips/faq.html', {})

# ----------------------------------
# participant list
# ----------------------------------

def detail(request, trip_id):
    try:
        trip = models.Trip.objects.get(pk=trip_id)
    except models.Trip.DoesNotExist:
        raise Http404
    participants = list(trip.participant_set.all())
    participants.sort(key=lambda p: (p.sublist.lower().strip() == 'staff', p.name.lower()))
    context = {'trip': trip,
               'participants': participants}
    return render(request, 'trips/detail.html', context)


# ----------------------------------
# topup
# ----------------------------------

class TopupForm(forms.ModelForm):
    class Meta:
        model = models.MoneyTransfer
        fields = ['member', 'value', 'description']


@staff_member_required
def topup(request):
    transfers = models.MoneyTransfer.objects.filter(date=date.today(),
                                                    value__gt=0)
    
    if request.method == 'POST':
        form = TopupForm(request.POST)
        money_transfer = form.save(commit=False)
        money_transfer.executed_by = request.user
        with transaction.atomic():
            money_transfer.save()
            money_transfer.member.balance += money_transfer.value
            money_transfer.member.save()

        msg = ("La ricarica di %s € è stata effettuata con successo.\n"
               "Il tuo credito è ora di %s €.")
        msg = msg % (money_transfer.value, money_transfer.member.balance)
        send_mail('Zena Ski Group: ricarica effettuata',
                  msg,
                  settings.DEFAULT_FROM_EMAIL,
                  [money_transfer.member.user.email],
                  fail_silently=True)

    form = TopupForm()
    context = {'form': form,
               'transfers': transfers}
    return render(request, 'trips/topup.html', context)

# ----------------------------------
# user profile
# ----------------------------------

@login_required
def profile(request):
    user = request.user
    transfers = models.MoneyTransfer.objects.filter(member=user.member)
    transfers = transfers.order_by('-date')
    context = {
        'user': user,
        'transfers': transfers,
    }
    return render(request, 'trips/profile.html', context)


class ProfileForm(forms.Form):
    name = forms.CharField(label='Nome e cognome',
                           max_length=200)
    email = forms.EmailField(label='Email')
    card_no = forms.CharField(label='Numero tessera', max_length=5)


@login_required
def editprofile(request):
    user = request.user
    if request.method == 'POST':
        form = ProfileForm(request.POST)
        if form.is_valid():
            data = form.clean()
            user.first_name = data['name']
            user.email = data['email']
            user.member.card_no = data['card_no']
            user.member.save()
            user.save()
            return redirect('/accounts/profile/')
    else:
        form = ProfileForm(initial=dict(
            name=user.first_name,
            email=user.email,
            card_no=user.member.card_no))

    context = {
        'user': user,
        'form': form,
    }
    return render(request, 'trips/editprofile.html', context)
    


# ----------------------------------
# registration
# ----------------------------------

class RegisterForm(forms.Form):
    name = forms.CharField(label='Nome',
                           max_length=200,
                           widget=forms.TextInput(
                               attrs={'placeholder': 'Nome da iscrivere',
                                      'class': 'form-control input-sm'}
                           ))
    is_member = forms.BooleanField(label='Socio?', initial=True, required=False)    


@login_required
def register(request, trip_id):
    try:
        trip = models.Trip.objects.get(pk=trip_id)
    except models.Trip.DoesNotExist:
        raise Http404

    error = None
    message = None
    if request.method == 'POST':
        if (request.user.member.balance < trip.deposit and
            not request.user.member.trusted):
            error = "Credito insufficiente"
        if trip.seats_left <= 0 and not trip.with_reservation:
            error = "Posti esauriti"
        form = RegisterForm(request.POST)
        if form.is_valid() and not error:
            participant = models.Participant(trip=trip,
                                             deposit=trip.deposit,
                                             name=form.cleaned_data['name'],
                                             is_member=form.cleaned_data['is_member'],
                                             sublist='Online',
                                             registered_by=request.user,
                                             with_reservation=trip.with_reservation)
            with transaction.atomic():
                trip.participant_set.add(participant)
                request.user.member.balance -= trip.deposit
                descr = u'Iscrizione di %s a %s' % (participant.name, trip)
                t = models.MoneyTransfer(member=request.user.member,
                                         value=-trip.deposit,
                                         executed_by=request.user,
                                         description=descr)
                t.save()
                request.user.member.save()
                trip.save()
            form = RegisterForm()
            message = (u"L'iscrizione è andata a buon fine. Credito residuo: %s €" %
                       request.user.member.balance)

            email = EmailMessage(subject = 'Zena Ski Group: conferma iscrizione',
                                 to = [request.user.email])

            if trip.with_reservation:
                body = (u"L'iscrizione di {name} per la gita a {destination} del "
                        u"{date} è stata effettuata CON RISERVA.\n"
                        u"In caso di conferma, verrai informato via email, oppure "
                        u"puoi controllare lo stato della tua iscrizione direttamente "
                        u'sul sito, nella pagina "Iscriviti online".\n')
            else:
                body = (u"L'iscrizione di {name} per la gita a {destination} del "
                        u"{date} è stata effettuata con successo.\n")
            #
            email.body =  body.format(name = participant.name,
                                      destination = trip.destination,
                                      date = trip.date.strftime("%d/%m/%Y"))
            email.bcc = [settings.ADMIN_EMAIL]
            email.send(fail_silently=True)
    else:
        form = RegisterForm()

    registration_allowed = trip.closing_date >= datetime.now()
    participants = trip.participant_set.filter(registered_by=request.user)
    context = {'trip': trip,
               'user': request.user,
               'participants': participants,
               'form': form,
               'error': error,
               'message': message,
               'registration_allowed': registration_allowed}
    return render(request, 'trips/register.html', context)
