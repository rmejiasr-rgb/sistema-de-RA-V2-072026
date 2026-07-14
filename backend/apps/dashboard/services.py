"""
Agregaciones analíticas para los bloques 3-7 del tablero (§7).

Todas las funciones reciben un queryset base de Evaluaciones ya filtrado por rol
y por los filtros globales, y devuelven estructuras JSON-serializables. Las
agregaciones se resuelven en SQL para responder <2 s a escala (§9).
"""

from django.conf import settings
from django.db.models import Avg, Count, Q

from apps.catalog.models import Materia, MateriaRA, Periodo
from apps.uploads.models import ResultadoCriterio, ResultadoEstudiante


def color_semaforo(pct):
    if pct is None:
        return "SIN_DATOS"
    pct = float(pct)
    if pct >= settings.SEMAFORO_UMBRAL_VERDE:
        return "VERDE"
    if pct >= settings.SEMAFORO_UMBRAL_AMARILLO:
        return "AMARILLO"
    return "ROJO"


# --- Bloque 3: Mapas de calor -------------------------------------------------

def heatmap_materia_ra(eval_qs):
    """% aprobados promedio por materia × RA."""
    filas = (
        eval_qs.values("materia__codigo", "ra__codigo")
        .annotate(pct=Avg("pct_aprobados_recalculado"), n=Count("id"))
        .order_by("materia__codigo", "ra__codigo")
    )
    materias = []
    ras = []
    celdas = {}
    for f in filas:
        m, r = f["materia__codigo"], f["ra__codigo"]
        if m not in materias:
            materias.append(m)
        if r not in ras:
            ras.append(r)
        celdas[(m, r)] = {"pct": round(float(f["pct"]), 2), "n": f["n"],
                          "semaforo": color_semaforo(f["pct"])}
    ras.sort()
    return {
        "materias": materias,
        "ras": ras,
        "celdas": [
            {"materia": m, "ra": r, **celdas[(m, r)]}
            for (m, r) in celdas
        ],
    }


def heatmap_criterio_seccion(eval_qs):
    """% aprobados (Excelente+Satisfactorio) por criterio × sección."""
    eval_ids = list(eval_qs.values_list("id", flat=True))
    filas = (
        ResultadoCriterio.objects.filter(
            resultado_estudiante__evaluacion_id__in=eval_ids
        )
        .values("criterio__nombre", "resultado_estudiante__evaluacion__seccion")
        .annotate(
            total=Count("id"),
            aprobados=Count("id", filter=~Q(nivel=ResultadoCriterio.INSATISFACTORIO)),
        )
    )
    criterios = []
    secciones = set()
    celdas = []
    for f in filas:
        crit = f["criterio__nombre"]
        secc = f["resultado_estudiante__evaluacion__seccion"]
        if crit not in criterios:
            criterios.append(crit)
        secciones.add(secc)
        pct = (f["aprobados"] / f["total"] * 100) if f["total"] else 0
        celdas.append({
            "criterio": crit, "seccion": secc, "pct": round(pct, 2),
            "n": f["total"], "semaforo": color_semaforo(pct),
        })
    criterios.sort()
    return {"criterios": criterios, "secciones": sorted(secciones), "celdas": celdas}


# --- Bloque 4: Desglose por carrera y por grupo -------------------------------

def desglose_carrera_grupo(eval_qs):
    eval_ids = list(eval_qs.values_list("id", flat=True))
    base = ResultadoEstudiante.objects.filter(evaluacion_id__in=eval_ids)

    por_carrera = list(
        base.values("carrera")
        .annotate(promedio=Avg("nota"), n=Count("id"))
        .order_by("-promedio")
    )
    por_grupo = list(
        base.values("grupo")
        .annotate(promedio=Avg("nota"), n=Count("id"))
        .order_by("-promedio")
    )

    def fmt(filas, clave):
        return [
            {clave: f[clave] or "(sin dato)", "promedio": round(float(f["promedio"]), 2), "n": f["n"]}
            for f in filas
        ]

    carreras = fmt(por_carrera, "carrera")
    grupos = fmt(por_grupo, "grupo")

    # Detección de grupos con desempeño extremo (fuera de media ± 1.5·desv)
    extremos = []
    if grupos:
        promedios = [g["promedio"] for g in grupos]
        media = sum(promedios) / len(promedios)
        var = sum((p - media) ** 2 for p in promedios) / len(promedios)
        desv = var ** 0.5
        for g in grupos:
            if desv > 0 and abs(g["promedio"] - media) > 1.5 * desv:
                extremos.append({**g, "tipo": "alto" if g["promedio"] > media else "bajo"})

    return {"por_carrera": carreras, "por_grupo": grupos, "grupos_extremos": extremos}


