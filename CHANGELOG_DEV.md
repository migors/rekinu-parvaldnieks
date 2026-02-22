# Izstrādes vēsture un veiktās izmaiņas (Developer Changelog)

Šis dokuments apkopo visas galvenās tehniskās izmaiņas, kas veiktas šajā izstrādes ciklā, lai atvieglotu projekta turpināšanu vai līdzīgu risinājumu izveidi.

## 1. Arhitektūra: Pāreja uz Windows EXE
- **Sākuma stāvoklis:** FastAPI aplikācija, kas darbojās caur termināli.
- **Risinājums:** Izveidots pašpietiekams Windows EXE izmantojot `PyInstaller`.
- **Launcher.py:** Speciāls fona procesa palaidējs, kas:
    - Izveido `AppData` mapes datubāzei (`%APPDATA%\InvoiceManager\`).
    - Startē `uvicorn` serveri bez atvērta melnā loga (fonā).
    - Pievieno ikonu System Tray (pulksteņa zonā) ērtai piekļuvei.
    - Nodrošina, ka var darboties tikai viena programmas kopija vienlaicīgi.

## 2. Datu glabāšana
- **AppData migrācija:** Datubāze (`invoices.db`) tiek glabāta ārpus programmas mapes. Tas ļauj lietotājam dzēst programmas mapi vai to atjaunināt, nezaudējot savus rēķinus.
- **Resursu ceļi:** Visas norādes uz statiskajiem failiem (HTML/CSS) ir pielāgotas tā, lai tās strādātu gan izstrādes režīmā, gan pēc sapakošanas EXE failā.

## 3. PDF Ģenerēšana (ReportLab)
- **Tehnoloģiju maiņa:** Pāreja no `xhtml2pdf` uz `ReportLab`.
- **Ieguvums:** 
    - Atrisinātas problēmas ar latviešu valodas mīkstinājuma zīmēm.
    - Rēķina dizains tagad precīzi atbilst ekrānā redzamajam.
    - Iespēja ģenerēt PDF ar iebūvētiem fontiem bez nepieciešamības tos instalēt Windows sistēmā.

## 4. Funkcionalitātes papildinājumi
- **Lietotāju vadība:** Pievienota pieteikšanās (Login) un iespēja iestatījumos mainīt paroli/lietotājvārdu.
- **Apmaksas statuss:** Rēķinu sarakstā pievienoti slēdži, lai iezīmētu apmaksātos rēķinus ar zaļu krāsu.
- **Rezerves kopijas:** Iestatījumos pievienota poga visas datubāzes lejupielādei.
- **Google Drive:** Pievienota automātiska rēķinu dublēšana mākonī.

## 5. Būvēšanas process
- Izveidots `build_exe.py` skripts, kas automātiski saliek visu programmu kopā.
- Izveidots `dist/NC_Invoice_Manager.zip` arhīvs, kas ir gatavs tūlītējai izplatīšanai.


## 6. Uzlabojumi (2026-02-18)
- **Pasta indekss:** Pievienots lauks `postal_code` klientu kartītē un datubāzē. Autocomplete funkcija tagad automātiski nolasa indeksu (LV-XXXX) no adrešu reģistra.
- **E-pasta sūtīšana:** Salabota integrācija ar SMTP (Gmail), izmantojot pagaidu failus pielikumiem.
- **Navigācija:** Uzlabota lietotņu navigācija, izmantojot URL vaicājuma parametrus (`?tab=...`).
    - Atverot rēķinu priekšskatījumu un nospiežot "Atpakaļ", lietotājs nonāk atpakaļ rēķinu sarakstā.
    - Pārlādējot lapu (Refresh), tiek saglabāta aktīvā sadaļa.

## 7. Koda audits un tīrīšana (2026-02-18)
- **Dzēsti ~20 lieki faili:** Testa un atkļūdošanas skripti (`test_*.py`, `verify_*.py`, `debug_*.py`, `check_*.py`, `fix_*.py`, `create_user.py`), testa PDF faili, vecie žurnāli (`build.log`, `uvicorn_*.log`), neizmantotie resursi (`arial_b64.txt`, `keys_new.txt`).
- **Dzēsta `sample pdf/` mape** ar testa PDF paraugiem.
- **Dzēsts dublikāts `data/invoice.db`** (aktīvā DB ir `invoices.db`).
- **Dzēsts neizmantotais šablons `invoice_pdf.html`** (aizstāts ar ReportLab natīvo PDF).
- **Noņemti neizmantotie importi:**
    - `utils.py`: `xhtml2pdf`, `Jinja2 Environment/FileSystemLoader`, `EmailStr`, Jinja2 env setup.
    - `routers/clients.py`, `routers/services.py`: `List`.
    - `routers/invoices.py`: dublikāts `Response` imports.
- **Atjaunināts `requirements.txt`:** Noņemts `xhtml2pdf`, pievienots `reportlab>=4.0.0` kā tiešā atkarība.
- **Noņemti `DEBUG print()`** izsaukumi no `database.py` un `utils.py`.
- **Noņemts DEV MODE baneris** no `index.html` augšdaļas.

## 8. UI uzlabojumi (2026-02-19)
- **Iestatījumu secība:** Pārkārtota uzņēmuma iestatījumu lapa:
    1. Rēķina numerācija (prefikss)
    2. Uzņēmuma rekvizīti
    3. Bankas rekvizīti (abas bankas blakus)
    4. Uzņēmuma logo (pārvietots uz leju)
- **Profila iestatījumi:** Pievienota iespēja mainīt lietotājvārdu (ne tikai paroli). Lietotājvārds tiek automātiski ielādēts no pašreizējā profila.
- **HTML rēķina priekšskatījums:** Pievienots pasta indekss (LV-XXXX) klienta adresei — tagad sakrīt ar PDF versiju.

## 9. Rēķina kartiņas uzlabojumi un "Saglabāt kā" (2026-02-22)

### Rēķina kartiņas UX
- **Dinamisks virsraksts:** Veidojot jaunu rēķinu, virsrakstā uzreiz rāda nākamo automātiski piešķiramo numuru (piemēram, `Jauns rēķins NC-000032`). Rediģējot esošu — `Rēķins NC-000030`.
- **Poga "Saglabāt":** Poga "Izveidot rēķinu" pārdēvēta uz "💾 Saglabāt". Strādā universāli — gan jaunu rēķinu izveidei (POST), gan esošu atjaunināšanai (PUT).
- **Forma paliek atvērta:** Pēc saglabāšanas forma vairs netiek aizvērta — tā pāriet labošanas režīmā ar saglabātā rēķina datiem.
- **Poga "📋 Kopēt":** Rediģēšanas režīmā parādās Kopēt poga. Tā duplificē pašreizējo rēķinu ar jauku fade animāciju un atstāj jauno kopiju atvērtu labošanai.
- **Darbību pogas (tikai rediģēšanas režīmā):**
  - `👁️ Skatīt` — atver rēķinu HTML priekšskatījumā jaunā cilnē
  - **"Saglabāt kā" dialogi:** Visas eksporta opcijas (CSV, PDF, XML e-rēķins) tagad izmanto `showSaveFilePicker`, ļaujot nomainīt faila nosaukumu pirms lejupielādes (ar *fallback* funkciju pārlūkiem bez šī API).
  - `✉️ E-pasts` — atver e-pasta sūtīšanas modāli
- **Jaunas API:** Pievienots `GET /api/invoices/next-number` endpoint nākamā rēķina numura iegūšanai.

## 10. Papildus UI Uzlabojumi un Kļūdu Labojumi (v1.5.1)
- **Vizuālais apstiprinājums saglabājot:** Spiežot "Saglabāt" rēķina labošanas formā, poga uz 2 sekundēm mainās uz "✅ Saglabāts!" ar zaļu izgaismojumu, skaidri norādot uz sekmīgu darbību.
- **EDS poga rēķina kartītē:** Pievienota ātrā poga "📤 EDS" tieši rēķina labošanas logā (blakus e-rēķina pogai), ļaujot nosūtīt atvērto rēķinu uz VID.
- **Pydantic v2 Datumu Kļūda:** Salabots `InvoiceUpdate` shēmas gļuks, kur `Optional[date] = None` izraisīja 422 kļūdu labojot rēķinu. Shēma tagad pieņem `Optional[str]` ar manuālu validāciju un konvertāciju `crud.py` līmenī.
- **Pārlūka Validācijas Bloķēšana:** Rēķina formai pievienots `novalidate` atribūts, lai novērstu "invalid form control" kļūdas, slēptajiem iestatījumu laukiem bloķējot rēķina saglabāšanu.

### "Saglabāt kā" dialogs — File System Access API
Izmantojot Chrome/Edge File System Access API (`showSaveFilePicker`), lietotājs var izvēlēties saglabāšanas mapi. Atbalstītas visas eksporta funkcijas:
- PDF (rēķinu saraksta 📄 ikona, kartiņas "Saglabāt PDF" poga)
- CSV (augšējā 📊 poga, bulk darbību CSV)
- ZIP e-rēķini (tikai vairāku rēķinu eksportam, jo .xml Chrome marķē kā bīstamu)
- Datubāzes rezerves kopija (Rezerves kopija sadaļa)
- Iekritumu ceptuve: ja pārlūks neatbalsta API (Firefox u.c.), automātiski krīt atpakaļ uz standarta lejupielādi.

---
*Izveidots ar AI (Antigravity) palīdzību, lai nodrošinātu pēctecību projektā.*
