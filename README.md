# Sistema de Gestión y Análisis de Resultados de Aprendizaje (RA) · UNIMET

Implementación de la **Fase 1** de la especificación (`SPECSistemaRAUNIMET.md`): núcleo
monousuario funcional de punta a punta — modelos de datos, parser de Excel, motor de
validaciones V1–V6, catálogo Materia→RA vía Django admin, API REST y un tablero mínimo
(bloques 1 y 2) con login.

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

Cubre (§11 del spec):
- Parser contra los 2 archivos Excel reales (`apps/uploads/tests/fixtures/`): valores
  exactos de cabecera, número de criterios, número de estudiantes y notas.
- Cada validación V1–V6, incluyendo el caso permitido de "Sección 2".
- Recálculo de % de aprobados == declarado en los archivos reales.
- Versionado: una re-subida con la misma clave de negocio reemplaza los datos vigentes y
  conserva la versión anterior consultable.

## Uso del catálogo (Fase 1)

El catálogo Materia→RA (qué RA y en qué nivel debe evidenciar cada materia) se administra
desde `/admin/` (Django admin), tal como especifica el documento para la Fase 1. Antes de
poder subir archivos hace falta registrar ahí: Escuela, Materia, Periodo, RACatalogo y
MateriaRA.

## Qué falta para las siguientes fases

- **Fase 2**: bloques 3–7 del tablero, cierre de periodo, edición de metadatos con
  auditoría en pantalla, exportación a Excel/PDF (WeasyPrint), seed sintético a escala e
  identidad visual UNIMET definitiva (colores del manual de marca — hoy son un placeholder
  en `frontend/src/index.css`).
- **Fase 3**: pantallas de coordinador, SSO Microsoft Entra ID, gestión de usuarios desde
  la UI (hoy solo por Django admin).
- **Fase 4**: despliegue en el servidor de TI UNIMET, HTTPS, backups automatizados.
