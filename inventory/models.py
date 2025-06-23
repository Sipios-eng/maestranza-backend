# backend/inventory/models.py

from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db.models.signals import post_save, pre_save, pre_delete
from django.dispatch import receiver
from django.conf import settings
from datetime import date, timedelta

# Definimos los roles de usuario como una tupla de tuplas
USER_ROLES = (
    ('ADMIN', 'Administrador'),
    ('GESTOR_INV', 'Gestor de Inventario'),
    ('COMPRADOR', 'Comprador'), # El comprador usará el historial de precios
    ('LOGISTICA', 'Logística'),
    ('JEFE_PROD', 'Jefe de Producción'),
    ('AUDITOR', 'Auditor'),
    ('GERENTE_PROY', 'Gerente de Proyecto'),
    ('USUARIO_FINAL', 'Usuario Final'),
)

class UserProfile(AbstractUser):
    role = models.CharField(max_length=20, choices=USER_ROLES, default='USUARIO_FINAL')

    groups = models.ManyToManyField(
        Group,
        verbose_name=('groups'),
        blank=True,
        help_text=(
            'The groups this user belongs to. A user will get all permissions '
            'granted to each of their groups.'
        ),
        related_name="user_profiles",
        related_query_name="user_profile",
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name=('user permissions'),
        blank=True,
        help_text=('Specific permissions for this user.'),
        related_name="user_profiles",
        related_query_name="user_profile",
    )

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class Supplier(models.Model):
    name = models.CharField(max_length=255, unique=True, verbose_name="Nombre del Proveedor")
    contact_person = models.CharField(max_length=255, blank=True, null=True, verbose_name="Persona de Contacto")
    contact_email = models.EmailField(blank=True, null=True, verbose_name="Email de Contacto")
    contact_phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Teléfono de Contacto")
    payment_terms = models.TextField(blank=True, null=True, verbose_name="Términos de Pago")
    address = models.TextField(blank=True, null=True, verbose_name="Dirección")

    class Meta:
        verbose_name = "Proveedor"
        verbose_name_plural = "Proveedores"
        ordering = ['name']

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Nombre de la Categoría")
    description = models.TextField(blank=True, null=True, verbose_name="Descripción")

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ['name']

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="Nombre de la Etiqueta")

    class Meta:
        verbose_name = "Etiqueta"
        verbose_name_plural = "Etiquetas"
        ordering = ['name']

    def __str__(self):
        return self.name


class InventoryItem(models.Model):
    name = models.CharField(max_length=255, verbose_name="Nombre del Ítem")
    description = models.TextField(blank=True, null=True, verbose_name="Descripción")
    serial_number = models.CharField(max_length=100, unique=True, blank=True, null=True, verbose_name="Número de Serie")
    location = models.CharField(max_length=100, blank=True, null=True, verbose_name="Ubicación en Almacén")
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Cantidad Actual")
    low_stock_threshold = models.DecimalField(max_digits=10, decimal_places=2, default=5.00, verbose_name="Umbral de Stock Bajo")
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Precio de Compra")
    expiration_date = models.DateField(blank=True, null=True, verbose_name="Fecha de Vencimiento")

    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='inventory_items', verbose_name="Categoría")
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True, related_name='supplied_items', verbose_name="Proveedor")
    tags = models.ManyToManyField(Tag, blank=True, related_name='inventory_items', verbose_name="Etiquetas")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última Actualización")

    class Meta:
        verbose_name = "Ítem de Inventario"
        verbose_name_plural = "Ítems de Inventario"
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def is_expiring_soon(self):
        """
        Determina si el ítem está por vencer pronto (ej. en los próximos 6 meses).
        """
        if self.expiration_date:
            return self.expiration_date <= date.today() + timedelta(days=180) # Menos de 6 meses
        return False

    @property
    def is_expired(self):
        """
        Determina si el ítem ya ha vencido.
        """
        if self.expiration_date:
            return self.expiration_date <= date.today()
        return False


class InventoryMovement(models.Model):
    MOVEMENT_TYPES = (
        ('ENTRADA', 'Entrada'),
        ('SALIDA', 'Salida'),
        ('TRANSFERENCIA', 'Transferencia'),
        ('DEVOLUCION', 'Devolución'),
    )

    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='movements', verbose_name="Ítem")
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES, verbose_name="Tipo de Movimiento")
    quantity = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Cantidad")
    moved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Realizado por")
    movement_date = models.DateTimeField(auto_now_add=True, verbose_name="Fecha y Hora del Movimiento")
    project = models.CharField(max_length=255, blank=True, null=True, verbose_name="Proyecto Asociado")
    notes = models.TextField(blank=True, null=True, verbose_name="Notas")

    class Meta:
        verbose_name = "Movimiento de Inventario"
        verbose_name_plural = "Movimientos de Inventario"
        ordering = ['-movement_date']

    def __str__(self):
        return f"{self.movement_type} de {self.quantity} de {self.item.name} por {self.moved_by or 'N/A'}"


