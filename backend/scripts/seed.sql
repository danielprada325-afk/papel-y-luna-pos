-- Datos iniciales de Papel y Luna POS (usuarios y catálogo de demostración).
-- Ejecutar DESPUÉS de crear las tablas (python manage.py migrate o scripts/schema.sql).
-- Equivale a: python manage.py seed_pos
-- Usuarios: admin / Admin123!  (administrador)  ·  cajero / Cajero123!  (cajero)
-- Las contraseñas se guardan con el hash PBKDF2 de Django.

INSERT INTO auth_user (id, username, password, email, first_name, last_name, is_staff, is_superuser, is_active, date_joined) VALUES (1, 'admin', 'pbkdf2_sha256$1500000$eLJY4lekAehV0VIORe5neZ$WNzbNUAsg0+tcx8YdwyU7AzR4BZcjidTgHTZMXaLJWQ=', 'admin@papelyluna.local', '', '', TRUE, TRUE, TRUE, CURRENT_TIMESTAMP);
INSERT INTO auth_user (id, username, password, email, first_name, last_name, is_staff, is_superuser, is_active, date_joined) VALUES (2, 'cajero', 'pbkdf2_sha256$1500000$w2hpTCYjYnJd2dmr3qqPk2$RUtDwENRzoqTopil1LMHBtiDLHCxjBZ32nUmTgMkbrE=', 'cajero@papelyluna.local', '', '', FALSE, FALSE, TRUE, CURRENT_TIMESTAMP);

INSERT INTO api_category (id, name) VALUES (1, 'Cuadernos');
INSERT INTO api_category (id, name) VALUES (2, 'Escritura');
INSERT INTO api_category (id, name) VALUES (3, 'Arte');
INSERT INTO api_category (id, name) VALUES (4, 'Papel');
INSERT INTO api_category (id, name) VALUES (5, 'Oficina');
INSERT INTO api_category (id, name) VALUES (6, 'Archivo');
INSERT INTO api_provider (id, name, phone, email, tax_id) VALUES (1, 'Distribuciones Luna', '3000000000', 'proveedor@papelyluna.local', '');
INSERT INTO api_client (id, name, phone, email) VALUES (1, 'Cliente mostrador', '', '');
INSERT INTO api_product (id, code, name, category_id, price, cost, track_inventory, stock, min_stock) VALUES (1, 'CUA-001', 'Cuaderno Argollado Luna', 1, 18500.00, 10500.00, TRUE, 12, 5);
INSERT INTO api_product (id, code, name, category_id, price, cost, track_inventory, stock, min_stock) VALUES (2, 'ESC-001', 'Set de Lápices Grafito', 2, 7200.00, 3800.00, TRUE, 20, 5);
INSERT INTO api_product (id, code, name, category_id, price, cost, track_inventory, stock, min_stock) VALUES (3, 'ART-001', 'Marcadores Pastel x6', 3, 15900.00, 9200.00, TRUE, 10, 5);
INSERT INTO api_product (id, code, name, category_id, price, cost, track_inventory, stock, min_stock) VALUES (4, 'PAP-001', 'Resma Carta 75g', 4, 21900.00, 16000.00, TRUE, 8, 5);
INSERT INTO api_product (id, code, name, category_id, price, cost, track_inventory, stock, min_stock) VALUES (5, 'OFI-001', 'Pegante en Barra', 5, 4800.00, 2500.00, TRUE, 15, 5);
INSERT INTO api_product (id, code, name, category_id, price, cost, track_inventory, stock, min_stock) VALUES (6, 'OFI-002', 'Tijeras Escolares', 5, 8900.00, 4800.00, TRUE, 9, 5);
INSERT INTO api_product (id, code, name, category_id, price, cost, track_inventory, stock, min_stock) VALUES (7, 'ARC-001', 'Carpeta Acordeón', 6, 24600.00, 14800.00, TRUE, 6, 5);
INSERT INTO api_product (id, code, name, category_id, price, cost, track_inventory, stock, min_stock) VALUES (8, 'OFI-003', 'Notas Adhesivas', 5, 6200.00, 3000.00, TRUE, 18, 5);
