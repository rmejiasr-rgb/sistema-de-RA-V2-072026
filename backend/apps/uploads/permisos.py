"""Filtrado de datos por rol (§3): un profesor jamás ve notas de otro."""

from django.db.models import Q

from .models import Carga, Evaluacion


def escuelas_ids_visibles(usuario):
    if usuario.es_administrador:
        return None  # None == sin restricción
    return set(usuario.escuelas_coordinadas().values_list("id", flat=True))


def evaluaciones_visibles(usuario, queryset=None):
    qs = Evaluacion.objects.all() if queryset is None else queryset
    if usuario.es_administrador:
        return qs
    escuelas = escuelas_ids_visibles(usuario)
    condicion = Q(carga__usuario=usuario)
    if escuelas:
        condicion |= Q(materia__escuela_id__in=escuelas)
    return qs.filter(condicion).distinct()


def cargas_visibles(usuario, queryset=None):
    qs = Carga.objects.all() if queryset is None else queryset
    if usuario.es_administrador:
        return qs
    escuelas = escuelas_ids_visibles(usuario)
    condicion = Q(usuario=usuario)
    if escuelas:
        condicion |= Q(materia__escuela_id__in=escuelas)
    return qs.filter(condicion).distinct()
