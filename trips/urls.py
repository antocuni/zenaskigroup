from django.conf.urls import patterns, url
from trips import views
from trips.register import RegisterView
from trips.paypal_view import PayPalView, PayPalReturn

urlpatterns = patterns('',
    url(r'^balance/topup/$', views.topup),
    url(r'^balance/summary/$', views.balance_summary),
    url(r'^balance/(?P<user_id>\d+)/$', views.balance_user),
    url(r'^faq/$', views.faq),
    url(r'^pictures/$', views.pictures),
    url(r'^trip/latest_poster/$', views.latest_poster),
    url(r'^trip/$', views.next_trip),
    url(r'^trip/register/$', views.next_trip_register),
    url(r'^trip/(?P<trip_id>\d+)/$', views.trip),
    url(r'^trip/(?P<trip_id>\d+)/register/$', RegisterView.as_view(),
        name='trips-register'),
    url(r'^trip/(?P<trip_id>\d+)/detail/$', views.detail),
    url(r'^pay/(?P<transaction_id>\d+)/$', PayPalView.as_view(),
        name='trips-paypal-pay'),
    url(r'^pay/(?P<transaction_id>\d+)/return/$', PayPalReturn.as_view(),
        name='trips-paypal-return'),
    url(r'^accounts/profile/$', views.profile),
    url(r'^accounts/profile/edit/$', views.editprofile),
    url(r'^sendmail/$', views.sendmail),
)
