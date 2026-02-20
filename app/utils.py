"""Utility helpers – number-to-words (Latvian) and invoice numbering."""

from sqlalchemy.orm import Session
from .models import Invoice
from io import BytesIO
import os
import sys
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
import requests
from typing import Optional


# ── Latvian number-to-words ───────────────────────────────────────────

_ONES = [
    "", "viens", "divi", "trīs", "četri", "pieci",
    "seši", "septiņi", "astoņi", "deviņi",
]
_TEENS = [
    "desmit", "vienpadsmit", "divpadsmit", "trīspadsmit", "četrpadsmit",
    "piecpadsmit", "sešpadsmit", "septiņpadsmit", "astoņpadsmit", "deviņpadsmit",
]
_TENS = [
    "", "desmit", "divdesmit", "trīsdesmit", "četrdesmit", "piecdesmit",
    "sešdesmit", "septiņdesmit", "astoņdesmit", "deviņdesmit",
]
_HUNDREDS = [
    "", "simts", "divsimt", "trīssimt", "četrsimt", "piecsimt",
    "sešsimt", "septiņsimt", "astoņsimt", "deviņsimt",
]


def _int_to_words(n: int) -> str:
    """Convert an integer 0-999999 to Latvian words."""
    if n == 0:
        return "nulle"

    parts: list[str] = []

    if n >= 1000:
        thousands = n // 1000
        n %= 1000
        if thousands == 1:
            parts.append("viens tūkstotis")
        else:
            parts.append(f"{_int_to_words(thousands)} tūkstoši")

    if n >= 100:
        parts.append(_HUNDREDS[n // 100])
        n %= 100

    if 10 <= n <= 19:
        parts.append(_TEENS[n - 10])
        n = 0
    else:
        if n >= 20:
            parts.append(_TENS[n // 10])
            n %= 10
        if n > 0:
            parts.append(_ONES[n])

    return " ".join(parts)


def number_to_words_lv(amount: float) -> str:
    """Convert a EUR amount to Latvian words.

    Example: 146.50 → 'Simts četrdesmit seši euro un 50 centi'
    """
    euros = int(amount)
    cents = round((amount - euros) * 100)

    euro_words = _int_to_words(euros)
    # Capitalize first letter
    euro_words = euro_words[0].upper() + euro_words[1:]

    euro_unit = "euro"
    cent_str = f"{cents:02d}"
    cent_unit = "centi" if cents != 1 else "cents"

    return f"{euro_words} {euro_unit} un {cent_str} {cent_unit}"


# ── Invoice number generation ────────────────────────────────────────

from . import models, schemas, crud

# ... (omitted imports)

def generate_invoice_number(db: Session) -> str:
    """Generate next invoice number in PREFIX-XXXXXX format."""
    settings = crud.get_settings(db)
    prefix = settings.get("invoice_prefix", "NC")
    if not prefix:
        prefix = "NC"
        
    # Find last invoice with this prefix
    last = (
        db.query(Invoice)
        .filter(Invoice.invoice_number.like(f"{prefix}-%"))
        .order_by(Invoice.id.desc())
        .first()
    )
    
    if last:
        try:
            parts = last.invoice_number.split("-")
            if len(parts) >= 2:
                num = int(parts[-1]) + 1
            else:
                num = 1
        except (ValueError, IndexError):
            num = 1
    else:
        num = 1
        
    return f"{prefix}-{num:06d}"


# ── Font Registration (Global) ────────────────────────────────────────

def _find_font(names: list[str]) -> str | None:
    """Search for a font file in common Windows locations."""
    search_dirs = [
        os.path.join(os.environ.get('WINDIR', r'C:\Windows'), 'Fonts'),
        os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Microsoft', 'Windows', 'Fonts'),
    ]
    for d in search_dirs:
        for name in names:
            path = os.path.join(d, name)
            if os.path.isfile(path):
                return path
    return None


try:
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    arial_path = _find_font(['arial.ttf', 'Arial.ttf'])
    arial_bold_path = _find_font(['arialbd.ttf', 'Arialbd.ttf', 'ARIALBD.TTF'])

    if arial_path:
        pdfmetrics.registerFont(TTFont('CustomArial', arial_path))
    if arial_bold_path:
        pdfmetrics.registerFont(TTFont('CustomArialBold', arial_bold_path))

    print(f"Fonts registered: Arial={'OK' if arial_path else 'MISSING'}, ArialBold={'OK' if arial_bold_path else 'MISSING'}")
except Exception as e:
    print(f"Warning: Could not register fonts: {e}")



def generate_invoice_pdf(invoice: Invoice, settings: dict) -> bytes:
    """Generate PDF bytes for a given invoice using ReportLab (native)."""
    # Import local ReportLab components
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.units import cm

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.5*cm,
        leftMargin=1.5*cm,
        topMargin=1.0*cm,
        bottomMargin=1.5*cm
    )

    elements = []
    
    # Styles
    styles = getSampleStyleSheet()
    # Define custom styles using our registered font
    style_normal = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontName='CustomArial',
        fontSize=10,
        leading=13
    )
    style_bold = ParagraphStyle(
        'CustomBold',
        parent=styles['Normal'],
        fontName='CustomArialBold',
        fontSize=10,
        leading=13
    )
    style_title = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontName='CustomArialBold',
        fontSize=18,
        textColor=colors.HexColor('#1d4ed8'), # blue-700
        alignment=2, # Right
        spaceBefore=0,
        spaceAfter=0
    )
    style_small = ParagraphStyle(
        'CustomSmall',
        parent=styles['Normal'],
        fontName='CustomArial',
        fontSize=9,
        textColor=colors.HexColor('#6b7280'), # gray-500
        leading=11
    )
    style_header = ParagraphStyle(
        'CustomHeader',
        parent=style_bold,
        fontSize=10,
        textColor=colors.white
    )

    # 1. Header (Logo / Company Info | Invoice Info)
    logo_img = None
    if settings.get('logo_base64'):
        try:
            import base64
            from reportlab.platypus import Image
            logo_data = settings['logo_base64']
            if ',' in logo_data:
                logo_data = logo_data.split(',')[1]
            img_data = base64.b64decode(logo_data)
            img_io = BytesIO(img_data)
            logo_img = Image(img_io, width=2.5*cm, height=2.5*cm, kind='proportional')
        except Exception as e:
            print(f"Error processing logo for PDF: {e}")

    # Right: Invoice Details
    inv_info = [
        [Paragraph("RĒĶINS", ParagraphStyle('InvTitle', parent=style_title, alignment=2))], # Right align
        [Paragraph(invoice.invoice_number, ParagraphStyle('InvNum', parent=style_bold, fontSize=11, alignment=2))],
        [Paragraph(f"Datums: <b>{invoice.date.strftime('%d.%m.%Y')}</b>", ParagraphStyle('InvDate', parent=style_small, alignment=2))],
        [Paragraph(f"Apmaksas termiņš: <b>{invoice.due_date.strftime('%d.%m.%Y')}</b>", ParagraphStyle('InvDue', parent=style_small, alignment=2))],
    ]

    # Left: Settings
    if logo_img:
        company_info = [
            [logo_img, Paragraph(settings.get('company_name', ''), ParagraphStyle('CoName', parent=style_bold, fontSize=14, spaceAfter=4))],
        ]
        # Adjust column widths if logo exists
        header_table = Table([
            [Table(company_info, colWidths=[3*cm, 8*cm], style=[('VALIGN',(0,0),(-1,-1),'MIDDLE'),('LEFTPADDING',(0,0),(-1,-1),0)]), 
             Table(inv_info, colWidths=[6*cm], style=[('RIGHTPADDING',(0,0),(-1,-1),0)])]
        ], colWidths=[11*cm, 7*cm])
    else:
        company_info = [
            [Paragraph(settings.get('company_name', ''), ParagraphStyle('CoName', parent=style_bold, fontSize=14, spaceAfter=4))],
        ]
        header_table = Table([
            [Table(company_info, colWidths=[11*cm], style=[('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),0)]), 
             Table(inv_info, colWidths=[6*cm], style=[('RIGHTPADDING',(0,0),(-1,-1),0)])]
        ], colWidths=[11*cm, 7*cm])
    
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('LINEBELOW', (0,0), (-1,-1), 1, colors.HexColor('#1f2937')), # gray-800
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 0.3*cm))

    # 2. Parties (Supplier | Client)
    
    def create_party_box(title, name, reg_no, vat_no, address, bank_name, bank_acc, phone, email):
        content = [
            [Paragraph(title, ParagraphStyle('BoxTitle', parent=style_bold, fontSize=8, textColor=colors.HexColor('#6b7280'), textTransform='uppercase'))],
            [Paragraph(name if name else "", style_bold)],
            [Paragraph(f"Reģ. Nr.: {reg_no}" if reg_no else "", style_normal)],
        ]
        if vat_no: content.append([Paragraph(f"PVN Nr.: {vat_no}", style_normal)])
        content.append([Paragraph(f"Adrese: {address}" if address else "", style_normal)])
        if bank_name: content.append([Paragraph(f"Banka: {bank_name}", style_normal)])
        if bank_acc: content.append([Paragraph(f"Konts: {bank_acc}", style_normal)])
        if phone: content.append([Paragraph(f"Tālr.: {phone}", style_normal)])
        if email: content.append([Paragraph(f"E-pasts: {email}", style_normal)])
        
        t = Table(content, colWidths=[8.5*cm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f9fafb')), # gray-50
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#e5e7eb')), # gray-200
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
            ('RIGHTPADDING', (0,0), (-1,-1), 8),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ]))
        return t

    supplier_box = create_party_box(
        "PAKALPOJUMU SNIEDZĒJS",
        settings.get('company_name', ''),
        settings.get('reg_number', ''),
        settings.get('vat_number', ''),
        settings.get('legal_address', ''),
        None, None,
        settings.get('phone', ''),
        settings.get('email', '')
    )

    client_box = create_party_box(
        "PAKALPOJUMU SAŅĒMĒJS",
        invoice.client.name,
        invoice.client.reg_number,
        invoice.client.vat_number,
        f"{invoice.client.legal_address}{', ' + invoice.client.postal_code if getattr(invoice.client, 'postal_code', None) else ''}",
        invoice.client.bank_name,
        invoice.client.bank_account,
        None, None
    )

    parties_table = Table([[supplier_box, "", client_box]], colWidths=[8.75*cm, 0.5*cm, 8.75*cm])
    parties_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    elements.append(parties_table)
    elements.append(Spacer(1, 0.3*cm))

    # 3. Banks (if any)
    if settings.get('bank1_name') or settings.get('bank2_name'):
        b1, b2 = None, None
        
        if settings.get('bank1_name'):
            content = [
                [Paragraph("NORĒĶINU KONTS NR. 1", ParagraphStyle('BankTitle', parent=style_bold, fontSize=8, textColor=colors.HexColor('#1d4ed8')))],
                [Paragraph(settings.get('bank1_name', ''), style_bold)],
                [Paragraph(f"SWIFT: {settings.get('bank1_swift', '')}", style_small)],
                [Paragraph(f"Konts: {settings.get('bank1_account', '')}", style_small)],
            ]
            b1 = Table(content, colWidths=[8.5*cm])
            b1.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#eff6ff')), # blue-50
                ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#bfdbfe')), # blue-200
                ('LEFTPADDING', (0,0), (-1,-1), 6),
                ('TOPPADDING', (0,0), (-1,-1), 6),
            ]))
            
        if settings.get('bank2_name'):
            content = [
                [Paragraph("NORĒĶINU KONTS NR. 2", ParagraphStyle('BankTitle', parent=style_bold, fontSize=8, textColor=colors.HexColor('#1d4ed8')))],
                [Paragraph(settings.get('bank2_name', ''), style_bold)],
                [Paragraph(f"SWIFT: {settings.get('bank2_swift', '')}", style_small)],
                [Paragraph(f"Konts: {settings.get('bank2_account', '')}", style_small)],
            ]
            b2 = Table(content, colWidths=[8.5*cm])
            b2.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#eff6ff')),
                ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#bfdbfe')),
                ('LEFTPADDING', (0,0), (-1,-1), 6),
                ('TOPPADDING', (0,0), (-1,-1), 6),
            ]))

        banks_table = Table([[b1 if b1 else "", "", b2 if b2 else ""]], colWidths=[8.75*cm, 0.5*cm, 8.75*cm])
        elements.append(banks_table)
        elements.append(Spacer(1, 0.3*cm))


    # 4. Items Table
    data = [[
        Paragraph("<b>Nr</b>", style_header),
        Paragraph("<b>Nosaukums</b>", style_header),
        Paragraph("<b>Mērv.</b>", style_header),
        Paragraph("<b>Skaits</b>", style_header),
        Paragraph("<b>Cena</b>", style_header),
        Paragraph("<b>PVN</b>", style_header),
        Paragraph("<b>Summa</b>", style_header)
    ]]
    
    for i, item in enumerate(invoice.items, 1):
        data.append([
            str(i),
            Paragraph(item.description, style_normal),
            item.unit,
            f"{item.quantity:.2f}",
            f"{item.unit_price:.2f}",
            f"{item.vat_rate}%",
            f"{item.total:.2f}"
        ])

    items_table = Table(data, colWidths=[1*cm, 6.5*cm, 1.5*cm, 2*cm, 2*cm, 2*cm, 3*cm])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1f2937')), # Header bg gray-800
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'), # Default left
        ('ALIGN', (0,0), (0,-1), 'CENTER'), # Nr center
        ('ALIGN', (2,0), (2,-1), 'CENTER'), # Unit center
        ('ALIGN', (5,0), (5,-1), 'CENTER'), # VAT center
        ('ALIGN', (3,0), (4,-1), 'RIGHT'), # Qty, Price right
        ('ALIGN', (6,0), (6,-1), 'RIGHT'), # Total right
        ('FONTNAME', (0,0), (-1,-1), 'CustomArial'),
        ('FONTNAME', (0,0), (-1,0), 'CustomArialBold'), # Header bold
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e5e7eb')), # Grid lines
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 0.3*cm))

    # 5. Totals
    totals_data = [
        ["Kopā (EUR):", f"{invoice.subtotal:.2f}"],
    ]
    
    # Calculate VAT breakdown
    vat_groups = {}
    for item in invoice.items:
        rate = item.vat_rate
        vat_groups[rate] = vat_groups.get(rate, 0) + item.vat_amount
        
    for rate in sorted(vat_groups.keys()):
        totals_data.append([f"PVN {int(rate)}% (EUR):", f"{vat_groups[rate]:.2f}"])
        
    totals_data.append(["Summa ar PVN (EUR):", f"{invoice.grand_total:.2f}"])
    totals_data.append([
        Paragraph("<b>Kopā apmaksai (EUR):</b>", style_normal), 
        Paragraph(f"<b>{invoice.grand_total:.2f}</b>", ParagraphStyle('GrandTot', parent=style_bold, textColor=colors.HexColor('#1d4ed8'), fontSize=11, alignment=2))
    ])
    
    totals_table = Table(totals_data, colWidths=[13*cm, 5*cm])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'RIGHT'),
        ('FONTNAME', (0,0), (-1,-1), 'CustomArial'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LINEABOVE', (0, -1), (-1, -1), 1, colors.HexColor('#1f2937')), # Line above Grand Total
    ]))
    elements.append(totals_table)
    elements.append(Spacer(1, 0.4*cm))

    # 6. Sum Words
    total_in_words = number_to_words_lv(invoice.grand_total)
    sum_words_box = Table([[
        Paragraph(f"<b>SUMMA VĀRDIEM:</b> {total_in_words}.", style_normal)
    ]], colWidths=[18*cm])
    sum_words_box.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f3f4f6')), # gray-100
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#d1d5db')), # gray-300
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ]))
    elements.append(sum_words_box)
    elements.append(Spacer(1, 0.3*cm))

    # 7. Notes & Issuer
    if invoice.notes:
        elements.append(Paragraph("<b>Piezīmes:</b>", style_bold))
        elements.append(Paragraph(invoice.notes, style_normal))
        elements.append(Spacer(1, 0.3*cm))
        
    if invoice.issuer_name:
        elements.append(Paragraph("<b>Rēķinu izrakstīja:</b>", style_bold))
        elements.append(Paragraph(invoice.issuer_name, style_normal))

    elements.append(Spacer(1, 0.5*cm))
    elements.append(Paragraph("Rēķins sagatavots elektroniski un ir derīgs bez paraksta", ParagraphStyle('Disclaimer', parent=style_small, alignment=1, fontName='CustomArial', fontStyle='Italic')))

    # Build
    doc.build(elements)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return pdf_bytes


