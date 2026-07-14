"""
Motor de validaciones V1-V6 (§6 de la especificación).

V1 (estructura) ya se resuelve en parser.parse_workbook (lanza ParserError).
Este módulo cubre V2-V5 sobre el resultado del parseo, y expone utilidades
para V6 (completitud), que no bloquea la carga sino el cierre de periodo.
"""

from dataclasses import dataclass, field
from decimal import Decimal

from apps.catalog.models import MateriaRA, Materia, Periodo, RACatalogo

from .parser import normalizar_nivel_criterio, normalizar_texto
from .models import Evaluacion


@dataclass
class ErrorValidacion:
    codigo: str
    mensaje: str

    def as_dict(self):
        return {"codigo": self.codigo, "mensaje": self.mensaje}


@dataclass
class ResultadoValidacion:
    errores: list = field(default_factory=list)
    advertencias: list = field(default_factory=list)
    materia: object = None
    periodo: object = None
    ra: object = None
    nivel_esperado: object = None
    pct_aprobados_recalculado: Decimal = None
    conteos_recalculados: dict = None
    evaluacion_anterior: object = None
    requiere_confirmacion: bool = False

    @property
    def aceptado(self):
        return not self.errores

    def agregar_error(self, codigo, mensaje):
        self.errores.append(ErrorValidacion(codigo, mensaje))

    def agregar_advertencia(self, codigo, mensaje):
        self.advertencias.append(ErrorValidacion(codigo, mensaje))

    def to_json(self):
        return {
            "aceptado": self.aceptado,
            "requiere_confirmacion": self.requiere_confirmacion,
            "errores": [e.as_dict() for e in self.errores],
            "advertencias": [a.as_dict() for a in self.advertencias],
        }


