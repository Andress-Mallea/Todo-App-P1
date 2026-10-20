from sqlalchemy import text

from app import create_app
from app.extensions import db

STATEMENTS = [
    # 1. category
    """
    INSERT INTO content.category (name, description)
    SELECT (ARRAY['Entradas','Sopas','Ensaladas','Platos fuertes','Postres',
                  'Bebidas','Cafetería','Pizzas','Parrilla','Mariscos'])[1 + (g % 10)]
           || ' ' || lpad(g::text, 5, '0'),
           'Categoría de menú número ' || g
    FROM generate_series(1, 10000) g
    """,
    # 2. product
    """
    INSERT INTO content.product (category_id, name, price, is_active, deleted_at)
    SELECT c.id,
           'Producto ' || lpad(s.g::text, 5, '0'),
           round((random() * 95 + 5)::numeric, 2),
           NOT s.del,
           CASE WHEN s.del THEN now() END
    FROM (SELECT g, 1 + (g * 7919) % 10000 AS crn, random() < 0.05 AS del
          FROM generate_series(1, 10000) g) s
    JOIN (SELECT id, row_number() OVER (ORDER BY id) rn FROM content.category) c
      ON c.rn = s.crn
    """,
    # 3. customer
    """
    INSERT INTO content.customer (first_name, last_name, email)
    SELECT (ARRAY['Ana','Luis','María','Carlos','Lucía','Jorge','Sofía','Pedro','Valeria','Diego'])[1 + (g % 10)],
           (ARRAY['García','Rodríguez','Fernández','López','Martínez','Pérez','Gómez','Sánchez','Ramírez','Flores'])[1 + ((g / 10) % 10)],
           'cliente' || lpad(g::text, 5, '0') || '@ejemplo.com'
    FROM generate_series(1, 10000) g
    """,
    # 4. dining_table
    """
    INSERT INTO content.dining_table (table_number, capacity, current_status)
    SELECT g,
           1 + (g % 12),
           ((ARRAY['AVAILABLE','OCCUPIED','RESERVED'])[1 + floor(random() * 3)::int])::content.table_status
    FROM generate_series(1, 10000) g
    """,
    # 5. customer_order (el total se calcula después con las líneas)
    """
    INSERT INTO content.customer_order (customer_id, table_id, order_type, status, created_at, updated_at)
    SELECT c.id,
           CASE WHEN s.otype = 'DINE_IN' THEN t.id END,
           s.otype::content.order_type,
           s.ostatus::content.order_status,
           s.ts,
           s.ts
    FROM (SELECT g,
                 1 + (g * 7919) % 10000   AS crn,
                 1 + (g * 104729) % 10000 AS trn,
                 (ARRAY['DINE_IN','TAKEOUT'])[1 + floor(random() * 2)::int] AS otype,
                 (ARRAY['PENDING','PREPARING','READY','COMPLETED','CANCELED'])[1 + floor(random() * 5)::int] AS ostatus,
                 now() - (random() * interval '365 days') AS ts
          FROM generate_series(1, 10000) g) s
    JOIN (SELECT id, row_number() OVER (ORDER BY id) rn FROM content.customer) c ON c.rn = s.crn
    JOIN (SELECT id, row_number() OVER (ORDER BY id) rn FROM content.dining_table) t ON t.rn = s.trn
    """,
    # 6. order_line
     """
    INSERT INTO content.order_line (order_id, product_id, quantity, unit_price)
    SELECT o.id, p.id, s.qty, p.price
    FROM (SELECT g,
                 1 + floor(random() * 10000)::int AS orn,
                 1 + (g * 7919) % 10000           AS prn,
                 1 + floor(random() * 5)::int     AS qty
          FROM generate_series(1, 10000) g) s
    JOIN (SELECT id, row_number() OVER (ORDER BY id) rn FROM content.customer_order) o ON o.rn = s.orn
    JOIN (SELECT id, price, row_number() OVER (ORDER BY id) rn FROM content.product) p ON p.rn = s.prn
    """,
    # 7. total de cada pedido = suma de sus líneas
    """
    UPDATE content.customer_order o
    SET total_amount = t.total
    FROM (SELECT order_id, SUM(quantity * unit_price) AS total
          FROM content.order_line GROUP BY order_id) t
    WHERE t.order_id = o.id
    """,
    # 8. promotion
    """
    INSERT INTO content.promotion (name, discount_percentage, start_date, end_date, is_active)
    SELECT 'Promoción ' || lpad(s.g::text, 5, '0'),
           round((random() * 70 + 5)::numeric, 2),
           s.sd,
           s.sd + (s.dur * interval '1 day'),
           random() > 0.2
    FROM (SELECT g,
                 now() - (random() * interval '180 days') AS sd,
                 7 + floor(random() * 60)::int            AS dur
          FROM generate_series(1, 10000) g) s
    """,
    # 9. promotion_product (pares únicos: cada promoción distinta)
    """
    INSERT INTO content.promotion_product (promotion_id, product_id)
    SELECT pr.id, p.id
    FROM generate_series(1, 10000) g
    JOIN (SELECT id, row_number() OVER (ORDER BY id) rn FROM content.promotion) pr ON pr.rn = g
    JOIN (SELECT id, row_number() OVER (ORDER BY id) rn FROM content.product) p
      ON p.rn = 1 + (g * 7919) % 10000
    """,
]


def poblar_restaurante():
    app = create_app()
    with app.app_context():
        if db.session.execute(text("SELECT count(*) FROM content.category")).scalar():
            print("Datos del restaurante ya existen, no se vuelven a cargar.")
            return
        for sql in STATEMENTS:
            db.session.execute(text(sql))
        db.session.commit()
        print("Datos del restaurante creados: 10000 filas por tabla.")


if __name__ == "__main__":
    poblar_restaurante()