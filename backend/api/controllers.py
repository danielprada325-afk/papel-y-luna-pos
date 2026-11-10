import re, unicodedata
from decimal import Decimal, InvalidOperation
from django.contrib.auth import authenticate, login, logout
from django.db import transaction
from django.db.models import Count, Sum
from django.utils import timezone
from .models import Category, Client, Discount, Product, Provider, Purchase, PurchaseItem, Refund, RefundItem, Sale, SaleItem, Shortage

def payload(request):
    import json
    try: return json.loads(request.body or b"{}")
    except (ValueError, TypeError): return {}

def user_data(user): return {"id": user.id, "username": user.username, "role": "admin" if user.is_staff else "cajero"}
def login_action(request, data):
    user = authenticate(request, username=data.get("username", ""), password=data.get("password", ""))
    if not user: return {"error": "Usuario o contraseña incorrectos", "status": 401}
    login(request, user); return {"user": user_data(user)}
def current_user(request): return {"user": user_data(request.user)}
def logout_action(request): logout(request); return {"ok": True}

def product_json(p): return {"id": p.id, "codigo": p.code, "nombre": p.name, "categoriaId": p.category_id, "categoria": p.category.name, "precio": float(p.price), "costo": float(p.cost), "seguimientoInventario": p.track_inventory, "stock": p.stock}
def sale_json(s):
    return {"id": s.id, "fecha": s.date.isoformat(), "estado": s.status, "clienteId": s.client_id, "cliente": s.client.name if s.client else "", "metodoPago": s.payment_method, "subtotal": float(s.subtotal), "descuento": float(s.discount_amount), "descuentoId": s.discount_id, "total": float(s.total), "valorRecibido": float(s.received) if s.received is not None else None, "cambio": float(s.change), "corregida": bool(s.corrected_at), "corregidaPor": s.corrected_by.username if s.corrected_by else "", "corregidaEn": s.corrected_at.isoformat() if s.corrected_at else None, "reembolsoEstado": s.refund_status, "items": [{"id": i.id, "productoId": i.product_id, "codigo": i.product.code, "nombre": i.product.name, "cantidad": i.quantity, "precio": float(i.unit_price)} for i in s.items.select_related("product").all()]}
def snapshot():
    return {"productos": [product_json(x) for x in Product.objects.select_related("category").order_by("name")], "categorias": [{"id": x.id, "nombre": x.name, "name": x.name} for x in Category.objects.order_by("name")], "clientes": [{"id": x.id, "nombre": x.name, "name": x.name, "telefono": x.phone, "correo": x.email} for x in Client.objects.order_by("name")], "proveedores": [{"id": x.id, "nombre": x.name, "name": x.name, "telefono": x.phone, "correo": x.email} for x in Provider.objects.order_by("name")], "ventas": [sale_json(x) for x in Sale.objects.select_related("client", "discount", "corrected_by").prefetch_related("items__product").order_by("-date")], "compras": [{"id": x.id, "fecha": x.date.isoformat(), "proveedorId": x.provider_id, "proveedor": x.provider.name, "metodoPago": x.payment_method, "total": float(x.total), "items": [{"productoId": i.product_id, "nombre": i.product.name, "cantidad": i.quantity, "costo": float(i.unit_cost)} for i in x.items.select_related("product").all()]} for x in Purchase.objects.select_related("provider").prefetch_related("items__product").order_by("-date")], "descuentos": [{"id": x.id, "nombre": x.name, "tipo": x.kind, "valor": float(x.value), "activo": x.active} for x in Discount.objects.order_by("name")], "faltantes": [{"id": x.id, "nombre": x.name, "productoId": x.product_id, "cantidad": x.quantity, "tipo": x.kind, "proveedorId": x.provider_id, "proveedor": x.provider.name if x.provider else "", "estado": x.status, "nota": x.note, "fecha": x.created_at.isoformat()} for x in Shortage.objects.select_related("product", "provider").order_by("-created_at")]}
def money(value, label):
    try: n = Decimal(str(value))
    except (InvalidOperation, TypeError): raise ValueError(f"{label}: valor inválido")
    if n < 0: raise ValueError(f"{label}: no puede ser negativo")
    return n.quantize(Decimal("0.01"))
def get_lines(data):
    lines, seen = [], set()
    for row in data.get("items", []):
        p = Product.objects.select_for_update().get(pk=row.get("productoId", row.get("productId")))
        q = int(row.get("cantidad", row.get("quantity", 0)))
        if q < 1: raise ValueError("La cantidad debe ser mayor que cero")
        if p.id in seen: raise ValueError("Producto duplicado en el detalle")
        seen.add(p.id); lines.append((p, q))
    if not lines: raise ValueError("Agrega al menos un producto")
    return lines
