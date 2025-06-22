# backend/inventory/serializers.py

from rest_framework import serializers
from .models import UserProfile, Supplier, Category, Tag, InventoryItem, InventoryMovement, Kit, KitItem

class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo UserProfile.
    """
    class Meta:
        model = UserProfile
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role']
        read_only_fields = ['username'] # El username no debería ser editable a través de la API en este contexto

class SupplierSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo Supplier.
    """
    class Meta:
        model = Supplier
        fields = '__all__' # Incluye todos los campos del modelo

class CategorySerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo Category.
    """
    class Meta:
        model = Category
        fields = '__all__'

class TagSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo Tag.
    """
    class Meta:
        model = Tag
        fields = '__all__'

class InventoryItemSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo InventoryItem.
    Utiliza Depth para mostrar información de la categoría, proveedor y etiquetas.
    """
    category_name = serializers.CharField(source='category.name', read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    tags_names = serializers.StringRelatedField(many=True, source='tags', read_only=True) # Muestra los nombres de las etiquetas

    class Meta:
        model = InventoryItem
        fields = [
            'id', 'name', 'description', 'serial_number', 'location',
            'quantity', 'low_stock_threshold', 'purchase_price', 'expiration_date',
            'category', 'category_name', # category para escribir, category_name para leer
            'supplier', 'supplier_name', # supplier para escribir, supplier_name para leer
            'tags', 'tags_names', # tags para escribir, tags_names para leer
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at'] # Estas fechas son gestionadas automáticamente

class InventoryMovementSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo InventoryMovement.
    Incluye información del ítem y el usuario que realizó el movimiento.
    """
    item_name = serializers.CharField(source='item.name', read_only=True)
    moved_by_username = serializers.CharField(source='moved_by.username', read_only=True)
    moved_by_role = serializers.CharField(source='moved_by.role', read_only=True)

    class Meta:
        model = InventoryMovement
        fields = [
            'id', 'item', 'item_name', 'movement_type', 'quantity', 'moved_by',
            'moved_by_username', 'moved_by_role', 'movement_date', 'project', 'notes'
        ]
        read_only_fields = ['movement_date', 'moved_by'] # Fecha y usuario son automáticos o establecidos por la vista

class KitItemSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo intermedio KitItem.
    Incluye información del ítem de inventario.
    """
    item_name = serializers.CharField(source='item.name', read_only=True)
    item_description = serializers.CharField(source='item.description', read_only=True)
    item_serial_number = serializers.CharField(source='item.serial_number', read_only=True)

    class Meta:
        model = KitItem
        fields = ['id', 'item', 'item_name', 'item_description', 'item_serial_number', 'quantity']

class KitSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo Kit.
    Utiliza el KitItemSerializer anidado para mostrar los ítems que componen el kit.
    """
    items = KitItemSerializer(source='kititem_set', many=True, read_only=True) # Muestra los ítems del kit
    # Campo para escribir los ítems del kit al crear/actualizar un kit
    # Se sobrescribirá en la vista para manejar la relación ManyToMany con 'through'
    item_ids = serializers.PrimaryKeyRelatedField(
        queryset=InventoryItem.objects.all(), many=True, write_only=True, required=False
    )

    class Meta:
        model = Kit
        fields = ['id', 'name', 'description', 'items', 'item_ids']

    # Método para crear el kit y sus ítems relacionados
    def create(self, validated_data):
        item_ids_data = validated_data.pop('item_ids', [])
        kit = Kit.objects.create(**validated_data)
        for item in item_ids_data:
            KitItem.objects.create(kit=kit, item=item) # Cantidad por defecto de 1
        return kit

    # Método para actualizar el kit y sus ítems relacionados
    def update(self, instance, validated_data):
        item_ids_data = validated_data.pop('item_ids', [])

        # Actualiza los campos del kit
        instance.name = validated_data.get('name', instance.name)
        instance.description = validated_data.get('description', instance.description)
        instance.save()

        # Actualiza los ítems del kit. Esto es una forma simple que elimina y recrea.
        # En un sistema de producción, se podría hacer una actualización más inteligente (diff).
        instance.kititem_set.all().delete()
        for item in item_ids_data:
            KitItem.objects.create(kit=instance, item=item)

        return instance
