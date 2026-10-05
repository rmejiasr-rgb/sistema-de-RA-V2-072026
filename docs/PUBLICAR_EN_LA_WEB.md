# Publicar el sistema en la web (gratis, con Render)

Guía para **alguien sin experiencia**. Al terminar tendrás una dirección web
(algo como `https://sistema-ra.onrender.com`) que **cualquier persona puede
abrir en su navegador, sin instalar nada**.

El proyecto ya quedó preparado para esto: Render lee un archivo de
configuración (`render.yaml`) y arma todo solo — tú solo das unos clics.

> **Importante (léelo antes):** esto es para **mostrar y probar** el sistema.
> El plan gratuito tiene límites (ver la sección final). Para el uso real de la
> universidad, con datos verdaderos de estudiantes, el camino correcto sigue
> siendo entregarlo a TI UNIMET (`docs/ENTREGA_TI.md`).

---

## Antes de empezar

1. Tu proyecto debe estar en GitHub (ya lo está).
2. Ten a la mano en qué **rama** está el código. En tu caso:
   `claude/python-postgres-react-system-h9tf8w`

---

## Paso 1 — Crear una cuenta gratuita en Render

1. Entra a **https://render.com**
2. Haz clic en **"Get Started"** / **"Sign Up"**.
3. Regístrate con tu cuenta de **GitHub** (el botón "GitHub"). Es lo más fácil,
   porque así Render puede ver tu proyecto.
4. Acepta los permisos que pida para leer tus repositorios.

> El plan gratuito no requiere tarjeta de crédito. Si te pide confirmar el
> correo, hazlo.

---

## Paso 2 — Crear el sistema desde el "plano" (Blueprint)

1. Ya dentro de Render, haz clic en el botón **"New +"** (arriba a la derecha).
2. Elige **"Blueprint"**.
3. Render te mostrará tus repositorios de GitHub. Busca y selecciona el de este
   proyecto. (Si no aparece, haz clic en "Configure account" / "Configurar" y
   dale acceso a ese repositorio.)
4. Cuando te lo pida, elige la **rama**:
   `claude/python-postgres-react-system-h9tf8w`
5. Render detectará el archivo `render.yaml` y te mostrará lo que va a crear:
   - un **servicio web** llamado `sistema-ra` (el sistema), y
   - una **base de datos** gratuita.
6. Haz clic en **"Apply"** (Aplicar).

---

## Paso 3 — Esperar a que se construya

- Render empezará a construir el sistema. **La primera vez tarda** (puede ser de
  5 a 12 minutos). Verás texto desplazándose; es normal.
- Cuando el servicio `sistema-ra` muestre el estado **"Live"** (en verde), ya
  está publicado.

---

## Paso 4 — Abrir y compartir

1. Haz clic en el nombre del servicio `sistema-ra`. Arriba verás su dirección,
   algo como **`https://sistema-ra.onrender.com`**.
2. Ábrela en el navegador. Entra con:
   - **Usuario:** `admin`
   - **Clave:** `admin12345`
3. **Esa misma dirección** es la que le pasas a cualquier persona. La abre en su
   navegador y entra con el mismo usuario y clave. **No instala nada.**

---

## Cosas que debes saber del plan gratuito

- **Se "duerme" si nadie lo usa.** Tras unos 15 minutos sin visitas, el plan
  gratuito se apaga. La siguiente persona que entre esperará **~1 minuto** a que
  despierte (la pantalla puede tardar en cargar esa primera vez). Después va
  normal. Es limitación del plan gratis, no del sistema.
- **La base de datos gratuita caduca** (Render la borra a los ~30 días). Si eso
  pasa, los datos se reinician; puedes volver a desplegar y tendrás de nuevo el
  usuario y los datos de ejemplo. Para algo permanente, se usa un plan de pago o
  el servidor de TI.
- **Cambia la clave de admin** si vas a compartir la dirección con varias
  personas. Entra a `https://TU-DIRECCION/admin/` con admin / admin12345 y
  cámbiala desde ahí (sección "Usuarios").

---

## Si algo sale mal

- **El build falla (estado "Failed").** Entra al servicio `sistema-ra` →
  pestaña **"Logs"**, copia las últimas líneas (sobre todo en rojo) y
  compártelas; con eso se diagnostica.
- **"Application failed to respond" al abrir la dirección.** Suele ser que
  todavía está despertando o terminando de construir; espera 1–2 minutos y
  recarga.
- **Olvidaste la dirección.** Está siempre en el panel de Render, dentro del
  servicio `sistema-ra`.

---

## ¿Y si quiero actualizar el sistema más adelante?

Cada vez que se suban cambios a la rama del proyecto en GitHub, Render puede
reconstruir solo (o le das al botón **"Manual Deploy" → "Deploy latest
commit"**). No hay que repetir toda la configuración.
