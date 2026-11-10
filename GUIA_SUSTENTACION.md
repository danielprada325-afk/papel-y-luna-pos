# Guía para presentar Papel y Luna POS

## Orden de la demostración

1. **Explica la arquitectura.** Muestra `frontend/src/main.jsx`, `backend/api/routes.py`, `backend/api/controllers.py` y `backend/api/models.py`. Resume el flujo: pantalla React → `fetch` REST → ruta → regla de negocio → modelo Django → SQLite/PostgreSQL → JSON de respuesta.
2. **Inicia sesión como administrador.** Usa `admin` / `Admin123!`. Muestra módulos administrativos y luego cierra sesión.
3. **Inicia como cajero.** Usa `cajero` / `Cajero123!`. Crea una venta de dos productos, selecciona efectivo, escribe un valor recibido mayor al total y cobra. Abre la factura e imprime o selecciona “Guardar como PDF”.
4. **Muestra persistencia.** Actualiza la página o entra al historial: la venta sigue allí, y el stock de los productos disminuyó.
5. **Demuestra una venta abierta.** En “Nueva venta”, agrega un producto y selecciona “Guardar abierta”. En “Ventas”, retómala y luego ciérrala.
6. **Como administrador, corrige una venta.** Cambia una cantidad y guarda. Explica que conserva el identificador, registra usuario y fecha y actualiza el inventario por la diferencia.
7. **Registra un reembolso parcial.** En la venta, elige qué unidades se devuelven; confirma si vuelven al stock. Explica que el reembolso respeta proporcionalmente un descuento.
8. **Muestra administración y análisis.** Registra una compra, enseña el aumento de stock, crea un descuento, registra y resuelve un faltante, y consulta reportes con fechas.
9. **Cierra explicando permisos y consistencia.** El servidor, no solo la interfaz, verifica el rol. Las operaciones de venta, corrección, compra y reembolso usan transacciones para evitar guardar el movimiento sin ajustar el inventario.

## Qué decir sobre el código

- **Modelos:** cada entidad tiene una tabla; `SaleItem` y `PurchaseItem` guardan los detalles de forma relacional, no como JSON de Google Sheets.
- **Rutas:** `routes.py` valida sesión, método HTTP y acceso por rol.
- **Controladores:** `controllers.py` calcula totales, valida efectivo, stock, descuento y límites de reembolso.
- **Transacciones:** `transaction.atomic` hace que el cambio de venta y el de stock se confirmen juntos o se reviertan juntos.
- **Frontend:** React guarda el estado temporal del carrito y pide persistirlo mediante JSON y `fetch`; el servidor devuelve el estado guardado.
- **Persistencia:** SQLite permite mostrar la app localmente. Para despliegue, se configura PostgreSQL en `DATABASE_URL`.

## Comandos rápidos

En local (desde la carpeta del proyecto):

```bash
bash iniciar.sh
```

URL local del frontend: `http://localhost:5173`  
URL local de la API: `http://localhost:8000/api/`

En Internet:

- Frontend: https://papel-y-luna-web.onrender.com
- Backend/API: https://papel-y-luna-api.onrender.com/api/

Abre la URL pública unos minutos antes de presentar: el plan gratuito tarda hasta un minuto en despertar.

## Preguntas posibles

- **¿Qué pasa si una venta supera el stock?** El backend la rechaza y no guarda ni la venta cerrada ni el descuento de inventario.
- **¿Qué sucede al corregir?** Compara cantidades anteriores y nuevas y aplica únicamente la diferencia al stock.
- **¿Cómo se calcula el reembolso con descuento?** Se calcula la parte correspondiente al precio de las unidades reembolsadas usando la proporción entre total pagado y subtotal.
- **¿Por qué mantener el detalle en tablas?** Permite consultar integridad relacional y evita depender de columnas con JSON serializado.
- **¿Dónde está desplegado?** Frontend estático y API Django en Render, con base PostgreSQL gestionada. El frontend reenvía `/api` al backend para que la cookie de sesión sea del mismo sitio.
- **¿Por qué ya no Google Sheets?** El MVP 3 exige backend propio con base de datos real; las líneas de venta y compra están en tablas de detalle con llaves foráneas.
