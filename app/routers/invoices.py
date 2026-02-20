"""Invoice API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, Response, StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from pydantic import BaseModel
import csv
import io
import os

from ..database import get_db
from ..auth import get_current_user
from .. import crud, schemas
from ..utils import number_to_words_lv

router = APIRouter(prefix="/api/invoices", tags=["invoices"])

_template_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "templates")
templates = Jinja2Templates(directory=_template_dir)


@router.get("", response_model=schemas.PaginatedInvoices)
def list_invoices(
    page: int = 1, 
    size: int = 10, 
    search: Optional[str] = None,
    status: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: Session = Depends(get_db), 
    user: str = Depends(get_current_user)
):
    """List invoices with pagination, search, status and date filters."""
    try:
        data = crud.get_invoices(db, page=page, size=size, search=search,
                                  status=status, date_from=date_from, date_to=date_to)
        
        # Manual serialization to ensure no Pydantic/ORM conflicts
        # This is the safest way to ensure data reaches the frontend
        serialized_items = []
        for inv in data["items"]:
            serialized_items.append({
                "id": inv.id,
                "invoice_number": inv.invoice_number,
                "client_id": inv.client_id,
                "client": {
                    "id": inv.client.id,
                    "name": inv.client.name,
                    "reg_number": inv.client.reg_number or "",
                    "vat_number": inv.client.vat_number or "",
                    "legal_address": inv.client.legal_address or "",
                    "bank_name": inv.client.bank_name or "",
                    "bank_swift": inv.client.bank_swift or "",
                    "bank_account": inv.client.bank_account or "",
                    "email": inv.client.email or ""
                } if inv.client else None,
                "date": inv.date,
                "due_date": inv.due_date,
                "issuer_name": inv.issuer_name or "",
                "notes": inv.notes or "",
                "status": inv.status or "sent",
                "subtotal": inv.subtotal,
                "vat_amount": inv.vat_amount,
                "grand_total": inv.grand_total,
                "items": [
                    {
                        "id": item.id,
                        "description": item.description,
                        "unit": item.unit,
                        "quantity": item.quantity,
                        "unit_price": item.unit_price,
                        "vat_rate": item.vat_rate,
                        "total": item.total,
                        "vat_amount": item.vat_amount,
                        "total_with_vat": item.total_with_vat
                    } for item in inv.items
                ]
            })
            
        return {
            "items": serialized_items,
            "total": data["total"],
            "page": data["page"],
            "size": data["size"],
            "pages": data["pages"]
        }

    except Exception as e:
        import traceback
        import os
        # Write to a file we can definitely read
        with open("api_error.log", "w", encoding="utf-8") as f:
            f.write(f"Error: {e}\n{traceback.format_exc()}")
        
        logging.getLogger(__name__).error(f"List invoices error: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Server Error: {str(e)}")


@router.get("/{invoice_id}", response_model=schemas.InvoiceRead)
def read_invoice(invoice_id: int, db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    invoice = crud.get_invoice(db, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice


@router.post("", response_model=schemas.InvoiceRead, status_code=201)
def create_invoice(data: schemas.InvoiceCreate, db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    invoice = crud.create_invoice(db, data)
    
    # Auto-upload PDF to Google Drive (background)
    settings = crud.get_settings(db)
    if settings.get("gdrive_enabled") == "true":
        try:
            from ..utils import generate_invoice_pdf
            from ..gdrive import upload_to_gdrive
            import threading
            
            pdf_bytes = generate_invoice_pdf(invoice, settings)
            filename = f"Invoice-{invoice.invoice_number}.pdf"
            threading.Thread(
                target=upload_to_gdrive,
                args=(pdf_bytes, filename, settings),
                daemon=True,
            ).start()
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Google Drive auto-upload failed: {e}")
    
    return invoice


@router.put("/{invoice_id}", response_model=schemas.InvoiceRead)
def update_invoice(invoice_id: int, data: schemas.InvoiceUpdate, db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    invoice = crud.update_invoice(db, invoice_id, data)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice


@router.delete("/{invoice_id}")
def delete_invoice(invoice_id: int, db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    if not crud.delete_invoice(db, invoice_id):
        raise HTTPException(status_code=404, detail="Invoice not found")
    return {"ok": True}

class BulkDeleteRequest(BaseModel):
    invoice_ids: List[int]

@router.post("/bulk-delete")
def delete_invoices_bulk(req: BulkDeleteRequest, db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    deleted_count = 0
    for iid in req.invoice_ids:
        if crud.delete_invoice(db, iid):
            deleted_count += 1
    return {"deleted": deleted_count}


@router.get("/{invoice_id}/html", response_class=HTMLResponse)
def render_invoice(invoice_id: int, request: Request, db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    """Render the invoice as a styled HTML page (for printing / PDF)."""
    invoice = crud.get_invoice(db, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    settings = crud.get_settings(db)
    total_words = number_to_words_lv(invoice.grand_total)
    vat_enabled = settings.get("vat_enabled", "true") == "true"

    return templates.TemplateResponse("invoice.html", {
        "request": request,
        "invoice": invoice,
        "settings": settings,
        "total_words": total_words,
        "vat_enabled": vat_enabled,
    })



@router.get("/export/csv")
def export_invoices_csv(db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    """Export all invoices as a CSV file."""
    from sqlalchemy.orm import joinedload
    from .. import models
    invoices = (
        db.query(models.Invoice)
        .options(joinedload(models.Invoice.client))
        .order_by(models.Invoice.id.desc())
        .all()
    )
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Nr.", "Klients", "Datums", "Apmaksas termiņš", "Summa bez PVN", "PVN", "Kopā", "Statuss"])
    for inv in invoices:
        writer.writerow([
            inv.invoice_number,
            inv.client.name if inv.client else "",
            inv.date.strftime("%d.%m.%Y"),
            inv.due_date.strftime("%d.%m.%Y"),
            f"{inv.subtotal:.2f}",
            f"{inv.vat_amount:.2f}",
            f"{inv.grand_total:.2f}",
            inv.status
        ])
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=invoices.csv"}
    )




class ExportXMLRequest(BaseModel):
    invoice_ids: List[int]

@router.post("/export/csv/bulk")
def export_invoices_csv_bulk(req: ExportXMLRequest, db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    """Export selected invoices as a CSV file."""
    from sqlalchemy.orm import joinedload
    from .. import models
    invoices = (
        db.query(models.Invoice)
        .options(joinedload(models.Invoice.client))
        .filter(models.Invoice.id.in_(req.invoice_ids))
        .order_by(models.Invoice.id.desc())
        .all()
    )
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Nr.", "Klients", "Datums", "Apmaksas termiņš", "Summa bez PVN", "PVN", "Kopā", "Statuss"])
    for inv in invoices:
        writer.writerow([
            inv.invoice_number,
            inv.client.name if inv.client else "",
            inv.date.strftime("%d.%m.%Y"),
            inv.due_date.strftime("%d.%m.%Y"),
            f"{inv.subtotal:.2f}",
            f"{inv.vat_amount:.2f}",
            f"{inv.grand_total:.2f}",
            inv.status
        ])
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=invoices_selected.csv"}
    )

@router.post("/send-eds")
def send_invoices_eds(
    req: ExportXMLRequest,
    db: Session = Depends(get_db),
    user: str = Depends(get_current_user)
):
    """Sutit iezimetos rekinus pa taisno uz VID EDS."""
    settings = crud.get_settings(db)
    from ..e_invoice import generate_peppol_xml
    from ..eds_api import send_invoice_to_eds
    
    eds_api_key = settings.get("eds_api_key", "").strip()
    if not eds_api_key:
        raise HTTPException(status_code=400, detail="EDS API atslēga nav konfigurēta iestatījumos.")
        
    success_count = 0
    errors = []
    
    for inv_id in req.invoice_ids:
        invoice = crud.get_invoice(db, inv_id)
        if invoice:
            client = invoice.client
            xml_bytes = generate_peppol_xml(invoice, client, settings)
            
            res = send_invoice_to_eds(xml_bytes, eds_api_key)
            if res.get("success"):
                success_count += 1
            else:
                errors.append({"invoice_id": invoice.invoice_number, "error": res.get("error")})
                
    return {
        "success_count": success_count,
        "error_count": len(errors),
        "errors": errors
    }

@router.post("/export/xml")
def export_xml_invoices(
    req: ExportXMLRequest,
    db: Session = Depends(get_db),
    user: str = Depends(get_current_user)
):
    """Export selected invoices as E-Invoice (PEPPOL XML)."""
    settings = crud.get_settings(db)
    from ..e_invoice import generate_peppol_xml
    import zipfile
    
    xml_files = []
    for inv_id in req.invoice_ids:
        invoice = crud.get_invoice(db, inv_id)
        if invoice:
            client = invoice.client
            xml_bytes = generate_peppol_xml(invoice, client, settings)
            prefix = settings.get('invoice_prefix', 'NC')
            filename = f"E-Invoice_{prefix}-{invoice.invoice_number}.xml"
            xml_files.append((filename, xml_bytes))
            
    if not xml_files:
        raise HTTPException(status_code=404, detail="No valid invoices found for export")
        
    if len(xml_files) == 1:
        return Response(
            content=xml_files[0][1],
            media_type="application/xml",
            headers={"Content-Disposition": f"attachment; filename={xml_files[0][0]}"}
        )
    
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        for filename, data in xml_files:
            zip_file.writestr(filename, data)
            
    return Response(
        content=zip_buffer.getvalue(),
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=e_invoices.zip"}
    )


@router.get("/{invoice_id}/pdf")
def download_pdf(invoice_id: int, db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    """Generate and download PDF invoice."""
    invoice = crud.get_invoice(db, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    settings = crud.get_settings(db)
    from ..utils import generate_invoice_pdf
    try:
        pdf_bytes = generate_invoice_pdf(invoice, settings)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")
    
    return Response(content=pdf_bytes, media_type="application/pdf", headers={
        "Content-Disposition": f"attachment; filename=Invoice-{invoice.invoice_number}.pdf"
    })


from pydantic import BaseModel, EmailStr

class EmailRequest(BaseModel):
    to_email: EmailStr

@router.post("/{invoice_id}/send")
async def send_invoice_with_email(
    invoice_id: int, 
    email_data: EmailRequest,
    db: Session = Depends(get_db), 
    user: str = Depends(get_current_user)
):
    """Generate PDF and send via email."""
    invoice = crud.get_invoice(db, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    settings = crud.get_settings(db)
    from ..utils import generate_invoice_pdf, send_invoice_email
    
    try:
        pdf_bytes = generate_invoice_pdf(invoice, settings)
        await send_invoice_email(invoice, settings, pdf_bytes, email_data.to_email)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")
        
    return {"message": "Email sent successfully"}
@router.post("/sync-gdrive")
def sync_all_to_gdrive(db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    """Synchronize all existing invoices to Google Drive."""
    settings = crud.get_settings(db)
    if settings.get("gdrive_enabled") != "true":
        raise HTTPException(status_code=400, detail="Google Drive is not enabled in settings")
    
    res = crud.get_invoices(db, size=1000) # Get a large batch for sync
    invoices = res["items"]
    from ..utils import generate_invoice_pdf
    from ..gdrive import upload_to_gdrive
    
    uploaded_count = 0
    for invoice in invoices:
        try:
            pdf_bytes = generate_invoice_pdf(invoice, settings)
            filename = f"Invoice-{invoice.invoice_number}.pdf"
            # In a real app we might want to check if it already exists, 
            # but for now we trust GDrive or just overwrite.
            # We don't use a background thread for EACH file to avoid rate limits, 
            # but we could wrap the whole loop in one.
            if upload_to_gdrive(pdf_bytes, filename, settings):
                uploaded_count += 1
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Sync failed for invoice {invoice.invoice_number}: {e}")
            continue
            
    return {"uploaded": uploaded_count}
