# backend/inventory/permissions.py

from rest_framework import permissions

class IsAdminOrGestorInventario(permissions.BasePermission):
    """
    Permiso personalizado para permitir acceso a ADMIN o GESTOR_INV.
    Solo estos roles pueden crear, actualizar o eliminar ítems.
    """
    def has_permission(self, request, view):
        # Permitir GET, HEAD, OPTIONS (lectura) para todos los usuarios autenticados
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        
        # Para otros métodos (POST, PUT, PATCH, DELETE), requiere ser ADMIN o GESTOR_INV
        return request.user and request.user.is_authenticated and \
               request.user.role in ['ADMIN', 'GESTOR_INV']

class IsAdminOrGestorInventarioOrLogistica(permissions.BasePermission):
    """
    Permiso para permitir acceso a ADMIN, GESTOR_INV o LOGISTICA.
    Útil para movimientos de inventario donde Logística también podría interactuar.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        
        return request.user and request.user.is_authenticated and \
               request.user.role in ['ADMIN', 'GESTOR_INV', 'LOGISTICA']

class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Permiso para permitir lectura a todos los autenticados y escritura solo a ADMIN.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        
        return request.user and request.user.is_authenticated and \
               request.user.role == 'ADMIN'

class IsAuthenticatedAndAssignedRole(permissions.BasePermission):
    """
    Permiso genérico que requiere autenticación y el rol especificado.
    """
    def __init__(self, allowed_roles=None):
        self.allowed_roles = allowed_roles if allowed_roles is not None else []

    def has_permission(self, request, view):
        # Si no se especifican roles, cualquier usuario autenticado tiene acceso.
        if not self.allowed_roles:
            return request.user and request.user.is_authenticated

        # Para otros métodos (POST, PUT, PATCH, DELETE), requiere tener un rol permitido.
        # La lectura (SAFE_METHODS) siempre está permitida para usuarios autenticados si no se restringe.
        if request.method not in permissions.SAFE_METHODS and \
           (request.user and request.user.is_authenticated and request.user.role in self.allowed_roles):
            return True
        elif request.method in permissions.SAFE_METHODS and \
             (request.user and request.user.is_authenticated):
            return True
        return False

# Ejemplos de uso específico para cada ViewSet si se necesitara:
# class CanManageSuppliers(IsAuthenticatedAndAssignedRole):
#     def __init__(self):
#         super().__init__(allowed_roles=['ADMIN', 'COMPRADOR'])

# class CanManageCategories(IsAuthenticatedAndAssignedRole):
#     def __init__(self):
#         super().__init__(allowed_roles=['ADMIN', 'GESTOR_INV'])
