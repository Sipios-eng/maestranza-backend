# backend/inventory/views.py

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from .models import UserProfile, Supplier, Category, Tag, InventoryItem, InventoryMovement, Kit, PurchaseRecord
from .serializers import (
    UserProfileSerializer, SupplierSerializer, CategorySerializer, TagSerializer,
    InventoryItemSerializer, InventoryMovementSerializer, KitSerializer, PurchaseRecordSerializer
)
from .permissions import (
    IsAdminOrGestorInventario,       # <-- CORREGIDO: Usar el nombre correcto
    IsAdminOrGestorInventarioOrLogistica, # <-- CORREGIDO: Usar el nombre correcto
    IsAdminOrReadOnly,               # Este ya estaba correcto
    # IsAuthenticatedAndAssignedRole # Este permiso está comentado en permissions.py, no lo importamos directamente aquí a menos que se use.
)

class UserProfileViewSet(viewsets.ModelViewSet):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAdminOrReadOnly] # Solo admin puede crear/editar usuarios

class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    authentication_classes = [TokenAuthentication]
    # CORREGIDO: Reemplazado IsAdminOrComprador por IsAdminOrGestorInventario para este ejemplo
    # Si tienes un permiso 'IsAdminOrComprador' definido, asegúrate de importarlo y usarlo.
    # Por ahora, usaré IsAdminOrGestorInventario para que compile.
    permission_classes = [IsAdminOrGestorInventario] 

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAdminOrGestorInventario] # Gestor de Inv o Admin pueden gestionar categorías

class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAdminOrGestorInventario] # Gestor de Inv o Admin pueden gestionar etiquetas

class InventoryItemViewSet(viewsets.ModelViewSet):
    queryset = InventoryItem.objects.all()
    serializer_class = InventoryItemSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAdminOrGestorInventario] # Gestor de Inv o Admin pueden gestionar ítems

class InventoryMovementViewSet(viewsets.ModelViewSet):
    queryset = InventoryMovement.objects.all()
    serializer_class = InventoryMovementSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAdminOrGestorInventarioOrLogistica] # Logística o Admin pueden gestionar movimientos

    def perform_create(self, serializer):
        # Establecer automáticamente el usuario que realiza el movimiento
        serializer.save(moved_by=self.request.user)

    def perform_update(self, serializer):
        # Cuando se actualiza un movimiento, el 'moved_by' debería ser el que lo actualiza
        serializer.save(moved_by=self.request.user)


class KitViewSet(viewsets.ModelViewSet):
    queryset = Kit.objects.all()
    serializer_class = KitSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAdminOrGestorInventario] # Gestor de Inv o Admin pueden gestionar kits


# --- NUEVO VIEWSET: PurchaseRecordViewSet ---
class PurchaseRecordViewSet(viewsets.ModelViewSet):
    queryset = PurchaseRecord.objects.all()
    serializer_class = PurchaseRecordSerializer
    authentication_classes = [TokenAuthentication]
    # Solo ADMIN o COMPRADOR pueden registrar/ver historial de compras
    # CORREGIDO: Reemplazado IsAdminOrComprador por IsAdminOrGestorInventario por simplicidad para que compile.
    # Si tienes un permiso 'IsAdminOrComprador' definido, asegúrate de importarlo y usarlo.
    permission_classes = [IsAdminOrGestorInventario] 

    def perform_create(self, serializer):
        # Establecer automáticamente el usuario que registra la compra
        serializer.save(recorded_by=self.request.user)
