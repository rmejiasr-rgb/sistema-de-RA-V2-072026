"""Orquesta parseo + validación + persistencia de una Carga."""

from django.core.files.uploadedfile import UploadedFile
from django.db import transaction

from .models import AuditLog, Carga, Criterio, Evaluacion, ResultadoCriterio, ResultadoEstudiante
from .parser import ParserError, normalizar_nivel_criterio, parse_workbook
from .validators import validar_carga


class CargaRechazada(Exception):
    def __init__(self, resultado_json):
        self.resultado_json = resultado_json
        super().__init__("Carga rechazada")


def procesar_carga(archivo: UploadedFile, usuario, confirmar_nueva_version=False):
    """Parsea, valida y (si corresponde) persiste una carga.

    Devuelve (carga, resultado_json). Lanza CargaRechazada si V1-V5 rechazan
    el archivo, o si V4 requiere confirmación explícita y aún no se dio.
    """
    contenido = archivo.read()
    archivo_hash = Carga.calcular_hash(contenido)
    archivo.seek(0)

    try:
        datos = parse_workbook(archivo, archivo.name)
    except ParserError as exc:
        resultado_json = {
            "aceptado": False,
            "requiere_confirmacion": False,
            "errores": [{"codigo": exc.codigo, "mensaje": exc.mensaje}],
            "advertencias": [],
        }
        _guardar_carga_rechazada(archivo, contenido, archivo_hash, usuario, resultado_json)
        raise CargaRechazada(resultado_json)

    resultado = validar_carga(datos, archivo.name, usuario, confirmar_nueva_version=confirmar_nueva_version)

    if not resultado.aceptado:
        resultado_json = resultado.to_json()
        _guardar_carga_rechazada(
            archivo, contenido, archivo_hash, usuario, resultado_json, datos=datos, resultado=resultado
        )
        raise CargaRechazada(resultado_json)

    if resultado.requiere_confirmacion:
        raise CargaRechazada(resultado.to_json())

    with transaction.atomic():
        version = 1
        if resultado.evaluacion_anterior is not None:
            version = resultado.evaluacion_anterior.carga.version + 1
            Evaluacion.objects.filter(id=resultado.evaluacion_anterior.id).update(vigente=False)

        archivo.seek(0)
        carga = Carga.objects.create(
            archivo=archivo,
            archivo_nombre_original=archivo.name,
            archivo_hash=archivo_hash,
            version=version,
            estado=Carga.ESTADO_VALIDADA,
            usuario=usuario,
            resultado_validacion=resultado.to_json(),
            periodo=resultado.periodo,
            materia=resultado.materia,
            seccion=datos.seccion,
            profesor_nombre=datos.profesor,
            ra=resultado.ra,
            nivel=datos.nivel,
        )

        evaluacion = Evaluacion.objects.create(
            carga=carga,
            periodo=resultado.periodo,
            materia=resultado.materia,
            seccion=datos.seccion,
            profesor_nombre=datos.profesor,
            ra=resultado.ra,
            nivel=datos.nivel,
            actividad=datos.actividad,
            fecha_actividad=datos.fecha_actividad,
            pct_aprobados_declarado=datos.pct_aprobados_declarado,
            pct_aprobados_recalculado=resultado.pct_aprobados_recalculado,
            vigente=True,
        )

        criterios_obj = {}
        for orden, nombre in enumerate(datos.criterios, start=1):
            criterios_obj[nombre] = Criterio.objects.create(
                evaluacion=evaluacion, nombre=nombre, orden=orden
            )

        resultados_estudiantes = ResultadoEstudiante.objects.bulk_create(
            [
                ResultadoEstudiante(
                    evaluacion=evaluacion,
                    grupo=est.grupo,
                    nombre=est.nombre,
                    carrera=est.carrera,
                    nota=est.nota,
                )
                for est in datos.estudiantes
            ]
        )

        resultados_criterio = []
        for est, resultado_est in zip(datos.estudiantes, resultados_estudiantes):
            for nombre_criterio, valor in est.niveles_por_criterio.items():
                resultados_criterio.append(
                    ResultadoCriterio(
                        resultado_estudiante=resultado_est,
                        criterio=criterios_obj[nombre_criterio],
                        nivel=normalizar_nivel_criterio(valor),
                    )
                )
        ResultadoCriterio.objects.bulk_create(resultados_criterio)

        AuditLog.objects.create(
            usuario=usuario,
            entidad="Carga",
            entidad_id=str(carga.id),
            campo="estado",
            valor_anterior="",
            valor_nuevo=f"VALIDADA (v{version})",
            motivo="Carga de archivo procesada y validada.",
        )

    return carga, resultado.to_json()


def _guardar_carga_rechazada(archivo, contenido, archivo_hash, usuario, resultado_json, datos=None, resultado=None):
    archivo.seek(0)
    Carga.objects.create(
        archivo=archivo,
        archivo_nombre_original=archivo.name,
        archivo_hash=archivo_hash,
        version=1,
        estado=Carga.ESTADO_RECHAZADA,
        usuario=usuario,
        resultado_validacion=resultado_json,
        periodo=getattr(resultado, "periodo", None) if resultado else None,
        materia=getattr(resultado, "materia", None) if resultado else None,
        seccion=getattr(datos, "seccion", None) if datos else None,
        profesor_nombre=getattr(datos, "profesor", None) if datos else None,
        ra=getattr(resultado, "ra", None) if resultado else None,
        nivel=getattr(datos, "nivel", None) if datos else None,
    )
