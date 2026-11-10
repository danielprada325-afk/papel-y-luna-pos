from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from . import controllers as c
from .models import Category, Client, Discount, Product, Provider, Purchase, Sale, Shortage

def response(data, status=200): return JsonResponse(data, safe=False, status=status)
def error(message, status=400): return response({"error": str(message)}, status)
def lookup(model, rid): return model.objects.get(pk=rid)
def require_admin(request): return request.user.is_staff

@csrf_exempt
def dispatch(request, resource="", record_id=""):
    record_id = record_id.rstrip("/")
    if request.method == "OPTIONS": return response({"ok": True})
    data = c.payload(request) if hasattr(c, "payload") else {}
    if request.path.endswith("/auth/login/"):
        if request.method != "POST": return error("Método no permitido",405)
        result=c.login_action(request,data); status=result.pop("status",200); return response(result,status)
    if request.path.endswith("/auth/me/"):
        return response({"user": c.user_data(request.user)}) if request.user.is_authenticated else error("Inicia sesión",401)
    if request.path.endswith("/auth/logout/"):
        if request.user.is_authenticated: c.logout_action(request)
        return response({"ok":True})
    if not request.user.is_authenticated: return error("Inicia sesión",401)
    if resource in ("", "dashboard") and request.method == "GET": return response(c.snapshot())
    if resource == "reports" and request.method == "GET":
        if not require_admin(request): return error("Solo el administrador puede consultar reportes",403)
        return response(c.reports(request.GET))
    admin_resources={"products","categories","providers","discounts","purchases"}
    hot_product_edit = resource == "products" and request.method in ("PATCH", "PUT") and bool(data.get("hotEdit"))
    if resource in admin_resources and request.method != "GET" and not require_admin(request) and not hot_product_edit: return error("Función disponible para administrador",403)
    try:
        if resource == "sales":
            if data.get("action") in ("correct", "refund") and not require_admin(request):
                return error("Solo el administrador puede corregir o reembolsar ventas", 403)
            if request.method == "GET": return response([c.sale_json(x) for x in Sale.objects.select_related("client","corrected_by").prefetch_related("items__product").order_by("-date")])
            if request.method == "POST":
                action=data.get("action","create")
                if action in ("create","save","close"):
                    sale=c.sale_create(request,data); return response(c.sale_json(sale),201)
                if action == "correct":
                    sale=c.sale_correct(request,lookup(Sale,data.get("id")),data); return response(c.sale_json(sale))
                if action == "refund":
                    sale=lookup(Sale,data.get("id")); refund=c.refund_create(request,sale,data); return response({"id":refund.id,"monto":float(refund.amount),"ventaId":sale.id},201)
            if request.method in ("PATCH","PUT"):
                sale=lookup(Sale,record_id); action=data.get("action", "update")
                if action == "correct": sale=c.sale_correct(request,sale,data)
                elif action == "refund":
                    refund=c.refund_create(request,sale,data); return response({"id":refund.id,"monto":float(refund.amount)})
                else: sale=c.sale_update(request,sale,data)
                return response(c.sale_json(sale))
        if resource == "purchases" and request.method == "POST":
            p=c.purchase_create(request,data); return response({"id":p.id,"total":float(p.total)},201)
        if resource == "shortages":
            if request.method == "GET":
                rows=Shortage.objects.select_related("product","provider").order_by("-created_at")
                if request.GET.get("tipo"): rows=rows.filter(kind=request.GET["tipo"])
                if request.GET.get("proveedorId"): rows=rows.filter(provider_id=request.GET["proveedorId"])
                return response([{"id":x.id,"nombre":x.name,"productoId":x.product_id,"cantidad":x.quantity,"tipo":x.kind,"proveedorId":x.provider_id,"proveedor":x.provider.name if x.provider else "","estado":x.status,"nota":x.note,"fecha":x.created_at.isoformat()} for x in rows])
            if request.method == "POST":
                name=str(data.get("nombre",data.get("name",""))).strip()
                if not name: return error("Escribe el producto faltante")
                p=Product.objects.filter(pk=data.get("productoId")).first() if data.get("productoId") else None
                shortage=Shortage.objects.create(name=name,normalized_name=c.normalized(name),product=p,quantity=max(1,int(data.get("cantidad",1))),kind=data.get("tipo","agotado"),provider_id=data.get("proveedorId") or None,note=data.get("nota",""),created_by=request.user)
                return response({"id":shortage.id,"nombre":shortage.name},201)
        if resource == "shortages" and record_id and request.method == "PATCH":
            item=lookup(Shortage,record_id); item.status="resuelto"; item.save(update_fields=["status"]); return response({"ok":True})
        models={"products":Product,"categories":Category,"clients":Client,"providers":Provider,"discounts":Discount}
        if resource in models:
            model=models[resource]
            if request.method == "GET":
                if resource == "products": return response([c.product_json(p) for p in Product.objects.select_related("category")])
                return response(c.snapshot()[{"categories":"categorias","clients":"clientes","providers":"proveedores","discounts":"descuentos"}[resource]])
            if request.method in ("POST","PUT","PATCH"):
                obj=lookup(model,record_id) if record_id else model()
                if resource == "products":
                    obj.code=data.get("codigo",data.get("code",obj.code or "")); obj.name=data.get("nombre",data.get("name",obj.name or "")); obj.category_id=data.get("categoriaId",data.get("categoryId",obj.category_id)); obj.price=Decimal(str(data.get("precio",data.get("price",obj.price or 0)))); obj.cost=Decimal(str(data.get("costo",data.get("cost",obj.cost or 0)))); obj.track_inventory=data.get("seguimientoInventario",data.get("trackInventory",True)); obj.stock=int(data.get("stock",obj.stock or 0))
                    if obj.price < 0 or obj.cost < 0 or obj.stock < 0: return error("Precio, costo y stock deben ser positivos")
                    obj.save(); return response(c.product_json(obj),201 if not record_id else 200)
                if resource == "categories": obj.name=data.get("nombre",data.get("name",obj.name or ""))
                elif resource == "clients": obj.name=data.get("nombre",data.get("name",obj.name or "")); obj.phone=data.get("telefono",data.get("phone",obj.phone or "")); obj.email=data.get("correo",data.get("email",obj.email or ""))
                elif resource == "providers": obj.name=data.get("nombre",data.get("name",obj.name or "")); obj.phone=data.get("telefono",data.get("phone",obj.phone or "")); obj.email=data.get("correo",data.get("email",obj.email or "")); obj.tax_id=data.get("nit",obj.tax_id or "")
                else: obj.name=data.get("nombre",data.get("name",obj.name or "")); obj.kind=data.get("tipo",obj.kind or "porcentaje"); obj.value=Decimal(str(data.get("valor",obj.value or 0))); obj.active=data.get("activo",True)
                obj.save(); return response({"id":obj.id,"nombre":obj.name,"name":obj.name,"tipo":getattr(obj,"kind",""),"valor":float(getattr(obj,"value",0) or 0)},201 if not record_id else 200)
            if request.method == "DELETE": lookup(model,record_id).delete(); return response({"ok":True})
        return error("Ruta o método no encontrado",404)
    except model_does_not_exist(): return error("Registro no encontrado",404)
    except (ValueError, KeyError, TypeError, IndexError) as exc: return error(exc)
    except ProtectedError: return error("No se puede eliminar: existen registros asociados")
    except IntegrityError: return error("No se pudo guardar. Revisa que el código o nombre no esté repetido.")

def model_does_not_exist():
    from django.core.exceptions import ObjectDoesNotExist
    return ObjectDoesNotExist
