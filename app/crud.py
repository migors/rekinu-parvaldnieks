"""CRUD operations for clients, invoices, services, and settings."""

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, func, extract
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from typing import Optional, List
from datetime import date as date_type
from . import models, schemas
from .utils import generate_invoice_number


# ── Settings ──────────────────────────────────────────────────────────

SETTINGS_KEYS = [
    "company_name", "reg_number", "vat_number", "vat_enabled", "legal_address",
    "bank1_name", "bank1_swift", "bank1_account",
    "bank2_name", "bank2_swift", "bank2_account",
    "phone", "email",
    "smtp_server", "smtp_port", "smtp_username", "smtp_password", "smtp_from_email", "smtp_tls",
    "gdrive_enabled", "gdrive_folder_id", "gdrive_client_id", "gdrive_client_secret", "gdrive_refresh_token",
    "logo_base64",
    "invoice_prefix",
    "eds_enabled", "eds_api_key",
]


def get_settings(db: Session) -> dict:
    rows = db.query(models.Settings).all()
    data = {k: "" for k in SETTINGS_KEYS}
    data["vat_enabled"] = "true"  # default
    for row in rows:
        if row.key in data:
            data[row.key] = row.value
    return data


def update_settings(db: Session, data: schemas.SettingsUpdate) -> dict:
    updates = data.model_dump(exclude_unset=True)
    for key, value in updates.items():
        stmt = sqlite_insert(models.Settings).values(key=key, value=value or "")
        stmt = stmt.on_conflict_do_update(
            index_elements=["key"],
            set_={"value": value or ""}
        )
        db.execute(stmt)
    db.commit()
    return get_settings(db)


def set_setting(db: Session, key: str, value: str):
    """Set a single setting value."""
    row = db.query(models.Settings).filter(models.Settings.key == key).first()
    if row:
        row.value = value
    else:
        db.add(models.Settings(key=key, value=value))
    db.commit()



# ── Clients ───────────────────────────────────────────────────────────

def get_clients(db: Session, page: int = 1, size: int = 10, search: str = None) -> dict:
    query = db.query(models.Client)
    
    if search:
        term = f"%{search}%"
        query = query.filter(
            or_(
                models.Client.name.ilike(term),
                models.Client.reg_number.ilike(term)
            )
        )
        
    total = query.count()
    pages = (total + size - 1) // size if size > 0 else 1
    
    items = (
        query.order_by(models.Client.name)
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
        "pages": pages
    }


def get_client(db: Session, client_id: int) -> Optional[models.Client]:
    return db.query(models.Client).filter(models.Client.id == client_id).first()


def create_client(db: Session, data: schemas.ClientCreate) -> models.Client:
    client = models.Client(**data.model_dump())
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


def update_client(db: Session, client_id: int, data: schemas.ClientUpdate) -> Optional[models.Client]:
    client = get_client(db, client_id)
    if not client:
        return None
    for k, v in data.model_dump().items():
        setattr(client, k, v)
    db.commit()
    db.refresh(client)
    return client


def delete_client(db: Session, client_id: int) -> bool:
    client = get_client(db, client_id)
    if not client:
        return False
    db.delete(client)
    db.commit()
    return True


# ── Services / Products ──────────────────────────────────────────────

def get_services(db: Session, page: int = 1, size: int = 10, search: str = None) -> dict:
    query = db.query(models.Service)
    
    if search:
        term = f"%{search}%"
        query = query.filter(models.Service.name.ilike(term))
        
    total = query.count()
    pages = (total + size - 1) // size if size > 0 else 1
    
    items = (
        query.order_by(models.Service.name)
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
        "pages": pages
    }


def get_service(db: Session, service_id: int) -> Optional[models.Service]:
    return db.query(models.Service).filter(models.Service.id == service_id).first()


def create_service(db: Session, data: schemas.ServiceCreate) -> models.Service:
    svc = models.Service(**data.model_dump())
    db.add(svc)
    db.commit()
    db.refresh(svc)
    return svc


def update_service(db: Session, service_id: int, data: schemas.ServiceUpdate) -> Optional[models.Service]:
    svc = get_service(db, service_id)
    if not svc:
        return None
    for k, v in data.model_dump().items():
        setattr(svc, k, v)
    db.commit()
    db.refresh(svc)
    return svc


def delete_service(db: Session, service_id: int) -> bool:
    svc = get_service(db, service_id)
    if not svc:
        return False
    db.delete(svc)
    db.commit()
    return True


# ── Invoices ──────────────────────────────────────────────────────────

def get_invoices(db: Session, page: int = 1, size: int = 10, search: str = None,
                 status: str = None, date_from: date_type = None, date_to: date_type = None) -> dict:
    query = db.query(models.Invoice).options(
        joinedload(models.Invoice.client), 
        joinedload(models.Invoice.items)
    )
    
    if search:
        term = f"%{search}%"
        query = query.join(models.Client).filter(
            or_(
                models.Invoice.invoice_number.ilike(term),
                models.Client.name.ilike(term)
            )
        )
    
    if status:
        query = query.filter(models.Invoice.status == status)
    
    if date_from:
        query = query.filter(models.Invoice.date >= date_from)
    
    if date_to:
        query = query.filter(models.Invoice.date <= date_to)
    
    total = query.count()
    pages = (total + size - 1) // size if size > 0 else 1
    
    items = (
        query.order_by(models.Invoice.id.desc())
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
        "pages": pages
    }


