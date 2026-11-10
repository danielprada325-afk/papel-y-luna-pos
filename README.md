# Papel y Luna POS — MVP 3

Aplicación full-stack para operar el punto de venta de la papelería Papel y Luna. El frontend React/Vite consume una API REST en Django. La información se almacena en SQLite para desarrollo local y puede conectarse a PostgreSQL mediante `DATABASE_URL`.

## Requisitos

- Python 3.10 o posterior
- Node.js 20 o posterior
- pnpm (o npm, ajustando los comandos)

## Ejecutar en local

Abre dos terminales desde la carpeta `papel-y-luna-mvp3`.

**Terminal 1 — backend:**

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py seed_pos
python manage.py runserver 8000
```

La API queda disponible en `http://localhost:8000/api/`.

**Terminal 2 — frontend:**

```bash
cd frontend
pnpm install
cp .env.example .env.local
pnpm dev
```

Abre `http://localhost:5173`. El frontend inicia sesión contra el backend y solicita los datos mediante HTTP. No utiliza Google Sheets.

## Usuarios de demostración

| Rol | Usuario | Contraseña |
|---|---|---|
| Administrador | `admin` | `Admin123!` |
| Cajero | `cajero` | `Cajero123!` |

`seed_pos` crea las cuentas solo si no existen. En despliegue, define `ADMIN_PASSWORD` y `CASHIER_PASSWORD` antes de ejecutar ese comando por primera vez. Cambia las claves de demostración antes de usar datos reales.

## Qué incluye

- Venta, pago en efectivo/Nequi/Debe, cambio, descuento por venta, factura imprimible y PDF del navegador.
- Ventas abiertas que se guardan y se pueden retomar.
- Inventario y CRUD administrativo de productos/categorías; edición rápida de productos desde la venta.
- Clientes y proveedores, compras y actualización de stock.
- Corrección de ventas cerradas conservando el ID y registrando usuario y hora.
- Reembolsos parciales/totales por producto con opción de retorno al inventario.
- Catálogo de descuentos porcentuales o de valor fijo.
- Registro, filtro básico, resolución y agrupación normalizada de faltantes.
- Reportes por fecha de ventas, productos más vendidos, compras y faltantes frecuentes.
- Acceso por roles de administrador y cajero.

## Datos y arquitectura

`frontend/src/main.jsx` presenta los módulos y llama a `fetch`. `backend/api/routes.py` recibe las rutas REST; `controllers.py` concentra los cálculos y reglas; `models.py` define las tablas relacionales y sus llaves foráneas. Ventas, compras, correcciones y reembolsos usan transacciones de Django para guardar juntos el movimiento y el inventario.

La base local se crea en `backend/db.sqlite3` al ejecutar migraciones. Las migraciones reproducibles están en `backend/api/migrations/`; `backend/scripts/schema.sql` incluye el SQL de la migración inicial para el motor local. `python manage.py seed_pos` agrega las cuentas y catálogo de demostración. Para PostgreSQL, configura `DATABASE_URL` y ejecuta los mismos comandos de migración y semilla.

## Rutas REST principales

Todas las rutas de negocio requieren iniciar sesión. La sesión se mantiene con cookie HTTP. Las rutas administrativas validan el rol en el servidor.

| Método y ruta | Uso |
|---|---|
| `POST /api/auth/login/` · `GET /api/auth/me/` · `POST /api/auth/logout/` | Sesión |
| `GET /api/` | Carga inicial de los módulos |
| `GET/POST/PATCH/DELETE /api/products/` | Catálogo de productos |
| `GET/POST/PATCH/DELETE /api/categories/` | Categorías |
| `GET/POST/PATCH/DELETE /api/clients/` y `/api/providers/` | Clientes y proveedores |
| `GET/POST/PATCH/DELETE /api/discounts/` | Catálogo de descuentos |
| `GET/POST/PATCH /api/sales/` | Ventas abiertas/cerradas, corrección y reembolso (`action`) |
| `POST /api/purchases/` | Compra y suma de inventario en transacción |
| `GET/POST/PATCH /api/shortages/` | Faltantes y resolución |
| `GET /api/reports/?desde=AAAA-MM-DD&hasta=AAAA-MM-DD` | Reportes administrativos |

## Despliegue

**URLs públicas** (completar después de desplegar):

- Frontend: `https://papel-y-luna-web.onrender.com`
- Backend/API: `https://papel-y-luna-api.onrender.com/api/`

### Opción recomendada: Render Blueprint (`render.yaml`)

El archivo `render.yaml` crea en una sola cuenta gratuita de Render la base de datos PostgreSQL, la API Django y el frontend estático.

1. Sube esta carpeta al repositorio de GitHub del equipo.
2. En [render.com](https://render.com), inicia sesión con GitHub y elige **New → Blueprint**.
3. Selecciona el repositorio y pulsa **Apply**. Render crea `papel-y-luna-db`, `papel-y-luna-api` y `papel-y-luna-web`.
4. Cuando los tres estén en verde, abre la URL del frontend e inicia sesión con `admin` / `Admin123!`.

El frontend llama a `/api` en su propio dominio y Render reenvía esas peticiones al backend (regla `rewrite` en `render.yaml`). Así la cookie de sesión funciona en cualquier navegador. Si Render asigna al backend un nombre distinto de `papel-y-luna-api.onrender.com`, actualiza el `destination` de esa regla.

Notas del plan gratuito: el backend se suspende tras 15 minutos sin uso y la primera petición tarda cerca de un minuto en despertarlo (ábrelo antes de la sustentación). La base PostgreSQL gratuita de Render vence a los 30 días.

### Despliegue manual en otra plataforma

El proyecto ya está preparado para base PostgreSQL mediante `DATABASE_URL`, y el frontend acepta la URL desplegada del API con `VITE_API_URL`. Para publicar, crea una base PostgreSQL, despliega el backend como servicio Python ejecutando `pip install -r requirements.txt` y como comando de inicio `python manage.py migrate && python manage.py seed_pos && gunicorn pos.wsgi:application --bind 0.0.0.0:$PORT`. Despliega `frontend/` como sitio estático usando `pnpm install --frozen-lockfile` y `pnpm build`; publica `dist/` y configura `VITE_API_URL` con la URL HTTPS del backend más `/api`. En backend configura `DEBUG=false`, una clave secreta nueva, `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS` con el dominio HTTPS del frontend, `DATABASE_URL` y contraseñas iniciales propias.

Las URLs públicas aún no están creadas: se generan al conectar estas carpetas a cuentas de despliegue. No inventes ni entregues URLs hasta comprobar el despliegue. Después de publicar, anota aquí `Frontend:` y `Backend/API:`.

## Presentación

Sigue la guía paso a paso en [`GUIA_SUSTENTACION.md`](GUIA_SUSTENTACION.md).
