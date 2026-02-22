# Invoice Form Enhancements (Recent Updates)

This document summarizes the recent enhancements made to the invoice creation and editing form to improve user workflow, specifically around editing existing records and duplicating invoices.

## Key Features Added:

1. **Invoice Number in Header (`Reķina galvene`)**
   - The generated or existing invoice number is now prominently displayed at the very top header of the invoice form. This provides immediate context so the user always knows exactly which invoice they are actively working on.

2. **"Save Changes" Functionality (`Saglabāt izmaiņas`)**
   - When an existing invoice is opened in edit mode, the save action is clearly distinguished to update the current record (typically via a `PUT` request), preventing accidental duplicates and making the edit state obvious.

3. **"Save As New" / Duplicate Invoice (`Saglabāt jaunu no esoša`)**
   - Added the ability to use an existing invoice as a template. Users can open an invoice and choose to save it as a completely new record.
   - This prevents the need to re-enter repetitive data for recurring or similar invoices.

4. **Green Animation on Invoice Number Change (`Zaļa animācija kopējot`)**
   - When a user triggers the "Save as new" (copy) action, the system automatically generates a new invoice number.
   - **Crucial UI Feedback:** To make it explicitly clear that the user is now looking at a *new* invoice and not the old one, a green flash/pulse animation is applied to the invoice number in the header. This confirms the duplication was successful and prevents confusion.
