from models import db, ProductType, Product, Variant
from services import InventoryService

def seed_all():
    # productos demo
    hoodie = ProductType.query.filter_by(name="Hoodie").first()
    jacket = ProductType.query.filter_by(name="Jacket").first()

    p1 = Product(sku="HOO-001", name="Hoodie Clásica", product_type=hoodie)
    p2 = Product(sku="JAC-001", name="Chaqueta Ligera", product_type=jacket)
    db.session.add_all([p1,p2])
    db.session.flush()

    v1 = Variant(product=p1, size="S", color="Negro", price=119000, stock=10)
    v2 = Variant(product=p1, size="M", color="Gris", price=119000, stock=15)
    v3 = Variant(product=p2, size="Única", color="Azul", price=159000, stock=8)
    db.session.add_all([v1,v2,v3])
    db.session.commit()