async def send_invoice_email(invoice: Invoice, settings: dict, pdf_bytes: bytes, to_email: str):
    """Send invoice via email using SMTP settings."""
    username = settings.get("smtp_username", "")
    password = settings.get("smtp_password", "")
    
    conf = ConnectionConfig(
        MAIL_USERNAME = username,
        MAIL_PASSWORD = password,
        MAIL_FROM = settings.get("smtp_from_email") or (username if "@" in username else None) or "noreply@example.com",
        MAIL_PORT = int(settings.get("smtp_port") or 587),
        MAIL_SERVER = settings.get("smtp_server") or "smtp.gmail.com",
        MAIL_STARTTLS = bool(settings.get("smtp_tls", "true") == "true"),
        MAIL_SSL_TLS = False,
        USE_CREDENTIALS = bool(username and password),
        VALIDATE_CERTS = True
    )

    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(pdf_bytes)
        tmp_path = tmp.name

    try:
        message = MessageSchema(
            subject=f"Rēķins {invoice.invoice_number}",
            recipients=[to_email],
            body=f"Labdien,\n\nNosūtām rēķinu Nr. {invoice.invoice_number} apmaksai.\n\nAr cieņu,\n{settings.get('company_name', '')}",
            subtype=MessageType.plain,
            attachments=[tmp_path]
        )

        fm = FastMail(conf)
        await fm.send_message(message)
    finally:
        # Cleanup temp file
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass


