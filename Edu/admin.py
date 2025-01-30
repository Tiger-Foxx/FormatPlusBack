# Edu/admin.py
from django.contrib import admin
from .models import Formation, Inscription, Payment, TelegramSubscription

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
            'fields': ('duration', 'presentation_video', 'drive_link','presentation_video_link','category')
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
    search_fields = ('user__username', 'user__email', 'sponsor_code_used')
    date_hierarchy = 'date_inscription'

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('user', 'payment_type', 'amount', 'status', 
                   'payment_method', 'payment_date')
    list_filter = ('payment_type', 'status', 'payment_method', 'payment_date')
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
    list_display = ('user', 'subscription_date', 'is_active')
    list_filter = ('is_active', 'subscription_date')
    search_fields = ('user__username', 'user__email')
