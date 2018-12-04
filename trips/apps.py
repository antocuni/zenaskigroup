from django.apps import AppConfig


class TripsConfig(AppConfig):
    name = 'trips'
    verbose_name = "trips"

    def ready(self):
        from trips import paypal_view
        paypal_view.setup_signals()