async def send_test_email(settings: dict, to_email: str):
    """Send a test email to verify SMTP settings."""
    username = settings.get("smtp_username", "")
    password = settings.get("smtp_password", "")
    try:
        conf = ConnectionConfig(
            MAIL_USERNAME=username,
            MAIL_PASSWORD=password,
            MAIL_FROM = settings.get("smtp_from_email") or (username if "@" in username else None) or "noreply@example.com",
            MAIL_PORT = int(settings.get("smtp_port") or 587),
            MAIL_SERVER = settings.get("smtp_server") or "smtp.gmail.com",
            MAIL_STARTTLS=bool(settings.get("smtp_tls", "true") == "true"),
            MAIL_SSL_TLS=False,
            USE_CREDENTIALS = bool(username and password),
            VALIDATE_CERTS=True
        )
    except Exception as e:
        pass  # Log silently
        raise e
    message = MessageSchema(
        subject="Invoice Manager — SMTP testa e-pasts",
        recipients=[to_email],
        body="Šis ir testa e-pasts no Invoice Manager.\n\nJa saņēmāt šo ziņu, SMTP iestatījumi ir pareizi konfigurēti.",
        subtype=MessageType.plain,
    )
    fm = FastMail(conf)
    await fm.send_message(message)


def fetch_company_data(reg_number: str) -> Optional[dict]:
    """Fetch company data from Latvian Open Data API (Enterprise Register)."""
    # Sanitize input: remove spaces and non-digits
    reg_clean = "".join(filter(str.isdigit, reg_number))
    
    if not reg_clean:
        return None

    try:
        reg_int = int(reg_clean)
    except ValueError:
        return None

    endpoint = "https://data.gov.lv/dati/lv/api/3/action/datastore_search"
    resource_id = "25e80bf3-f107-4ab4-89ef-251b5b9374e9"
    
    # Filter by integer regcode
    params = {
        "resource_id": resource_id,
        "filters": f'{{"regcode": {reg_int}}}'
    }
    
    try:
        response = requests.get(endpoint, params=params, timeout=5)
