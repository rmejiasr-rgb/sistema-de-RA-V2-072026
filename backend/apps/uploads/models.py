import hashlib

from django.conf import settings
from django.db import models


def ruta_carga(instance, filename):
    return f"cargas/{instance.periodo or 'sin_periodo'}/{filename}"


class Carga(models.Model):
    """Un archivo Excel subido. Cada re-subida con la misma clave de negocio crea una nueva versión."""

    ESTADO_PENDIENTE = "PENDIENTE"
    ESTADO_VALIDADA = "VALIDADA"
    ESTADO_RECHAZADA = "RECHAZADA"
    ESTADO_CHOICES = [
        (ESTADO_PENDIENTE, "Pendiente"),
        (ESTADO_VALIDADA, "Validada"),
        (ESTADO_RECHAZADA, "Rechazada"),
    ]

    archivo = models.FileField(upload_to=ruta_carga)
    archivo_nombre_original = models.CharField(max_length=255)
    archivo_hash = models.CharField(max_length=64, db_index=True)
    version = models.PositiveIntegerField(default=1)
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default=ESTADO_PENDIENTE)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="cargas"
    )
    creado_en = models.DateTimeField(auto_now_add=True)
    resultado_validacion = models.JSONField(default=dict, blank=True)

    # Clave de negocio parseada del archivo (poblada si V1 estructura pasa)
    periodo = models.ForeignKey(
        "catalog.Periodo", on_delete=models.PROTECT, null=True, blank=True, related_name="cargas"
    )
    materia = models.ForeignKey(
        "catalog.Materia", on_delete=models.PROTECT, null=True, blank=True, related_name="cargas"
    )
    seccion = models.CharField(max_length=20, null=True, blank=True)
    profesor_nombre = models.CharField(max_length=200, null=True, blank=True)
    ra = models.ForeignKey(
        "catalog.RACatalogo", on_delete=models.PROTECT, null=True, blank=True, related_name="cargas"
    )
    nivel = models.PositiveSmallIntegerField(null=True, blank=True)

    class Meta:
        verbose_name = "Carga"
        verbose_name_plural = "Cargas"
        ordering = ["-creado_en"]

    def __str__(self):
        return f"{self.archivo_nombre_original} (v{self.version}) — {self.estado}"

    @staticmethod
    def calcular_hash(contenido_bytes):
        return hashlib.sha256(contenido_bytes).hexdigest()


class Evaluacion(models.Model):
    """Cabecera parseada de una Carga VALIDADA. Clave única de negocio entre versiones vigentes."""

    carga = models.OneToOneField(Carga, on_delete=models.CASCADE, related_name="evaluacion")

    periodo = models.ForeignKey("catalog.Periodo", on_delete=models.PROTECT, related_name="evaluaciones")
    materia = models.ForeignKey("catalog.Materia", on_delete=models.PROTECT, related_name="evaluaciones")
    seccion = models.CharField(max_length=20)
    profesor_nombre = models.CharField(max_length=200)
    ra = models.ForeignKey("catalog.RACatalogo", on_delete=models.PROTECT, related_name="evaluaciones")
    nivel = models.PositiveSmallIntegerField()

    actividad = models.CharField(max_length=300)
    fecha_actividad = models.DateField()

    pct_aprobados_declarado = models.DecimalField(max_digits=6, decimal_places=3)
    pct_aprobados_recalculado = models.DecimalField(max_digits=6, decimal_places=3)

    # Solo una versión vigente por clave de negocio; versiones previas quedan con vigente=False
    vigente = models.BooleanField(default=True)

    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Evaluación"
        verbose_name_plural = "Evaluaciones"
        ordering = ["-creado_en"]
        constraints = [
            models.UniqueConstraint(
                fields=["periodo", "materia", "seccion", "profesor_nombre", "ra"],
                condition=models.Q(vigente=True),
                name="evaluacion_vigente_unica",
            )
        ]
        indexes = [
            models.Index(fields=["periodo", "materia", "ra"]),
            models.Index(fields=["periodo", "materia", "seccion", "profesor_nombre", "ra"]),
        ]

    def __str__(self):
        return f"{self.materia.codigo}/{self.seccion} · {self.ra.codigo} N{self.nivel} · {self.periodo.codigo}"

    @property
    def discrepancia_pct(self):
        return abs(self.pct_aprobados_declarado - self.pct_aprobados_recalculado) > 0


class Criterio(models.Model):
    evaluacion = models.ForeignKey(Evaluacion, on_delete=models.CASCADE, related_name="criterios")
    nombre = models.CharField(max_length=300)
    orden = models.PositiveSmallIntegerField()

    class Meta:
        verbose_name = "Criterio"
        verbose_name_plural = "Criterios"
        ordering = ["evaluacion", "orden"]
        unique_together = [("evaluacion", "orden")]

    def __str__(self):
        return self.nombre


class ResultadoEstudiante(models.Model):
    evaluacion = models.ForeignKey(
        Evaluacion, on_delete=models.CASCADE, related_name="resultados_estudiantes"
    )
    grupo = models.CharField(max_length=20, blank=True)
    nombre = models.CharField(max_length=200)
    carrera = models.CharField(max_length=200, blank=True)
    nota = models.DecimalField(max_digits=6, decimal_places=3)

    class Meta:
        verbose_name = "Resultado de estudiante"
        verbose_name_plural = "Resultados de estudiantes"
        ordering = ["evaluacion", "nombre"]

    def __str__(self):
        return f"{self.nombre} ({self.nota}%)"


class ResultadoCriterio(models.Model):
    EXCELENTE = "EXCELENTE"
    SATISFACTORIO = "SATISFACTORIO"
    INSATISFACTORIO = "INSATISFACTORIO"
    NIVEL_CHOICES = [
        (EXCELENTE, "Excelente"),
        (SATISFACTORIO, "Satisfactorio"),
        (INSATISFACTORIO, "Insatisfactorio"),
    ]

    resultado_estudiante = models.ForeignKey(
        ResultadoEstudiante, on_delete=models.CASCADE, related_name="resultados_criterios"
    )
    criterio = models.ForeignKey(Criterio, on_delete=models.CASCADE, related_name="resultados")
    nivel = models.CharField(max_length=20, choices=NIVEL_CHOICES)

    class Meta:
        verbose_name = "Resultado de criterio"
        verbose_name_plural = "Resultados de criterios"
        unique_together = [("resultado_estudiante", "criterio")]

    def __str__(self):
        return f"{self.resultado_estudiante.nombre} · {self.criterio.nombre}: {self.nivel}"


class AuditLog(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="acciones_auditadas"
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    entidad = models.CharField(max_length=100)
    entidad_id = models.CharField(max_length=50)
    campo = models.CharField(max_length=100)
    valor_anterior = models.TextField(blank=True)
    valor_nuevo = models.TextField(blank=True)
    motivo = models.TextField(blank=True)

    class Meta:
        verbose_name = "Registro de auditoría"
        verbose_name_plural = "Registros de auditoría"
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.timestamp} · {self.usuario} · {self.entidad}#{self.entidad_id}.{self.campo}"
