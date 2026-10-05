"""
Prepara el sistema para una demostración rápida en una sola orden:

  - crea un usuario administrador (admin / admin12345) si no existe;
  - carga un conjunto pequeño de datos de ejemplo si la base está vacía.

Pensado para que una persona sin experiencia pueda entrar y ver los tableros
inmediatamente. No usar en producción con datos reales.

Uso:
    python manage.py bootstrap_demo
"""

from datetime import date

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand

from apps.uploads.models import Evaluacion

Usuario = get_user_model()

ADMIN_USER = "admin"
ADMIN_PASS = "admin12345"


class Command(BaseCommand):
    help = "Crea un admin de demostración y carga datos de ejemplo si la base está vacía."

    def add_arguments(self, parser):
        parser.add_argument("--escala", type=int, default=150,
                            help="Cantidad de evaluaciones de ejemplo (default 150).")

    def handle(self, *args, **opts):
        # 1. Usuario administrador de demostración
        admin = Usuario.objects.filter(username=ADMIN_USER).first()
        if admin is None:
            admin = Usuario.objects.create_superuser(
                username=ADMIN_USER, email="admin@unimet.edu.ve", password=ADMIN_PASS,
                first_name="Administrador", last_name="Demo",
            )
            self.stdout.write(self.style.SUCCESS(
                f"Usuario administrador creado: {ADMIN_USER} / {ADMIN_PASS}"
            ))
        else:
            self.stdout.write(f"El usuario '{ADMIN_USER}' ya existe (no se cambia la contraseña).")

        # 2. Datos de ejemplo (solo si la base está vacía). Si por cualquier
        #    motivo la generación falla, se registra el aviso pero NO se detiene
        #    el arranque: el sistema igual queda disponible para iniciar sesión.
        if Evaluacion.objects.exists():
            self.stdout.write("Ya hay datos cargados; no se generan datos de ejemplo.")
        else:
            self.stdout.write("Generando datos de ejemplo (puede tardar un momento)…")
            try:
                call_command("seed_demo", escala=opts["escala"])
            except Exception as exc:  # noqa: BLE001 — queremos que el arranque no falle
                self.stderr.write(self.style.WARNING(
                    f"Aviso: no se pudieron generar los datos de ejemplo ({exc}). "
                    "El sistema arranca igual; podrás cargar datos manualmente."
                ))

        # 3. Catálogo para los archivos de EJEMPLO que vienen con el proyecto
        #    (materia FPTPI13, RA10-IP y RA11-IP). Así esos dos .xlsx se pueden
        #    cargar desde la pantalla "Cargar archivo" sin registrar nada a mano.
        self._registrar_catalogo_de_ejemplo()

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("¡Listo! Ya puedes entrar al sistema."))
        self.stdout.write("  Abre en el navegador:  http://localhost:5173")
        self.stdout.write(f"  Usuario:  {ADMIN_USER}")
        self.stdout.write(f"  Clave:    {ADMIN_PASS}")

    def _registrar_catalogo_de_ejemplo(self):
        """Registra, de forma idempotente, la materia y RAs de los archivos de
        ejemplo del proyecto, para que esos .xlsx se puedan cargar y validar."""
        from apps.catalog.models import (
            Escuela, Materia, MateriaRA, Periodo, RACatalogo,
        )

        try:
            escuela, _ = Escuela.objects.get_or_create(
                codigo="PROD", defaults={"nombre": "Escuela de Ingeniería de Producción"},
            )
            materia, _ = Materia.objects.get_or_create(
                codigo="FPTPI13",
                defaults={"nombre": "Productividad", "escuela": escuela},
            )
            Periodo.objects.get_or_create(
                codigo="2526-3",
                defaults={"fecha_inicio": date(2026, 1, 1), "fecha_fin": date(2026, 12, 31)},
            )
            for codigo_ra, nombre_ra in [("RA10-IP", "RA10 IP"), ("RA11-IP", "RA11 IP")]:
                ra, _ = RACatalogo.objects.get_or_create(
                    codigo=codigo_ra, defaults={"nombre": nombre_ra},
                )
                MateriaRA.objects.get_or_create(
                    materia=materia, ra=ra, defaults={"nivel_esperado": 3},
                )
            self.stdout.write(
                "Catálogo de ejemplo listo: materia FPTPI13 (RA10-IP, RA11-IP). "
                "Ya puedes cargar los .xlsx de ejemplo del proyecto."
            )
        except Exception as exc:  # noqa: BLE001 — no debe detener el arranque
            self.stderr.write(self.style.WARNING(
                f"Aviso: no se pudo registrar el catálogo de ejemplo ({exc})."
            ))
