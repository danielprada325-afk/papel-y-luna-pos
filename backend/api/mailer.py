"""Envío de la factura por correo cuando la venta solicita factura electrónica.

Proveedores soportados (se elige según las variables de entorno):
- Brevo (recomendado en Render): BREVO_API_KEY y EMAIL_FROM (remitente verificado en Brevo).
- SMTP (por ejemplo Gmail con contraseña de aplicación): EMAIL_HOST, EMAIL_PORT,
  EMAIL_HOST_USER, EMAIL_HOST_PASSWORD y EMAIL_FROM.
Si no hay ninguno configurado, la venta queda marcada como "no enviada" con el motivo.
Este envío es una copia de la factura de venta: no transmite el documento a la DIAN.
"""
import json
import os
import urllib.error
import urllib.request

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils import timezone
from django.utils.html import escape

BUSINESS = "Papel y Luna"


def cop(value):
    return "$ " + f"{float(value):,.0f}".replace(",", ".")


def local_dt(value):
    return timezone.localtime(value).strftime("%d/%m/%Y %I:%M %p")


def provider():
    if os.getenv("BREVO_API_KEY"):
        return "brevo"
    if os.getenv("EMAIL_HOST"):
        return "smtp"
    if getattr(settings, "EMAIL_BACKEND", "").endswith("locmem.EmailBackend"):
        return "smtp"  # pruebas automáticas
    return None


def invoice_lines(sale):
    return [(i.product.name, i.quantity, i.unit_price * i.quantity) for i in sale.items.select_related("product").all()]


def invoice_text(sale):
    rows = "\n".join(f"- {n} x {q}: {cop(t)}" for n, q, t in invoice_lines(sale))
    extra = f"\nIVA {sale.tax_rate:.0f}%: {cop(sale.tax_amount)}" if sale.tax_applied else ""
    return (
        f"{BUSINESS} - Factura de venta #{sale.id}\n"
        f"Fecha: {local_dt(sale.date)}\n"
        f"Cliente: {sale.e_invoice_name} - NIT/CC {sale.e_invoice_doc}\n\n{rows}\n\n"
        f"Subtotal: {cop(sale.subtotal)}\nDescuento: -{cop(sale.discount_amount)}{extra}\n"
        f"TOTAL: {cop(sale.total)}\nMedio de pago: {sale.payment_method}\n\n"
        "Gracias por tu compra.\n"
        "Este correo es una copia de tu factura de venta; no corresponde a una factura electrónica validada por la DIAN."
    )


