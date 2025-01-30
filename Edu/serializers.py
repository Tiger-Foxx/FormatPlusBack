from rest_framework import serializers
from validators import uuid

from accounts.models import Withdrawal

from .models import *

class FormationListSerializer(serializers.ModelSerializer):
    """Serializer pour la liste des formations (vue légère)"""
    class Meta:
        model = Formation
        fields = ['id', 'title', 'thumbnail', 'description', 'duration', 
                 'points', 'participants_number', 'notation', 'created_at','category']

class FormationDetailSerializer(serializers.ModelSerializer):
    """Serializer pour le détail d'une formation (vue complète)"""
    class Meta:
        model = Formation
        fields = '__all__'

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ('user', 'payment_type', 'amount', 'status', 'transaction_id', 'payment_method', 'payment_details')
        read_only_fields = ('payment_date', 'status')

    def create(self, validated_data):
        # Générer un ID de transaction unique
        validated_data['transaction_id'] = f"TRX-{uuid.uuid4().hex[:12].upper()}"
        return super().create(validated_data)

class InscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Inscription
        fields = ('id', 'amount_paid', 'payment_status', 'is_validated',
                 'sponsor_code_used')
        read_only_fields = ('payment_status', 'is_validated')

class TelegramSubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TelegramSubscription
        fields = ('id', 'subscription_date', 'is_active')
        read_only_fields = ('subscription_date',)
        
class WithdrawalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Withdrawal
        fields = ['id', 'amount', 'beneficiary_name', 'beneficiary_number', 'status', 'created_at']
        read_only_fields = ['status', 'created_at']