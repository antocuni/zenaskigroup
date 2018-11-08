from django.conf.urls import patterns, url
from trips import views

urlpatterns = patterns('',
    url(r'^balance/topup/$', views.balance_topup, name='topup'),
    url(r'^balance/summary/$', views.balance_summary, name='balance_summary'),
    url(r'^balance/(?P<user_id>\d+)/$', views.balance_user, name='balance_user'),
    url(r'^faq/$', views.faq, name='faq'),
    url(r'^pictures/$', views.pictures, name='pictures'),
    url(r'^trip/latest_poster/$', views.latest_poster, name='latest_poster'),
    url(r'^trip/$', views.next_trip, name='next_trip'),
    url(r'^trip/register/$', views.next_trip_register, name='next_trip_register'),
    url(r'^trip/(?P<trip_id>\d+)/$', views.trip, name='trip'),
    url(r'^trip/(?P<trip_id>\d+)/register/$', views.register, name='register'),
    url(r'^trip/(?P<trip_id>\d+)/detail/$', views.detail, name='detail'),
    url(r'^accounts/profile/$', views.profile, name='profile'),
    url(r'^accounts/profile/edit/$', views.editprofile, name='editprofile'),
    url(r'^accounts/topup/$', views.account_topup, name='account_topup'),
    url(r'^tuta/$', views.jacket, name='jacket'),
    url(r'^sendmail/$', views.sendmail, name='sendmail'),
)
