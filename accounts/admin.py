# accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Sponsorship


class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'sponsor_code', 'wallet_balance',
                    'is_paid', 'telegram_group_joined', 'date_joined')
    list_filter = ('is_paid', 'telegram_group_joined', 'date_joined')
    search_fields = ('username', 'email', 'sponsor_code', 'phone_number')
    ordering = ('-date_joined',)

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Informations personnelles', {'fields': ('email', 'phone_number')}),
        ('Parrainage & Paiement', {
            'fields': ('sponsor_code', 'wallet_balance', 'is_paid', 'telegram_group_joined'),
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'phone_number', 'password1', 'password2'),
        }),
    )


class SponsorshipAdmin(admin.ModelAdmin):
    list_display = ('sponsor', 'sponsored_user', 'date_sponsored',
                    'commission_percentage', 'indirect_commission_percentage')
    list_filter = ('date_sponsored',)
    search_fields = ('sponsor__username', 'sponsored_user__username')
    date_hierarchy = 'date_sponsored'


admin.site.register(User, CustomUserAdmin)
admin.site.register(Sponsorship, SponsorshipAdmin)