# --- Bloque 5: Tendencias históricas ------------------------------------------

def tendencias_historicas(eval_qs):
    """Evolución de % aprobados por periodo, desglosado por materia o por RA."""
    filas = (
        eval_qs.values("periodo__codigo", "materia__codigo", "ra__codigo")
        .annotate(pct=Avg("pct_aprobados_recalculado"), n=Count("id"))
        .order_by("periodo__codigo")
    )
    periodos = sorted({f["periodo__codigo"] for f in filas})
    # Serie por materia
    series_materia = {}
    series_ra = {}
    for f in filas:
        series_materia.setdefault(f["materia__codigo"], {})[f["periodo__codigo"]] = round(float(f["pct"]), 2)
        # promedio ponderado simple por RA acumulando
    # Serie por RA (promedio por periodo)
    por_ra = (
        eval_qs.values("periodo__codigo", "ra__codigo")
        .annotate(pct=Avg("pct_aprobados_recalculado"))
    )
    for f in por_ra:
        series_ra.setdefault(f["ra__codigo"], {})[f["periodo__codigo"]] = round(float(f["pct"]), 2)

    def a_series(dic):
        return [
            {"nombre": nombre, "puntos": [{"periodo": p, "pct": vals.get(p)} for p in periodos]}
            for nombre, vals in sorted(dic.items())
        ]

    return {
        "periodos": periodos,
        "por_materia": a_series(series_materia),
        "por_ra": a_series(series_ra),
    }


# --- Bloque 6: Cobertura y completitud ----------------------------------------

def cobertura_completitud(eval_qs, periodo_id=None, escuela_id=None):
    """RAs esperados vs cargados por materia/periodo; faltantes; % por escuela."""
    # Catálogo esperado (materia -> set de ra_id)
    mr_qs = MateriaRA.objects.select_related("materia", "ra")
    if escuela_id:
        mr_qs = mr_qs.filter(materia__escuela_id=escuela_id)
    esperado = {}
    for mr in mr_qs:
        esperado.setdefault(mr.materia_id, {"materia": mr.materia.codigo,
                                            "escuela_id": mr.materia.escuela_id,
                                            "ras": {}})
        esperado[mr.materia_id]["ras"][mr.ra_id] = mr.ra.codigo

    # Cargado por (periodo, materia, seccion, profesor)
    cargado_qs = eval_qs.filter(vigente=True)
    if periodo_id:
        cargado_qs = cargado_qs.filter(periodo_id=periodo_id)

    cargado = {}
    for ev in cargado_qs.values("periodo__codigo", "periodo_id", "materia_id",
                                "materia__codigo", "seccion", "profesor_nombre", "ra_id"):
        clave = (ev["periodo_id"], ev["materia_id"], ev["seccion"], ev["profesor_nombre"])
        cargado.setdefault(clave, {
            "periodo": ev["periodo__codigo"], "materia": ev["materia__codigo"],
            "seccion": ev["seccion"], "profesor": ev["profesor_nombre"],
            "materia_id": ev["materia_id"], "ras_cargados": set(),
        })
        cargado[clave]["ras_cargados"].add(ev["ra_id"])

    detalle = []
    completas = 0
    for clave, info in cargado.items():
        esperado_materia = esperado.get(info["materia_id"], {"ras": {}})
        ras_esperados = set(esperado_materia["ras"].keys())
        faltan = ras_esperados - info["ras_cargados"]
        completa = len(ras_esperados) > 0 and not faltan
        if completa:
            completas += 1
        detalle.append({
            "periodo": info["periodo"], "materia": info["materia"],
            "seccion": info["seccion"], "profesor": info["profesor"],
            "esperados": len(ras_esperados), "cargados": len(info["ras_cargados"] & ras_esperados),
            "faltantes": sorted(esperado_materia["ras"][r] for r in faltan),
            "completa": completa,
        })

    detalle.sort(key=lambda d: (d["periodo"], d["materia"], d["seccion"]))

    total = len(detalle)
    return {
        "detalle": detalle,
        "total_combinaciones": total,
        "completas": completas,
        "pct_completitud": round(completas / total * 100, 1) if total else 0,
    }


