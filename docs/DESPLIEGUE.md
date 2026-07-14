# Guía de despliegue institucional (Fase 4)

Despliegue en el servidor Linux de TI UNIMET con Docker Compose, HTTPS y
backups automatizados.

## 1. Requisitos en el servidor

- Docker y Docker Compose v2.
- Un subdominio (ej. `ra.unimet.edu.ve`) apuntando al servidor.
- Certificado TLS para ese subdominio (Let's Encrypt o el de la universidad).
- Puertos 80 y 443 abiertos.

## 2. Trámites con TI UNIMET (iniciar temprano)

1. Servidor Linux con Docker (o Python 3.12 + PostgreSQL 16).
2. Subdominio + certificado TLS.
3. Registro de la aplicación en Microsoft Entra ID si se usará SSO
   (ver `docs/SSO_ENTRA.md`).

## 3. Preparación

```bash
git clone <repo> && cd sistema-de-RA-V2-072026
cp .env.prod.example .env
# Editar .env: SECRET_KEY, dominio, contraseñas, etc.
```

Colocar los certificados TLS en `deploy/nginx/certs/`:

```
deploy/nginx/certs/fullchain.pem
deploy/nginx/certs/privkey.pem
```

Con Let's Encrypt (certbot) se pueden generar y luego copiar/enlazar ahí.

## 4. Levantar

```bash
docker compose -f docker-compose.prod.yml --env-file .env up -d --build
```

Esto migra la base de datos, recolecta estáticos, construye el frontend y
levanta nginx con TLS. Crear el primer administrador:

```bash
docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

Cargar el catálogo inicial (escuelas, materias, periodos, RAs, MateriaRA)
desde el panel de administración (`/admin/`) o las pantallas de coordinador.

## 5. Backups automatizados (§9)

El script `scripts/backup.sh` hace dump de PostgreSQL + copia de los xlsx.
Programarlo en cron (diario a las 02:00):

```cron
0 2 * * * cd /ruta/al/proyecto && ./scripts/backup.sh >> /var/log/sistema_ra_backup.log 2>&1
```

Restaurar con `scripts/restore.sh <dump_db.sql.gz> [media.tar.gz]`.

## 6. Actualizaciones

```bash
git pull
docker compose -f docker-compose.prod.yml up -d --build
```

Las migraciones se aplican automáticamente al arrancar el contenedor `web`.

## 7. Verificación post-despliegue

- `https://<subdominio>/` carga el frontend.
- `https://<subdominio>/admin/` carga el panel de administración.
- HTTP redirige a HTTPS.
- Un profesor sube un archivo real y ve el tablero.
- Un backup manual (`./scripts/backup.sh`) genera archivos en `./backups/`.

## 8. Piloto (§10, Fase 4)

Comenzar con la Escuela de Producción, recoger retroalimentación y abrir
gradualmente al resto de las escuelas.

## 9. Seguridad operativa

- `DEBUG=False` en producción activa HSTS, cookies seguras y redirección a
  HTTPS (ver `config/settings.py`).
- Nunca subir `.env`, certificados ni backups al repositorio.
- Los archivos xlsx originales son la fuente de verdad: se conservan siempre.
