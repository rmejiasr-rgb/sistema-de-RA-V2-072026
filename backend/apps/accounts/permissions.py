"""Clases de permisos DRF basadas en roles (§3)."""

from rest_framework.permissions import BasePermission, SAFE_METHODS


class EsAdministrador(BasePermission):
    message = "Se requiere rol de Administrador."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.es_administrador)


class EsCoordinadorOAdministrador(BasePermission):
    message = "Se requiere rol de Coordinador o Administrador."

    def has_permission(self, request, view):
        u = request.user
        return bool(u and u.is_authenticated and (u.es_coordinador or u.es_administrador))


class LecturaOCoordinador(BasePermission):
    """Lectura para cualquier autenticado; escritura solo coordinador/administrador."""

    def has_permission(self, request, view):
        u = request.user
        if not (u and u.is_authenticated):
            return False
        if request.method in SAFE_METHODS:
            return True
        return u.es_coordinador or u.es_administrador
