import os
from datetime import datetime
from flask import current_app
from models import db, Product, Variant, InventoryMovement, Order, OrderItem

def ensure_instance_dir(app):
    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except OSError:
        pass

class InventoryService:
    @staticmethod
    def add_movement(variant: Variant, delta: int, reason: str, reference: str=None):
        variant.stock = (variant.stock or 0) + delta
        move = InventoryMovement(variant=variant, change=delta, reason=reason, reference=reference)
        db.session.add(move)
        db.session.add(variant)
        db.session.commit()
        return move

class OrderService:
    @staticmethod
    def _next_order_number():
        # simple sequential number
        last = Order.query.order_by(Order.id.desc()).first()
        n = 1 if not last else last.id + 1
        return f"{n:06d}"

    @staticmethod
    def create_order(customer_name: str, items: list[tuple[Variant,int]]):
        order = Order(order_number=OrderService._next_order_number(), customer_name=customer_name)
        db.session.add(order)
        db.session.flush()
        total = 0.0
        for variant, qty in items:
            if variant.stock < qty:
                raise ValueError(f"Stock insuficiente para {variant.product.name} {variant.size}/{variant.color}")
            oi = OrderItem(order=order, variant=variant, quantity=qty, unit_price=variant.price)
            db.session.add(oi)
            InventoryService.add_movement(variant, -qty, "Sale", reference=f"order:{order.order_number}")
            total += variant.price * qty
        db.session.commit()
        return order
