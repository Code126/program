from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class ProductType(db.Model):
    __tablename__ = "product_types"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

    @staticmethod
    def seed_defaults():
        if not ProductType.query.first():
            for n in ("Hoodie","Jacket"):
                db.session.add(ProductType(name=n))
            db.session.commit()

class Product(db.Model):
    __tablename__ = "products"
    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(64), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    product_type_id = db.Column(db.Integer, db.ForeignKey("product_types.id"), nullable=False)
    product_type = db.relationship("ProductType", backref=db.backref("products", lazy=True))

class Variant(db.Model):
    __tablename__ = "variants"
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    product = db.relationship("Product", backref=db.backref("variants", lazy=True, cascade="all, delete-orphan"))
    size = db.Column(db.String(20), nullable=False)
    color = db.Column(db.String(30), nullable=False)
    price = db.Column(db.Float, nullable=False, default=0.0)
    stock = db.Column(db.Integer, nullable=False, default=0)

class InventoryMovement(db.Model):
    __tablename__ = "inventory_movements"
    id = db.Column(db.Integer, primary_key=True)
    variant_id = db.Column(db.Integer, db.ForeignKey("variants.id"), nullable=False)
    variant = db.relationship("Variant", backref=db.backref("movements", lazy=True, cascade="all, delete-orphan"))
    change = db.Column(db.Integer, nullable=False)  # +restock, -venta
    reason = db.Column(db.String(120), nullable=False)
    reference = db.Column(db.String(120))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

class Order(db.Model):
    __tablename__ = "orders"
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(20), unique=True, nullable=False)
    customer_name = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    status = db.Column(db.String(20), default="CREATED", nullable=False)

class OrderItem(db.Model):
    __tablename__ = "order_items"
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    order = db.relationship("Order", backref=db.backref("items", lazy=True, cascade="all, delete-orphan"))
    variant_id = db.Column(db.Integer, db.ForeignKey("variants.id"), nullable=False)
    variant = db.relationship("Variant")
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
