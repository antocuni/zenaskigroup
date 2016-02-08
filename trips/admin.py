import django.contrib.auth.admin as auth_admin
from django.contrib import admin
from django.contrib.auth.models import User, Group
from django.utils.translation import ugettext, ugettext_lazy as _
from trips import models

# modify the User admin to include our member info and exclude some fields we
# are not interested info (e.g., groups)
class MemberInline(admin.StackedInline):
    model = models.Member
    can_delete = False
    verbose_name_plural = 'Informazioni Zena'

# Define a "simplified" User admin
class UserAdmin(auth_admin.UserAdmin):

    list_display = ('username', 'email', 'first_name', 'last_name', 'balance',
                    'card_no', 'is_staff', 'trusted')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'email')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser',
                                       'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )

    def balance(self, obj):
        return obj.member.balance
    balance.short_description = 'Credito'

    def card_no(self, obj):
        return obj.member.card_no
    card_no.short_description = 'Numero tessera'

    def trusted(self, obj):
        return obj.member.trusted
    trusted.short_description = 'Fidato?'
    trusted.boolean = True

    inlines = (MemberInline, )

# Re-register UserAdmin
admin.site.unregister(auth_admin.User)
admin.site.register(User, UserAdmin)



class ParticipantInline(admin.TabularInline):
    model = models.Participant
    extra = 1

class TripAdmin(admin.ModelAdmin):
    inlines = [ParticipantInline]
    readonly_fields = ('sublist_table', 'poster_preview')



# Register your models here.
admin.site.register(models.Trip, TripAdmin)
admin.site.register(models.MoneyTransfer)
admin.site.register(models.JacketSubscribe)