def calc(lines, discount=None):
    sub = sum((p.price * q for p, q in lines), Decimal(0)); off = Decimal(0)
    if discount: off = min(sub, sub * discount.value / 100 if discount.kind == Discount.PERCENT else discount.value)
    return sub, off, sub - off
def persist_lines(sale, lines):
    sale.items.all().delete()
    SaleItem.objects.bulk_create([SaleItem(sale=sale, product=p, quantity=q, unit_price=p.price) for p, q in lines])
def close_sale(sale, data, request, correcting=False):
    lines = get_lines(data)
    old = {i.product_id: i.quantity for i in sale.items.select_related("product")} if correcting else {}
    products = {p.id: p for p, q in lines}
    if correcting:
        for item in sale.items.select_related("product"): products[item.product_id] = item.product
        refunded = {x["product_id"]: x["total"] for x in RefundItem.objects.filter(refund__sale=sale).values("product_id").annotate(total=Sum("quantity"))}
        for pid, quantity in refunded.items():
            if next((q for p, q in lines if p.id == pid), 0) < quantity:
                raise ValueError("La cantidad corregida no puede ser menor a las unidades ya reembolsadas")
    for pid, p in products.items():
        delta = next((q for x, q in lines if x.id == pid), 0) - old.get(pid, 0)
        if p.track_inventory and p.stock - delta < 0: raise ValueError(f"Stock insuficiente para {p.name}; disponible: {p.stock}")
    discount_id = data.get("descuentoId", data.get("discountId"))
    discount = Discount.objects.filter(pk=discount_id, active=True).first() if discount_id else None
    if discount_id and not discount: raise ValueError("El descuento no existe o está inactivo")
    client_id = data.get("clienteId", data.get("clientId")); client = Client.objects.filter(pk=client_id).first() if client_id else None
    method = data.get("metodoPago", data.get("paymentMethod", sale.payment_method or "Efectivo"))
    if method == "Debe" and not client: raise ValueError("Selecciona un cliente para una venta a crédito")
    sale.client, sale.payment_method, sale.discount = client, method, discount
    sale.subtotal, sale.discount_amount, sale.total = calc(lines, discount)
    received = data.get("valorRecibido", data.get("received", sale.total))
    sale.received = money(received, "Valor recibido") if method == "Efectivo" else None
    if method == "Efectivo" and sale.received < sale.total: raise ValueError("El valor recibido es menor al total")
    sale.change = sale.received - sale.total if method == "Efectivo" else Decimal(0)
    sale.status = Sale.CLOSED
    if correcting: sale.corrected_by, sale.corrected_at = request.user, timezone.now()
    sale.save()
    for pid, p in products.items():
        delta = next((q for x, q in lines if x.id == pid), 0) - old.get(pid, 0)
        if p.track_inventory: p.stock -= delta; p.save(update_fields=["stock"])
    persist_lines(sale, lines)
    return sale

@transaction.atomic
def sale_create(request, data):
    sale = Sale(status=Sale.OPEN)
    if data.get("estado", data.get("status", "cerrada")) == "abierta":
        lines = get_lines(data); sale.client_id = data.get("clienteId") or None
        sale.subtotal, sale.discount_amount, sale.total = calc(lines); sale.save(); persist_lines(sale, lines); return sale
    return close_sale(sale, data, request)
@transaction.atomic
def sale_update(request, sale, data):
    if sale.status == Sale.CLOSED: raise ValueError("La venta cerrada requiere acción de corrección")
    lines = get_lines(data); sale.client_id = data.get("clienteId") or None
    sale.subtotal, sale.discount_amount, sale.total = calc(lines); sale.save(); persist_lines(sale, lines)
    if data.get("estado", data.get("status")) == "cerrada": return close_sale(sale, data, request)
    return sale
@transaction.atomic
def sale_correct(request, sale, data):
    if sale.status != Sale.CLOSED: raise ValueError("Solo se pueden corregir ventas cerradas")
    return close_sale(sale, data, request, True)