#         print(f"DEBUG URL: {response.url}")
#         print(f"DEBUG RESP: {response.text}") 
        response.raise_for_status()
        data = response.json()
        
        if data.get("success") and data.get("result", {}).get("records"):
            # Return the first match
            record = data["result"]["records"][0]
            
            # Construct VAT number (assumption: LV + regcode)
            vat_number = f"LV{reg_clean}"
            
            return {
                "name": record.get("name"),
                "reg_number": str(record.get("regcode")),
                "vat_number": vat_number,
                "legal_address": record.get("address"),
                "registration_date": record.get("registered")
            }
            
    except Exception as e:
        print(f"Error fetching company data: {e}")
        return None
    
    return None


def search_companies(q: str):
    """Search companies by name in Latvian Open Data API."""
    if not q or len(q) < 2:
        return []

    endpoint = "https://data.gov.lv/dati/lv/api/3/action/datastore_search"
    # Resource ID for "Uzņēmumu reģistra dati"
    resource_id = "25e80bf3-f107-4ab4-89ef-251b5b9374e9"
    
    params = {
        "resource_id": resource_id,
        "q": q,
        "limit": 10
    }
    
    try:
        response = requests.get(endpoint, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        results = []
        if data.get("success") and data.get("result", {}).get("records"):
            for record in data["result"]["records"]:
                
                reg_clean = str(record.get("regcode", ""))
                
                # Try to construct a VAT number if it looks like a valid reg number
                vat_number = f"LV{reg_clean}" if reg_clean.isdigit() else ""
                
                # Postal code
                postal_index = record.get("index")
                postal_code = f"LV-{postal_index}" if postal_index else ""

                results.append({
                    "name": record.get("name"),
                    "reg_number": reg_clean,
                    "vat_number": vat_number,
                    "legal_address": record.get("address"),
                    "postal_code": postal_code,
                    "registration_date": record.get("registered")
                })
        return results
            
    except Exception as e:
        print(f"Error searching companies: {e}")
        return []
