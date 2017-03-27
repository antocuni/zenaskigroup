from datetime import datetime

SOLD_OUT = 0
CRITICAL = 1
LOW = 2
LIMITED = 3
HIGH = 4

def seats_availability(trip):
    """
    Compute an approximate non-numeric estimate of how many seats are left. To
    convince users to book early, we also take the current time into account:
    the more we are close to the date, the easier is to display "limitata" or
    "bassa".
    """
    left = trip.seats_left
    dt = trip.date
    dt = datetime(dt.year, dt.month, dt.day) # convert from "date" to "datetime"
    delta = (dt - datetime.now())
    days_left = delta.total_seconds() / (3600*24.0)
    #
    if left <= 0:
        return SOLD_OUT
    ratio = float(left) / trip.seats
    if ratio <= 0.25:
        return CRITICAL
    elif ratio <= 0.50 or days_left <= 4.5:
        return LOW
    elif ratio <= 0.75 or days_left <= 8.5:
        return LIMITED
    else:
        return HIGH
