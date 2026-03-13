# PROMPT FOR AI VIDEO GENERATOR (Google Vids / NotebookLM / Synthesia)

**System Instruction for the AI Generator:**
You are an expert SaaS product marketer and video scriptwriter. Your task is to generate a professional, engaging, and clear voiceover script and visual storyboard for a software product called "Invoice Manager" (Latvian: "Rēķinu Pārvaldnieks"). The primary target audience is small to medium business owners, freelancers, and accountants in Latvia. The tone should be professional, reassuring, and clearly highlight how these specific features work. 
Use the provided screenshots from the `screenshots/full_guide/` folder and feature descriptions below to structure your video sequentially. For each step, provide:
1.  **Visual Instructions:** What should be shown on the screen (zoom ins, highlighting specific elements).
2.  **Voiceover (Latvian):** The spoken script for the narrator.

---

## Video Flow & Scene Breakdown

### 1. Panelis (Dashboard)
**Sagaidāmā bilde:** `01_dashboard_...png`
**Scenārija uzdevums:** Parādīt sistēmas galveno paneli, kurā ir apkopota kopsavilkuma statistika un grafiki par ienākumiem. Uzsvars uz to, ka visu biznesa finansiālo stāvokli var redzēt vienuviet un tas ir vizuāli pievilcīgs.
**Aptuvenais teksts:** "Esiet sveicināti Rēķinu Pārvaldniekā. Galvenais panelis sniedz tūlītēju, vizuālu pārskatu par jūsu biznesa asinsriti — no kopējiem ieņēmumiem līdz neapmaksāto rēķinu statistikai."

### 2. Rēķinu Saraksts (Invoices List)
**Sagaidāmā bilde:** `02_invoices_list_...png`
**Scenārija uzdevums:** Parādīt tabulu ar visiem izrakstītajiem rēķiniem un to statusiem (Apmaksāts, Neapmaksāts).
**Aptuvenais teksts:** "Pārslēdzoties uz Rēķinu sadaļu, jūs iegūstat pilnu kontroli pār visiem izrakstītajiem dokumentiem, kurus var ērti atlasīt, meklēt un pārvaldīt."

### 3. Vairāku rēķinu apstrāde (Bulk Actions)
**Sagaidāmā bilde:** `03_bulk_actions_...png`
**Scenārija uzdevums:** Kad sarakstā atķeksē vienu vai vairākus rēķinus, parādās "Bulk actions" (Grupas darbību) panelis. Tajā var lejupielādēt visus rēķinus uzreiz ZIP formātā, mainīt to statusus vai eksportēt kā vienotu CSV failu grāmatvedībai.
**Aptuvenais teksts:** "Iezīmējot vairākus rēķinus, varat veikt grupas darbības — vienlaicīgi eksportēt tos visus kā CSV grāmatvedībai vai lejupielādēt mapē."

### 4. Kā pievienot jaunu rēķinu
**Sagaidāmā bilde:** `04_new_invoice_blank_...png`
**Scenārija uzdevums:** Parādīt tukšu rēķina formu. Noklikšķinot "+ Jauns rēķins", atveras ērta forma, kur var izvēlēties klientu, pievienot rēķina rindas un automātiski aprēķināsies PVN.
**Aptuvenais teksts:** "Rēķina izveide aizņem vien pāris sekundes. Atverot jaunu rēķinu, intuitīvā forma palīdz ātri izvēlēties klientu un ievadīt preces vai pakalpojumus, automātiski aprēķinot nodokļus."

### 5. Kā saglabāt rēķinu
**Sagaidāmā bilde:** `05_invoice_saved_success_...png`
**Scenārija uzdevums:** Parādīt saglabāšanas pogas vizuālo apstiprinājumu. Kad nospiež pogu, tā uz 2 sekundēm iedegas zaļa ("✅ Saglabāts!"), skaidri norādot uz sekmīgu darbību, un poga neaizver formu, ļaujot turpināt darbu.
**Aptuvenais teksts:** "Nospiežot Saglabāt, sistēma sniedz tūlītēju vizuālu apstiprinājumu, ļaujot jums turpināt darbu bez logu pārslēgšanas."

### 6. Kā kopēt rēķinu
**Sagaidāmā bilde:** `07_invoice_copied_result_...png`
**Scenārija uzdevums:** Izmantojot "Kopēt" pogu, var nokopēt esošu rēķinu. Lapa eleganti pārslēdzas uz jauno rēķinu ar jau aizpildītiem datiem, bet jaunu numuru, kas ideāli der regulāru ikmēneša rēķinu izrakstīšanai (piemēram, īrei vai abonentiem).
**Aptuvenais teksts:** "Bieži izrakstāt vienādus rēķinus? Ar 'Kopēt' funkciju jūs varat dublēt esošu dokumentu, pielāgot nepieciešamo, un tas ir gatavs nosūtīšanai."

