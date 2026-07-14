from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.uploads.models import AuditLog

from .completitud import completitud_periodo
from .models import Carrera, Escuela, Materia, MateriaRA, Periodo, RACatalogo
from .serializers import (
    CarreraSerializer,
    EscuelaSerializer,
    MateriaRASerializer,
    MateriaSerializer,
    PeriodoSerializer,
    RACatalogoSerializer,
)


def _escuelas_ids_gestion(usuario):
    """Escuelas que el usuario puede gestionar para cierre/completitud.
    None == todas (administrador)."""
    if usuario.es_administrador:
        return None
    return list(usuario.escuelas_coordinadas().values_list("id", flat=True))


class CompletitudPeriodoView(APIView):
    """Preview de completitud de un periodo (RAs esperados vs cargados)."""

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        periodo = Periodo.objects.filter(pk=pk).first()
        if periodo is None:
            return Response({"detail": "Periodo no encontrado."}, status=status.HTTP_404_NOT_FOUND)
        escuelas = _escuelas_ids_gestion(request.user)
        return Response(completitud_periodo(periodo, escuelas_ids=escuelas))


class CerrarPeriodoView(APIView):
    """Cierre de periodo (acción de coordinador/administrador). No permite cerrar
    con combinaciones incompletas."""

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        usuario = request.user
        if not (usuario.es_coordinador or usuario.es_administrador):
            return Response(
                {"detail": "Solo un coordinador o administrador puede cerrar un periodo."},
                status=status.HTTP_403_FORBIDDEN,
            )
        periodo = Periodo.objects.filter(pk=pk).first()
        if periodo is None:
            return Response({"detail": "Periodo no encontrado."}, status=status.HTTP_404_NOT_FOUND)
        if periodo.estado == Periodo.ESTADO_CERRADO:
            return Response({"detail": "El periodo ya está cerrado."}, status=status.HTTP_400_BAD_REQUEST)

        escuelas = _escuelas_ids_gestion(usuario)
        resumen = completitud_periodo(periodo, escuelas_ids=escuelas)
        if not resumen["puede_cerrarse"]:
            return Response(
                {
                    "detail": "No se puede cerrar el periodo: hay combinaciones incompletas.",
                    "incompletas": resumen["incompletas"],
                    "n_incompletas": resumen["n_incompletas"],
                },
                status=status.HTTP_409_CONFLICT,
            )

        periodo.estado = Periodo.ESTADO_CERRADO
        periodo.save(update_fields=["estado"])
        AuditLog.objects.create(
            usuario=usuario, entidad="Periodo", entidad_id=str(periodo.id),
            campo="estado", valor_anterior=Periodo.ESTADO_ABIERTO,
            valor_nuevo=Periodo.ESTADO_CERRADO,
            motivo=f"Cierre de periodo con {resumen['n_completas']} combinaciones completas.",
        )
        return Response({"detail": "Periodo cerrado.", "periodo": PeriodoSerializer(periodo).data})


class CatalogoReadOnlyViewSet(viewsets.ReadOnlyModelViewSet):
    """Catálogo de referencia para poblar filtros. El CRUD se hace vía Django admin (Fase 1)."""

    permission_classes = [IsAuthenticated]
    pagination_class = None


class EscuelaViewSet(CatalogoReadOnlyViewSet):
    queryset = Escuela.objects.all()
    serializer_class = EscuelaSerializer


class CarreraViewSet(CatalogoReadOnlyViewSet):
    queryset = Carrera.objects.all()
    serializer_class = CarreraSerializer
    filterset_fields = ["escuela"]


class PeriodoViewSet(CatalogoReadOnlyViewSet):
    queryset = Periodo.objects.all()
    serializer_class = PeriodoSerializer


class MateriaViewSet(CatalogoReadOnlyViewSet):
    queryset = Materia.objects.select_related("escuela").all()
    serializer_class = MateriaSerializer
    filterset_fields = ["escuela"]


class RACatalogoViewSet(CatalogoReadOnlyViewSet):
    queryset = RACatalogo.objects.all()
    serializer_class = RACatalogoSerializer


class MateriaRAViewSet(viewsets.ModelViewSet):
    """Catálogo Materia→RA. Lectura para todos; gestión (crear/editar/borrar)
    solo para coordinador de la escuela de la materia o administrador (§3)."""

    queryset = MateriaRA.objects.select_related("materia", "ra", "materia__escuela").all()
    serializer_class = MateriaRASerializer
    filterset_fields = ["materia", "materia__escuela"]
    pagination_class = None

    def get_permissions(self):
        from apps.accounts.permissions import LecturaOCoordinador
        return [LecturaOCoordinador()]

    def _verificar_escuela(self, materia):
        u = self.request.user
        if u.es_administrador:
            return True
        return u.escuelas_coordinadas().filter(id=materia.escuela_id).exists()

    def perform_create(self, serializer):
        from rest_framework.exceptions import PermissionDenied

        materia = serializer.validated_data["materia"]
        if not self._verificar_escuela(materia):
            raise PermissionDenied("Solo puede gestionar el catálogo de su escuela.")
        obj = serializer.save()
        self._auditar("crear", obj, "")

    def perform_update(self, serializer):
        from rest_framework.exceptions import PermissionDenied

        materia = serializer.validated_data.get("materia", serializer.instance.materia)
        if not self._verificar_escuela(materia):
            raise PermissionDenied("Solo puede gestionar el catálogo de su escuela.")
        anterior = f"{serializer.instance.ra.codigo} N{serializer.instance.nivel_esperado}"
        obj = serializer.save()
        self._auditar("editar", obj, anterior)

    def perform_destroy(self, instance):
        from rest_framework.exceptions import PermissionDenied

        if not self._verificar_escuela(instance.materia):
            raise PermissionDenied("Solo puede gestionar el catálogo de su escuela.")
        self._auditar("borrar", instance, f"{instance.ra.codigo} N{instance.nivel_esperado}")
        instance.delete()

    def _auditar(self, accion, obj, anterior):
        AuditLog.objects.create(
            usuario=self.request.user, entidad="MateriaRA", entidad_id=str(obj.id),
            campo="catalogo", valor_anterior=anterior,
            valor_nuevo=f"{obj.materia.codigo} → {obj.ra.codigo} N{obj.nivel_esperado}",
            motivo=f"Gestión de catálogo ({accion}).",
        )
