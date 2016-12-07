from menus.base import Menu, NavigationNode
from menus.menu_pool import menu_pool
from django.utils.translation import ugettext_lazy as _

class TripMenu(Menu):

    def get_nodes(self, request):
        N = NavigationNode
        nodes = [
            N('Prossima gita', "/trip/", id='next_trip'),
            N('Profilo utente', "/accounts/profile/", id='profile'),
            N('Aiuto', "/faq/", id='help'),
        ]
        if request.user.is_staff:
            nodes += self.get_admin_nodes()
        return nodes

    def get_admin_nodes(self):
        N = NavigationNode
        return [
            N('Credito online', "/balance/", id='balance'),
            N('Ricarica', "/balance/topup/", id='topup', parent_id='balance'),
            N('Riepilogo', "/balance/summary", id='summary', parent_id='balance'),
        ]

menu_pool.register_menu(TripMenu)