def get_invoice(db: Session, invoice_id: int) -> Optional[models.Invoice]:
    return (
        db.query(models.Invoice)
        .options(joinedload(models.Invoice.client), joinedload(models.Invoice.items))
        .filter(models.Invoice.id == invoice_id)
        .first()
    )


def create_invoice(db: Session, data: schemas.InvoiceCreate) -> models.Invoice:
    invoice_number = generate_invoice_number(db)
    invoice = models.Invoice(
        invoice_number=invoice_number,
        client_id=data.client_id,
        date=data.date,
        due_date=data.due_date,
        issuer_name=data.issuer_name,
        notes=data.notes,
    )
    db.add(invoice)
    db.flush()

    for item_data in data.items:
        item = models.InvoiceItem(invoice_id=invoice.id, **item_data.model_dump())
        db.add(item)

    db.commit()
    db.refresh(invoice)
    return get_invoice(db, invoice.id)


def update_invoice(db: Session, invoice_id: int, data: schemas.InvoiceUpdate) -> Optional[models.Invoice]:
    invoice = db.query(models.Invoice).filter(models.Invoice.id == invoice_id).first()
    if not invoice:
        return None

    update_data = data.model_dump(exclude_unset=True)
    items_data = update_data.pop("items", None)

    for k, v in update_data.items():
        if v is not None:
            if k in ['date', 'due_date'] and isinstance(v, str):
                from datetime import datetime
                v = datetime.strptime(v, "%Y-%m-%d").date()
            setattr(invoice, k, v)

    if items_data is not None:
        # Replace all items
        db.query(models.InvoiceItem).filter(models.InvoiceItem.invoice_id == invoice_id).delete()
        for item_data in items_data:
            item = models.InvoiceItem(invoice_id=invoice_id, **item_data)
            db.add(item)

    db.commit()
    return get_invoice(db, invoice_id)


def delete_invoice(db: Session, invoice_id: int) -> bool:
    invoice = db.query(models.Invoice).filter(models.Invoice.id == invoice_id).first()
    if not invoice:
        return False
    db.delete(invoice)
    db.commit()
    return True


# ── User Profile ──────────────────────────────────────────────────────

def update_user_profile(db: Session, current_username: str, data: schemas.UserProfileUpdate):
    from .models import User
    from .auth import get_password_hash
    
    user = db.query(User).filter(User.username == current_username).first()
    if not user:
        return None
        
    user.username = data.username
    if data.password:
        user.password_hash = get_password_hash(data.password)
        
    db.commit()
    db.refresh(user)
    return user

def get_stats(db: Session) -> dict:
    """Calculate dashboard statistics using SQL aggregations."""
    from datetime import date
    import calendar

    today = date.today()

    # Unpaid total — sum line items for non-paid invoices using SQL
    unpaid_q = (
        db.query(
            func.sum(
                models.InvoiceItem.quantity * models.InvoiceItem.unit_price *
                (1 + models.InvoiceItem.vat_rate / 100)
            )
        )
        .join(models.Invoice, models.InvoiceItem.invoice_id == models.Invoice.id)
        .filter(models.Invoice.status != "paid")
        .scalar()
    )
    unpaid_total = round(unpaid_q or 0, 2)

    # Monthly turnover — current month
    monthly_q = (
        db.query(
            func.sum(
                models.InvoiceItem.quantity * models.InvoiceItem.unit_price *
                (1 + models.InvoiceItem.vat_rate / 100)
            )
        )
        .join(models.Invoice, models.InvoiceItem.invoice_id == models.Invoice.id)
        .filter(
            extract("year", models.Invoice.date) == today.year,
            extract("month", models.Invoice.date) == today.month,
        )
        .scalar()
    )
    monthly_turnover = round(monthly_q or 0, 2)

    # Last 6 months breakdown
    monthly_data = []
    for i in range(5, -1, -1):
        month = today.month - i
        year = today.year
        if month <= 0:
            month += 12
            year -= 1
        month_q = (
            db.query(
                func.sum(
                    models.InvoiceItem.quantity * models.InvoiceItem.unit_price *
                    (1 + models.InvoiceItem.vat_rate / 100)
                )
            )
            .join(models.Invoice, models.InvoiceItem.invoice_id == models.Invoice.id)
            .filter(
                extract("year", models.Invoice.date) == year,
                extract("month", models.Invoice.date) == month,
            )
            .scalar()
        )
        month_name = calendar.month_name[month][:3]
        monthly_data.append({
            "label": f"{month_name} {year}",
            "total": round(month_q or 0, 2)
        })

    return {
        "unpaid_total": unpaid_total,
        "monthly_turnover": monthly_turnover,
        "monthly_data": monthly_data
    }