def invoice_html(sale):
    purple, ink, muted, line = "#6f4fc4", "#252638", "#85869a", "#ecebf2"
    rows = "".join(
        f'<tr><td style="padding:10px 0;border-bottom:1px solid {line};color:{ink}">{escape(n)}'
        f'<span style="color:{muted}"> &times; {q}</span></td>'
        f'<td style="padding:10px 0;border-bottom:1px solid {line};text-align:right;color:{ink};white-space:nowrap">{cop(t)}</td></tr>'
        for n, q, t in invoice_lines(sale)
    )

    def total_row(label, value, strong=False):
        weight = "700" if strong else "400"
        size = "18px" if strong else "14px"
        color = ink if strong else muted
        return (f'<tr><td style="padding:4px 0;color:{color};font-size:{size};font-weight:{weight}">{label}</td>'
                f'<td style="padding:4px 0;text-align:right;color:{ink};font-size:{size};font-weight:{weight};white-space:nowrap">{value}</td></tr>')

    totals = total_row("Subtotal", cop(sale.subtotal))
    if sale.discount_amount:
        totals += total_row("Descuento", "&minus;" + cop(sale.discount_amount))
    if sale.tax_applied:
        totals += total_row(f"IVA {sale.tax_rate:.0f}%", cop(sale.tax_amount))
    totals += total_row("Total", cop(sale.total), strong=True)
    payment = escape(sale.payment_method)
    if sale.payment_method == "Efectivo" and sale.received is not None:
        payment += f" &middot; Recibido {cop(sale.received)} &middot; Cambio {cop(sale.change)}"
    corrected = (f'<p style="margin:12px 0 0;font-size:12px;color:{purple}">Factura corregida el {local_dt(sale.corrected_at)}</p>'
                 if sale.corrected_at else "")
    return f"""<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Factura de venta #{sale.id}</title></head>
<body style="margin:0;padding:0;background:#f4f3f8;font-family:Arial,Helvetica,sans-serif;-webkit-text-size-adjust:100%">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f4f3f8;padding:24px 12px"><tr><td align="center">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:520px;background:#ffffff;border-radius:16px;overflow:hidden">
<tr><td style="background:{purple};padding:22px 26px;color:#ffffff">
  <div style="font-size:12px;letter-spacing:2px;opacity:.85">PAPELERÍA</div>
  <div style="font-size:24px;font-weight:700;margin-top:2px">{BUSINESS}</div>
  <div style="font-size:14px;margin-top:6px;opacity:.95">Factura de venta #{sale.id}</div>
</td></tr>
<tr><td style="padding:22px 26px">
  <p style="margin:0 0 4px;color:{ink};font-size:15px">Hola <b>{escape(sale.e_invoice_name)}</b>,</p>
  <p style="margin:0 0 18px;color:{muted};font-size:13px">Te enviamos la factura de tu compra del {local_dt(sale.date)}.</p>
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#faf9fd;border:1px solid {line};border-radius:12px;margin-bottom:16px">
    <tr><td style="padding:12px 14px;font-size:12px;color:{muted};line-height:1.7">
      <b style="color:{ink}">Datos de facturación</b><br>
      Nombre o razón social: {escape(sale.e_invoice_name)}<br>
      NIT / C.C.: {escape(sale.e_invoice_doc)}<br>
      Correo: {escape(sale.e_invoice_email)}
    </td></tr></table>
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="font-size:14px">{rows}</table>
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin-top:12px">{totals}</table>
  <p style="margin:14px 0 0;font-size:13px;color:{muted}">Medio de pago: <b style="color:{ink}">{payment}</b></p>
  {corrected}
</td></tr>
<tr><td style="padding:16px 26px;background:#faf9fd;border-top:1px solid {line};font-size:11px;color:{muted};line-height:1.6">
  Gracias por comprar en {BUSINESS}.<br>
  Este correo es una copia de tu factura de venta y no corresponde a una factura electrónica validada por la DIAN.
</td></tr>
</table></td></tr></table></body></html>"""


def send(sale):
    to = (sale.e_invoice_email or "").strip()
    if not to:
        raise ValueError("la venta no tiene correo de factura electrónica")
    kind = provider()
    if not kind:
        raise RuntimeError("el servidor no tiene configurado un servicio de correo (ver README)")
    subject = f"Factura de venta #{sale.id} · {BUSINESS}"
    sender = os.getenv("EMAIL_FROM") or settings.DEFAULT_FROM_EMAIL
    html, text = invoice_html(sale), invoice_text(sale)
    if kind == "brevo":
        body = json.dumps({
            "sender": {"name": BUSINESS, "email": sender},
            "to": [{"email": to, "name": sale.e_invoice_name or to}],
            "subject": subject, "htmlContent": html, "textContent": text,
        }).encode()
        req = urllib.request.Request("https://api.brevo.com/v3/smtp/email", data=body, method="POST", headers={
            "api-key": os.environ["BREVO_API_KEY"], "Content-Type": "application/json", "Accept": "application/json"})
        try:
            urllib.request.urlopen(req, timeout=15).read()
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode(errors="ignore")[:160]
            raise RuntimeError(f"Brevo respondió {exc.code}: {detail}") from exc
        return
    message = EmailMultiAlternatives(subject, text, f"{BUSINESS} <{sender}>", [to])
    message.attach_alternative(html, "text/html")
    message.send()


def deliver(sale):
    """Envía la factura y guarda el resultado en la venta. Nunca lanza excepción."""
    try:
        send(sale)
        sale.e_invoice_sent_at = timezone.now()
        sale.e_invoice_status = f"Enviada a {sale.e_invoice_email}"
    except Exception as exc:  # el cobro ya quedó guardado; solo se informa el fallo del correo
        sale.e_invoice_status = f"No enviada: {exc}"[:255]
    sale.save(update_fields=["e_invoice_sent_at", "e_invoice_status"])
    return sale
