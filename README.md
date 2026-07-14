# Sistema de Gestión y Análisis de Resultados de Aprendizaje (RA) · UNIMET

Implementación de las **Fases 1 a 4** de la especificación (`SPECSistemaRAUNIMET.md`):

- **Fase 1 — Núcleo**: modelos de datos, parser de Excel, validaciones V1–V6,
  catálogo Materia→RA, API REST, tablero mínimo (bloques 1–2) y login local.
- **Fase 2 — Analítica**: bloques 3–7 del tablero (mapas de calor, carrera/grupo,
  tendencias, cobertura, riesgo) + proxy de consistencia, cierre de periodo (V6),
  edición de metadatos con auditoría, exportación Excel/PDF, seed sintético a
  escala (~3.000 evaluaciones, tableros <2 s) e identidad visual UNIMET.
- **Fase 3 — Multiusuario**: roles y permisos, pantallas de coordinador (catálogo,
  completitud, faltantes), gestión de usuarios y SSO Microsoft Entra ID (opcional).
- **Fase 4 — Despliegue**: docker-compose de producción (nginx + TLS + gunicorn),
  HTTPS, backups automatizados y manuales de usuario (ver `docs/`).

## Nota sobre el stack

El spec (§2, "decisiones ya tomadas") especifica **Django templates + HTMX + ECharts, sin
SPA/React**. Este proyecto se construyó con **React** en el frontend por instrucción
explícita y directa del usuario en esta sesión, que prevalece sobre el documento. El
backend usa Django REST Framework como API en lugar de vistas con templates para poder
servir un frontend React. El resto de las decisiones del spec (Python 3.12, Django 5,
PostgreSQL 16, openpyxl, WeasyPrint para PDF, etc.) se respetan sin cambios.

## Estructura

```
backend/    Django 5 + Django REST Framework + PostgreSQL
frontend/   React 19 + Vite + React Router + Recharts
docker-compose.yml
```

## Levantar con Docker Compose (recomendado)

```bash
cp backend/.env.example backend/.env      # ajustar si hace falta
cp frontend/.env.example frontend/.env
docker compose up --build
```

- Backend: http://localhost:8000 (admin en `/admin/`)
- Frontend: http://localhost:5173
- PostgreSQL: localhost:5432

Al primer arranque hay que crear un superusuario:

```bash
docker compose exec web python manage.py createsuperuser
```

## Desarrollo local sin Docker

### Backend

```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
# PostgreSQL 16 corriendo localmente, con una base de datos/usuario "sistema_ra"
export POSTGRES_DB=sistema_ra POSTGRES_USER=sistema_ra POSTGRES_PASSWORD=sistema_ra POSTGRES_HOST=localhost
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Tests

```bash
cd backend
source venv/bin/activate
python manage.py test apps.uploads -v 2
```

Ejecutar toda la suite: `python manage.py test apps` (51 tests). Cubre (§11 del spec):
- Parser contra los 2 archivos Excel reales (`apps/uploads/tests/fixtures/`): valores
  exactos de cabecera, número de criterios, número de estudiantes y notas.
- Cada validación V1–V6, incluyendo el caso permitido de "Sección 2".
- Recálculo de % de aprobados == declarado en los archivos reales.
- Versionado: una re-subida con la misma clave de negocio reemplaza los datos vigentes y
  conserva la versión anterior consultable.
- Cierre de periodo, edición de metadatos con auditoría, exportación Excel/PDF y
  gestión de catálogo/usuarios por rol.

## Datos de prueba a escala

```bash
python manage.py seed_demo --escala 3000        # ~3.000 evaluaciones × ~40 estudiantes
python manage.py seed_demo --limpiar --escala 500
```

Genera datos sintéticos (sin datos personales reales) multi-periodo para probar el
rendimiento de los tableros (<2 s).

## Catálogo Materia→RA

Define qué RA y en qué nivel debe evidenciar cada materia. Se administra desde la pantalla
**Catálogo** (coordinador/administrador) o desde `/admin/`. Antes de poder subir archivos
hace falta registrar: Escuela, Materia, Periodo, RACatalogo y MateriaRA.

## Despliegue en producción

Ver **`docs/DESPLIEGUE.md`** (docker-compose de producción con nginx + TLS + gunicorn,
backups automatizados). Manuales por rol en **`docs/MANUAL_USUARIO.md`**. SSO Microsoft
Entra ID en **`docs/SSO_ENTRA.md`**.

```bash
cp .env.prod.example .env   # completar secretos y dominio
# colocar certificados en deploy/nginx/certs/
docker compose -f docker-compose.prod.yml --env-file .env up -d --build
```

## Notas de la implementación

- **Identidad visual UNIMET**: la paleta institucional está centralizada en variables CSS
  (`frontend/src/index.css`) y en la plantilla del PDF. Los códigos hex actuales son un
  **placeholder** aproximado (naranja/azul): confirmar los valores exactos con el manual de
  marca y ajustarlos en ese único lugar.
- **SSO Microsoft Entra ID**: implementado como integración opcional (`SSO_ENABLED`), lista
  para activarse en cuanto TI UNIMET registre la aplicación en Entra ID. Mientras tanto, el
  login local/JWT funciona por defecto. Ver `docs/SSO_ENTRA.md`.
- **Trámites con TI UNIMET** (servidor, subdominio+TLS, registro en Entra ID): son
  externos al código; la guía `docs/DESPLIEGUE.md` los enumera.
