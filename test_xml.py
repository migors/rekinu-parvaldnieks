from app.database import SessionLocal
from app.models import Invoice, Client, Settings
from app.e_invoice import generate_peppol_xml

db = SessionLocal()
try:
    inv = db.query(Invoice).first()
    if inv:
        client = db.query(Client).filter(Client.id == inv.client_id).first()
        settings_raw = db.query(Settings).all()
        settings = {s.key: s.value for s in settings_raw}
        
        xml_bytes = generate_peppol_xml(inv, client, settings)
        print("Generated XML (first 500 bytes):")
        print(xml_bytes[:500].decode('utf-8'))
        
        with open("test_einvoice.xml", "wb") as f:
            f.write(xml_bytes)
        print(f"Saved to test_einvoice.xml, size: {len(xml_bytes)} bytes")
    else:
        print("No invoices found to test.")
finally:
    db.close()
