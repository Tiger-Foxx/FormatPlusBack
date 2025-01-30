"""
URL configuration for EduDriveBack project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


from EduDriveBack import settings
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from accounts.views import *
from Edu.views import *
from accounts.models import *
from Edu.models import *
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

router = DefaultRouter()
router.register('users', UserViewSet,'users')
router.register('formations', FormationViewSet,'formations')
router.register('payments', PaymentViewSet, basename='payment')
router.register('withdrawals', WithdrawalViewSet, 'withdrawals')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('register/', UserRegistrationView.as_view(), name='user-registration'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('webhook/payment/', PaymentWebhookView.as_view(), name='payment-webhook'),
    # Inclusion des URLs du router
     path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),  # Route pour récupérer un access et refresh token
path('token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),    path('', include(router.urls)),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
