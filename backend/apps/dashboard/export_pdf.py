"""
Exportación a PDF (§8): reporte gerencial con portada, KPIs, semáforos,
completitud y hallazgos automáticos. Plantilla HTML → WeasyPrint.
"""

from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone

from apps.uploads.models import ResultadoCriterio


def _semaforo(pct, verde, amarillo):
    if pct >= verde:
        return "Verde", "verde"
    if pct >= amarillo:
        return "Amarillo", "amarillo"
    return "Rojo", "rojo"


def construir_contexto(evaluaciones, usuario, titulo, completitud=None):
    verde = settings.SEMAFORO_UMBRAL_VERDE
    amarillo = settings.SEMAFORO_UMBRAL_AMARILLO

    evaluaciones = list(evaluaciones.select_related("materia", "ra", "periodo"))
    n = len(evaluaciones)
    suma = sum(float(ev.pct_aprobados_recalculado) for ev in evaluaciones)
    promedio = round(suma / n, 2) if n else 0

    cumplimiento = []
    n_verde = n_rojo = 0
    for ev in sorted(evaluaciones, key=lambda e: (e.materia.codigo, e.ra.codigo, e.seccion)):
        pct = float(ev.pct_aprobados_recalculado)
        semaforo, color = _semaforo(pct, verde, amarillo)
        if color == "verde":
            n_verde += 1
        elif color == "rojo":
            n_rojo += 1
        cumplimiento.append({
            "materia": ev.materia.codigo, "seccion": ev.seccion, "ra": ev.ra.codigo,
            "nivel": ev.nivel, "pct": round(pct, 2), "semaforo": semaforo, "color": color,
        })

    # Hallazgos automáticos: criterios débiles recurrentes
    hallazgos = []
    eval_ids = [ev.id for ev in evaluaciones]
    from django.db.models import Count
    agregados = {}
    for fila in (ResultadoCriterio.objects
                 .filter(resultado_estudiante__evaluacion_id__in=eval_ids)
                 .values("criterio__nombre", "nivel")
                 .annotate(total=Count("id"))):
        nombre = fila["criterio__nombre"]
        agregados.setdefault(nombre, {"EXCELENTE": 0, "SATISFACTORIO": 0, "INSATISFACTORIO": 0})
        agregados[nombre][fila["nivel"]] = fila["total"]
    for nombre, d in agregados.items():
        total = d["EXCELENTE"] + d["SATISFACTORIO"] + d["INSATISFACTORIO"]
        if total == 0:
            continue
        if d["EXCELENTE"] == 0:
            hallazgos.append(f"El criterio «{nombre}» no tiene ningún resultado Excelente.")
        if d["INSATISFACTORIO"] > total / 2:
            hallazgos.append(f"El criterio «{nombre}» tiene mayoría de resultados Insatisfactorio.")

    completitud = completitud or {"pct": "—", "completas": 0, "total": 0, "incompletas": []}

    return {
        "titulo": titulo,
        "fecha_generacion": timezone.localtime().strftime("%d/%m/%Y %H:%M"),
        "usuario": usuario.get_full_name() or usuario.username,
        "kpis": {"n_evaluaciones": n, "pct_promedio": promedio, "n_verde": n_verde, "n_rojo": n_rojo},
        "cumplimiento": cumplimiento,
        "completitud": completitud,
        "hallazgos": hallazgos,
    }


def exportar_reporte_pdf(evaluaciones, usuario, titulo, completitud=None):
    from weasyprint import HTML

    contexto = construir_contexto(evaluaciones, usuario, titulo, completitud=completitud)
    html = render_to_string("dashboard/reporte_pdf.html", contexto)
    return HTML(string=html).write_pdf()
