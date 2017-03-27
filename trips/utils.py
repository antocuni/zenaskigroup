def seats_availability(trip):
    left = trip.seats_left
    if left <= 0:
        # XXX: think about "with reserve" case
        return 'esauriti'
    ratio = float(left) / trip.seats
    if ratio <= 0.25:
        return 'critica'
    elif ratio <= 0.50:
        return 'bassa'
    elif ratio <= 0.75:
        return 'limitata'
    else:
        return 'alta'
