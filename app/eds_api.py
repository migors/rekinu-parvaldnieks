import logging
import requests
from typing import Dict, Any

logger = logging.getLogger(__name__)

VID_EDS_API_URL = "https://eds.vid.gov.lv/api/v2/einvoice"

def send_invoice_to_eds(xml_bytes: bytes, api_key: str, is_test: bool = False) -> Dict[str, Any]:
    """
    Sutit e-rekinu (XML) uz VID EDS API.
    Dokumentacija: https://eds.vid.gov.lv/api/swagger/ui/index#!/EInvoice/EInvoice_Post
    """
    headers = {
        "X-API-Key": api_key, # Pienemam, ka atslēga tiek sūtīta šādā veidā, parasti tas ir Authorization: Bearer <token> vai X-API-Key.
    }
    
    # Let's try to infer if standard UBL URN is required or standard upload format.
    # VID EDS accepts UBL 2.1 via multipart/form-data with file upload or raw XML body.
    # We will send raw XML body for simplicity, with correct content-type.
    headers["Content-Type"] = "application/xml"
    
    # If the documentation strictly uses Bearer tokens, we might need to adjust this depending on the actual scheme.
    # For now, we will send to the default URL.
    try:
        # Since we don't have access to the real production API documentation details, we are doing a generic POST.
        # Often it requires a POST request with the file.
        files = {
            'file': ('invoice.xml', xml_bytes, 'application/xml')
        }
        # If multipart/form-data is used, we drop the raw Content-Type
        del headers["Content-Type"]
        
        response = requests.post(
            VID_EDS_API_URL,
            headers=headers,
            files=files,
            timeout=10
        )
        
        if response.status_code in (200, 201, 202):
            return {"success": True, "message": "Veiksmīgi nosūtīts uz EDS", "status_code": response.status_code}
        else:
            logger.error(f"EDS API sūtīšanas kļūda: {response.status_code} - {response.text}")
            return {
                "success": False, 
                "error": f"EDS API atgrieza kļūdu ({response.status_code})",
                "details": response.text,
                "status_code": response.status_code
            }
            
    except requests.RequestException as e:
        logger.error(f"Neizdevās sazināties ar EDS API: {e}")
        return {
            "success": False,
            "error": f"Neizdevās savienoties ar VID EDS: {str(e)}"
        }