class Kit(models.Model):
    name = models.CharField(max_length=255, unique=True, verbose_name="Nombre del Kit")
    description = models.TextField(blank=True, null=True, verbose_name="Descripción del Kit")
    items = models.ManyToManyField(InventoryItem, through='KitItem', related_name='kits', verbose_name="Ítems del Kit")

    class Meta:
        verbose_name = "Kit"
        verbose_name_plural = "Kits"
        ordering = ['name']

    def __str__(self):
        return self.name

class KitItem(models.Model):
    kit = models.ForeignKey(Kit, on_delete=models.CASCADE)
    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1.00, verbose_name="Cantidad en el Kit")

    class Meta:
        unique_together = ('kit', 'item')
        verbose_name = "Ítem en Kit"
        verbose_name_plural = "Ítems en Kits"
    def __str__(self):
        return f"{self.item.name} ({self.quantity}) en {self.kit.name}"


# --- NUEVO MODELO: PurchaseRecord (Historial de Precios de Compra) ---
class PurchaseRecord(models.Model):
    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='purchase_records', verbose_name="Ítem")
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True, related_name='purchase_records', verbose_name="Proveedor")
    purchase_date = models.DateField(default=date.today, verbose_name="Fecha de Compra")
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio Unitario")
    quantity_purchased = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Cantidad Comprada")
    notes = models.TextField(blank=True, null=True, verbose_name="Notas de Compra")
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Registrado por")

    class Meta:
        verbose_name = "Registro de Compra"
        verbose_name_plural = "Registros de Compra"
        ordering = ['-purchase_date', 'item__name'] # Ordenar por fecha descendente y luego por nombre del ítem

    def __str__(self):
        return f"Compra de {self.quantity_purchased} de {self.item.name} a ${self.unit_price} el {self.purchase_date}"


# --- Señales de Django ---

@receiver(pre_save, sender=InventoryMovement)
def store_old_movement_data(sender, instance, **kwargs):
    """
    Almacena los valores antiguos de un movimiento antes de que se guarde,
    necesario para recalcular correctamente el stock en caso de actualización.
    """
    if instance.pk: # Si la instancia ya existe (es una actualización)
        try:
            # Obtener la instancia antigua de la base de datos
            old_instance = sender.objects.get(pk=instance.pk)
            # Almacenar los valores antiguos temporalmente
            instance._old_quantity = old_instance.quantity
            instance._old_movement_type = old_instance.movement_type
        except sender.DoesNotExist:
            instance._old_quantity = None
            instance._old_movement_type = None
    else: # Es una nueva creación
        instance._old_quantity = None
        instance._old_movement_type = None


