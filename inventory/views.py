# backend/inventory/views.py

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated # Permiso por defecto de DRF
from .models import UserProfile, Supplier, Category, Tag, InventoryItem, InventoryMovement, Kit
from .serializers import (
    UserProfileSerializer, SupplierSerializer, CategorySerializer, TagSerializer,
    InventoryItemSerializer, InventoryMovementSerializer, KitSerializer
)
from .permissions import IsAdminOrGestorInventario, IsAdminOrGestorInventarioOrLogistica, IsAdminOrReadOnly # Importa los permisos personalizados

class UserProfileViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint que permite a los usuarios ser vistos.
    Solo permite lectura para que los roles no puedan ser modificados fácilmente.
    La creación y modificación de usuarios se haría a través del admin o un endpoint dedicado de registro.
    """
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated] # Solo usuarios autenticados pueden ver perfiles

class SupplierViewSet(viewsets.ModelViewSet):
    """
    API endpoint que permite a los proveedores ser vistos o editados.
    """
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = [IsAdminOrGestorInventario] # ADMIN o GESTOR_INV pueden modificar, todos autenticados pueden ver

class CategoryViewSet(viewsets.ModelViewSet):
    """
    API endpoint que permite a las categorías ser vistas o editadas.
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrGestorInventario]

class TagViewSet(viewsets.ModelViewSet):
    """
    API endpoint que permite a las etiquetas ser vistas o editadas.
    """
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsAdminOrGestorInventario]

class InventoryItemViewSet(viewsets.ModelViewSet):
    """
    API endpoint que permite a los ítems de inventario ser vistos o editados.
    """
    queryset = InventoryItem.objects.all()
    serializer_class = InventoryItemSerializer
    permission_classes = [IsAdminOrGestorInventario]

    # Permite buscar por nombre o número de serie
    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.query_params.get('search', None)
        if search_query:
            queryset = queryset.filter(
                models.Q(name__icontains=search_query) |
                models.Q(serial_number__icontains=search_query)
            )
        return queryset

class InventoryMovementViewSet(viewsets.ModelViewSet):
    """
    API endpoint que permite a los movimientos de inventario ser vistos o creados.
    El campo 'moved_by' se asigna automáticamente al usuario actual.
    """
    queryset = InventoryMovement.objects.all()
    serializer_class = InventoryMovementSerializer
    permission_classes = [IsAdminOrGestorInventarioOrLogistica] # ADMIN, GESTOR_INV o LOGISTICA pueden modificar

    def perform_create(self, serializer):
        """
        Asigna el usuario actual como 'moved_by' al crear un movimiento.
        """
        serializer.save(moved_by=self.request.user)

class KitViewSet(viewsets.ModelViewSet):
    """
    API endpoint que permite a los kits ser vistos o editados.
    """
    queryset = Kit.objects.all()
    serializer_class = KitSerializer
    permission_classes = [IsAdminOrGestorInventario] # ADMIN o GESTOR_INV pueden modificar
