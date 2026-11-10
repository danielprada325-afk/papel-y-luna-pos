BEGIN;
--
-- Create model Category
--
CREATE TABLE "api_category" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "name" varchar(100) NOT NULL UNIQUE);
--
-- Create model Client
--
CREATE TABLE "api_client" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "name" varchar(150) NOT NULL, "phone" varchar(40) NOT NULL, "email" varchar(254) NOT NULL);
--
-- Create model Discount
--
CREATE TABLE "api_discount" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "name" varchar(100) NOT NULL UNIQUE, "kind" varchar(12) NOT NULL, "value" decimal NOT NULL, "active" bool NOT NULL);
--
-- Create model Provider
--
CREATE TABLE "api_provider" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "name" varchar(150) NOT NULL, "phone" varchar(40) NOT NULL, "email" varchar(254) NOT NULL, "tax_id" varchar(40) NOT NULL);
--
-- Create model Product
--
CREATE TABLE "api_product" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "code" varchar(40) NOT NULL UNIQUE, "name" varchar(150) NOT NULL, "price" decimal NOT NULL, "cost" decimal NOT NULL, "track_inventory" bool NOT NULL, "stock" integer unsigned NOT NULL CHECK ("stock" >= 0), "category_id" bigint NOT NULL REFERENCES "api_category" ("id") DEFERRABLE INITIALLY DEFERRED);
--
-- Create model Purchase
--
CREATE TABLE "api_purchase" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "date" datetime NOT NULL, "payment_method" varchar(30) NOT NULL, "total" decimal NOT NULL, "created_by_id" integer NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED, "provider_id" bigint NOT NULL REFERENCES "api_provider" ("id") DEFERRABLE INITIALLY DEFERRED);
--
-- Create model PurchaseItem
--
CREATE TABLE "api_purchaseitem" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "quantity" integer unsigned NOT NULL CHECK ("quantity" >= 0), "unit_cost" decimal NOT NULL, "product_id" bigint NOT NULL REFERENCES "api_product" ("id") DEFERRABLE INITIALLY DEFERRED, "purchase_id" bigint NOT NULL REFERENCES "api_purchase" ("id") DEFERRABLE INITIALLY DEFERRED);
--
-- Create model Sale
--
CREATE TABLE "api_sale" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "date" datetime NOT NULL, "status" varchar(12) NOT NULL, "payment_method" varchar(20) NOT NULL, "subtotal" decimal NOT NULL, "discount_amount" decimal NOT NULL, "total" decimal NOT NULL, "received" decimal NULL, "change" decimal NOT NULL, "corrected_at" datetime NULL, "refund_status" varchar(12) NOT NULL, "client_id" bigint NULL REFERENCES "api_client" ("id") DEFERRABLE INITIALLY DEFERRED, "corrected_by_id" integer NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED, "discount_id" bigint NULL REFERENCES "api_discount" ("id") DEFERRABLE INITIALLY DEFERRED);
--
-- Create model Refund
--
CREATE TABLE "api_refund" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "created_at" datetime NOT NULL, "amount" decimal NOT NULL, "created_by_id" integer NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED, "sale_id" bigint NOT NULL REFERENCES "api_sale" ("id") DEFERRABLE INITIALLY DEFERRED);
--
-- Create model SaleItem
--
CREATE TABLE "api_saleitem" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "quantity" integer unsigned NOT NULL CHECK ("quantity" >= 0), "unit_price" decimal NOT NULL, "product_id" bigint NOT NULL REFERENCES "api_product" ("id") DEFERRABLE INITIALLY DEFERRED, "sale_id" bigint NOT NULL REFERENCES "api_sale" ("id") DEFERRABLE INITIALLY DEFERRED);
--
-- Create model RefundItem
--
CREATE TABLE "api_refunditem" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "quantity" integer unsigned NOT NULL CHECK ("quantity" >= 0), "unit_amount" decimal NOT NULL, "return_to_stock" bool NOT NULL, "refund_id" bigint NOT NULL REFERENCES "api_refund" ("id") DEFERRABLE INITIALLY DEFERRED, "sale_item_id" bigint NOT NULL REFERENCES "api_saleitem" ("id") DEFERRABLE INITIALLY DEFERRED);
--
-- Create model Shortage
--
CREATE TABLE "api_shortage" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "name" varchar(150) NOT NULL, "normalized_name" varchar(150) NOT NULL, "quantity" integer unsigned NOT NULL CHECK ("quantity" >= 0), "kind" varchar(20) NOT NULL, "status" varchar(12) NOT NULL, "note" text NOT NULL, "created_at" datetime NOT NULL, "created_by_id" integer NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED, "product_id" bigint NULL REFERENCES "api_product" ("id") DEFERRABLE INITIALLY DEFERRED, "provider_id" bigint NULL REFERENCES "api_provider" ("id") DEFERRABLE INITIALLY DEFERRED);
CREATE INDEX "api_product_category_id_a2b9d1e7" ON "api_product" ("category_id");
CREATE INDEX "api_purchase_created_by_id_a62188e1" ON "api_purchase" ("created_by_id");
CREATE INDEX "api_purchase_provider_id_e8d16047" ON "api_purchase" ("provider_id");
CREATE INDEX "api_purchaseitem_product_id_2fa80a71" ON "api_purchaseitem" ("product_id");
CREATE INDEX "api_purchaseitem_purchase_id_a7a0c19e" ON "api_purchaseitem" ("purchase_id");
CREATE INDEX "api_sale_client_id_04ca5649" ON "api_sale" ("client_id");
CREATE INDEX "api_sale_corrected_by_id_46ae6a63" ON "api_sale" ("corrected_by_id");
CREATE INDEX "api_sale_discount_id_123caeb6" ON "api_sale" ("discount_id");
CREATE INDEX "api_refund_created_by_id_6399602b" ON "api_refund" ("created_by_id");
CREATE INDEX "api_refund_sale_id_6971c42f" ON "api_refund" ("sale_id");
CREATE INDEX "api_saleitem_product_id_250ad899" ON "api_saleitem" ("product_id");
CREATE INDEX "api_saleitem_sale_id_a1e52429" ON "api_saleitem" ("sale_id");
CREATE INDEX "api_refunditem_refund_id_f3124f7a" ON "api_refunditem" ("refund_id");
CREATE INDEX "api_refunditem_sale_item_id_8d4c14c6" ON "api_refunditem" ("sale_item_id");
CREATE INDEX "api_shortage_normalized_name_c89c4c7d" ON "api_shortage" ("normalized_name");
CREATE INDEX "api_shortage_created_by_id_72291419" ON "api_shortage" ("created_by_id");
CREATE INDEX "api_shortage_product_id_4aaca845" ON "api_shortage" ("product_id");
CREATE INDEX "api_shortage_provider_id_64de3c0e" ON "api_shortage" ("provider_id");
COMMIT;
BEGIN;
--
-- Add field product to refunditem
--
ALTER TABLE "api_refunditem" ADD COLUMN "product_id" bigint NULL REFERENCES "api_product" ("id") DEFERRABLE INITIALLY DEFERRED;
--
-- Alter field sale_item on refunditem
--
CREATE TABLE "new__api_refunditem" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "quantity" integer unsigned NOT NULL CHECK ("quantity" >= 0), "unit_amount" decimal NOT NULL, "return_to_stock" bool NOT NULL, "refund_id" bigint NOT NULL REFERENCES "api_refund" ("id") DEFERRABLE INITIALLY DEFERRED, "product_id" bigint NULL REFERENCES "api_product" ("id") DEFERRABLE INITIALLY DEFERRED, "sale_item_id" bigint NULL REFERENCES "api_saleitem" ("id") DEFERRABLE INITIALLY DEFERRED);
INSERT INTO "new__api_refunditem" ("id", "quantity", "unit_amount", "return_to_stock", "refund_id", "product_id", "sale_item_id") SELECT "id", "quantity", "unit_amount", "return_to_stock", "refund_id", "product_id", "sale_item_id" FROM "api_refunditem";
DROP TABLE "api_refunditem";
ALTER TABLE "new__api_refunditem" RENAME TO "api_refunditem";
CREATE INDEX "api_refunditem_refund_id_f3124f7a" ON "api_refunditem" ("refund_id");
CREATE INDEX "api_refunditem_product_id_07f5d057" ON "api_refunditem" ("product_id");
CREATE INDEX "api_refunditem_sale_item_id_8d4c14c6" ON "api_refunditem" ("sale_item_id");
--
-- Alter field client on sale
--
-- (no-op)
COMMIT;
