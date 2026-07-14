"""
Genera un seed sintético a escala (§9): ~3.000 evaluaciones × ~40 estudiantes,
multi-periodo, para probar el rendimiento de los tableros (<2 s).

Uso:
    python manage.py seed_demo                # escala completa (~3000 evaluaciones)
    python manage.py seed_demo --escala 200   # escala reducida para desarrollo
    python manage.py seed_demo --limpiar      # borra datos sintéticos previos

No usa datos personales reales: nombres de estudiantes son generados.
"""

import random
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts.models import RolAsignado
from apps.catalog.models import Carrera, Escuela, Materia, MateriaRA, Periodo, RACatalogo
from apps.uploads.models import (
    Carga,
    Criterio,
    Evaluacion,
    ResultadoCriterio,
    ResultadoEstudiante,
)

Usuario = get_user_model()

NIVELES = [
    ResultadoCriterio.EXCELENTE,
    ResultadoCriterio.SATISFACTORIO,
    ResultadoCriterio.INSATISFACTORIO,
]

NOMBRES = [
    "Ana", "Luis", "María", "Carlos", "Sofía", "José", "Valentina", "Diego",
    "Camila", "Andrés", "Isabella", "Miguel", "Gabriela", "Javier", "Daniela",
    "Ricardo", "Paula", "Fernando", "Lucía", "Alejandro", "Victoria", "Manuel",
    "Adriana", "Roberto", "Natalia", "Pedro", "Andrea", "Santiago", "Elena", "Rafael",
]
APELLIDOS = [
    "González", "Rodríguez", "Pérez", "Martínez", "López", "Sánchez", "Ramírez",
    "Torres", "Flores", "Rivera", "Gómez", "Díaz", "Reyes", "Morales", "Cruz",
    "Ortiz", "Gutiérrez", "Chávez", "Ramos", "Herrera", "Medina", "Castillo",
]

ESCUELAS = [
    ("Escuela de Ingeniería de Producción", "PROD"),
    ("Escuela de Ingeniería de Sistemas", "SIS"),
    ("Escuela de Ingeniería Química", "QUI"),
    ("Escuela de Ingeniería Civil", "CIV"),
    ("Escuela de Ingeniería Mecánica", "MEC"),
]

CARRERAS = [
    "Ingeniería de Producción", "Ingeniería de Sistemas", "Ingeniería Química",
    "Ingeniería Civil", "Ingeniería Mecánica", "Ingeniería Eléctrica",
]

CRITERIOS_POOL = [
    "Identificación y análisis de problemas de ingeniería",
    "Aplicación de conocimientos técnicos para la resolución de problemas",
    "Consideración de restricciones y normativas",
    "Enfoque en la sostenibilidad e impacto social",
    "Selección y aplicación de recursos y herramientas modernas",
    "Predicción y modelación en la resolución de problemas complejos",
    "Optimización y mejora de procesos",
    "Comunicación efectiva de resultados",
]

PERIODOS = ["2324-1", "2324-2", "2324-3", "2425-1", "2425-2", "2425-3", "2526-1", "2526-2", "2526-3"]

PREFIJO_SINTETICO = "SEED"


