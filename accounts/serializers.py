# accounts/serializers.py
from decimal import Decimal
from rest_framework import serializers

from EduDriveBack.settings import FRONT_END_LINK
from .models import User, Sponsorship


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'nom', 'email', 'phone_number', 'sponsor_code',
                  'wallet_balance', 'is_paid', 'telegram_group_joined')
        read_only_fields = ('wallet_balance', 'sponsor_code', 'is_paid',
                            'telegram_group_joined')

# accounts/serializers.py
class DetailedUserSerializer(serializers.ModelSerializer):
    direct_referrals_count = serializers.SerializerMethodField()
    indirect_referrals_count = serializers.SerializerMethodField()
    referral_link = serializers.SerializerMethodField()
    recent_referrals = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ('id', 'nom', 'email', 'phone_number', 'sponsor_code', 
                 'wallet_balance', 'is_paid', 'telegram_group_joined',
                 'direct_referrals_count', 'indirect_referrals_count',
                 'referral_link', 'recent_referrals')
        read_only_fields = ('wallet_balance', 'sponsor_code', 'is_paid',
                          'telegram_group_joined')

    def get_direct_referrals_count(self, obj):
        return Sponsorship.objects.filter(sponsor=obj).count()
        
    def get_indirect_referrals_count(self, obj):
        # D'abord, obtenir tous les utilisateurs parrainés directement
        direct_sponsored_users = User.objects.filter(
            sponsored_by__sponsor=obj
        )
        # Ensuite, compter les parrainages de ces utilisateurs
        return Sponsorship.objects.filter(sponsor__in=direct_sponsored_users).count()
        
    def get_referral_link(self, obj):
        request = self.context.get('request')
        if request is None:
            return None
        return f"{FRONT_END_LINK}//signup/{obj.sponsor_code}"
        
    def get_recent_referrals(self, obj):
        referrals = []
        
        # Parrainages directs
        direct_sponsorships = (
            Sponsorship.objects.filter(sponsor=obj)
            .select_related('sponsored_user')
            .order_by('-date_sponsored')
        )
        
        for sponsorship in direct_sponsorships:
            referrals.append({
                'name': sponsorship.sponsored_user.nom,
                'date': sponsorship.date_sponsored,
                'amount': float(sponsorship.sponsored_user.wallet_balance * Decimal('0.4')),
                'level': 'direct'
            })
        
        # Parrainages indirects
        direct_sponsored_users = User.objects.filter(
            sponsored_by__sponsor=obj
        )
        
        indirect_sponsorships = (
            Sponsorship.objects.filter(sponsor__in=direct_sponsored_users)
            .select_related('sponsored_user', 'sponsor')
            .order_by('-date_sponsored')
        )
        
        for sponsorship in indirect_sponsorships:
            referrals.append({
                'name': sponsorship.sponsored_user.nom,
                'date': sponsorship.date_sponsored,
                'amount': float(sponsorship.sponsored_user.wallet_balance * Decimal('0.1')),
                'level': 'indirect'
            })
        
        # Trier par date décroissante
        return sorted(referrals, key=lambda x: x['date'], reverse=True)
    
class UserRegistrationSerializer(serializers.ModelSerializer):
    sponsor_code_input = serializers.CharField(write_only=True, required=False, allow_blank=True, allow_null=True)
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('nom', 'email', 'phone_number', 'password',
                  'sponsor_code_input')

    def validate_sponsor_code_input(self, value):
        if value and not User.objects.filter(sponsor_code=value).exists():
            raise serializers.ValidationError("Code de parrainage invalide")
        return value

    def create(self, validated_data):
        sponsor_code = validated_data.pop('sponsor_code_input', None)
        password = validated_data.pop('password')

        # Création de l'utilisateur
        user = User(**validated_data)
        user.set_password(password)
        user.is_active = False  # Compte inactif jusqu'à ce que le paiement soit effectué
        user.save()

        # Créer la relation de parrainage si un code est fourni
        if sponsor_code:
            sponsor = User.objects.get(sponsor_code=sponsor_code)
            Sponsorship.objects.create(sponsor=sponsor, sponsored_user=user)

        return user

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(style={'input_type': 'password'})