def validar_carga(datos, nombre_archivo, usuario, confirmar_nueva_version=False):
    """Ejecuta V2-V5 sobre un ArchivoParseado. Devuelve ResultadoValidacion."""
    resultado = ResultadoValidacion()

    # --- V2: consistencia archivo <-> contenido -------------------------------
    info_archivo = datos.nombre_archivo_info
    if info_archivo is None:
        resultado.agregar_error(
            "V2_NOMBRE_ARCHIVO",
            f"El nombre del archivo '{nombre_archivo}' no sigue el patrón esperado "
            "'CODMAT-SECCION-PROFESOR-PERIODO-RA-NIVEL.xlsx' (ej. "
            "'FPTPI13-1-RICHARD_MEJIAS-2526-3-RA10-IP-N3.xlsx'). Renombre el archivo "
            "y vuelva a intentarlo.",
        )
        return resultado

    discrepancias = []
    if info_archivo["seccion"] != datos.seccion:
        discrepancias.append(
            f"Sección: archivo='{info_archivo['seccion']}' vs. contenido='{datos.seccion}'"
        )
    if info_archivo["periodo"] != datos.periodo_codigo:
        discrepancias.append(
            f"Periodo: archivo='{info_archivo['periodo']}' vs. contenido='{datos.periodo_codigo}'"
        )
    if info_archivo["ra"] != datos.ra_codigo:
        discrepancias.append(
            f"RA: archivo='{info_archivo['ra']}' vs. contenido='{datos.ra_codigo}'"
        )
    if info_archivo["nivel"] != datos.nivel:
        discrepancias.append(
            f"Nivel: archivo='{info_archivo['nivel']}' vs. contenido='{datos.nivel}'"
        )
    if not _nombres_profesor_compatibles(info_archivo["profesor"], datos.profesor):
        discrepancias.append(
            f"Profesor: archivo='{info_archivo['profesor']}' vs. contenido='{datos.profesor}'"
        )
    if discrepancias:
        resultado.agregar_error(
            "V2_DISCREPANCIA",
            "El nombre del archivo no coincide con el contenido de la plantilla: "
            + "; ".join(discrepancias) + ".",
        )
        return resultado

    materia = Materia.objects.filter(codigo__iexact=info_archivo["codmat"]).first()
    if materia is None:
        resultado.agregar_error(
            "V3_MATERIA_NO_CATALOGADA",
            f"La materia con código '{info_archivo['codmat']}' no existe en el catálogo del "
            "sistema. Contacte al coordinador de su escuela para registrarla.",
        )
        return resultado
    resultado.materia = materia

    periodo = Periodo.objects.filter(codigo=datos.periodo_codigo).first()
    if periodo is None:
        resultado.agregar_error(
            "V2_PERIODO_NO_REGISTRADO",
            f"El periodo '{datos.periodo_codigo}' no está registrado en el sistema. "
            "Contacte al administrador para crearlo antes de volver a cargar el archivo.",
        )
        return resultado
    resultado.periodo = periodo

    ra = RACatalogo.objects.filter(codigo__iexact=datos.ra_codigo).first()
    if ra is None:
        resultado.agregar_error(
            "V3_RA_NO_CATALOGADO",
            f"El RA '{datos.ra_codigo}' no existe en el catálogo general de RAs del sistema. "
            "Contacte al coordinador de su escuela.",
        )
        return resultado
    resultado.ra = ra

    # --- V3: (materia, RA, nivel) debe existir en MateriaRA ---------------------
    materia_ras = list(MateriaRA.objects.filter(materia=materia).select_related("ra"))
    if not materia_ras:
        resultado.agregar_error(
            "V3_MATERIA_SIN_CATALOGO",
            f"La materia '{materia.codigo}' no tiene ningún RA catalogado. "
            "Contacte al coordinador de su escuela para definir el catálogo Materia→RA.",
        )
        return resultado

    coincidencia = next((mr for mr in materia_ras if mr.ra_id == ra.id), None)
    if coincidencia is None:
        esperados = ", ".join(f"{mr.ra.codigo} (Nivel {mr.nivel_esperado})" for mr in materia_ras)
        resultado.agregar_error(
            "V3_RA_NO_ESPERADO",
            f"La materia '{materia.codigo}' no tiene catalogado el RA '{ra.codigo}'. "
            f"RAs esperados para esta materia: {esperados}.",
        )
        return resultado

    if coincidencia.nivel_esperado != datos.nivel:
        resultado.agregar_error(
            "V3_NIVEL_NO_ESPERADO",
            f"La materia '{materia.codigo}' espera el RA '{ra.codigo}' en Nivel "
            f"{coincidencia.nivel_esperado}, pero el archivo trae Nivel {datos.nivel}.",
        )
        return resultado
    resultado.nivel_esperado = coincidencia.nivel_esperado

    # --- V4: duplicado / versión -------------------------------------------------
    vigente_existente = Evaluacion.objects.filter(
        periodo=periodo,
        materia=materia,
        seccion=datos.seccion,
        profesor_nombre=datos.profesor,
        ra=ra,
        vigente=True,
    ).select_related("carga__usuario").first()

    if vigente_existente is not None:
        carga_previa = vigente_existente.carga
        puede_re_subir = (
            carga_previa.usuario_id == usuario.id
            or usuario.es_administrador
            or (usuario.es_coordinador and usuario.id in _ids_coordinador_escuela(usuario, materia))
        )
        if not puede_re_subir:
            resultado.agregar_error(
                "V4_DUPLICADO_OTRO_USUARIO",
                "Ya existe una carga vigente para esta combinación (periodo, materia, "
                f"sección {datos.seccion}, profesor, RA {ra.codigo}) subida por otro usuario. "
                "Si corresponde a una corrección, contacte al coordinador de su escuela.",
            )
            return resultado
        resultado.evaluacion_anterior = vigente_existente
        if not confirmar_nueva_version:
            resultado.requiere_confirmacion = True
            resultado.agregar_advertencia(
                "V4_NUEVA_VERSION",
                f"Ya existe una versión (v{carga_previa.version}) para esta combinación. "
                "Confirme para re-subir como nueva versión; la versión anterior se conservará "
                "consultable pero dejará de ser la vigente.",
            )

    # --- V5: datos -----------------------------------------------------------
    nombres_vistos = {}
    for est in datos.estudiantes:
        clave_nombre = normalizar_texto(est.nombre)
        nombres_vistos.setdefault(clave_nombre, []).append(est)

    for clave, filas in nombres_vistos.items():
        if len(filas) > 1:
            resultado.agregar_error(
                "V5_ESTUDIANTE_DUPLICADO",
                f"El estudiante '{filas[0].nombre}' aparece {len(filas)} veces en el archivo "
                f"(filas {', '.join(str(f.fila_excel) for f in filas)}).",
            )

    total_criterio_eval = 0
    aprobados_criterio_eval = 0
    for est in datos.estudiantes:
        if est.nota is None or est.nota < 0 or est.nota > 100:
            resultado.agregar_error(
                "V5_NOTA_FUERA_DE_RANGO",
                f"La nota de '{est.nombre}' (fila {est.fila_excel}) es inválida o está fuera "
                f"del rango 0-100: '{est.nota}'.",
            )
        for nombre_criterio, valor_nivel in est.niveles_por_criterio.items():
            nivel_normalizado = normalizar_nivel_criterio(valor_nivel)
            if nivel_normalizado is None:
                resultado.agregar_error(
                    "V5_NIVEL_INVALIDO",
                    f"El nivel de '{est.nombre}' en el criterio '{nombre_criterio}' "
                    f"(fila {est.fila_excel}) no es uno de Excelente/Satisfactorio/"
                    f"Insatisfactorio: '{valor_nivel}'.",
                )
                continue
            total_criterio_eval += 1
            if nivel_normalizado in ("EXCELENTE", "SATISFACTORIO"):
                aprobados_criterio_eval += 1

    if resultado.errores:
        return resultado

    pct_recalculado = (
        (Decimal(aprobados_criterio_eval) / Decimal(total_criterio_eval) * 100)
        if total_criterio_eval
        else Decimal("0")
    )
    pct_recalculado = pct_recalculado.quantize(Decimal("0.001"))
    resultado.pct_aprobados_recalculado = pct_recalculado
    resultado.conteos_recalculados = {
        "total_evaluaciones_criterio": total_criterio_eval,
        "aprobadas": aprobados_criterio_eval,
    }

    if abs(pct_recalculado - datos.pct_aprobados_declarado) > Decimal("0.01"):
        resultado.agregar_advertencia(
            "V5_DISCREPANCIA_PCT",
            f"El % de aprobados declarado en el archivo ({datos.pct_aprobados_declarado}%) "
            f"no coincide con el recalculado a partir del detalle ({pct_recalculado}%). "
            "Se guardaron ambos valores.",
        )

    return resultado


