# Documento de entrega para TI UNIMET — Sistema de Gestión y Análisis de RA

*Este documento está dirigido al equipo técnico (TI). El resto del proyecto vive
en el repositorio junto a este archivo.*

## 1. Qué es

Aplicación web donde los profesores suben archivos Excel de rúbricas de
Resultados de Aprendizaje (RA). El sistema los valida, versiona y almacena, y
ofrece un tablero analítico (semáforos, mapas de calor, tendencias) con
exportación a Excel y PDF. Está pensado para escalar a toda la universidad,
empezando con un piloto en una escuela.

## 2. En qué está construido

| Parte | Tecnología |
|---|---|
| Backend / API | Python 3.12 · Django 5 · Django REST Framework |
| Base de datos | PostgreSQL 16 |
| Frontend | React (Vite) |
| Reportes | openpyxl (Excel) · WeasyPrint (PDF) |
| Empaquetado | Docker / Docker Compose |

Todo el sistema está listo y probado (51 pruebas automatizadas en verde,
incluyendo pruebas contra archivos Excel reales de la Escuela de Producción).

## 3. Qué necesitamos de TI (los 3 trámites que bloquean el despliegue)

1. **Un servidor Linux** con Docker y Docker Compose (o Python 3.12 +
   PostgreSQL 16). Recursos modestos: 2 vCPU / 4 GB RAM son suficientes para el
   piloto.
2. **Un subdominio + certificado TLS** (ej. `ra.unimet.edu.ve`) para servir el
   sistema por HTTPS.
3. **(Opcional, solo si se quiere inicio de sesión con la cuenta institucional)**
   Registro de la aplicación en Microsoft Entra ID (Client ID, Secret, Tenant y
   Redirect URI). Sin esto, el sistema funciona igual con usuarios y contraseñas
   propios. Detalle en `docs/SSO_ENTRA.md`.

## 4. Cómo se pone en marcha (resumen para TI)

La guía completa y detallada está en **`docs/DESPLIEGUE.md`**. En resumen:

```bash
git clone <URL-del-repositorio>
cd sistema-de-RA-V2-072026
cp .env.prod.example .env          # completar dominio, contraseñas y clave secreta
# colocar los certificados TLS en deploy/nginx/certs/
docker compose -f docker-compose.prod.yml --env-file .env up -d --build
docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

- Migraciones, recolección de estáticos y arranque son automáticos.
- El primer usuario administrador se crea con el último comando.
- Backups diarios: programar `scripts/backup.sh` en cron (ejemplo en
  `docs/DESPLIEGUE.md`).

## 5. Seguridad (ya contemplada en el código)

- HTTPS obligatorio; con `DEBUG=False` se activan HSTS, cookies seguras y
  redirección a HTTPS.
- Acceso solo autenticado; el filtrado de datos por rol se hace en el servidor
  (un profesor nunca ve notas de otro).
- Datos sensibles (nombres y notas de estudiantes): no se guardan datos reales
  en el repositorio ni en los registros del sistema.
- Los archivos Excel originales se conservan siempre (son la fuente de verdad) y
  entran en el backup diario.

## 6. Documentación incluida

| Documento | Contenido |
|---|---|
| `README.md` | Visión general y cómo levantar en desarrollo |
| `docs/DESPLIEGUE.md` | Guía paso a paso de puesta en producción |
| `docs/MANUAL_USUARIO.md` | Manual por rol (profesor, coordinador, admin) |
| `docs/SSO_ENTRA.md` | Activación del inicio de sesión con Microsoft |

## 7. Contacto funcional

Richard Mejías — Ingeniería de Producción, UNIMET (autor funcional del sistema).
Para dudas sobre *qué hace* el sistema y las reglas de negocio; para el
despliegue técnico, este documento y `docs/DESPLIEGUE.md`.
