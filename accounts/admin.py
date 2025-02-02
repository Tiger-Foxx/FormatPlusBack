# accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Sponsorship
from django.http import HttpResponse
import xlsxwriter
from io import BytesIO
from django.utils import timezone
from datetime import timedelta
from django.contrib import messages

class CustomUserAdmin(UserAdmin):
    list_display = ('nom', 'email', 'sponsor_code', 'wallet_balance',
                    'is_paid', 'telegram_group_joined', 'date_joined', 'is_active')
    list_filter = ('nom','is_paid', 'telegram_group_joined', 'date_joined', 'is_active')
    search_fields = ('nom', 'email', 'sponsor_code', 'phone_number')
    ordering = ('-date_joined',)
    
    # Ajouter is_paid et is_active aux champs modifiables directement dans la liste
    list_editable = ('is_paid', 'is_active')
    
    actions = ['export_inactive_users_excel', 'mark_users_active_paid']

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Informations personnelles', {'fields': ('email', 'phone_number','nom')}),
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

    def export_inactive_users_excel(self, request, queryset):
        # Créer un buffer pour le fichier Excel
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet()

        # Définir les en-têtes
        headers = ['Email', 'Date d\'inscription']
        for col, header in enumerate(headers):
            worksheet.write(0, col, header)

        # Calculer la date limite (48h)
        time_threshold = timezone.now() - timedelta(hours=48)

        # Filtrer les utilisateurs
        users = User.objects.filter(
            is_active=False,
            is_paid=False,
            date_joined__gte=time_threshold
        )

        # Écrire les données
        for row, user in enumerate(users, start=1):
            worksheet.write(row, 0, user.email)
            worksheet.write(row, 1, user.date_joined.strftime('%Y-%m-%d %H:%M:%S'))

        workbook.close()
        
        # Configurer la réponse HTTP
        output.seek(0)
        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=utilisateurs_inactifs.xlsx'
        
        return response
    
    export_inactive_users_excel.short_description = "Exporter les utilisateurs inactifs (48h) en Excel"

    def mark_users_active_paid(self, request, queryset):
        # Calculer la date limite (48h)
        time_threshold = timezone.now() - timedelta(hours=48)
        
        # Filtrer et mettre à jour les utilisateurs
        updated = User.objects.filter(
            date_joined__gte=time_threshold
        ).update(is_active=True, is_paid=True)
        
        self.message_user(
            request,
            f"{updated} utilisateurs ont été marqués comme actifs et payés.",
            messages.SUCCESS
        )
    
    mark_users_active_paid.short_description = "Marquer comme actif et payé (utilisateurs < 48h)"

class SponsorshipAdmin(admin.ModelAdmin):
    list_display = ('sponsor', 'sponsored_user', 'date_sponsored',
                    'commission_percentage', 'indirect_commission_percentage')
    list_filter = ('date_sponsored',)
    search_fields = ('sponsor__username', 'sponsored_user__username')
    date_hierarchy = 'date_sponsored'

admin.site.register(User, CustomUserAdmin)
admin.site.register(Sponsorship, SponsorshipAdmin)