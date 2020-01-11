# -*- encoding: utf-8 -*-

from datetime import date, datetime
from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import render, redirect
from django.http import HttpResponse, Http404
from django.views.decorators.csrf import csrf_exempt
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
    compute_availability(request.user, context)
    return render(request, 'trips/trip.html', context)


def compute_availability(user, context):
    from trips.utils import seats_availability, SOLD_OUT, CRITICAL, LOW, LIMITED, HIGH
    classes = {
        SOLD_OUT: ('Esauriti', 'text-danger'),
        CRITICAL: ('Critica', 'danger'),
        LOW:      ('Bassa', 'text-danger'),
        LIMITED:  ('Limitata', 'text-warning'),
        HIGH:     ('Alta', 'text-success'),
        }

    availability = seats_availability(context['trip'])
    availability, cls = classes.get(availability, ('', ''))
    context['availability'] = availability
    context['availability_class'] = cls
    #
    show_seats = False
    trusted = hasattr(user, 'member') and user.member.trusted
    if user.is_staff or trusted:
        # staff and trusted users always see the actual number of seats left
        show_seats = True
    context['show_seats'] = show_seats



# ----------------------------------
# faq & pictures
# ----------------------------------

def faq(request):
    return render(request, 'trips/faq.html', {})

def pictures(request):
    # XXX: remove the hardcoded date, and think how to separate seasons
    trips = models.Trip.objects.filter(date__gt='2017-11-01').order_by('-date')
    return render(request, 'trips/pictures.html', {'trips': trips})


# ----------------------------------
# participant list
# ----------------------------------

def detail(request, trip_id):
    try:
        trip = models.Trip.objects.get(pk=trip_id)
    except models.Trip.DoesNotExist:
        raise Http404
    #
    participants = trip.participant_set.filter(with_reservation=False)
    participants = list(participants.all())
    participants.sort(key=lambda p: (p.sublist.lower().strip() == 'staff', p.name.lower()))
    #
    reserves = trip.participant_set.filter(with_reservation=True)
    reserves = list(reserves.all())
    #
    header = '%s %s' % (trip.destination, trip.date)
    tables = [(header, participants, 'main')]
    if reserves:
        tables.append(('Riserve', reserves, 'reserves'))
    context = {'trip': trip,
               'tables': tables}
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


@staff_member_required
def balance_summary(request):
    users = models.User.objects.exclude(member__balance=0)
    users = users.order_by('member__balance')
    context = {'users': users}
    return render(request, 'trips/balance_summary.html', context)

@staff_member_required
def balance_user(request, user_id):
    user_id = int(user_id)
    user = models.User.objects.get(pk=user_id)
    transfers = models.MoneyTransfer.objects.filter(member=user.member)
    transfers = transfers.order_by('-date')
    context = {
        'user': user,
        'transfers': transfers,
        'hide_edit': True,
    }
    return render(request, 'trips/profile.html', context)


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
    card_no = forms.CharField(label='Numero tessera', max_length=5, required=False)


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

class SendEmailForm(forms.Form):
    to = forms.CharField(label='To', initial=settings.ADMIN_EMAIL)


@csrf_exempt
@staff_member_required
def sendmail(request):
    if request.method == 'POST':
        form = SendEmailForm(request.POST)
        if form.is_valid():
            data = form.clean()
            to = data['to']
            sendmail.n += 1
            subject = 'Zena Ski Group: Test Email #%s' % sendmail.n
            body = ("This is a test email to check the SMTP.\n"
                    "Date sent: %s\n" % datetime.now())
            send_mail(subject,
                      body,
                      settings.DEFAULT_FROM_EMAIL,
                      [to],
                      fail_silently=True)
            #
            content = "To: %s\n\n%s\n%s\n " % (to, subject, body)
            return HttpResponse(content, content_type="text/plain")
    else:
        form = SendEmailForm()
        content = """
        <html>
          <body>
           <h4>Send test email</h4>
            <form method="POST">
              %s
            <input type="submit">
            </form>
          </body>
        </html>
        """ % form.as_table()
        return HttpResponse(content)

sendmail.n = 0
