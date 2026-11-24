# NIT Trichy Order-to-Audit – Dummy CSV dataset

All records are synthetic and intended only for local development/testing.

## Folders
- `schema_compatible/`: CSVs whose columns match the 10 tables in the supplied schema.sql.
- `extended_for_full_requirements/`: useful additional CSVs for suppliers, BOM, purchases, material-level consumption, dispatch and audit history. These require additional database tables/columns before import.

## Demo users
All five users have the same demo password: `Demo@123`.
The `password_hash` column contains a bcrypt hash generated for this password if bcrypt was available when this bundle was created. If your app uses a different password hashing scheme, generate hashes through your own authentication utility instead of storing plaintext passwords.

## Import order for schema-compatible CSVs
1. users.csv
2. customers.csv
3. products.csv
4. items.csv
5. movements.csv
6. orders.csv
7. runs.csv
8. invoices.csv
9. payments.csv
10. costs.csv

Use pgAdmin Import/Export for each file, matching columns by header. Ensure the target tables are empty or use a controlled upsert strategy; SERIAL sequences may need resetting after explicit IDs are imported.

## Benchmark scenario notes
- Purchase receipt: 60 kg flour @ ₹45/kg.
- Production: 40 kg flour, 10.5 L oil, 1.2 kg spice; 188 good packets; 6 damaged pouches; 9 cartons.
- Opening finished goods: 50 packets; production adds 188; Retailer A dispatches 150; closing finished goods = 88.
- Retailer A invoice: taxable ₹7,500; CGST ₹187.50; SGST ₹187.50; total ₹7,875; payment ₹4,000; outstanding ₹3,875.
- Distributor B order: 120 packets; shortage 32 against 88 available after Retailer A dispatch.
- Flour closing: 100 + 60 - 40 = 120 kg.
- Oil closing: 30 - 10.5 = 19.5 L.
- Pouch closing: 500 - 194 = 306 pieces.

## Important schema limitations
The supplied schema has no supplier, BOM, purchase, dispatch, material-consumption or audit-log tables. It also does not store order product lines or explicit finished-goods references. Therefore the `extended_for_full_requirements` files cannot be imported into the current schema without adding those structures. The schema-compatible `movements.csv` records the benchmark events using the existing `items` and `movements` tables, with source descriptions carrying document references.
