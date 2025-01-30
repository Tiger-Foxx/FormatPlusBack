# Edu/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser

from accounts.models import Withdrawal
from .models import *
from .serializers import (FormationDetailSerializer, FormationListSerializer,  PaymentSerializer,
                          InscriptionSerializer, TelegramSubscriptionSerializer, WithdrawalSerializer)
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.conf import settings
import hmac
import hashlib

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import AllowAny  # Changé de IsAuthenticated à AllowAny
from .models import Payment, User
from .serializers import PaymentSerializer
import logging

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import requests
logger = logging.getLogger(__name__)


class FormationViewSet(viewsets.ModelViewSet):
    queryset = Formation.objects.all()
    permission_classes = [AllowAny]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return FormationDetailSerializer
        return FormationListSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return []

    def get_queryset(self):
        queryset = Formation.objects.all()
        if self.action == 'list':
            # Trier par points et date de création pour avoir les plus populaires
            queryset = queryset.order_by('-points', '-created_at')
        return queryset

    def list(self, request, *args, **kwargs):
        # Permet de limiter le nombre de formations si demandé
        limit = request.query_params.get('limit', None)
        queryset = self.get_queryset()
        
        if limit:
            queryset = queryset[:int(limit)]
            
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)




class PaymentViewSet(ModelViewSet):
    serializer_class = PaymentSerializer
    permission_classes = [AllowAny]  # Modifié car l'utilisateur n'est pas encore authentifié

    def get_queryset(self):
        # Si l'utilisateur est authentifié, retourne ses paiements
        if self.request.user.is_authenticated:
            return Payment.objects.filter(user=self.request.user)
        return Payment.objects.none()

    @action(detail=False, methods=['POST'], url_path='verify')
    def verify_payment(self, request):
        try:
            # Récupération des données
            user_id = request.data.get('user_id')
            transaction_id = request.data.get('transaction_id')
            provider = request.data.get('provider')
            payment_status = request.data.get('status')

            if not all([user_id, transaction_id, provider, payment_status]):
                return Response({
                    'success': False,
                    'message': 'Données de vérification incomplètes'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Récupération de l'utilisateur
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return Response({
                    'success': False,
                    'message': 'Utilisateur non trouvé'
                }, status=status.HTTP_404_NOT_FOUND)

            # Vérification si le paiement existe déjà
            existing_payment = Payment.objects.filter(
                transaction_id=transaction_id,
                user=user
            ).first()

            if existing_payment:
                return Response({
                    'success': False,
                    'message': 'Ce paiement a déjà été traité'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Vérification du statut selon le provider
            payment_verified = False
            if provider == 'moneroo':
                payment_verified = payment_status == 'completed'
            elif provider == 'moneyfusion':
                payment_verified = payment_status == 'paid'
            else:
                return Response({
                    'success': False,
                    'message': 'Provider de paiement non reconnu'
                }, status=status.HTTP_400_BAD_REQUEST)

            if payment_verified:
                # Création du paiement
                payment = Payment.objects.create(
                    user=user,
                    amount=1000,  # Montant fixe pour l'inscription
                    transaction_id=transaction_id,
                    provider=provider,
                    status='completed'
                )

                # Activation du compte utilisateur
                user.is_active = True
                user.is_paid = True
                user.save()

                # Gestion des commissions de parrainage
                sponsorship = user.sponsored_by.first()
                if sponsorship:
                    sponsor = sponsorship.sponsor
                    commission = payment.amount * (sponsorship.commission_percentage / 100)
                    sponsor.wallet_balance += commission
                    sponsor.save()

                logger.info(f"Paiement vérifié et compte activé pour l'utilisateur {user_id}")
                
                return Response({
                    'success': True,
                    'message': 'Votre compte a été activé avec succès !'
                }, status=status.HTTP_200_OK)
            else:
                logger.warning(f"Échec de la vérification du paiement pour l'utilisateur {user_id}")
                return Response({
                    'success': False,
                    'message': 'Le paiement n\'a pas pu être vérifié'
                }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f"Erreur lors de la vérification du paiement: {str(e)}")
            return Response({
                'success': False,
                'message': 'Une erreur est survenue lors de la vérification'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)





class PaymentWebhookView(APIView):
    permission_classes = [AllowAny]  # Les webhooks doivent être accessibles sans auth

    def verify_signature(self, request):
        """Vérifie la signature du webhook"""
        received_signature = request.headers.get('X-Payment-Signature')
        if not received_signature:
            return False

        # Calculer la signature avec votre clé secrète
        payload = request.body
        secret = settings.PAYMENT_WEBHOOK_SECRET
        expected_signature = hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(received_signature, expected_signature)

    def post(self, request):
        # Vérifier la signature
        if not self.verify_signature(request):
            return Response(
                {'error': 'Invalid signature'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Traiter la notification
        payment_data = request.data
        transaction_id = payment_data.get('transaction_id')

        try:
            payment = Payment.objects.get(transaction_id=transaction_id)

            if payment_data['status'] == 'success':
                payment.status = 'completed'
                payment.save()

                # Mettre à jour le statut de l'utilisateur si c'est un paiement d'inscription
                if payment.payment_type == 'inscription':
                    user = payment.user
                    user.is_paid = True
                    user.save()

                    # Traiter les commissions de parrainage
                    sponsorship = user.sponsored_by.first()
                    if sponsorship:
                        sponsor = sponsorship.sponsor
                        commission = payment.amount * (sponsorship.commission_percentage / 100)
                        sponsor.wallet_balance += commission
                        sponsor.save()

            elif payment_data['status'] == 'failed':
                payment.status = 'failed'
                payment.save()

            return Response({'status': 'processed'})

        except Payment.DoesNotExist:
            return Response(
                {'error': 'Payment not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class VerifyAndCreatePaymentView(APIView):
    def post(self, request):
        """
        Vérifier le statut du paiement auprès de Moneroo et créer un objet Payment.
        """
        transaction_id = request.data.get('transaction_id')  # ID de transaction Moneroo
        user_id = request.data.get('user_id')  # ID de l'utilisateur
        
        if not transaction_id or not user_id:
            return Response({"error": "transaction_id et user_id sont requis."}, status=status.HTTP_400_BAD_REQUEST)

        # Vérifier le statut du paiement auprès de Moneroo
        moneroo_url = f"https://api.moneroo.io/v1/payments/{transaction_id}"
        headers = {
            "Authorization": "Bearer YOUR_SECRET_KEY",
            "Accept": "application/json",
        }
        response = requests.get(moneroo_url, headers=headers)

        if response.status_code != 200:
            return Response({"error": "Échec de la vérification du paiement."}, status=status.HTTP_400_BAD_REQUEST)

        payment_data = response.json()
        payment_status = payment_data.get("status")
        payment_method = payment_data.get("method")
        payment_details = payment_data.get("details", {})

        # Créer un objet Payment uniquement si le paiement est "completed"
        if payment_status == "completed":
            payment = Payment.objects.create(
                user_id=user_id,
                payment_type="inscription",
                amount=1000,  # Montant fixe pour l'inscription
                status="completed",
                transaction_id=transaction_id,
                payment_method=payment_method,
                payment_details=payment_details,
            )
            serializer = PaymentSerializer(payment)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response({"error": "Le paiement n'est pas terminé."}, status=status.HTTP_400_BAD_REQUEST)
    


class WithdrawalViewSet(viewsets.ModelViewSet):
    serializer_class = WithdrawalSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Withdrawal.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)