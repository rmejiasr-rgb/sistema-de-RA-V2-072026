from django.conf import settings
from django.db.models import Count
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.uploads.models import ResultadoCriterio
from apps.uploads.permisos import evaluaciones_visibles

from . import services


def color_semaforo(pct):
    if pct is None:
        return "SIN_DATOS"
    if pct >= settings.SEMAFORO_UMBRAL_VERDE:
        return "VERDE"
    if pct >= settings.SEMAFORO_UMBRAL_AMARILLO:
        return "AMARILLO"
    return "ROJO"


FILTROS_EVALUACION = {
    "periodo": "periodo_id",
    "escuela": "materia__escuela_id",
    "materia": "materia_id",
    "seccion": "seccion",
    "profesor": "profesor_nombre",
    "ra": "ra_id",
    "nivel": "nivel",
}


def _aplicar_filtros(qs, params):
    for param, campo in FILTROS_EVALUACION.items():
        valor = params.get(param)
        if valor:
            qs = qs.filter(**{campo: valor})
    return qs


class CumplimientoRAView(APIView):
    """Bloque 1: % aprobados por RA/materia/sección con semáforo (§7.1)."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = evaluaciones_visibles(request.user).filter(vigente=True).select_related(
            "materia", "ra", "periodo"
        )
        qs = _aplicar_filtros(qs, request.query_params)

        resultados = [
            {
                "evaluacion_id": ev.id,
                "periodo": ev.periodo.codigo,
                "escuela_id": ev.materia.escuela_id,
                "materia": ev.materia.codigo,
                "materia_nombre": ev.materia.nombre,
                "seccion": ev.seccion,
                "profesor": ev.profesor_nombre,
                "ra": ev.ra.codigo,
                "nivel": ev.nivel,
                "pct_aprobados_declarado": ev.pct_aprobados_declarado,
                "pct_aprobados_recalculado": ev.pct_aprobados_recalculado,
                "semaforo": color_semaforo(ev.pct_aprobados_recalculado),
                "discrepancia": ev.discrepancia_pct,
            }
            for ev in qs.order_by("materia__codigo", "ra__codigo", "seccion")
        ]
        return Response({
            "umbrales": {
                "verde": settings.SEMAFORO_UMBRAL_VERDE,
                "amarillo": settings.SEMAFORO_UMBRAL_AMARILLO,
            },
            "resultados": resultados,
        })


class DesagregacionCriterioView(APIView):
    """Bloque 2: distribución E/S/I por criterio (§7.2)."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = evaluaciones_visibles(request.user).filter(vigente=True)
        qs = _aplicar_filtros(qs, request.query_params)
        evaluacion_ids = list(qs.values_list("id", flat=True))

        conteos = (
            ResultadoCriterio.objects.filter(
                resultado_estudiante__evaluacion_id__in=evaluacion_ids
            )
            .values("criterio__nombre", "nivel")
            .annotate(total=Count("id"))
        )

        agregados = {}
        for fila in conteos:
            nombre = fila["criterio__nombre"]
            agregados.setdefault(
                nombre, {"criterio": nombre, "excelente": 0, "satisfactorio": 0, "insatisfactorio": 0}
            )
            clave = fila["nivel"].lower()
            agregados[nombre][clave] = fila["total"]

        resultados = []
        for datos in agregados.values():
            total = datos["excelente"] + datos["satisfactorio"] + datos["insatisfactorio"]
            datos["total"] = total
            datos["cero_excelente"] = datos["excelente"] == 0
            datos["mayoria_insatisfactorio"] = total > 0 and datos["insatisfactorio"] > total / 2
            resultados.append(datos)

        resultados.sort(key=lambda d: d["criterio"])
        return Response({"resultados": resultados})


class _BloqueBaseView(APIView):
    """Base para bloques 3-7: aplica visibilidad por rol + filtros globales."""

    permission_classes = [IsAuthenticated]

    def get_queryset(self, request):
        qs = evaluaciones_visibles(request.user).filter(vigente=True)
        return _aplicar_filtros(qs, request.query_params)


class HeatmapMateriaRAView(_BloqueBaseView):
    """Bloque 3a: mapa de calor materia × RA (§7.3)."""

    def get(self, request):
        return Response(services.heatmap_materia_ra(self.get_queryset(request)))


class HeatmapCriterioSeccionView(_BloqueBaseView):
    """Bloque 3b: mapa de calor criterio × sección (§7.3)."""

    def get(self, request):
        return Response(services.heatmap_criterio_seccion(self.get_queryset(request)))


class DesgloseCarreraGrupoView(_BloqueBaseView):
    """Bloque 4: desglose por carrera y por grupo (§7.4)."""

    def get(self, request):
        return Response(services.desglose_carrera_grupo(self.get_queryset(request)))


class TendenciasView(_BloqueBaseView):
    """Bloque 5: tendencias históricas (§7.5)."""

    def get(self, request):
        return Response(services.tendencias_historicas(self.get_queryset(request)))


class CoberturaView(_BloqueBaseView):
    """Bloque 6: cobertura y completitud (§7.6)."""

    def get(self, request):
        qs = self.get_queryset(request)
        return Response(services.cobertura_completitud(
            qs,
            periodo_id=request.query_params.get("periodo") or None,
            escuela_id=request.query_params.get("escuela") or None,
        ))


class RiesgoAcreditacionView(_BloqueBaseView):
    """Bloque 7: riesgo de acreditación (§7.7)."""

    def get(self, request):
        n = int(request.query_params.get("n_periodos", 2))
        return Response(services.riesgo_acreditacion(self.get_queryset(request), n_periodos=n))


class ProxyConsistenciaView(_BloqueBaseView):
    """Bloque secundario: proxy de consistencia entre evaluadores (§7)."""

    def get(self, request):
        return Response(services.proxy_consistencia(self.get_queryset(request)))
