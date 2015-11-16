from menus.base import Menu, NavigationNode
from menus.menu_pool import menu_pool
from django.utils.translation import ugettext_lazy as _

class TestMenu(Menu):

    def get_nodes(self, request):
        nodes = []
        n = NavigationNode(_('Prossima gita'), "/trip/", 1)
        n2 = NavigationNode(_('Profilo utente'), "/accounts/profile/", 2)
        n3 = NavigationNode(_('Aiuto'), "/faq/", 3)
        n4 = NavigationNode(_('Ricarica'), "/topup/", 4)
        nodes.append(n)
        nodes.append(n2)
        nodes.append(n3)
        if request.user.is_staff:
            nodes.append(n4)
        return nodes

menu_pool.register_menu(TestMenu)
