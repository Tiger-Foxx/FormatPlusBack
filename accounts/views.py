# accounts/views.py
from venv import logger
from django.contrib.auth import authenticate
from rest_framework import viewsets, status, views
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.db.models import Q
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework.response import Response
from rest_framework import status


from .models import User, Sponsorship
from .serializers import *


class UserRegistrationView(views.APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        # Vérifier si un utilisateur avec ce numéro ou cet email existe déjà
        email = request.data.get('email', '').strip()
        phone_number = request.data.get('phone_number', '').strip()

        existing_user = User.objects.filter(
            Q(email=email) | Q(phone_number=phone_number),
            # is_active=False  # On ne vérifie que les comptes inactifs
        ).first()

        if existing_user:
            # Si un utilisateur inactif existe déjà, renvoyer ses données
            user_serializer = UserSerializer(existing_user)
            return Response({
                'message': 'Utilisateur déjà inscrit mais en attente de paiement.',
                'user': user_serializer.data
            }, status=status.HTTP_200_OK)

        # Sinon, créer un nouvel utilisateur
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            user_serializer = UserSerializer(user)
            return Response({
                'message': 'Inscription réussie, en attente de paiement.',
                'user': user_serializer.data
            }, status=status.HTTP_201_CREATED)
        logger.error("Erreurs de validation : %s", serializer.errors)  # Log des erreurs


        # En cas d'erreur de validation
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    
    
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['GET'])
    def me(self, request):
        serializer = DetailedUserSerializer(request.user, context={'request': request})
        response_data = serializer.data
        
        # Mise à jour du localStorage via le front-end
        return Response(response_data)
    def update(self, request, *args, **kwargs):
        # instance = self.get_object()
        # if instance.user.id != self.request.user.id:
        #     raise PermissionDenied("Vous n'êtes pas autorisé à modifier ce profil.")
        return super().update(request, *args, **kwargs)

    def get_serializer_class(self):
        if self.action == 'me':
            return DetailedUserSerializer
        return UserSerializer
    
class CustomTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        print("Données reçues pour le refresh:", request.data)  # Debugging
        return super().post(request, *args, **kwargs)





class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = authenticate(
                username=serializer.validated_data['username'],
                password=serializer.validated_data['password']
            )

            if user is not None:
                refresh = RefreshToken.for_user(user)
                return Response({
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                    'user': UserSerializer(user).data
                })
            return Response({'error': 'Identifiants invalides'},
                            status=status.HTTP_401_UNAUTHORIZED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    def post(self, request):
        try:
            refresh_token = request.data["refresh_token"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"message": "Déconnexion réussie"})
        except Exception:
            return Response({"error": "Token invalide"},
                            status=status.HTTP_400_BAD_REQUEST)