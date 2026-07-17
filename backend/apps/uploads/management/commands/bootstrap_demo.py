"""
Prepara el sistema para una demostración rápida en una sola orden:

  - crea un usuario administrador (admin / admin12345) si no existe;
  - carga un conjunto pequeño de datos de ejemplo si la base está vacía.

Pensado para que una persona sin experiencia pueda entrar y ver los tableros
inmediatamente. No usar en producción con datos reales.

Uso:
    python manage.py bootstrap_demo
"""

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

        # 2. Datos de ejemplo (solo si la base está vacía)
        if Evaluacion.objects.exists():
            self.stdout.write("Ya hay datos cargados; no se generan datos de ejemplo.")
        else:
            self.stdout.write("Generando datos de ejemplo (puede tardar un momento)…")
            call_command("seed_demo", escala=opts["escala"])

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("¡Listo! Ya puedes entrar al sistema."))
        self.stdout.write("  Abre en el navegador:  http://localhost:5173")
        self.stdout.write(f"  Usuario:  {ADMIN_USER}")
        self.stdout.write(f"  Clave:    {ADMIN_PASS}")
