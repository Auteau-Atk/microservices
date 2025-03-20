from sqlalchemy.orm import DeclarativeBase, mapped_column
from sqlalchemy import Float, Integer, String, DateTime
from datetime import datetime
import uuid

class Base(DeclarativeBase):
    pass

class PartPurchased(Base):
    __tablename__ = "part_purchased"
    part_id = mapped_column(Integer, primary_key=True, nullable=False, autoincrement=True)
    trace_id = mapped_column(String(255), default=lambda: str(uuid.uuid4()), nullable=False)
    part_name = mapped_column(String(255), nullable=False)
    price = mapped_column(Float, nullable=False)
    seller_id = mapped_column(Integer, nullable=False)
    buyer_id = mapped_column(Integer, nullable=False)
    date_created = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "part_id": self.part_id,
            "trace_id": self.trace_id,
            "part_name": self.part_name,
            "price": self.price,
            "seller_id": self.seller_id,
            "buyer_id": self.buyer_id,
            "date_created": self.date_created.isoformat() if self.date_created else None,
        }

class PartDelivery(Base):
    __tablename__ = "part_delivery"
    delivery_id = mapped_column(Integer, primary_key=True, nullable=False, autoincrement=True)
    trace_id = mapped_column(String(255), default=lambda: str(uuid.uuid4()), nullable=False)
    estimated_days_of_delivery = mapped_column(Integer, nullable=False)
    departure_date = mapped_column(DateTime, nullable=False)
    destination = mapped_column(String(255), nullable=False)
    buyer_id = mapped_column(Integer, nullable=False)
    part_id = mapped_column(Integer, nullable=False)
    date_created = mapped_column(DateTime, default=datetime.utcnow(), nullable=False)

    def to_dict(self):
        return {
            "delivery_id": self.delivery_id,
            "trace_id": self.trace_id,
            "estimated_days_of_delivery": self.estimated_days_of_delivery,
            "departure_date": self.departure_date.isoformat() if self.departure_date else None,
            "destination": self.destination,
            "buyer_id": self.buyer_id,
            "part_id": self.part_id,
            "date_created": self.date_created.isoformat() if self.date_created else None,
        }

