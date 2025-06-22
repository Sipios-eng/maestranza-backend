# backend/inventory/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import UserProfile, Supplier, Category, Tag, InventoryItem, InventoryMovement, Kit, KitItem

# Personaliza el Admin para UserProfile
class UserProfileAdmin(UserAdmin):
    """
    Administración personalizada para el modelo UserProfile.
    Añade el campo 'role' al panel de administración.
    """
    # Define explícitamente los fieldsets, incluyendo el campo 'role'.
    # Esto asegura la estructura correcta de cada tupla (nombre, diccionario_opciones).
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Información Personal", {"fields": ("first_name", "last_name", "email")}),
        ("Permisos", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions",), "classes": ("collapse",),}),
        ("Fechas Importantes", {"fields": ("last_login", "date_joined")}),
        ('Roles', {'fields': ('role',)}), # Nuestro fieldset personalizado para el rol
    )

    # Para el formulario de "Añadir Usuario", también definimos los add_fieldsets.
    # Aquí es común extender los predeterminados y añadir el campo de rol.
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Roles', {'fields': ('role',)}),
    )

    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'role') # Mostrar el rol en la lista
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active') # Permitir filtrar por rol


class KitItemInline(admin.TabularInline):
    """
    Permite la edición de KitItem directamente desde el formulario de Kit en el Admin.
    """
    model = KitItem
    extra = 1 # Número de formularios vacíos a mostrar

@admin.register(Kit)
class KitAdmin(admin.ModelAdmin):
    """
    Administración para el modelo Kit, incluyendo sus ítems.
    """
    list_display = ('name', 'description', 'get_total_items')
    search_fields = ('name',)
    inlines = [KitItemInline]

    def get_total_items(self, obj):
        """
        Calcula y muestra el número total de ítems en el kit.
        """
        return obj.kititem_set.count()
    get_total_items.short_description = "Número de Ítems"


# Registra tus modelos en el panel de administración de Django
admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(Supplier)
admin.site.register(Category)
admin.site.register(Tag)
admin.site.register(InventoryItem)
admin.site.register(InventoryMovement)
# Kit ya está registrado con el decorador @admin.register
