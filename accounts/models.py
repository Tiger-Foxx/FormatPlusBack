# accounts/models.py
import string
import random
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator

class User(AbstractUser):
    email = models.EmailField(unique=True)  # Champ email unique
    phone_number = models.CharField(max_length=20)
    sponsor_code = models.CharField(max_length=12, blank=True,null=True)
    nom=models.CharField(max_length=300)
    wallet_balance = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    is_paid = models.BooleanField(default=False)
    telegram_group_joined = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    is_active=models.BooleanField(default=False)

    # Indiquer que l'email est utilisé comme username
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []  # Aucun champ supplémentaire obligatoire

    def save(self, *args, **kwargs):
        if not self.sponsor_code or self.sponsor_code=='':
            # Générer un code de parrainage aléatoire
            chars = string.ascii_uppercase + string.digits
            while True:
                code = ''.join(random.choices(chars, k=12))
                if not User.objects.filter(sponsor_code=code).exists():
                    self.sponsor_code = code
                    break
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.email} - {self.sponsor_code}"

class Sponsorship(models.Model):
    sponsor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sponsorships_given'
    )
    sponsored_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sponsored_by'
    )
    date_sponsored = models.DateTimeField(auto_now_add=True)
    commission_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=40.00
    )
    indirect_commission_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=10.00
    )

    class Meta:
        unique_together = ['sponsor', 'sponsored_user']

    def __str__(self):
        return f"{self.sponsor.username} parraine {self.sponsored_user.username}"


from decimal import Decimal

class Withdrawal(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'En attente'),
        ('PROCESSING', 'En cours de traitement'),
        ('COMPLETED', 'Complété'),
        ('REJECTED', 'Rejeté')
    ]
    
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='withdrawals')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    beneficiary_name = models.CharField(max_length=255)
    beneficiary_number = models.CharField(max_length=20)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if self._state.adding:  # Si c'est une nouvelle création
            if self.amount > self.user.wallet_balance * Decimal('0.98'):
                raise ValueError("Le montant demandé dépasse le maximum autorisé")
            self.user.wallet_balance -= self.amount
            self.user.save()
        super().save(*args, **kwargs)