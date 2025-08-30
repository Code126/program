import os
from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from models import db, ProductType, Product, Variant, Order, OrderItem, InventoryMovement
from services import InventoryService, OrderService, ensure_instance_dir
from excel_io import export_inventory_xlsx, export_orders_xlsx, export_template_xlsx, import_inventory_from_xlsx

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.secret_key = os.environ.get("SECRET_KEY", "dev-secret")
    ensure_instance_dir(app)

    # SQLite en carpeta instance
    db_path = os.path.join(app.instance_path, "inventory.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + db_path
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    with app.app_context():
        db.create_all()
        ProductType.seed_defaults()

    return app

app = create_app()

@app.route("/")
def index():
    # KPIs simples
    total_products = Product.query.count()
    total_variants = Variant.query.count()
    total_stock = db.session.query(db.func.sum(Variant.stock)).scalar() or 0
    total_orders = Order.query.count()
    return render_template("index.html",
                           total_products=total_products,
                           total_variants=total_variants,
                           total_stock=total_stock,
                           total_orders=total_orders)

# -------- Products --------
@app.route("/products")
def products_list():
    products = Product.query.order_by(Product.name.asc()).all()
    return render_template("products_list.html", products=products)

@app.route("/products/new", methods=["GET", "POST"])
def products_new():
    if request.method == "POST":
        sku = request.form.get("sku","").strip()
        name = request.form.get("name","").strip()
        ptype = request.form.get("product_type","").strip()
        if not sku or not name or ptype not in ("Hoodie","Jacket"):
            flash("Datos inválidos. Revisa SKU, nombre y tipo.", "danger")
            return redirect(url_for("products_new"))
        pt = ProductType.query.filter_by(name=ptype).first()
        p = Product(sku=sku, name=name, product_type=pt)
        db.session.add(p)
        db.session.commit()
        flash("Producto creado", "success")
        return redirect(url_for("products_list"))
    return render_template("products_new.html")

@app.route("/variants/new/<int:product_id>", methods=["GET","POST"])
def variants_new(product_id):
    product = Product.query.get_or_404(product_id)
    if request.method == "POST":
        size = request.form.get("size","").strip()
        color = request.form.get("color","").strip()
        price = float(request.form.get("price","0") or 0)
        stock = int(request.form.get("stock","0") or 0)
        v = Variant(product=product, size=size, color=color, price=price, stock=stock)
        db.session.add(v)
        db.session.commit()
        if stock:
            InventoryService.add_movement(variant=v, delta=stock, reason="Initial stock", reference="init")
        flash("Variante creada", "success")
        return redirect(url_for("inventory_list"))
    return render_template("variants_new.html", product=product)

# -------- Inventory --------
@app.route("/inventory")
def inventory_list():
    variants = Variant.query.order_by(Variant.id.desc()).all()
    return render_template("inventory_list.html", variants=variants)

@app.route("/inventory/adjust/<int:variant_id>", methods=["POST"])
def inventory_adjust(variant_id):
    variant = Variant.query.get_or_404(variant_id)
    try:
        delta = int(request.form.get("delta","0"))
    except ValueError:
        flash("Cantidad inválida", "danger")
        return redirect(url_for("inventory_list"))
    reason = request.form.get("reason","Adjustment").strip() or "Adjustment"
    InventoryService.add_movement(variant, delta, reason, reference="manual")
    flash("Inventario actualizado", "success")
    return redirect(url_for("inventory_list"))

@app.route("/inventory/import", methods=["GET","POST"])
def inventory_import():
    if request.method == "POST":
        f = request.files.get("file")
        if not f:
            flash("Sube un archivo .xlsx", "danger")
            return redirect(url_for("inventory_import"))
        path = os.path.join(app.instance_path, "upload.xlsx")
        f.save(path)
        msgs = import_inventory_from_xlsx(path)
        flash("\n".join(msgs), "info")
        return redirect(url_for("inventory_list"))
    return render_template("inventory_import.html")

@app.route("/export/inventory.xlsx")
def export_inventory():
    path = os.path.join(app.instance_path, "inventory_export.xlsx")
    export_inventory_xlsx(path)
    return send_file(path, as_attachment=True, download_name="inventory.xlsx")

@app.route("/export/orders.xlsx")
def export_orders():
    path = os.path.join(app.instance_path, "orders_export.xlsx")
    export_orders_xlsx(path)
    return send_file(path, as_attachment=True, download_name="orders.xlsx")

@app.route("/export/template.xlsx")
def export_template():
    path = os.path.join(app.instance_path, "template.xlsx")
    export_template_xlsx(path)
    return send_file(path, as_attachment=True, download_name="template.xlsx")

# -------- Orders --------
@app.route("/orders")
def orders_list():
    orders = Order.query.order_by(Order.id.desc()).all()
    return render_template("orders_list.html", orders=orders)

@app.route("/orders/new", methods=["GET","POST"])
def orders_new():
    variants = Variant.query.order_by(Variant.id.desc()).all()
    if request.method == "POST":
        customer = request.form.get("customer_name","").strip() or "Cliente"
        items = []
        for v in variants:
            qty = int(request.form.get(f"qty_{v.id}", "0") or 0)
            if qty > 0:
                items.append((v, qty))
        if not items:
            flash("Agrega al menos un ítem", "danger")
            return redirect(url_for("orders_new"))
        order = OrderService.create_order(customer, items)
        flash(f"Pedido #{order.order_number} creado", "success")
        return redirect(url_for("orders_list"))
    return render_template("orders_new.html", variants=variants)

if __name__ == "__main__":
    app.run(debug=True)