# --- Bloque 7: Riesgo de acreditación -----------------------------------------

def riesgo_acreditacion(eval_qs, n_periodos=2):
    umbral = settings.SEMAFORO_UMBRAL_AMARILLO
    hallazgos = {
        "materias_sin_catalogo": [],
        "ras_sin_evidencia": [],
        "ras_bajo_umbral_consecutivo": [],
    }

    # Materias sin catálogo definido
    sin_catalogo = Materia.objects.filter(materia_ras__isnull=True)
    hallazgos["materias_sin_catalogo"] = [
        {"materia": m.codigo, "nombre": m.nombre} for m in sin_catalogo
    ]

    # RAs catalogados sin evidencia (ninguna evaluación vigente)
    con_evidencia = set(
        eval_qs.values_list("materia_id", "ra_id").distinct()
    )
    for mr in MateriaRA.objects.select_related("materia", "ra"):
        if (mr.materia_id, mr.ra_id) not in con_evidencia:
            hallazgos["ras_sin_evidencia"].append({
                "materia": mr.materia.codigo, "ra": mr.ra.codigo,
                "nivel_esperado": mr.nivel_esperado,
            })

    # RAs bajo umbral en periodos consecutivos
    periodos_orden = list(Periodo.objects.order_by("codigo").values_list("codigo", flat=True))
    orden_idx = {c: i for i, c in enumerate(periodos_orden)}
    por_materia_ra = {}
    for f in (eval_qs.values("materia__codigo", "ra__codigo", "periodo__codigo")
              .annotate(pct=Avg("pct_aprobados_recalculado"))):
        clave = (f["materia__codigo"], f["ra__codigo"])
        por_materia_ra.setdefault(clave, []).append((f["periodo__codigo"], float(f["pct"])))

    for (materia, ra), puntos in por_materia_ra.items():
        puntos.sort(key=lambda x: orden_idx.get(x[0], 0))
        consecutivos = 0
        max_consec = 0
        periodos_afectados = []
        for periodo, pct in puntos:
            if pct < umbral:
                consecutivos += 1
                periodos_afectados.append(periodo)
                max_consec = max(max_consec, consecutivos)
            else:
                consecutivos = 0
                periodos_afectados = []
        if max_consec >= n_periodos:
            hallazgos["ras_bajo_umbral_consecutivo"].append({
                "materia": materia, "ra": ra,
                "periodos_consecutivos": max_consec,
                "periodos": periodos_afectados[-max_consec:],
            })

    hallazgos["resumen"] = {
        "materias_sin_catalogo": len(hallazgos["materias_sin_catalogo"]),
        "ras_sin_evidencia": len(hallazgos["ras_sin_evidencia"]),
        "ras_bajo_umbral_consecutivo": len(hallazgos["ras_bajo_umbral_consecutivo"]),
    }
    return hallazgos


# --- Proxy de consistencia entre evaluadores ----------------------------------

def proxy_consistencia(eval_qs):
    """Compara distribuciones de la misma materia entre secciones/profesores.
    Es un PROXY, no consistencia inter-evaluador real (no hay doble calificación)."""
    filas = (
        eval_qs.values("materia__codigo", "ra__codigo", "seccion", "profesor_nombre")
        .annotate(pct=Avg("pct_aprobados_recalculado"), n=Count("id"))
    )
    agrupado = {}
    for f in filas:
        clave = (f["materia__codigo"], f["ra__codigo"])
        agrupado.setdefault(clave, []).append({
            "seccion": f["seccion"], "profesor": f["profesor_nombre"],
            "pct": round(float(f["pct"]), 2),
        })

    resultados = []
    for (materia, ra), grupos in agrupado.items():
        if len(grupos) < 2:
            continue
        pcts = [g["pct"] for g in grupos]
        dispersion = max(pcts) - min(pcts)
        resultados.append({
            "materia": materia, "ra": ra, "grupos": grupos,
            "dispersion": round(dispersion, 2),
            "alerta": dispersion >= 20,  # >20 puntos de diferencia
        })
    resultados.sort(key=lambda r: -r["dispersion"])
    return {"es_proxy": True, "resultados": resultados}
