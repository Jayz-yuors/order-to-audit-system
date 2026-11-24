-- PostgreSQL extension for the original starter schema.
-- Safe to re-run: creates missing objects and adds missing columns only.

ALTER TABLE movements ADD COLUMN IF NOT EXISTS created_at TIMESTAMP;
ALTER TABLE movements ADD COLUMN IF NOT EXISTS reference_type VARCHAR(50);
ALTER TABLE movements ADD COLUMN IF NOT EXISTS reference_id INTEGER;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS product_id INTEGER REFERENCES products(id);
ALTER TABLE runs ADD COLUMN IF NOT EXISTS product_id INTEGER REFERENCES products(id);
ALTER TABLE runs ADD COLUMN IF NOT EXISTS run_date DATE;

CREATE TABLE IF NOT EXISTS suppliers (
  supplier_id SERIAL PRIMARY KEY,
  supplier_name VARCHAR(160) NOT NULL,
  state VARCHAR(80) NOT NULL,
  gstin VARCHAR(20)
);
CREATE TABLE IF NOT EXISTS gst_rates (
  gst_rate_id SERIAL PRIMARY KEY,
  description VARCHAR(160) NOT NULL,
  rate_percent NUMERIC(5,2) NOT NULL,
  effective_from DATE NOT NULL
);
CREATE TABLE IF NOT EXISTS bom_headers (
  bom_id SERIAL PRIMARY KEY,
  product_id INTEGER NOT NULL REFERENCES products(id),
  product_name VARCHAR(160) NOT NULL,
  batch_size_packets INTEGER NOT NULL,
  expected_output_packets INTEGER NOT NULL,
  created_at TIMESTAMP
);
CREATE TABLE IF NOT EXISTS bom_lines (
  bom_line_id SERIAL PRIMARY KEY,
  bom_id INTEGER NOT NULL REFERENCES bom_headers(bom_id),
  item_id INTEGER NOT NULL REFERENCES items(id),
  item_name VARCHAR(160) NOT NULL,
  quantity_per_batch NUMERIC(14,3) NOT NULL,
  unit VARCHAR(20) NOT NULL
);
CREATE TABLE IF NOT EXISTS purchases (
  purchase_id SERIAL PRIMARY KEY,
  supplier_id INTEGER NOT NULL REFERENCES suppliers(supplier_id),
  purchase_date DATE NOT NULL,
  reference_no VARCHAR(80) UNIQUE NOT NULL,
  item_id INTEGER NOT NULL REFERENCES items(id),
  quantity NUMERIC(14,3) NOT NULL,
  unit VARCHAR(20) NOT NULL,
  unit_rate NUMERIC(12,2) NOT NULL,
  line_total NUMERIC(14,2) NOT NULL
);
CREATE TABLE IF NOT EXISTS production_consumption (
  consumption_id SERIAL PRIMARY KEY,
  run_id INTEGER NOT NULL REFERENCES runs(id),
  item_id INTEGER NOT NULL REFERENCES items(id),
  planned_qty NUMERIC(14,3) NOT NULL,
  actual_qty NUMERIC(14,3) NOT NULL,
  unit VARCHAR(20) NOT NULL,
  variance_qty NUMERIC(14,3) NOT NULL,
  variance_percent NUMERIC(8,3) NOT NULL
);
CREATE TABLE IF NOT EXISTS dispatches (
  dispatch_id SERIAL PRIMARY KEY,
  invoice_id INTEGER NOT NULL REFERENCES invoices(id),
  dispatch_date DATE NOT NULL,
  product_id INTEGER NOT NULL REFERENCES products(id),
  quantity_dispatched INTEGER NOT NULL,
  status VARCHAR(30) NOT NULL
);
CREATE TABLE IF NOT EXISTS audit_log (
  audit_id SERIAL PRIMARY KEY,
  entity_type VARCHAR(80) NOT NULL,
  entity_id INTEGER NOT NULL,
  action VARCHAR(80) NOT NULL,
  performed_by_user_id INTEGER REFERENCES users(id),
  event_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  details TEXT
);

-- Backfill the one-product demo's product references where needed.
UPDATE orders SET product_id = 1 WHERE product_id IS NULL;
UPDATE runs SET product_id = 1 WHERE product_id IS NULL;

-- Set NOT NULL only after backfill; this project seed contains product id 1.
ALTER TABLE orders ALTER COLUMN product_id SET NOT NULL;
ALTER TABLE runs ALTER COLUMN product_id SET NOT NULL;
