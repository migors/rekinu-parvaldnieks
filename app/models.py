from sqlalchemy import (
    Column, Integer, String, Float, Date, DateTime, ForeignKey, Text, Boolean, func
)
from sqlalchemy.orm import relationship
from .database import Base



class User(Base):
    """Application users (admins)."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, server_default=func.now())


class Settings(Base):
    """Stores issuer / company settings as key-value pairs."""
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(Text, default="")


class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    reg_number = Column(String(50), default="")
    vat_number = Column(String(50), default="")
    legal_address = Column(String(500), default="")
    bank_name = Column(String(255), default="")
    bank_swift = Column(String(20), default="")
    bank_account = Column(String(50), default="")
    postal_code = Column(String(20), default="")
    email = Column(String(255), default="")
    created_at = Column(DateTime, server_default=func.now())

    invoices = relationship("Invoice", back_populates="client")


class Service(Base):
    """Predefined service or product catalog entry."""
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(500), nullable=False)
    unit = Column(String(50), default="gab.")
    default_price = Column(Float, default=0)
    vat_rate = Column(Float, default=21)  # 0 or 21
    created_at = Column(DateTime, server_default=func.now())


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    invoice_number = Column(String(20), unique=True, nullable=False, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)
    issuer_name = Column(String(255), default="")
    notes = Column(Text, default="")
    status = Column(String(20), default="sent")  # sent, paid (draft removed)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    client = relationship("Client", back_populates="invoices")
    items = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")

    @property
    def subtotal(self) -> float:
        return round(sum(item.total for item in self.items), 2)

    @property
    def vat_amount(self) -> float:
        """Sum of VAT per each line item (supports mixed rates)."""
        return round(sum(item.vat_amount for item in self.items), 2)

    @property
    def grand_total(self) -> float:
        return round(self.subtotal + self.vat_amount, 2)


class InvoiceItem(Base):
    __tablename__ = "invoice_items"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False)
    description = Column(String(500), nullable=False)
    unit = Column(String(50), default="gab.")
    quantity = Column(Float, nullable=False, default=1)
    unit_price = Column(Float, nullable=False, default=0)
    vat_rate = Column(Float, nullable=False, default=21)  # 0 or 21

    invoice = relationship("Invoice", back_populates="items")

    @property
    def total(self) -> float:
        return round(self.quantity * self.unit_price, 2)

    @property
    def vat_amount(self) -> float:
        return round(self.total * self.vat_rate / 100, 2)

    @property
    def total_with_vat(self) -> float:
        return round(self.total + self.vat_amount, 2)