def _nombres_profesor_compatibles(nombre_archivo, nombre_contenido):
    """Compara nombres de forma tolerante: el nombre del archivo suele venir
    abreviado (sin segundo nombre). Se acepta si el conjunto de palabras de
    uno es subconjunto del otro (ignorando acentos, may/min y orden)."""
    tokens_archivo = set(normalizar_texto(nombre_archivo).split())
    tokens_contenido = set(normalizar_texto(nombre_contenido).split())
    if not tokens_archivo or not tokens_contenido:
        return False
    return tokens_archivo <= tokens_contenido or tokens_contenido <= tokens_archivo


def _ids_coordinador_escuela(usuario, materia):
    if usuario.escuelas_coordinadas().filter(id=materia.escuela_id).exists():
        return {usuario.id}
    return set()


def materia_seccion_completa(periodo, materia, seccion, profesor_nombre):
    """V6: True si están cargados todos los RAs catalogados para la materia."""
    ras_esperados = set(
        MateriaRA.objects.filter(materia=materia).values_list("ra_id", "nivel_esperado")
    )
    if not ras_esperados:
        return False, set(), set()

    ras_cargados = set(
        Evaluacion.objects.filter(
            periodo=periodo,
            materia=materia,
            seccion=seccion,
            profesor_nombre=profesor_nombre,
            vigente=True,
        ).values_list("ra_id", "nivel")
    )
    faltantes = ras_esperados - ras_cargados
    return (len(faltantes) == 0), ras_esperados, faltantes