### 7. Kā eksportēt un saglabāt failus
**Sagaidāmā bilde:** `06_invoice_actions_buttons_...png`
**Scenārija uzdevums:** Rēķina apakšā ir rīku pogas. Varat lejupielādēt rēķinu kā skaistu **PDF** (kas prasa izvēlēties direktoriju ar pārlūka izvēlni) vai nosūtīt to tieši klientam caur iebūvēto **E-pasta sistēmu**.
*(NB: Nekādā gadījumā nepieminēt un nerādīt EDS funkciju).*
**Aptuvenais teksts:** "Kad rēķins pabeigts, klikšķiniet, lai saglabātu to kā PDF failu savā datorā, vai izmantojiet iebūvēto e-pasta rīku, lai to nekavējoties nosūtītu klientam."

### 8. Kā pievienot uzņēmumu (Klientu)
**Sagaidāmā bilde:** `add_client_modal_...png`
**Scenārija uzdevums:** Atverot jauna klienta modālo logu, jūs varat tieši ierakstīt nosaukumu un sistēma veiks integrētu meklēšanu Latvijas Uzņēmumu Reģistrā (UR Open Data), automātiski aizpildot PVN, Reģistrācijas numuru un Juridisko adresi.
**Aptuvenais teksts:** "Jauna klienta pievienošana ir maģiska — vienkārši ierakstiet nosaukumu, un sistēma automātiski ielādēs datus no Uzņēmumu Reģistra."

### 9. Kā pievienot pakalpojumu
**Sagaidāmā bilde:** `add_service_modal_...png`
**Scenārija uzdevums:** Sadaļā var izveidot katalogu ar tipiskiem pakalpojumiem vai produktiem, fiksēt to cenas un atbilstošo PVN likmi, lai rēķinā tos pievienotu ar vienu klikšķi.
**Aptuvenais teksts:** "Izveidojiet savu pakalpojumu katalogu, iestatiet cenas un PVN likmes, lai turpmāk rindu pievienošana būtu vēl ātrāka."

### 10. Rezerves Kopija (Backup funkcija)
**Sagaidāmā bilde:** `backup_tab_...png`
**Scenārija uzdevums:** Rēķini glabājas Jūsu ierīcē (jeb privātajā vidē). Varat jebkurā brīdī lejupielādēt pilnu sistēmas datubāzes failu, kā arī atjaunot visu informāciju gadījumā, ja kaut kas nobrūk. 
**Aptuvenais teksts:** "Mēs rūpējamies par jūsu datu drošību. Backup sadaļa ļauj mirklī saglabāt visu sistēmas datubāzi lokāli vai atjaunot to nepieciešamības gadījumā."

### 11. Iestatījumu Sadaļa
Šajā nodaļā secīgi rādām Iestatījumu tabus.

**11.1 Uzņēmuma dati** (`settings_company_tab_...png`):
**Scenārijs:** Konfigurējam savus rekvizītus, logotipu un rēķina prefiksus (piemēram, "MANSUZNEMUMS-"). 
**Aptuvenais teksts:** "Pielāgojiet sistēmu sev — ievadiet savus rekvizītus, pievienojiet logo un nosakiet sava rēķina numura formātu."

**11.2 E-pasts (SMTP)** (`settings_email_tab_...png`):
**Scenārijs:** Var piesaistīt savu e-pastu, lai sistēma sūtītu rēķinus tieši no Jūsu darba e-pasta adreses.
**Aptuvenais teksts:** "Savienojiet sistēmu ar savu e-pastu, un rēķini pie klientiem nonāks pa tiešo no jūsu pastkastītes."

**11.3 Google Drive** (`settings_gdrive_tab_...png`):
**Scenārijs:** Piesaistiet Google Drive, un norādiet Mapi, un aplikācija fonā katru izrakstīto PDF rēķinu automātiski nosūtīs uz mākoni. Nekādas manuālas organizēšanas.
**Aptuvenais teksts:** "Un visbeidzot, ieslēdziet Google Drive sinhronizāciju — katrs izveidotais PDF automātiski nogulsnēsies jūsu drošajā mākoņkrātuvē, ļaujot jums gulēt mierīgi."

---
**Final Call to Action for AI Generator:**
Please output a highly structured, 2-3 minute video script using the exact sequencing of these 11 chapters. Do not invent any additional features.
