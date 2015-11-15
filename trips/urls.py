from django.conf.urls import patterns, url
from trips import views

urlpatterns = patterns('',
    url(r'^$', views.index, name='index'),
    url(r'^topup/$', views.topup, name='topup'),
    url(r'^faq/$', views.faq, name='faq'),
    url(r'^latest_poster/$', views.latest_poster, name='latest_poster'),
    url(r'^(?P<trip_id>\d+)/$', views.trip, name='trip'),
    url(r'^(?P<trip_id>\d+)/register/$', views.register, name='register'),
    url(r'^(?P<trip_id>\d+)/detail/$', views.detail, name='detail'),
    url(r'^accounts/profile/$', views.profile, name='profile'),
    url(r'^accounts/profile/edit/$', views.editprofile, name='editprofile'),
)
