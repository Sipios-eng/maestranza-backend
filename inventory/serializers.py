# backend/inventory/serializers.py

from rest_framework import serializers
from .models import UserProfile, Supplier, Category, Tag, InventoryItem, InventoryMovement, Kit, KitItem, PurchaseRecord # <-- Importar PurchaseRecord

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['id', 'username', 'email', 'role']

class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = '__all__'

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'

class InventoryItemSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    
    is_low_stock = serializers.SerializerMethodField()
    is_expiring_soon = serializers.SerializerMethodField()
    is_expired = serializers.SerializerMethodField()

    class Meta:
        model = InventoryItem
        fields = [
            'id', 'name', 'description', 'serial_number', 'location',
            'quantity', 'low_stock_threshold', 'purchase_price', 'expiration_date',
            'category', 'category_name', 'supplier', 'supplier_name', 'tags',
            'created_at', 'updated_at', 'is_low_stock', 'is_expiring_soon', 'is_expired'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_is_low_stock(self, obj):
        if obj.low_stock_threshold is not None:
            return obj.quantity <= obj.low_stock_threshold
        return False

    def get_is_expiring_soon(self, obj):
        return obj.is_expiring_soon

    def get_is_expired(self, obj):
        return obj.is_expired


class InventoryMovementSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source='item.name', read_only=True)
    moved_by_username = serializers.CharField(source='moved_by.username', read_only=True)

    class Meta:
        model = InventoryMovement
        fields = [
            'id', 'item', 'item_name', 'movement_type', 'quantity',
            'moved_by', 'moved_by_username', 'movement_date', 'project', 'notes'
        ]
        read_only_fields = ['movement_date']


class KitItemSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source='item.name', read_only=True)
    class Meta:
        model = KitItem
        fields = ['id', 'kit', 'item', 'item_name', 'quantity']

class KitSerializer(serializers.ModelSerializer):
    items = KitItemSerializer(source='kititem_set', many=True, read_only=True)

    class Meta:
        model = Kit
        fields = ['id', 'name', 'description', 'items']


# --- NUEVO SERIALIZER: PurchaseRecordSerializer ---
class PurchaseRecordSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source='item.name', read_only=True) # Mostrar nombre del ítem
    supplier_name = serializers.CharField(source='supplier.name', read_only=True) # Mostrar nombre del proveedor
    recorded_by_username = serializers.CharField(source='recorded_by.username', read_only=True) # Mostrar nombre del usuario que registró

    class Meta:
        model = PurchaseRecord
        fields = [
            'id', 'item', 'item_name', 'supplier', 'supplier_name',
            'purchase_date', 'unit_price', 'quantity_purchased', 'notes',
            'recorded_by', 'recorded_by_username'
        ]
        read_only_fields = ['recorded_by'] # El usuario que registra se establecerá automáticamente
