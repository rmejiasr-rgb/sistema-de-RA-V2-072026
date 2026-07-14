from django.core.exceptions import ValidationError
from django.db import models


class Escuela(models.Model):
    nombre = models.CharField(max_length=200, unique=True)
    codigo = models.CharField(max_length=20, unique=True)

    class Meta:
        verbose_name = "Escuela"
        verbose_name_plural = "Escuelas"
        ordering = ["nombre"]

    def __str__(self):
        return f"{self.codigo} — {self.nombre}"


class Carrera(models.Model):
    nombre = models.CharField(max_length=200)
    escuela = models.ForeignKey(Escuela, on_delete=models.PROTECT, related_name="carreras")

    class Meta:
        verbose_name = "Carrera"
        verbose_name_plural = "Carreras"
        unique_together = [("nombre", "escuela")]
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Periodo(models.Model):
    ESTADO_ABIERTO = "ABIERTO"
    ESTADO_CERRADO = "CERRADO"
    ESTADO_CHOICES = [
        (ESTADO_ABIERTO, "Abierto"),
        (ESTADO_CERRADO, "Cerrado"),
    ]

    # Código normalizado, ej. "2526-3" (año académico 25-26, trimestre 3)
    codigo = models.CharField(max_length=20, unique=True)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default=ESTADO_ABIERTO)

    class Meta:
        verbose_name = "Periodo"
        verbose_name_plural = "Periodos"
        ordering = ["-codigo"]

    def __str__(self):
        return self.codigo

    def clean(self):
        if self.fecha_inicio and self.fecha_fin and self.fecha_inicio > self.fecha_fin:
            raise ValidationError("La fecha de inicio no puede ser posterior a la fecha de fin.")


class Materia(models.Model):
    codigo = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=200)
    escuela = models.ForeignKey(Escuela, on_delete=models.PROTECT, related_name="materias")

    class Meta:
        verbose_name = "Materia"
        verbose_name_plural = "Materias"
        ordering = ["codigo"]

    def __str__(self):
        return f"{self.codigo} — {self.nombre}"


class RACatalogo(models.Model):
    # Código normalizado de catálogo, ej. "RA8", "RA10-IP"
    codigo = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)

    class Meta:
        verbose_name = "RA de catálogo"
        verbose_name_plural = "RAs de catálogo"
        ordering = ["codigo"]

    def __str__(self):
        return self.codigo


class MateriaRA(models.Model):
    """Catálogo maestro editable: qué RA(s) y en qué nivel debe evidenciar cada materia."""

    NIVEL_CHOICES = [(1, "Nivel 1"), (2, "Nivel 2"), (3, "Nivel 3")]

    materia = models.ForeignKey(Materia, on_delete=models.CASCADE, related_name="materia_ras")
    ra = models.ForeignKey(RACatalogo, on_delete=models.PROTECT, related_name="materia_ras")
    nivel_esperado = models.PositiveSmallIntegerField(choices=NIVEL_CHOICES)

    class Meta:
        verbose_name = "Materia ↔ RA esperado"
        verbose_name_plural = "Catálogo Materia ↔ RA"
        unique_together = [("materia", "ra")]
        ordering = ["materia__codigo", "ra__codigo"]

    def __str__(self):
        return f"{self.materia.codigo} → {self.ra.codigo} (Nivel {self.nivel_esperado})"
