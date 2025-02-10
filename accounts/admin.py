# accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Sponsorship, Withdrawal
from django.http import HttpResponse
import xlsxwriter
from io import BytesIO
from django.utils import timezone
from datetime import timedelta
from django.contrib import messages

class CustomUserAdmin(UserAdmin):
    list_display = ('nom', 'email', 'sponsor_code', 'wallet_balance',
                    'is_paid', 'telegram_group_joined', 'date_joined', 'is_active','username')
    list_filter = ('nom','is_paid', 'telegram_group_joined', 'date_joined', 'is_active')
    search_fields = ('nom', 'email', 'sponsor_code', 'phone_number')
    ordering = ('-date_joined',)
    
    # Ajouter is_paid et is_active aux champs modifiables directement dans la liste
    list_editable = ('is_paid', 'is_active')
    
    actions = ['export_active_users_excel', 'export_active_users_text', 'mark_users_active_paid']

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

    def export_active_users_excel(self, request, queryset):
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
            is_active=True,
            is_paid=True,
            date_joined__gte=time_threshold
        ).order_by('-date_joined')[:70]

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
    
    export_active_users_excel.short_description = "Exporter les utilisateurs ayant payés et inscrit il y a moins de 48h - en Excel"

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
    def export_active_users_text(self, request, queryset):
        # Calculer la date limite (48h)
        time_threshold = timezone.now() - timedelta(hours=48)

        # Filtrer les utilisateurs
        users = User.objects.filter(
            is_active=True,
            is_paid=True,
            date_joined__gte=time_threshold
        ).order_by('-date_joined')[:70]

        # Créer la chaîne de texte avec les emails séparés par des virgules
        emails = ' , '.join(user.email for user in users)

        # Créer la réponse HTTP avec le fichier texte
        response = HttpResponse(content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename=utilisateurs_inscrits.txt'
        response.write(emails)
        
        return response
    
    export_active_users_text.short_description = "Exporter les utilisateurs  ayant payés (48h) - en TXT"

class SponsorshipAdmin(admin.ModelAdmin):
    list_display = ('sponsor', 'sponsored_user', 'date_sponsored',
                    'commission_percentage', 'indirect_commission_percentage')
    list_filter = ('date_sponsored',)
    search_fields = ('sponsor__username', 'sponsored_user__username')
    date_hierarchy = 'date_sponsored'

admin.site.register(User, CustomUserAdmin)
admin.site.register(Sponsorship, SponsorshipAdmin)



@admin.register(Withdrawal)
class WithdrawalAdmin(admin.ModelAdmin):
    list_display = ['beneficiary_number', 'user', 'amount', 'country', 'operator', 'status', 'created_at']
    list_filter = ['status', 'created_at', 'country']
    search_fields = ['user__username', 'beneficiary_name', 'beneficiary_number', 'country', 'operator']
    
    actions = ['mark_as_processing', 'mark_as_completed', 'mark_as_rejected']

    def mark_as_processing(self, request, queryset):
        queryset.update(status='PROCESSING')
    mark_as_processing.short_description = "Mark selected withdrawals as Processing"

    def mark_as_completed(self, request, queryset):
        for withdrawal in queryset:
            withdrawal.status = 'COMPLETED'
            withdrawal.processed_at = timezone.now()
            withdrawal.save()
    mark_as_completed.short_description = "Mark selected withdrawals as Completed"

    def mark_as_rejected(self, request, queryset):
        for withdrawal in queryset:
            withdrawal.status = 'REJECTED'
            withdrawal.processed_at = timezone.now()
            withdrawal.save()
    mark_as_rejected.short_description = "Mark selected withdrawals as Rejected"