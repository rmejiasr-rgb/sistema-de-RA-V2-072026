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


class MateriaRAViewSet(CatalogoReadOnlyViewSet):
    queryset = MateriaRA.objects.select_related("materia", "ra").all()
    serializer_class = MateriaRASerializer
    filterset_fields = ["materia"]
