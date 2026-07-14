"""
Completitud y cierre de periodo (§6 V6).

Una combinación (periodo, materia, sección, profesor) está COMPLETA cuando tiene
cargados todos los RAs del catálogo de esa materia. El cierre de periodo lista
faltantes y no permite cerrar con incompletos.
"""

from apps.catalog.models import MateriaRA
from apps.uploads.models import Evaluacion


def completitud_periodo(periodo, escuelas_ids=None):
    """Devuelve el estado de completitud de todas las combinaciones con al menos
    una carga vigente en el periodo. Si escuelas_ids se pasa, se acota a esas escuelas.
    """
    ev_qs = Evaluacion.objects.filter(periodo=periodo, vigente=True)
    if escuelas_ids is not None:
        ev_qs = ev_qs.filter(materia__escuela_id__in=escuelas_ids)

    # RAs esperados por materia (id -> {ra_id: codigo})
    mr_qs = MateriaRA.objects.select_related("ra", "materia")
    if escuelas_ids is not None:
        mr_qs = mr_qs.filter(materia__escuela_id__in=escuelas_ids)
    esperados = {}
    for mr in mr_qs:
        esperados.setdefault(mr.materia_id, {})[mr.ra_id] = mr.ra.codigo

    # RAs cargados por combinación
    cargado = {}
    for ev in ev_qs.values("materia_id", "materia__codigo", "seccion",
                           "profesor_nombre", "ra_id"):
        clave = (ev["materia_id"], ev["seccion"], ev["profesor_nombre"])
        cargado.setdefault(clave, {"materia": ev["materia__codigo"], "ras": set()})
        cargado[clave]["ras"].add(ev["ra_id"])

    completas = []
    incompletas = []
    for (materia_id, seccion, profesor), info in cargado.items():
        ras_esperados = esperados.get(materia_id, {})
        faltan_ids = set(ras_esperados.keys()) - info["ras"]
        item = {
            "materia": info["materia"],
            "seccion": seccion,
            "profesor": profesor,
            "esperados": len(ras_esperados),
            "cargados": len(info["ras"] & set(ras_esperados.keys())),
            "faltantes": sorted(ras_esperados[r] for r in faltan_ids),
        }
        if ras_esperados and not faltan_ids:
            completas.append(item)
        else:
            incompletas.append(item)

    completas.sort(key=lambda d: (d["materia"], d["seccion"]))
    incompletas.sort(key=lambda d: (d["materia"], d["seccion"]))
    total = len(completas) + len(incompletas)
    return {
        "periodo": periodo.codigo,
        "estado": periodo.estado,
        "completas": completas,
        "incompletas": incompletas,
        "total_combinaciones": total,
        "n_completas": len(completas),
        "n_incompletas": len(incompletas),
        "pct_completitud": round(len(completas) / total * 100, 1) if total else 0,
        "puede_cerrarse": len(incompletas) == 0 and total > 0,
    }