@transaction.atomic
def purchase_create(request, data):
    provider = Provider.objects.get(pk=data.get("proveedorId", data.get("providerId")))
    if not data.get("items"): raise ValueError("Agrega al menos un producto")
    purchase = Purchase.objects.create(provider=provider, payment_method=data.get("metodoPago", "Efectivo"), created_by=request.user)
    total = Decimal(0)
    for row in data["items"]:
        p = Product.objects.select_for_update().get(pk=row.get("productoId", row.get("productId")))
        q, cost = int(row.get("cantidad", row.get("quantity", 0))), money(row.get("costo", row.get("cost", p.cost)), "Costo")
        if q < 1: raise ValueError("La cantidad debe ser mayor que cero")
        PurchaseItem.objects.create(purchase=purchase, product=p, quantity=q, unit_cost=cost); total += cost*q
        if p.track_inventory: p.stock += q
        p.cost = cost; p.save(update_fields=["stock", "cost"])
    purchase.total = total; purchase.save(update_fields=["total"]); return purchase
@transaction.atomic
def refund_create(request, sale, data):
    if sale.status != Sale.CLOSED: raise ValueError("Solo se pueden reembolsar ventas cerradas")
    previous = {x["product_id"]: x["total"] for x in RefundItem.objects.filter(refund__sale=sale).values("product_id").annotate(total=Sum("quantity"))}
    sale_items = {i.id: i for i in sale.items.select_related("product")}; picked=[]; base=Decimal(0)
    for row in data.get("items", []):
        item = sale_items.get(int(row.get("ventaItemId", row.get("saleItemId", 0)))); q=int(row.get("cantidad", row.get("quantity", 0)))
        if not item or q < 1 or q + previous.get(item.product_id, 0) > item.quantity: raise ValueError("Cantidad de reembolso superior a lo disponible")
        returned = bool(row.get("retornaInventario", row.get("returnToStock", False))); picked.append((item,q,returned)); base += item.unit_price*q
    if not picked: raise ValueError("Selecciona productos para reembolsar")
    ratio = sale.total / sale.subtotal if sale.subtotal else Decimal(0); amount=(base*ratio).quantize(Decimal("0.01"))
    prior_amount=Refund.objects.filter(sale=sale).aggregate(x=Sum("amount"))["x"] or Decimal(0)
    amounts_by_product={x["product_id"]:x["total"] for x in RefundItem.objects.filter(refund__sale=sale).values("product_id").annotate(total=Sum("quantity"))}
    for item,q,_ in picked: amounts_by_product[item.product_id]=amounts_by_product.get(item.product_id,0)+q
    if all(amounts_by_product.get(item.product_id,0)>=item.quantity for item in sale.items.all()): amount=sale.total-prior_amount
    refund=Refund.objects.create(sale=sale, amount=amount, created_by=request.user)
    for item,q,returned in picked:
        RefundItem.objects.create(refund=refund,sale_item=item,product=item.product,quantity=q,unit_amount=(item.unit_price*ratio).quantize(Decimal("0.01")),return_to_stock=returned)
        if returned and item.product.track_inventory:
            p=Product.objects.select_for_update().get(pk=item.product_id); p.stock+=q; p.save(update_fields=["stock"])
    total=Refund.objects.filter(sale=sale).aggregate(x=Sum("amount"))["x"] or 0
    sale.refund_status="total" if total >= sale.total else "parcial"; sale.save(update_fields=["refund_status"]); return refund
def normalized(name):
    name="".join(c for c in unicodedata.normalize("NFD",name.lower().strip()) if unicodedata.category(c)!="Mn"); name=re.sub(r"\s+"," ",name)
    return name[:-2] if name.endswith("es") and len(name)>4 else name[:-1] if name.endswith("s") and len(name)>3 else name
def reports(params):
    sales=Sale.objects.filter(status=Sale.CLOSED); buys=Purchase.objects.all()
    if params.get("desde"): sales=sales.filter(date__date__gte=params["desde"]); buys=buys.filter(date__date__gte=params["desde"])
    if params.get("hasta"): sales=sales.filter(date__date__lte=params["hasta"]); buys=buys.filter(date__date__lte=params["hasta"])
    top=SaleItem.objects.filter(sale__in=sales).values("product__name").annotate(unidades=Sum("quantity")).order_by("-unidades")[:10]
    shortages=Shortage.objects.values("normalized_name").annotate(solicitudes=Count("id"),cantidad=Sum("quantity")).order_by("-solicitudes")[:10]
    return {"ventasTotal":float(sales.aggregate(x=Sum("total"))["x"] or 0),"cantidadVentas":sales.count(),"productosMasVendidos":list(top),"compras":[{"id":x.id,"fecha":x.date.isoformat(),"proveedor":x.provider.name,"total":float(x.total)} for x in buys.select_related("provider").order_by("-date")],"faltantesFrecuentes":list(shortages)}
