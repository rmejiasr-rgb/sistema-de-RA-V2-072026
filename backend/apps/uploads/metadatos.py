"""
Edición de metadatos con auditoría (§2, §4 AuditLog).

Solo metadatos: actividad, fecha de actividad, nombre del profesor (mal escrito),
y nombre/carrera de estudiantes. Las notas/resultados NO se editan aquí: solo se
corrigen re-subiendo el archivo (versionado).
"""

from django.db import transaction

from .models import AuditLog, Evaluacion, ResultadoEstudiante

CAMPOS_EVALUACION = {"actividad", "fecha_actividad", "profesor_nombre", "seccion"}
CAMPOS_ESTUDIANTE = {"nombre", "carrera", "grupo"}


def _registrar(usuario, entidad, entidad_id, campo, anterior, nuevo, motivo):
    AuditLog.objects.create(
        usuario=usuario, entidad=entidad, entidad_id=str(entidad_id), campo=campo,
        valor_anterior="" if anterior is None else str(anterior),
        valor_nuevo="" if nuevo is None else str(nuevo), motivo=motivo or "",
    )


@transaction.atomic
def editar_metadatos_evaluacion(usuario, evaluacion, datos, motivo=""):
    """Aplica cambios de metadatos a una Evaluacion y su Carga, auditando cada campo."""
    cambios = []
    for campo in CAMPOS_EVALUACION:
        if campo not in datos:
            continue
        nuevo = datos[campo]
        anterior = getattr(evaluacion, campo)
        # Normalizar fecha a str comparable
        if str(anterior) == str(nuevo):
            continue
        setattr(evaluacion, campo, nuevo)
        _registrar(usuario, "Evaluacion", evaluacion.id, campo, anterior, nuevo, motivo)
        cambios.append(campo)

    if cambios:
        evaluacion.save(update_fields=cambios)
        # Reflejar clave de negocio en la Carga si cambió sección/profesor
        carga = evaluacion.carga
        actualizar_carga = []
        if "profesor_nombre" in cambios:
            carga.profesor_nombre = evaluacion.profesor_nombre
            actualizar_carga.append("profesor_nombre")
        if "seccion" in cambios:
            carga.seccion = evaluacion.seccion
            actualizar_carga.append("seccion")
        if actualizar_carga:
            carga.save(update_fields=actualizar_carga)

    return cambios


@transaction.atomic
def editar_estudiante(usuario, estudiante, datos, motivo=""):
    cambios = []
    for campo in CAMPOS_ESTUDIANTE:
        if campo not in datos:
            continue
        nuevo = datos[campo]
        anterior = getattr(estudiante, campo)
        if str(anterior) == str(nuevo):
            continue
        setattr(estudiante, campo, nuevo)
        _registrar(usuario, "ResultadoEstudiante", estudiante.id, campo, anterior, nuevo, motivo)
        cambios.append(campo)
    if cambios:
        estudiante.save(update_fields=cambios)
    return cambios
