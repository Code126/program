import pandas as pd
from models import db, ProductType, Product, Variant, Order, OrderItem

def export_inventory_xlsx(path):
    rows = []
    for v in Variant.query.all():
        rows.append({
            "sku": v.product.sku,
            "product_name": v.product.name,
            "product_type": v.product.product_type.name,
            "size": v.size,
            "color": v.color,
            "price": v.price,
            "stock": v.stock,
        })
    df = pd.DataFrame(rows)
    df.to_excel(path, index=False)

def export_orders_xlsx(path):
    rows = []
    for o in Order.query.order_by(Order.id.asc()).all():
        for it in o.items:
            rows.append({
                "order_number": o.order_number,
                "created_at": o.created_at,
                "customer_name": o.customer_name,
                "variant": f"{it.variant.product.name} {it.variant.size}/{it.variant.color}",
                "quantity": it.quantity,
                "unit_price": it.unit_price,
                "line_total": it.quantity * it.unit_price
            })
    df = pd.DataFrame(rows)
    df.to_excel(path, index=False)

def export_template_xlsx(path):
    cols = ["sku","product_name","product_type","size","color","price","initial_stock"]
    df = pd.DataFrame(columns=cols)
    with pd.ExcelWriter(path) as writer:
        df.to_excel(writer, sheet_name="variants", index=False)

def import_inventory_from_xlsx(path):
    msgs = []
    df = pd.read_excel(path, sheet_name="variants")
    for _, row in df.iterrows():
        sku = str(row.get("sku","")).strip()
        name = str(row.get("product_name","")).strip()
        ptype = str(row.get("product_type","")).strip().title()
        size = str(row.get("size","")).strip()
        color = str(row.get("color","")).strip()
        price = float(row.get("price", 0) or 0)
        initial_stock = int(row.get("initial_stock", 0) or 0)
        if not sku or not name or ptype not in ("Hoodie","Jacket"):
            msgs.append(f"Fila inválida (SKU {sku}), tipo debe ser Hoodie/Jacket")
            continue
        pt = ProductType.query.filter_by(name=ptype).first()
        p = Product.query.filter_by(sku=sku).first()
        if not p:
            p = Product(sku=sku, name=name, product_type=pt)
            db.session.add(p)
            db.session.flush()
        v = Variant(product=p, size=size, color=color, price=price, stock=initial_stock)
        db.session.add(v)
    db.session.commit()
    msgs.append("Importación completada")
    return msgs
