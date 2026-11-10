import os
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from api.models import Category, Client, Product, Provider

class Command(BaseCommand):
    help = "Crea usuarios iniciales y catálogo de demostración Papel y Luna"
    def handle(self, *args, **options):
        admin, created = User.objects.get_or_create(username="admin", defaults={"email":"admin@papelyluna.local", "is_staff":True, "is_superuser":True})
        if created: admin.set_password(os.getenv("ADMIN_PASSWORD", "Admin123!")); admin.save()
        cashier, created = User.objects.get_or_create(username="cajero", defaults={"email":"cajero@papelyluna.local"})
        if created: cashier.set_password(os.getenv("CASHIER_PASSWORD", "Cajero123!")); cashier.save()
        provider, _ = Provider.objects.get_or_create(name="Distribuciones Luna", defaults={"phone":"3000000000", "email":"proveedor@papelyluna.local"})
        client, _ = Client.objects.get_or_create(name="Cliente mostrador")
        catalog = [("Cuadernos","CUA-001","Cuaderno Argollado Luna",18500,10500,12),("Escritura","ESC-001","Set de Lápices Grafito",7200,3800,20),("Arte","ART-001","Marcadores Pastel x6",15900,9200,10),("Papel","PAP-001","Resma Carta 75g",21900,16000,8),("Oficina","OFI-001","Pegante en Barra",4800,2500,15),("Oficina","OFI-002","Tijeras Escolares",8900,4800,9),("Archivo","ARC-001","Carpeta Acordeón",24600,14800,6),("Oficina","OFI-003","Notas Adhesivas",6200,3000,18)]
        for category_name, code, name, price, cost, stock in catalog:
            category, _ = Category.objects.get_or_create(name=category_name)
            Product.objects.get_or_create(code=code, defaults={"name":name,"category":category,"price":price,"cost":cost,"track_inventory":True,"stock":stock})
        self.stdout.write(self.style.SUCCESS("POS inicializado. Usuarios: admin y cajero; datos de demostración listos."))
