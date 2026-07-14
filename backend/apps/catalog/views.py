from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Carrera, Escuela, Materia, MateriaRA, Periodo, RACatalogo
from .serializers import (
    CarreraSerializer,
    EscuelaSerializer,
    MateriaRASerializer,
    MateriaSerializer,
    PeriodoSerializer,
    RACatalogoSerializer,
)


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
