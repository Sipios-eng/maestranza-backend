# backend/inventory/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserProfileViewSet, SupplierViewSet, CategoryViewSet, TagViewSet,
    InventoryItemViewSet, InventoryMovementViewSet, KitViewSet
)

# Crea un router y registra nuestros ViewSets con él.
router = DefaultRouter()
router.register(r'users', UserProfileViewSet)
router.register(r'suppliers', SupplierViewSet)
router.register(r'categories', CategoryViewSet)
router.register(r'tags', TagViewSet)
router.register(r'inventory', InventoryItemViewSet) # Endpoint será /api/inventory/
router.register(r'movements', InventoryMovementViewSet)
router.register(r'kits', KitViewSet)

# Las URLs de la API ahora son determinadas automáticamente por el router.
urlpatterns = [
    path('', include(router.urls)),
]
