# Edu/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser

from accounts.models import Withdrawal
from .models import *
from .serializers import (FooterInfoSerializer, FormationDetailSerializer, FormationListSerializer,  PaymentSerializer,
                          InscriptionSerializer, TelegramSubscriptionSerializer)
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
                    'success': True,
                    'message': 'Ce paiement a déjà été traité'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Vérification du statut selon le provider
            payment_verified = False
            if provider == 'campay':
                payment_verified = (payment_status == 'success' or payment_status =="pending")
            elif provider == 'moneyfusion':
                payment_verified = (payment_status == 'success' or payment_status =="pending" or "paid" )
            else:
                return Response({
                    'success': False,
                    'message': 'Provider de paiement non reconnu'
                }, status=status.HTTP_400_BAD_REQUEST)

            if payment_verified:
                # Création du paiement
                payment = Payment.objects.create(
                    user=user,
                    amount=3500,  # Montant fixe pour l'inscription
                    transaction_id=transaction_id,
                    payment_method=provider,
                    status='completed'
                )
                
                # Enregistrement d'un objet inscription :
                inscription = Inscription.objects.create(
                    user=user,
                    amount_paid=3500,
                    payment_status='completed',
                    is_validated=True,
                    sponsor_code_used='',
                    email=user.email
                    
                )
                
                

                # Activation du compte utilisateur
                user.is_active = True
                user.is_paid = True
                user.save()

                # Gestion des commissions de parrainage
                # Gestion des commissions de parrainage
                # Gestion des commissions de parrainage
                sponsorship = user.sponsored_by.first()
                if sponsorship:
                    sponsor = sponsorship.sponsor
                    commission = payment.amount * (sponsorship.commission_percentage / 100)
                    sponsor.wallet_balance += commission
                    sponsor.save()

                    # Gestion des commissions de parrainage indirect
                    try:
                        indirect_sponsorship = sponsor.sponsored_by.first()
                        if indirect_sponsorship:
                            indirect_sponsor = indirect_sponsorship.sponsor
                            indirect_commission = payment.amount * (sponsorship.indirect_commission_percentage / 100)
                            indirect_sponsor.wallet_balance += indirect_commission
                            indirect_sponsor.save()
                            
                            # Gestion des commissions de parrainage indirect indirect
                            try:
                                indirect_indirect_sponsorship = indirect_sponsor.sponsored_by.first()
                                if indirect_indirect_sponsorship:
                                    indirect_indirect_sponsor = indirect_indirect_sponsorship.sponsor
                                    indirect_indirect_commission = payment.amount * (sponsorship.indirect_indirect_commission_percentage / 100)
                                    indirect_indirect_sponsor.wallet_balance += indirect_indirect_commission
                                    indirect_indirect_sponsor.save()
                            except Exception as e:
                                # Gérer l'erreur ou simplement passer si aucun parrain indirect indirect n'existe
                                pass
                    except Exception as e:
                        # Gérer l'erreur ou simplement passer si aucun parrain indirect n'existe
                        pass

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
    @action(detail=False, methods=['POST'], url_path='verify-telegram')
    def verify_telegram_payment(self, request):
        try:
            # Récupération des données
            user_id = request.data.get('user_id')
            transaction_id = request.data.get('transaction_id')
            provider = request.data.get('provider')
            payment_status = request.data.get('status')
            telegram_phone = request.data.get('telegram_phone')
            telegram_username = request.data.get('telegram_username')

            if not all([user_id, transaction_id, provider, payment_status, telegram_phone]):
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
                    'success': True,
                    'message': 'Ce paiement a déjà été traité'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Vérification du statut selon le provider
            payment_verified = False
            if provider == 'campay':
                payment_verified = (payment_status == 'success' or payment_status =="pending")
            elif provider == 'moneyfusion':
                payment_verified = (payment_status == 'success' or payment_status =="pending" or payment_status=="paid")
            else:
                return Response({
                    'success': False,
                    'message': 'Provider de paiement non reconnu'
                }, status=status.HTTP_400_BAD_REQUEST)

            if payment_verified:
                # Création du paiement
                payment = Payment.objects.create(
                    user=user,
                    amount=10000,  # Montant fixe pour la souscription Telegram
                    transaction_id=transaction_id,
                    payment_method=provider,
                    status='completed',
                    payment_type='telegram'  # Nouveau type de paiement
                )
                user.updateTelegramGroupJoined()
                # Création de la souscription Telegram
                if telegram_username :
                    telegram_subscription = TelegramSubscription.objects.create(
                        user=user,
                        phone_number=telegram_phone,
                        username=telegram_username,
                        payment=payment
                    )
                else :
                     telegram_subscription = TelegramSubscription.objects.create(
                        user=user,
                        phone_number=telegram_phone,
                        payment=payment
                    )

                logger.info(f"Souscription Telegram créée pour l'utilisateur {user_id}")

                return Response({
                    'success': True,
                    'message': 'Votre souscription au canal Telegram a été confirmée !',
                    'subscription': TelegramSubscriptionSerializer(telegram_subscription).data
                }, status=status.HTTP_200_OK)
            else:
                logger.warning(f"Échec de la vérification du paiement Telegram pour l'utilisateur {user_id}")
                return Response({
                    'success': False,
                    'message': 'Le paiement n\'a pas pu être vérifié'
                }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f"Erreur lors de la vérification du paiement Telegram: {str(e)}")
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
        Vérifier le statut du paiement auprès de campay et créer un objet Payment.
        """
        transaction_id = request.data.get('transaction_id')  # ID de transaction campay
        user_id = request.data.get('user_id')  # ID de l'utilisateur
        
        if not transaction_id or not user_id:
            return Response({"error": "transaction_id et user_id sont requis."}, status=status.HTTP_400_BAD_REQUEST)

        # Vérifier le statut du paiement auprès de campay
        campay_url = f"https://api.campay.io/v1/payments/{transaction_id}"
        headers = {
            "Authorization": "Bearer YOUR_SECRET_KEY",
            "Accept": "application/json",
        }
        response = requests.get(campay_url, headers=headers)

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
    


class FooterInfoViewSet(viewsets.ModelViewSet):
    queryset = FooterInfo.objects.all()
    serializer_class = FooterInfoSerializer
    permission_classes = [AllowAny]

