SELECT i.name,COALESCE(SUM(m.delta),0) balance,i.unit FROM items i LEFT JOIN movements m ON m.item_id=i.id GROUP BY i.id ORDER BY i.id;
SELECT * FROM runs ORDER BY id DESC;
SELECT * FROM orders ORDER BY id DESC;
SELECT * FROM invoices ORDER BY id DESC;
