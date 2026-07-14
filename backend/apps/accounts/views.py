from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.uploads.models import AuditLog

from .models import Usuario
from .permissions import EsAdministrador
from .serializers import UsuarioAdminSerializer, UsuarioSerializer


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UsuarioSerializer(request.user).data)


class UsuarioViewSet(viewsets.ModelViewSet):
    """Gestión de usuarios y roles (solo administrador, §3)."""

    queryset = Usuario.objects.prefetch_related("roles__escuela").all().order_by("username")
    serializer_class = UsuarioAdminSerializer
    permission_classes = [EsAdministrador]
    pagination_class = None

    def perform_create(self, serializer):
        usuario = serializer.save()
        AuditLog.objects.create(
            usuario=self.request.user, entidad="Usuario", entidad_id=str(usuario.id),
            campo="alta", valor_anterior="", valor_nuevo=usuario.username,
            motivo="Alta de usuario.",
        )

    def perform_update(self, serializer):
        usuario = serializer.save()
        AuditLog.objects.create(
            usuario=self.request.user, entidad="Usuario", entidad_id=str(usuario.id),
            campo="edicion", valor_anterior="", valor_nuevo=usuario.username,
            motivo="Edición de usuario/roles.",
        )
