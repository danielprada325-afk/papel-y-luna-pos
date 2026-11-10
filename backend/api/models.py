from django.conf import settings
from django.db import models
from django.utils import timezone

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    def __str__(self): return self.name

class Client(models.Model):
    name = models.CharField(max_length=150)
    phone = models.CharField(max_length=40, blank=True)
    email = models.EmailField(blank=True)
    def __str__(self): return self.name

class Provider(models.Model):
    name = models.CharField(max_length=150)
    phone = models.CharField(max_length=40, blank=True)
    email = models.EmailField(blank=True)
    tax_id = models.CharField(max_length=40, blank=True)
    def __str__(self): return self.name

class Discount(models.Model):
    PERCENT = "porcentaje"
    FIXED = "fijo"
    name = models.CharField(max_length=100, unique=True)
    kind = models.CharField(max_length=12, choices=[(PERCENT, "Porcentaje"), (FIXED, "Valor fijo")])
    value = models.DecimalField(max_digits=12, decimal_places=2)
    active = models.BooleanField(default=True)
    def __str__(self): return self.name

class Product(models.Model):
    code = models.CharField(max_length=40, unique=True)
    name = models.CharField(max_length=150)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    price = models.DecimalField(max_digits=12, decimal_places=2)
    cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    track_inventory = models.BooleanField(default=True)
    stock = models.PositiveIntegerField(default=0)
    def __str__(self): return self.name

class Sale(models.Model):
    OPEN, CLOSED = "abierta", "cerrada"
    date = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=12, default=OPEN)
    client = models.ForeignKey(Client, on_delete=models.PROTECT, null=True, blank=True)
    payment_method = models.CharField(max_length=20, default="Efectivo")
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    received = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    change = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount = models.ForeignKey(Discount, on_delete=models.SET_NULL, null=True, blank=True)
    corrected_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="corrected_sales")
    corrected_at = models.DateTimeField(null=True, blank=True)
    refund_status = models.CharField(max_length=12, blank=True)

class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)

class Purchase(models.Model):
    date = models.DateTimeField(default=timezone.now)
    provider = models.ForeignKey(Provider, on_delete=models.PROTECT, related_name="purchases")
    payment_method = models.CharField(max_length=30, default="Efectivo")
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

class PurchaseItem(models.Model):
    purchase = models.ForeignKey(Purchase, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2)

class Refund(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.PROTECT, related_name="refunds")
    created_at = models.DateTimeField(default=timezone.now)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

class RefundItem(models.Model):
    refund = models.ForeignKey(Refund, on_delete=models.CASCADE, related_name="items")
    sale_item = models.ForeignKey(SaleItem, on_delete=models.SET_NULL, null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.PROTECT, null=True, blank=True)
    quantity = models.PositiveIntegerField()
    unit_amount = models.DecimalField(max_digits=12, decimal_places=2)
    return_to_stock = models.BooleanField(default=False)

class Shortage(models.Model):
    name = models.CharField(max_length=150)
    normalized_name = models.CharField(max_length=150, db_index=True)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    kind = models.CharField(max_length=20, choices=[("agotado", "Agotado"), ("inexistente", "Inexistente")])
    provider = models.ForeignKey(Provider, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=12, default="pendiente")
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
