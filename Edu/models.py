# Edu/models.py
import random
from django.db import models
from accounts.models import User

# Edu/models.py

from django.db import models

import random

from django.conf import settings
from django.db import models

class Formation(models.Model):
    title = models.CharField(max_length=200)
    thumbnail = models.ImageField(upload_to='formations/thumbnails/')
    description = models.TextField(blank=True, null=True)
    duration = models.IntegerField(null=True, blank=True, default=6)
    presentation_video = models.FileField(
        upload_to='formations/videos/',
        blank=True,
        null=True
    )
    CATEGORY_CHOICES = [
        ('marketing', 'Marketing'),
        ('development', 'Développement Personnel'),
        ('business', 'Business'),
        ('sales', 'Ventes'),
        ('tech', 'Technologie'),
        ('other', 'Autres'),
    ]
    category = models.CharField(
        max_length=60,
        choices=CATEGORY_CHOICES,
        default='other'
    )
    presentation_video_link = models.URLField(blank=True, null=True)
    drive_link = models.URLField()
    points = models.IntegerField(default=40)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notions = models.TextField(blank=True, null=True)
    participants_number = models.IntegerField(null=True, blank=True, default=2153)
    notation = models.FloatField(null=True, blank=True, default=4.5)

    def save(self, *args, **kwargs):
        # Génère des statistiques aléatoires si c'est une nouvelle formation
        if not self.pk:  # Si c'est une nouvelle formation
            self.notation = round(random.uniform(4.0, 5.0), 1)
            self.participants_number = random.randint(2150, 3250)
        
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-points', '-created_at']


class Inscription(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('completed', 'Complété'),
        ('failed', 'Échoué'),
    ]

    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='inscription'
    )
    email=models.EmailField(blank=True, null=True)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending'
    )
    is_validated = models.BooleanField(default=False)
    sponsor_code_used = models.CharField(max_length=12)
    date_inscription = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.email=self.user.email
        if self.payment_status == 'completed':
            self.is_validated = True
        super().save(*args, **kwargs)
    def __str__(self):
        return f"Inscription de {self.user.username}"

class Payment(models.Model):
    PAYMENT_TYPES = [
        ('inscription', 'Inscription'),
        ('telegram', 'Groupe Telegram'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('completed', 'Complété'),
        ('failed', 'Échoué'),
    ]

    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='payments'
    )
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending'
    )
    transaction_id = models.CharField(max_length=100, unique=True)
    payment_date = models.DateTimeField(auto_now_add=True)
    payment_method = models.CharField(max_length=50)
    payment_details = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"Paiement de {self.user.username} - {self.payment_type}"

from django.contrib.auth import get_user_model

User = get_user_model()

class TelegramSubscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='telegram_subscriptions')
    phone_number = models.CharField(max_length=20)
    username = models.CharField(max_length=100, null=True, blank=True)
    payment = models.OneToOneField('Payment', on_delete=models.CASCADE, related_name='telegram_subscription')
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Subscription for {self.user.email} - {self.phone_number}"





