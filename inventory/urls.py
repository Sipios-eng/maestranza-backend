# backend/inventory/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserProfileViewSet, SupplierViewSet, CategoryViewSet, TagViewSet,
    InventoryItemViewSet, InventoryMovementViewSet, KitViewSet, PurchaseRecordViewSet # <-- Importar PurchaseRecordViewSet
)
from .reports_views import InventoryReportView

router = DefaultRouter()
router.register(r'users', UserProfileViewSet)
router.register(r'suppliers', SupplierViewSet)
router.register(r'categories', CategoryViewSet)
router.register(r'tags', TagViewSet)
router.register(r'inventory', InventoryItemViewSet)
router.register(r'movements', InventoryMovementViewSet)
router.register(r'kits', KitViewSet)
router.register(r'purchase-records', PurchaseRecordViewSet) # <-- NUEVA RUTA para Historial de Precios

urlpatterns = [
    path('', include(router.urls)),
    path('reports/', InventoryReportView.as_view(), name='inventory-reports'),
]
