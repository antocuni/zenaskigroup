from datetime import date, datetime
from trips import models

def test_next_trip(db, client):
    t = models.Trip.objects.create(date=date(2018, 12, 1),
                                   closing_date=datetime(2018, 11, 30, 12, 0, 0),
                                   destination='Cervinia',
                                   seats=50,
                                   deposit=25)
    assert t.id == 1
    resp = client.get('/trip/')
    assert resp.status_code == 302 # redirect
    assert resp.url == 'http://testserver/trip/1/'