@receiver(post_save, sender=InventoryMovement)
def update_inventory_quantity(sender, instance, created, **kwargs):
    """
    Actualiza la cantidad del InventoryItem asociado después de un movimiento.
    Maneja tanto creaciones como actualizaciones de movimientos.
    """
    try:
        # Obtener el InventoryItem más reciente desde la base de datos
        item = InventoryItem.objects.get(pk=instance.item.pk)
        current_item_quantity = item.quantity # Cantidad actual del ítem en DB
    except InventoryItem.DoesNotExist:
        print(f"ERROR: InventoryItem con ID {instance.item.pk} no encontrado para el movimiento {instance.pk}. No se puede actualizar el stock.")
        return # Salir si el ítem no existe

    new_quantity_value = current_item_quantity

    if created: # Es un nuevo movimiento
        if instance.movement_type == 'ENTRADA' or instance.movement_type == 'DEVOLUCION':
            new_quantity_value += instance.quantity
        elif instance.movement_type == 'SALIDA' or instance.movement_type == 'TRANSFERENCIA':
            new_quantity_value -= instance.quantity

    else: # El movimiento fue actualizado
        old_quantity = getattr(instance, '_old_quantity', None)
        old_movement_type = getattr(instance, '_old_movement_type', None)

        if old_quantity is not None and old_movement_type is not None:
            # Revertir el efecto del movimiento antiguo
            if old_movement_type == 'ENTRADA' or old_movement_type == 'DEVOLUCION':
                new_quantity_value -= old_quantity
            elif old_movement_type == 'SALIDA' or old_movement_type == 'TRANSFERENCIA':
                new_quantity_value += old_quantity
            
            # Aplicar el efecto del nuevo movimiento
            if instance.movement_type == 'ENTRADA' or instance.movement_type == 'DEVOLUCION':
                new_quantity_value += instance.quantity
            elif instance.movement_type == 'SALIDA' or instance.movement_type == 'TRANSFERENCIA':
                new_quantity_value -= instance.quantity
        else:
            # Fallback: Si no hay datos antiguos, solo aplicar el nuevo cambio de forma simple
            if instance.movement_type == 'ENTRADA' or instance.movement_type == 'DEVOLUCION':
                new_quantity_value += instance.quantity
            elif instance.movement_type == 'SALIDA' or instance.movement_type == 'TRANSFERENCIA':
                new_quantity_value -= instance.quantity

    # Actualizar la cantidad en la base de datos de forma directa
    try:
        InventoryItem.objects.filter(pk=item.pk).update(quantity=new_quantity_value)
        # Recargar el ítem desde la DB para la comprobación del umbral y vencimiento
        item_updated_from_db = InventoryItem.objects.get(pk=item.pk)
    except Exception as e:
        print(f"ERROR: Fallo al actualizar la cantidad del ítem '{item.name}' en la base de datos: {e}")
        return # Salir si no se pudo actualizar la DB

    # Verificar el umbral de stock bajo y fechas de vencimiento
    if item_updated_from_db.quantity <= item_updated_from_db.low_stock_threshold:
        print(f"!!! ALERTA DE STOCK BAJO: El ítem '{item_updated_from_db.name}' tiene {item_updated_from_db.quantity} unidades. El umbral es {item_updated_from_db.low_stock_threshold}.")
    
    if item_updated_from_db.is_expired:
        print(f"!!! ALERTA DE VENCIMIENTO: El ítem '{item_updated_from_db.name}' ha VENCIDO el {item_updated_from_db.expiration_date}.")
    elif item_updated_from_db.is_expiring_soon:
        print(f"!!! ALERTA DE VENCIMIENTO PROXIMO: El ítem '{item_updated_from_db.name}' vencerá pronto ({item_updated_from_db.expiration_date}).")


@receiver(pre_delete, sender=InventoryMovement)
def revert_inventory_quantity_on_delete(sender, instance, **kwargs):
    """
    Revertir el stock del InventoryItem cuando un InventoryMovement es eliminado.
    """
    try:
        item = InventoryItem.objects.get(pk=instance.item.pk)
        
        reverted_quantity = item.quantity
        if instance.movement_type == 'ENTRADA' or instance.movement_type == 'DEVOLUCION':
            reverted_quantity -= instance.quantity
        elif instance.movement_type == 'SALIDA' or instance.movement_type == 'TRANSFERENCIA':
            reverted_quantity += instance.quantity
        
        InventoryItem.objects.filter(pk=item.pk).update(quantity=reverted_quantity)
        
        # Opcional: Re-verificar umbral después de la eliminación
        item_after_revert = InventoryItem.objects.get(pk=item.pk)
        if item_after_revert.quantity <= item_after_revert.low_stock_threshold:
            print(f"!!! ALERTA DE STOCK BAJO DESPUÉS DE REVERTIR: El ítem '{item_after_revert.name}' tiene {item_after_revert.quantity} unidades. El umbral es {item_after_revert.low_stock_threshold}.")
        
        if item_after_revert.is_expired:
            print(f"!!! ALERTA DE VENCIMIENTO DESPUÉS DE REVERTIR: El ítem '{item_after_revert.name}' ha VENCIDO el {item_after_revert.expiration_date}.")
        elif item_after_revert.is_expiring_soon:
            print(f"!!! ALERTA DE VENCIMIENTO PROXIMO DESPUÉS DE REVERTIR: El ítem '{item_after_revert.name}' vencerá pronto ({item_after_revert.expiration_date}).")

    except InventoryItem.DoesNotExist:
        print(f"ERROR: InventoryItem con ID {instance.item.pk} no encontrado durante pre_delete para movimiento {instance.pk}.")
    except Exception as e:
        print(f"ERROR: Fallo al revertir stock para '{instance.item.name}' en pre_delete: {e}")

