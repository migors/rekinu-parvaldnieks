import xml.etree.ElementTree as ET
from datetime import datetime
import io

def generate_peppol_xml(invoice, client, settings) -> bytes:
    """
    Generate a UBL 2.1 / PEPPOL BIS Billing 3.0 compliant XML e-invoice (EN 16931).
    invoice: app.models.Invoice or schemas.InvoiceRead
    client: app.models.Client or schemas.ClientRead
    settings: dictionary of settings (crud.get_settings)
    """
    
    # Namespaces
    ns = {
        'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
        'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2',
        '': 'urn:oasis:names:specification:ubl:schema:xsd:Invoice-2'
    }

    # Register namespaces for correct prefixing during serialization
    ET.register_namespace('', ns[''])
    ET.register_namespace('cac', ns['cac'])
    ET.register_namespace('cbc', ns['cbc'])

    root = ET.Element(f"{{{ns['']}}}Invoice")

    # Customization and Profile ID for PEPPOL BIS Billing 3.0
    ET.SubElement(root, f"{{{ns['cbc']}}}CustomizationID").text = "urn:cen.eu:en16931:2017#compliant#urn:fdc:peppol.eu:2017:poacc:billing:3.0"
    ET.SubElement(root, f"{{{ns['cbc']}}}ProfileID").text = "urn:fdc:peppol.eu:2017:poacc:billing:01:1.0"

    # Invoice basic info
    ET.SubElement(root, f"{{{ns['cbc']}}}ID").text = f"{settings.get('invoice_prefix', 'INV')}-{invoice.id:06d}"
    ET.SubElement(root, f"{{{ns['cbc']}}}IssueDate").text = str(invoice.date)
    ET.SubElement(root, f"{{{ns['cbc']}}}DueDate").text = str(invoice.due_date)
    ET.SubElement(root, f"{{{ns['cbc']}}}InvoiceTypeCode").text = "380" # 380 = Commercial Invoice
    ET.SubElement(root, f"{{{ns['cbc']}}}DocumentCurrencyCode").text = "EUR"

    # ── AccountingSupplierParty (Seller) ──
    supplier = ET.SubElement(root, f"{{{ns['cac']}}}AccountingSupplierParty")
    party_supplier = ET.SubElement(supplier, f"{{{ns['cac']}}}Party")
    
    # Endpoint ID (usually VAT or Reg no)
    endpoint_scheme = "9936" if settings.get('vat_number') else "0184" # 9936: Latvian VAT, 0184: Latvian Reg
    endpoint_id = settings.get('vat_number') or settings.get('reg_number') or "UNKNOWN"
    endpoint_el = ET.SubElement(party_supplier, f"{{{ns['cbc']}}}EndpointID", schemeID=endpoint_scheme)
    endpoint_el.text = endpoint_id

    # Supplier Name
    party_name_supp = ET.SubElement(party_supplier, f"{{{ns['cac']}}}PartyName")
    ET.SubElement(party_name_supp, f"{{{ns['cbc']}}}Name").text = settings.get('company_name', 'Unknown Company')

    # Supplier Postal Address
    postal_supp = ET.SubElement(party_supplier, f"{{{ns['cac']}}}PostalAddress")
    ET.SubElement(postal_supp, f"{{{ns['cbc']}}}StreetName").text = settings.get('legal_address', '')
    ET.SubElement(postal_supp, f"{{{ns['cbc']}}}CityName").text = "Riga" # Fallback if not parsed
    # We could parse zip/city from address if needed, keeping simple for now
    country_supp = ET.SubElement(postal_supp, f"{{{ns['cac']}}}Country")
    ET.SubElement(country_supp, f"{{{ns['cbc']}}}IdentificationCode").text = "LV"

    # Supplier Legal Entity
    legal_entity_supp = ET.SubElement(party_supplier, f"{{{ns['cac']}}}PartyLegalEntity")
    ET.SubElement(legal_entity_supp, f"{{{ns['cbc']}}}RegistrationName").text = settings.get('company_name', 'Unknown Company')
    ET.SubElement(legal_entity_supp, f"{{{ns['cbc']}}}CompanyID").text = settings.get('reg_number', '')

    # Supplier Tax Scheme
    if settings.get('vat_enabled') == 'true' and settings.get('vat_number'):
        tax_scheme_supp = ET.SubElement(party_supplier, f"{{{ns['cac']}}}PartyTaxScheme")
        ET.SubElement(tax_scheme_supp, f"{{{ns['cbc']}}}CompanyID").text = settings.get('vat_number')
        tax_scheme = ET.SubElement(tax_scheme_supp, f"{{{ns['cac']}}}TaxScheme")
        ET.SubElement(tax_scheme, f"{{{ns['cbc']}}}ID").text = "VAT"

    # ── AccountingCustomerParty (Buyer) ──
    customer = ET.SubElement(root, f"{{{ns['cac']}}}AccountingCustomerParty")
    party_customer = ET.SubElement(customer, f"{{{ns['cac']}}}Party")

    cust_endpoint_scheme = "9936" if getattr(client, 'vat_number', None) else "0184"
    cust_endpoint_id = getattr(client, 'vat_number', None) or getattr(client, 'reg_number', None) or "UNKNOWN"
    cust_endpoint_el = ET.SubElement(party_customer, f"{{{ns['cbc']}}}EndpointID", schemeID=cust_endpoint_scheme)
    cust_endpoint_el.text = cust_endpoint_id

    # Customer Name
    party_name_cust = ET.SubElement(party_customer, f"{{{ns['cac']}}}PartyName")
    ET.SubElement(party_name_cust, f"{{{ns['cbc']}}}Name").text = client.name

    # Customer Postal Address
    postal_cust = ET.SubElement(party_customer, f"{{{ns['cac']}}}PostalAddress")
    ET.SubElement(postal_cust, f"{{{ns['cbc']}}}StreetName").text = getattr(client, 'address', '') or ''
    if getattr(client, 'postal_code', None):
        ET.SubElement(postal_cust, f"{{{ns['cbc']}}}PostalZone").text = client.postal_code
    country_cust = ET.SubElement(postal_cust, f"{{{ns['cac']}}}Country")
    ET.SubElement(country_cust, f"{{{ns['cbc']}}}IdentificationCode").text = "LV"

    # Customer Legal Entity
    legal_entity_cust = ET.SubElement(party_customer, f"{{{ns['cac']}}}PartyLegalEntity")
    ET.SubElement(legal_entity_cust, f"{{{ns['cbc']}}}RegistrationName").text = client.name
    if getattr(client, 'reg_number', None):
        ET.SubElement(legal_entity_cust, f"{{{ns['cbc']}}}CompanyID").text = client.reg_number

    # Customer Tax Scheme
    if getattr(client, 'vat_number', None):
        tax_scheme_cust = ET.SubElement(party_customer, f"{{{ns['cac']}}}PartyTaxScheme")
        ET.SubElement(tax_scheme_cust, f"{{{ns['cbc']}}}CompanyID").text = client.vat_number
        tax_scheme = ET.SubElement(tax_scheme_cust, f"{{{ns['cac']}}}TaxScheme")
        ET.SubElement(tax_scheme, f"{{{ns['cbc']}}}ID").text = "VAT"

    # ── PaymentMeans ──
    payment_means = ET.SubElement(root, f"{{{ns['cac']}}}PaymentMeans")
    ET.SubElement(payment_means, f"{{{ns['cbc']}}}PaymentMeansCode").text = "30" # Credit transfer
    payee_account = ET.SubElement(payment_means, f"{{{ns['cac']}}}PayeeFinancialAccount")
    ET.SubElement(payee_account, f"{{{ns['cbc']}}}ID").text = settings.get('bank1_account', 'N/A')
    payee_institution = ET.SubElement(payee_account, f"{{{ns['cac']}}}FinancialInstitutionBranch")
    ET.SubElement(payee_institution, f"{{{ns['cbc']}}}ID").text = settings.get('bank1_swift', 'N/A')

    # Calculate Totals
    line_extension_amount = 0.0
    tax_exclusive_amount = 0.0
    tax_inclusive_amount = 0.0
    payable_amount = 0.0

    tax_subtotals = {}

    for item in invoice.items:
        qty = float(item.quantity)
        price = float(item.unit_price)
        vat_rate = float(item.vat_rate) if settings.get('vat_enabled') == 'true' else 0.0
        
        line_total = qty * price
        line_extension_amount += line_total
        tax_excl = line_total
        tax_incl = tax_excl * (1 + vat_rate / 100)
        
        tax_exclusive_amount += tax_excl
        tax_inclusive_amount += tax_incl
        
        # Group taxes
        rate_key = f"{vat_rate:.2f}"
        if rate_key not in tax_subtotals:
            tax_subtotals[rate_key] = {'amount': 0.0, 'base': 0.0, 'rate': vat_rate}
        tax_subtotals[rate_key]['amount'] += (tax_incl - tax_excl)
        tax_subtotals[rate_key]['base'] += tax_excl

    payable_amount = tax_inclusive_amount

    # ── TaxTotal ──
    tax_total = ET.SubElement(root, f"{{{ns['cac']}}}TaxTotal")
    ET.SubElement(tax_total, f"{{{ns['cbc']}}}TaxAmount", currencyID="EUR").text = f"{(tax_inclusive_amount - tax_exclusive_amount):.2f}"
    
    for rate_key, tax_data in tax_subtotals.items():
        tax_subtotal = ET.SubElement(tax_total, f"{{{ns['cac']}}}TaxSubtotal")
        ET.SubElement(tax_subtotal, f"{{{ns['cbc']}}}TaxableAmount", currencyID="EUR").text = f"{tax_data['base']:.2f}"
        ET.SubElement(tax_subtotal, f"{{{ns['cbc']}}}TaxAmount", currencyID="EUR").text = f"{tax_data['amount']:.2f}"
        tax_category = ET.SubElement(tax_subtotal, f"{{{ns['cac']}}}TaxCategory")
        ET.SubElement(tax_category, f"{{{ns['cbc']}}}ID").text = "S" if tax_data['rate'] > 0 else "E" # S=Standard, E=Exempt
        ET.SubElement(tax_category, f"{{{ns['cbc']}}}Percent").text = f"{tax_data['rate']:.2f}"
        scheme = ET.SubElement(tax_category, f"{{{ns['cac']}}}TaxScheme")
        ET.SubElement(scheme, f"{{{ns['cbc']}}}ID").text = "VAT"

    # ── LegalMonetaryTotal ──
    legal_monetary_total = ET.SubElement(root, f"{{{ns['cac']}}}LegalMonetaryTotal")
    ET.SubElement(legal_monetary_total, f"{{{ns['cbc']}}}LineExtensionAmount", currencyID="EUR").text = f"{line_extension_amount:.2f}"
    ET.SubElement(legal_monetary_total, f"{{{ns['cbc']}}}TaxExclusiveAmount", currencyID="EUR").text = f"{tax_exclusive_amount:.2f}"
    ET.SubElement(legal_monetary_total, f"{{{ns['cbc']}}}TaxInclusiveAmount", currencyID="EUR").text = f"{tax_inclusive_amount:.2f}"
    ET.SubElement(legal_monetary_total, f"{{{ns['cbc']}}}PayableAmount", currencyID="EUR").text = f"{payable_amount:.2f}"

    # ── InvoiceLines ──
    line_id = 1
    for item in invoice.items:
        qty = float(item.quantity)
        price = float(item.unit_price)
        vat_rate = float(item.vat_rate) if settings.get('vat_enabled') == 'true' else 0.0
        
        invoice_line = ET.SubElement(root, f"{{{ns['cac']}}}InvoiceLine")
        ET.SubElement(invoice_line, f"{{{ns['cbc']}}}ID").text = str(line_id)
        ET.SubElement(invoice_line, f"{{{ns['cbc']}}}InvoicedQuantity", unitCode="EA").text = f"{qty:.2f}" # 'EA' for Each (gab.)
        ET.SubElement(invoice_line, f"{{{ns['cbc']}}}LineExtensionAmount", currencyID="EUR").text = f"{(qty * price):.2f}"
        
        item_node = ET.SubElement(invoice_line, f"{{{ns['cac']}}}Item")
        ET.SubElement(item_node, f"{{{ns['cbc']}}}Name").text = item.description or "Service"
        
        item_tax = ET.SubElement(item_node, f"{{{ns['cac']}}}ClassifiedTaxCategory")
        ET.SubElement(item_tax, f"{{{ns['cbc']}}}ID").text = "S" if vat_rate > 0 else "E"
        ET.SubElement(item_tax, f"{{{ns['cbc']}}}Percent").text = f"{vat_rate:.2f}"
        scheme2 = ET.SubElement(item_tax, f"{{{ns['cac']}}}TaxScheme")
        ET.SubElement(scheme2, f"{{{ns['cbc']}}}ID").text = "VAT"
        
        price_node = ET.SubElement(invoice_line, f"{{{ns['cac']}}}Price")
        ET.SubElement(price_node, f"{{{ns['cbc']}}}PriceAmount", currencyID="EUR").text = f"{price:.2f}"
        
        line_id += 1

    # XML string output
    # Encoding with xml_declaration ensures proper prolog: <?xml version="1.0" encoding="UTF-8"?>
    return ET.tostring(root, encoding='UTF-8', xml_declaration=True)
