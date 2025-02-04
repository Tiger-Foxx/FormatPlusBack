# Edu/admin.py
from django.contrib import admin
from .models import Formation, Inscription, Payment, TelegramSubscription
from django.http import HttpResponse
import xlsxwriter
from io import BytesIO
from django.utils import timezone
from datetime import timedelta
from django.contrib import messages

@admin.register(Formation)
class FormationAdmin(admin.ModelAdmin):
    list_display = ('title', 'points', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('title', 'description')
    fieldsets = (
        ('Informations principales', {
            'fields': ('title', 'thumbnail', 'description')
        }),
        ('Détails de la formation', {
            'fields': ('duration', 'presentation_video', 'drive_link', 'presentation_video_link', 'category')
        }),
        ('Statistiques', {
            'fields': ('points',)
        }),
    )

@admin.register(Inscription)
class InscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount_paid', 'payment_status', 'is_validated', 
                   'sponsor_code_used', 'date_inscription')
    list_filter = ('payment_status', 'is_validated', 'date_inscription')
    list_editable = ('payment_status', 'is_validated')  # Permet la modification directe
    search_fields = ('user__username', 'user__email', 'sponsor_code_used')
    date_hierarchy = 'date_inscription'
    actions = ['export_recent_inscriptions', 'validate_recent_inscriptions']

    def export_recent_inscriptions(self, request, queryset):
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet()

        # En-têtes
        headers = ['Email', 'Date d\'inscription', 'Montant payé', 'Code parrain', 'Statut paiement']
        for col, header in enumerate(headers):
            worksheet.write(0, col, header)

        # Filtrer les inscriptions des dernières 48h
        time_threshold = timezone.now() - timedelta(hours=48)
        inscriptions = Inscription.objects.filter(
            date_inscription__gte=time_threshold,
        ).select_related('user')

        # Écrire les données
        for row, inscription in enumerate(inscriptions, start=1):
            worksheet.write(row, 0, inscription.user.email)
            worksheet.write(row, 1, inscription.date_inscription.strftime('%Y-%m-%d %H:%M:%S'))
            worksheet.write(row, 2, str(inscription.amount_paid))
            worksheet.write(row, 3, inscription.sponsor_code_used)
            worksheet.write(row, 4, inscription.payment_status)

        workbook.close()
        output.seek(0)
        
        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=inscriptions_recentes.xlsx'
        return response
    
    export_recent_inscriptions.short_description = "Exporter les inscriptions récentes (48h) en Excel"

    def validate_recent_inscriptions(self, request, queryset):
        time_threshold = timezone.now() - timedelta(hours=48)
        updated = Inscription.objects.filter(
            date_inscription__gte=time_threshold
        ).update(is_validated=True, payment_status='COMPLETED')
        
        self.message_user(
            request,
            f"{updated} inscriptions ont été validées.",
            messages.SUCCESS
        )
    
    validate_recent_inscriptions.short_description = "Valider les inscriptions récentes (48h)"
    
    def export_inactive_users_text(self, request, queryset):
        # Calculer la date limite (48h)
        time_threshold = timezone.now() - timedelta(hours=48)

        # Filtrer les utilisateurs
        inscriptions = Inscription.objects.filter(
            date_inscription__gte=time_threshold,
        )

        # Créer la chaîne de texte avec les emails séparés par des virgules
        emails = ' , '.join(inscription.email for inscription in inscriptions)

        # Créer la réponse HTTP avec le fichier texte
        response = HttpResponse(content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename=utilisateurs_inscrits.txt'
        response.write(emails)
        
        return response
    
    export_inactive_users_text.short_description = "Exporter les utilisateurs  ayant payés (48h) - en TXT"

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('user', 'payment_type', 'amount', 'status', 
                   'payment_method', 'payment_date')
    list_filter = ('payment_type', 'status', 'payment_method', 'payment_date')
    list_editable = ('status',)  # Permet la modification directe du statut
    search_fields = ('user__username', 'transaction_id')
    date_hierarchy = 'payment_date'
    fieldsets = (
        ('Informations de paiement', {
            'fields': ('user', 'payment_type', 'amount', 'payment_method')
        }),
        ('Statut et transaction', {
            'fields': ('status', 'transaction_id')
        }),
        ('Détails supplémentaires', {
            'fields': ('payment_details',),
            'classes': ('collapse',)
        }),
    )

@admin.register(TelegramSubscription)
class TelegramSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'is_active')
    list_filter = ('is_active', 'created_at')
    list_editable = ('is_active',)  # Permet la modification directe
    search_fields = ('user__username', 'user__email')
    actions = ['export_recent_subs', 'activate_recent_subs']

    def export_recent_subs(self, request, queryset):
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet()

        # En-têtes
        headers = ['Email', 'Date d\'inscription', 'Statut']
        for col, header in enumerate(headers):
            worksheet.write(0, col, header)

        # Filtrer les souscriptions des dernières 48h
        time_threshold = timezone.now() - timedelta(hours=48)
        subscriptions = TelegramSubscription.objects.filter(
            created_at__gte=time_threshold,
            is_active=False
        ).select_related('user')

        # Écrire les données
        for row, sub in enumerate(subscriptions, start=1):
            worksheet.write(row, 0, sub.user.email)
            worksheet.write(row, 1, sub.created_at.strftime('%Y-%m-%d %H:%M:%S'))
            worksheet.write(row, 2, 'Inactif')

        workbook.close()
        output.seek(0)
        
        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=souscriptions_telegram_recentes.xlsx'
        return response
    
    export_recent_subs.short_description = "Exporter les souscriptions Telegram récentes (48h)"

    def activate_recent_subs(self, request, queryset):
        time_threshold = timezone.now() - timedelta(hours=48)
        updated = TelegramSubscription.objects.filter(
            created_at__gte=time_threshold
        ).update(is_active=True)
        
        self.message_user(
            request,
            f"{updated} souscriptions Telegram ont été activées.",
            messages.SUCCESS
        )
    
    activate_recent_subs.short_description = "Activer les souscriptions récentes (48h)"