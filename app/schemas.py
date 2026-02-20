from pydantic import BaseModel
from typing import Optional, List, Generic, TypeVar
from datetime import date

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper."""
    items: List[T]
    total: int
    page: int
    size: int
    pages: int


# ── Settings ──────────────────────────────────────────────────────────

class SettingsUpdate(BaseModel):
    company_name: Optional[str] = ""
    reg_number: Optional[str] = ""
    vat_number: Optional[str] = ""
    vat_enabled: Optional[str] = "true"  # "true" / "false"
    legal_address: Optional[str] = ""
    bank1_name: Optional[str] = ""
    bank1_swift: Optional[str] = ""
    bank1_account: Optional[str] = ""
    bank2_name: Optional[str] = ""
    bank2_swift: Optional[str] = ""
    bank2_account: Optional[str] = ""
    phone: Optional[str] = ""
    email: Optional[str] = ""
    
    # SMTP Settings
    smtp_server: Optional[str] = ""
    smtp_port: Optional[str] = ""
    smtp_username: Optional[str] = ""
    smtp_password: Optional[str] = ""
    smtp_from_email: Optional[str] = ""
    smtp_tls: Optional[str] = "true"
    
    # Google Drive Settings
    gdrive_enabled: Optional[str] = "false"
    gdrive_folder_id: Optional[str] = ""
    gdrive_client_id: Optional[str] = ""
    gdrive_client_secret: Optional[str] = ""
    gdrive_refresh_token: Optional[str] = ""
    
    # EDS Settings
    eds_enabled: Optional[str] = "false"
    eds_api_key: Optional[str] = ""
    
    logo_base64: Optional[str] = ""
    invoice_prefix: Optional[str] = "NC"


class SettingsRead(SettingsUpdate):
    pass


# ── User Profile ──────────────────────────────────────────────────────

class UserProfileUpdate(BaseModel):
    username: str
    password: Optional[str] = None


# ── Client ────────────────────────────────────────────────────────────

class ClientBase(BaseModel):
    name: str
    reg_number: Optional[str] = ""
    vat_number: Optional[str] = ""
    legal_address: Optional[str] = ""
    bank_name: Optional[str] = ""
    bank_swift: Optional[str] = ""
    bank_account: Optional[str] = ""
    postal_code: Optional[str] = ""
    email: Optional[str] = ""


class ClientCreate(ClientBase):
    pass


class ClientUpdate(ClientBase):
    pass


class ClientRead(ClientBase):
    id: int

    class Config:
        from_attributes = True


# ── Service / Product ─────────────────────────────────────────────────

class ServiceBase(BaseModel):
    name: str
    unit: Optional[str] = "gab."
    default_price: Optional[float] = 0
    vat_rate: Optional[float] = 21  # 0 or 21


class ServiceCreate(ServiceBase):
    pass


class ServiceUpdate(ServiceBase):
    pass


class ServiceRead(ServiceBase):
    id: int

    class Config:
        from_attributes = True


# ── Invoice Item ──────────────────────────────────────────────────────

class InvoiceItemBase(BaseModel):
    description: str
    unit: Optional[str] = "gab."
    quantity: float = 1
    unit_price: float = 0
    vat_rate: float = 21  # 0 or 21


class InvoiceItemCreate(InvoiceItemBase):
    pass


class InvoiceItemRead(InvoiceItemBase):
    id: int
    total: float
    vat_amount: float
    total_with_vat: float

    class Config:
        from_attributes = True


# ── Invoice ───────────────────────────────────────────────────────────

class InvoiceBase(BaseModel):
    client_id: int
    date: date
    due_date: date
    issuer_name: Optional[str] = ""
    notes: Optional[str] = ""


class InvoiceCreate(InvoiceBase):
    items: List[InvoiceItemCreate] = []


class InvoiceUpdate(BaseModel):
    client_id: Optional[int] = None
    date: Optional[date] = None
    due_date: Optional[date] = None
    issuer_name: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None
    items: Optional[List[InvoiceItemCreate]] = None


class InvoiceRead(InvoiceBase):
    id: int
    invoice_number: str
    status: str
    subtotal: float
    vat_amount: float
    grand_total: float
    items: List[InvoiceItemRead] = []
    client: Optional[ClientRead] = None

    class Config:
        from_attributes = True
class DashboardStats(BaseModel):
    unpaid_total: float
    monthly_turnover: float
    monthly_data: List[dict]


# Convenience type aliases
PaginatedInvoices = PaginatedResponse[InvoiceRead]
PaginatedClients = PaginatedResponse[ClientRead]
PaginatedServices = PaginatedResponse[ServiceRead]