class Command(BaseCommand):
    help = "Genera un seed sintético a escala para probar los tableros."

    def add_arguments(self, parser):
        parser.add_argument("--escala", type=int, default=3000,
                            help="Número aproximado de evaluaciones a generar (default 3000).")
        parser.add_argument("--estudiantes", type=int, default=40,
                            help="Estudiantes por evaluación (default 40).")
        parser.add_argument("--limpiar", action="store_true",
                            help="Borra los datos sintéticos previos antes de generar.")
        parser.add_argument("--semilla", type=int, default=42)

    def handle(self, *args, **opts):
        random.seed(opts["semilla"])
        if opts["limpiar"]:
            self._limpiar()

        with transaction.atomic():
            escuelas = self._crear_escuelas()
            carreras = self._crear_carreras(escuelas)
            periodos = self._crear_periodos()
            ras = self._crear_ras()
            materias, materia_ras = self._crear_materias(escuelas, ras)
            usuario = self._crear_usuario_seed(escuelas)

        self._generar_evaluaciones(
            materias, materia_ras, periodos, carreras, usuario,
            objetivo=opts["escala"], n_estudiantes=opts["estudiantes"],
        )
        self.stdout.write(self.style.SUCCESS("Seed sintético generado."))

    def _limpiar(self):
        # Solo borra datos sintéticos. No toca periodos ni RAs porque pueden
        # compartirse con cargas reales; se reutilizan vía get_or_create.
        self.stdout.write("Borrando datos sintéticos previos…")
        Carga.objects.filter(archivo_nombre_original__startswith=PREFIJO_SINTETICO).delete()
        Materia.objects.filter(codigo__startswith=PREFIJO_SINTETICO).delete()
        # Los RA-SEED ya no tienen referencias tras borrar materias sintéticas.
        RACatalogo.objects.filter(codigo__startswith="RA-SEED").delete()
        Usuario.objects.filter(username="seed_profesor").delete()

    def _crear_escuelas(self):
        objetos = []
        for nombre, codigo in ESCUELAS:
            esc, _ = Escuela.objects.get_or_create(codigo=codigo, defaults={"nombre": nombre})
            objetos.append(esc)
        return objetos

    def _crear_carreras(self, escuelas):
        objetos = []
        for i, nombre in enumerate(CARRERAS):
            escuela = escuelas[i % len(escuelas)]
            car, _ = Carrera.objects.get_or_create(nombre=nombre, escuela=escuela)
            objetos.append(car)
        return objetos

    def _crear_periodos(self):
        objetos = []
        for i, codigo in enumerate(PERIODOS):
            inicio = date(2023, 1, 1) + timedelta(days=120 * i)
            estado = Periodo.ESTADO_CERRADO if i < len(PERIODOS) - 1 else Periodo.ESTADO_ABIERTO
            per, _ = Periodo.objects.get_or_create(
                codigo=codigo,
                defaults={"fecha_inicio": inicio, "fecha_fin": inicio + timedelta(days=90), "estado": estado},
            )
            objetos.append(per)
        return objetos

    def _crear_ras(self):
        objetos = []
        for i in range(1, 13):
            codigo = f"RA-SEED{i}"
            ra, _ = RACatalogo.objects.get_or_create(
                codigo=codigo,
                defaults={"nombre": f"Resultado de Aprendizaje sintético {i}",
                          "descripcion": f"Descripción del RA sintético {i}."},
            )
            objetos.append(ra)
        return objetos

    def _crear_materias(self, escuelas, ras):
        materias = []
        materia_ras = {}
        idx = 0
        for escuela in escuelas:
            for m in range(10):  # 10 materias por escuela = 50 materias
                idx += 1
                codigo = f"{PREFIJO_SINTETICO}{idx:03d}"
                materia, _ = Materia.objects.get_or_create(
                    codigo=codigo,
                    defaults={"nombre": f"Materia sintética {idx}", "escuela": escuela},
                )
                materias.append(materia)
                # 3 RAs por materia
                ras_materia = random.sample(ras, 3)
                lista = []
                for ra in ras_materia:
                    nivel = random.choice([1, 2, 3])
                    mr, _ = MateriaRA.objects.get_or_create(
                        materia=materia, ra=ra, defaults={"nivel_esperado": nivel}
                    )
                    lista.append(mr)
                materia_ras[materia.id] = lista
        return materias, materia_ras

    def _crear_usuario_seed(self, escuelas):
        usuario, creado = Usuario.objects.get_or_create(
            username="seed_profesor",
            defaults={"first_name": "Profesor", "last_name": "Sintético",
                      "email": "seed@example.com", "escuela": escuelas[0]},
        )
        if creado:
            usuario.set_password("seed12345")
            usuario.save()
            RolAsignado.objects.get_or_create(
                usuario=usuario, rol=RolAsignado.PROFESOR, escuela=escuelas[0]
            )
        return usuario

    def _perfil_desempeno(self):
        """Devuelve pesos [excelente, satisfactorio, insatisfactorio] variados
        para que los tableros muestren semáforos verdes/amarillos/rojos."""
        return random.choice([
            [0.5, 0.4, 0.1],   # bueno
            [0.2, 0.6, 0.2],   # medio
            [0.1, 0.5, 0.4],   # flojo
            [0.05, 0.35, 0.6], # crítico
            [0.7, 0.25, 0.05], # excelente
        ])

    def _generar_evaluaciones(self, materias, materia_ras, periodos, carreras,
                              usuario, objetivo, n_estudiantes):
        self.stdout.write(f"Generando ~{objetivo} evaluaciones…")
        creadas = 0
        # Recorremos combinaciones materia × RA-catalogado × periodo × sección
        combinaciones = []
        for materia in materias:
            for mr in materia_ras[materia.id]:
                for periodo in periodos:
                    for seccion in ("1", "2", "3"):
                        combinaciones.append((materia, mr, periodo, seccion))
        random.shuffle(combinaciones)

        for materia, mr, periodo, seccion in combinaciones:
            if creadas >= objetivo:
                break
            self._crear_una_evaluacion(
                materia, mr, periodo, seccion, carreras, usuario, n_estudiantes
            )
            creadas += 1
            if creadas % 250 == 0:
                self.stdout.write(f"  {creadas} evaluaciones…")
        self.stdout.write(self.style.SUCCESS(f"  {creadas} evaluaciones creadas."))

    def _crear_una_evaluacion(self, materia, mr, periodo, seccion, carreras,
                              usuario, n_estudiantes):
        n_criterios = random.choice([3, 4])
        nombres_criterios = random.sample(CRITERIOS_POOL, n_criterios)
        pesos = self._perfil_desempeno()

        carga = Carga.objects.create(
            archivo="cargas/synthetic.xlsx",
            archivo_nombre_original=f"{PREFIJO_SINTETICO}-{materia.codigo}-{seccion}-{periodo.codigo}-{mr.ra.codigo}.xlsx",
            archivo_hash=f"seed{random.getrandbits(200):050x}"[:64],
            version=1,
            estado=Carga.ESTADO_VALIDADA,
            usuario=usuario,
            periodo=periodo,
            materia=materia,
            seccion=seccion,
            profesor_nombre=f"{usuario.first_name} {usuario.last_name}",
            ra=mr.ra,
            nivel=mr.nivel_esperado,
        )

        criterios_niveles = []  # (estudiante_idx -> list of niveles)
        total_eval = 0
        aprobados = 0
        estudiantes = []
        for _ in range(n_estudiantes):
            niveles_est = []
            aprob_criterios = 0
            for _ in range(n_criterios):
                nivel = random.choices(NIVELES, weights=pesos)[0]
                niveles_est.append(nivel)
                total_eval += 1
                if nivel in (ResultadoCriterio.EXCELENTE, ResultadoCriterio.SATISFACTORIO):
                    aprobados += 1
                    aprob_criterios += 1
            nota = Decimal(aprob_criterios) / Decimal(n_criterios) * 100
            estudiantes.append((niveles_est, nota.quantize(Decimal("0.001"))))
            criterios_niveles.append(niveles_est)

        pct = (Decimal(aprobados) / Decimal(total_eval) * 100).quantize(Decimal("0.001")) if total_eval else Decimal(0)

        evaluacion = Evaluacion.objects.create(
            carga=carga, periodo=periodo, materia=materia, seccion=seccion,
            profesor_nombre=carga.profesor_nombre, ra=mr.ra, nivel=mr.nivel_esperado,
            actividad=f"Actividad evaluativa {mr.ra.codigo}",
            fecha_actividad=periodo.fecha_inicio + timedelta(days=random.randint(10, 80)),
            pct_aprobados_declarado=pct, pct_aprobados_recalculado=pct, vigente=True,
        )

        criterios_obj = [
            Criterio.objects.create(evaluacion=evaluacion, nombre=nombre, orden=i + 1)
            for i, nombre in enumerate(nombres_criterios)
        ]

        resultados_est = ResultadoEstudiante.objects.bulk_create([
            ResultadoEstudiante(
                evaluacion=evaluacion, grupo=str(random.randint(1, 8)),
                nombre=f"{random.choice(NOMBRES)} {random.choice(APELLIDOS)}",
                carrera=random.choice(carreras).nombre, nota=nota,
            )
            for niveles_est, nota in estudiantes
        ])

        rc = []
        for (niveles_est, _), res_est in zip(estudiantes, resultados_est):
            for criterio, nivel in zip(criterios_obj, niveles_est):
                rc.append(ResultadoCriterio(
                    resultado_estudiante=res_est, criterio=criterio, nivel=nivel
                ))
        ResultadoCriterio.objects.bulk_create(rc)
