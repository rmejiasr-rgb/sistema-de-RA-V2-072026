# SSO con Microsoft Entra ID (Fase 3)

El sistema soporta inicio de sesión con Microsoft Entra ID (antes Azure AD)
restringido a correos `@unimet.edu.ve`, además del login local de Django/JWT.

Está **desactivado por defecto** porque requiere que TI UNIMET registre la
aplicación en Entra ID. La Fase 1 y el desarrollo local funcionan con login
local sin necesidad de esto.

## 1. Trámite con TI UNIMET (bloquea la activación)

Solicitar el registro de la aplicación en Microsoft Entra ID y obtener:

- **Client ID** (Application ID)
- **Client Secret**
- **Tenant ID** (o usar `organizations`)
- Configurar el **Redirect URI**:
  `https://<subdominio-unimet>/accounts/microsoft/login/callback/`

Permisos delegados mínimos: `openid`, `email`, `profile`, `User.Read`.

## 2. Variables de entorno

Una vez con las credenciales, definir en el entorno del backend:

```bash
SSO_ENABLED=True
ENTRA_CLIENT_ID=<client-id>
ENTRA_CLIENT_SECRET=<client-secret>
ENTRA_TENANT_ID=<tenant-id>            # o "organizations"
SSO_DOMINIO_PERMITIDO=unimet.edu.ve
SSO_LOGIN_REDIRECT=/                    # a dónde redirige tras el login
```

## 3. Migraciones

Al activar `SSO_ENABLED=True` se incorporan las apps de `django-allauth` y
`django.contrib.sites`, que traen sus propias tablas:

```bash
python manage.py migrate
```

## 4. Comportamiento

- Solo se acepta el ingreso con correos del dominio configurado
  (`apps/accounts/adapters.py`). Cualquier otro correo es rechazado.
- Un usuario nuevo que ingresa por SSO recibe el rol **Profesor** por
  defecto; el Administrador ajusta sus roles/escuela desde la gestión de
  usuarios.
- El login local de Django/JWT sigue disponible en paralelo (útil para el
  Administrador y para cuentas de servicio).

## 5. Frontend

El botón "Ingresar con Microsoft" aparece en la pantalla de login cuando el
frontend se construye con `VITE_SSO_ENABLED=true`. Redirige a
`/accounts/microsoft/login/` del backend, que inicia el flujo OAuth.

## 6. Seguridad

- El filtrado de datos por rol se hace siempre en el servidor (§9); el SSO
  solo cambia el mecanismo de autenticación, no la autorización.
- Mantener el `ENTRA_CLIENT_SECRET` fuera del repositorio (variables de
  entorno o gestor de secretos del servidor).
