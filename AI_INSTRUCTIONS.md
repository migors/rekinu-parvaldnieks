# AI Agent Context: Invoice Manager (Latvia)

This document serves as a comprehensive overview of the `Invoice Manager` project designed to help AI coding assistants (like Cursor, Copilot, or Antigravity) understand the architecture, core features, and current state of the application.

## 🏗️ Technical Stack
- **Backend:** Python 3.10+, FastAPI
- **Database:** SQLite with SQLAlchemy ORM (Database file at `data/invoice.db`)
- **Frontend:** Vanilla JavaScript, HTML5, Tailwind CSS
- **Packaging:** PyInstaller (for creating `.exe` Windows executables)

---

## 🚀 Core Features & Business Logic

### 1. Authentication & Users
- The system uses short-lived JWT Bearer tokens for API access and standard form login.
- **Admin Setup:** At first run, a default `admin` (`admin123`) user is generated.
- **User Profile:** Users can change their username and password via the "Profils" (Profile) tab in the frontend.

### 2. Settings Management (`app/models.py` -> `Settings`)
Settings are stored flexibly as key-value pairs in the database. The frontend settings panel is divided into 4 tabs:
- **🏢 Uzņēmums (Company):** Core details (Name, Reg. Nr., VAT Nr., Bank Accounts, Legal Address, VAT mode, Invoice Prefix). Also handles Logo Base64 string uploading.
- **✉️ E-pasts (Email):** SMTP configuration for sending emails directly to clients.
- **☁️ Google Drive:** OAuth2 integration to automatically backup PDFs and `.db` files.
- **🏛️ VID EDS API:** Toggle EDS integration and store the external API key for direct invoice uploads to the Latvian State Revenue Service.

### 3. Clients & Services (Catalogs)
- **Clients:** Stores client details. Automatically auto-completes Reg. Nr. and Legal Address using the Latvian UR Open Data API (`https://data.gov.lv/dati/lv/api/3/action/datastore_search?resource_id=25e80bf3-f107-4ab4-89ef-8511fdcd1ff1`).
- **Services:** Standard catalog of services with default prices, units, and VAT rates for quick invoice building.

### 4. Invoice Processing
- **Creation:** Invoices consist of a main model (`Invoice`) and line items (`InvoiceItem`). Prices and VAT are calculated dynamically in Python properties.
- **PDF Generation (`app/utils.py`):** Uses `reportlab` to instantly build heavily styled, localized PDF invoices reflecting the active Company settings and Logo.
- **E-Invoicing (XML):** Fully compliant PEPPOL BIS 3.0 / UBL 2.1 XML generation (`app/e_invoice.py`) tailored for the Latvian market.
- **Delivery:** 
  - Send via Email (SMTP with attached PDF).
  - Upload to Google Drive.

### 5. Invoice Dashboard & Bulk Actions (Important UI logic)
The "Rēķini" (Invoices) view includes interactive checkboxes (`[]`) next to each invoice row:
- **Checkbox Logic:** When 1 or more invoices are selected, a floating bulk-action toolbar appears at the top.
- **Export to CSV:** Selected invoices can be exported to a CSV file.
- **Send to EDS (VID EDS API):** Selected invoices can be bundled as an XML byte-stream and sent directly to the Latvian SRS (VID EDS) via a POST API request using the stored API Key. Endpoint: `POST /api/invoices/send-eds`.
- **Delete:** Bulk delete tool.

---

## 📂 Project Structure

- `app/main.py`: Main FastAPI application, middleware, startup events (automatic DB schema generation).
- `app/models.py`: SQLAlchemy database models (`User`, `Settings`, `Client`, `Service`, `Invoice`, `InvoiceItem`).
- `app/schemas.py`: Pydantic validation schemas (e.g., `SettingsUpdate` uses `exclude_unset=True` to allow partial setting updates).
- `app/crud.py`: Database operations and queries.
- `app/routers/`: Segmented API routes (`auth.py`, `clients.py`, `services.py`, `invoices.py`).
- `app/utils.py`: PDF Builder, SMTP Email sender, and dashboard statistics calculator.
- `app/eds_api.py`: Logic for formatting API calls to the official VID EDS endpoints.
- `app/e_invoice.py`: ElementTree based XML builder for PEPPOL BIS 3.0.
- `app/static/index.html`: The single-page application frontend. Uses `fetch` API, no frontend framework. Very heavy reliance on JS DOM manipulation (e.g. `switchSettingsTab()`, invoice checklist listeners).

## ⚠️ Important Implementation Notes for AI Agents
1. **Frontend Architecture:** Because the frontend is pure HTML/JS (`index.html`), any new layout components must be meticulously styled with Tailwind CSS utility classes to match the existing dark-mode UI. Modals are manually controlled via `.classList.remove("hidden")` functions.
2. **Settings Parsing:** Settings are retrieved as a dictionary in Python (`{s.key: s.value for s in db.query(models.Settings).all()}`). Never overwrite unset values when saving via the `PUT /api/settings` route – respect `exclude_unset`.
3. **Distribution Setup:** The project generates a `dist/` Windows executable using PyInstaller via `build_exe.py`. The `launcher.py` hides the terminal console loop natively to support Windows users nicely. `app/` templates and static files are bundled inside the EXE via `sys._MEIPASS`. Do NOT hardcode absolute file system paths. Always use `get_base_path()` logic in Python.
