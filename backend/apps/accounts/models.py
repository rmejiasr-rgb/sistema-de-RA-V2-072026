from django.contrib.auth.models import AbstractUser
from django.db import models


class Usuario(AbstractUser):
    """Usuario del sistema. Puede tener más de un rol (ver RolAsignado)."""

    escuela = models.ForeignKey(
        "catalog.Escuela",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="usuarios",
        help_text="Escuela principal del usuario (para profesores).",
    )

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"

    def __str__(self):
        return self.get_full_name() or self.username

    def tiene_rol(self, rol, escuela=None):
        qs = self.roles.filter(rol=rol)
        if escuela is not None:
            qs = qs.filter(models.Q(escuela__isnull=True) | models.Q(escuela=escuela))
        return qs.exists()

    @property
    def es_administrador(self):
        return self.is_superuser or self.tiene_rol(RolAsignado.ADMINISTRADOR)

    @property
    def es_coordinador(self):
        return self.tiene_rol(RolAsignado.COORDINADOR)

    @property
    def es_profesor(self):
        return self.tiene_rol(RolAsignado.PROFESOR)

    def escuelas_coordinadas(self):
        """Escuelas donde el usuario tiene rol de coordinador (None = todas)."""
        from apps.catalog.models import Escuela

        asignaciones = self.roles.filter(rol=RolAsignado.COORDINADOR)
        if asignaciones.filter(escuela__isnull=True).exists():
            return Escuela.objects.all()
        return Escuela.objects.filter(id__in=asignaciones.values_list("escuela_id", flat=True))


class RolAsignado(models.Model):
    """Asigna un rol a un usuario, opcionalmente acotado a una escuela (coordinador)."""

    PROFESOR = "PROFESOR"
    COORDINADOR = "COORDINADOR"
    ADMINISTRADOR = "ADMINISTRADOR"
    ROL_CHOICES = [
        (PROFESOR, "Profesor"),
        (COORDINADOR, "Coordinador"),
        (ADMINISTRADOR, "Administrador"),
    ]

    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="roles")
    rol = models.CharField(max_length=20, choices=ROL_CHOICES)
    escuela = models.ForeignKey(
        "catalog.Escuela",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="roles_asignados",
        help_text="Dejar vacío para Administrador (alcance global) o Coordinador de toda la universidad.",
    )

    class Meta:
        verbose_name = "Rol asignado"
        verbose_name_plural = "Roles asignados"
        unique_together = [("usuario", "rol", "escuela")]

    def __str__(self):
        alcance = f" ({self.escuela.codigo})" if self.escuela else ""
        return f"{self.usuario} — {self.get_rol_display()}{alcance}"
