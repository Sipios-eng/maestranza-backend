# backend/maestranza_project/urls.py

from django.contrib import admin
from django.urls import path, include
from rest_framework.authtoken.views import obtain_auth_token # Para obtener el token de autenticación

urlpatterns = [
    path('admin/', admin.site.urls), # Panel de administración de Django
    path('api/', include('inventory.urls')), # Incluye las URLs de nuestra API
    path('api-token-auth/', obtain_auth_token, name='api_token_auth'), # Endpoint para obtener el token
]
