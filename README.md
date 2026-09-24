# bra-kriminalstatistik

Verktyg för att **automatiskt hämta Sveriges officiella kriminalstatistik från Brå** (Brottsförebyggande rådet). Repot innehåller också en kurerad **katalog över brottstyper och brottskoder** för penningtvätt (AML), terrorfinansiering (CTF), sanktionsbrott och bedrägeri.

- **SOL-klient:** uttag ur Brås interaktiva statistikdatabas [SOL](https://statistik.bra.se/solwebb/action/index). Välj brottstyp eller brottskod, område och år, månad eller kvartal. Resultatet blir CSV i långt format.
- **Tabellhämtare:** Brås färdiga Excel-tabeller (anmälda, misstänkta, lagförda och handlagda brott, målsägare, NTU), diagramdata, rapporter och metoddokument från bra.se.
- **Bevakningslista:** ett kommando hämtar ett 20-tal färdiga serier om bedrägeri, penningtvätt, CTF och sanktioner ([`config/watchlist_aml_fraud.json`](config/watchlist_aml_fraud.json)).
- **Dashboards:** Excel- och HTML-dashboard (fristående, utan CDN) med trender, rullande 12 månader, regioner och åldersprofil för misstänkta.
- **Körskript för macOS/Linux (`.sh`) och Windows (`.ps1`/`.bat`)**, inklusive schemaläggning med launchd, cron och Windows Schemaläggaren.

Själva hämtningen kräver bara Pythons standardbibliotek. `pandas` och `openpyxl` behövs bara för dashboards.

> Brå har inget officiellt API. Skripten efterliknar webbläsaren och kan sluta fungera om Brå ändrar sin webbplats. Se [docs/03-teknik-hamtning.md](docs/03-teknik-hamtning.md).

---

## Snabbstart

### macOS / Linux

```bash
git clone https://github.com/overjoyde/bra-kriminalstatistik.git
cd bra-kriminalstatistik
./run/mac-linux/setup.sh              # skapar .venv, installerar beroenden, kör testerna
./run/mac-linux/sol_watchlist.sh      # AML/bedrägeri-serier från SOL -> data/sol/  (~30 s)
./run/mac-linux/fetch_all.sh          # allt: tabeller + SOL + dashboards  (~5 min första gången)
open data/dashboard/Bra_trendbevakning_dashboard.html   # Linux: xdg-open
```

### Windows

Installera Python 3.10 eller senare (`winget install Python.Python.3.12`). Klona eller ladda ned repot och gör sedan något av följande:

- **Dubbelklicka** på `run\windows\setup.bat` och därefter `run\windows\fetch_all.bat`.
- Kör från PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File run\windows\setup.ps1
powershell -ExecutionPolicy Bypass -File run\windows\sol_watchlist.ps1
powershell -ExecutionPolicy Bypass -File run\windows\fetch_all.ps1 --no-pdf
start data\dashboard\Bra_trendbevakning_dashboard.html
```

### Utan skript (valfritt OS)

```bash
python -m pip install -r requirements.txt
python scripts/sol_watchlist.py
python scripts/fetch_tables.py --no-pdf
```

---

## Skript

| Uppgift | Python | macOS/Linux | Windows |
|---|---|---|---|
| Installera | – | `run/mac-linux/setup.sh` | `run\windows\setup.bat` / `.ps1` |
| Hela kedjan | `scripts/fetch_all.py` | `fetch_all.sh` | `fetch_all.bat` / `.ps1` |
| Färdiga tabeller från bra.se | `scripts/fetch_tables.py` | `fetch_tables.sh` | `fetch_tables.bat` / `.ps1` |
| SOL: bevakningslista | `scripts/sol_watchlist.py` | `sol_watchlist.sh` | `sol_watchlist.bat` / `.ps1` |
| SOL: eget uttag | `scripts/sol_query.py` | `sol_query.sh` | `sol_query.bat` / `.ps1` |
| SOL: sök eller exportera koder | `scripts/sol_catalog.py` | `sol_catalog.sh` | `sol_catalog.bat` / `.ps1` |
| Dashboards | `scripts/build_excel_dashboard.py`, `build_html_dashboard.py` | `build_dashboards.sh` | `build_dashboards.bat` / `.ps1` |
| Schemalägg månadsvis | – | `schedule_macos.sh` (launchd), `schedule_cron.sh` | `schedule_task.bat` / `.ps1` |
| Felsök bra.se-formulär | `scripts/inspect_forms.py` | – | – |

Alla skript har `--help`. Argument till `.sh`, `.ps1` och `.bat` skickas vidare till Python-skriptet.

### Exempel: egna SOL-uttag

```bash
# Hitta koder och id:n
python scripts/sol_catalog.py --menus brottskod-ar-region --search penningtvätt
python scripts/sol_catalog.py --list-menus

# Befogenhetsbedrägeri mot äldre (kod 0950 + 0951) per månad, hela landet och alla polisregioner
python scripts/sol_query.py --menu brottskod-manad-region --codes 0950 0951 \
    --periods 2024-01..2026-08 --all-regions

# Penningtvätt totalt (brottstyp 13092) per år, med antal per 100 000 invånare
python scripts/sol_query.py --menu brottstyp-ar-region --ids 13092 --periods 2015-2025

# Terrorfinansiering senaste året, direkt till skärmen
python scripts/sol_query.py --menu brottskod-ar-region --codes 7035 7036 7037 --periods senaste --out -
```

**Perioder:** `senaste`, `alla`, `2015-2025`, `2024,2025` eller, i månadsmenyer, `2024-01..2026-08`.
**Områden:** `"Hela landet"`, `Stockholm` (tolkas som Region Stockholm), `"Skåne län"` (1975–2014) eller kommunnamn i kommunmenyerna.

### Som Python-bibliotek

```python
from brastat.sol import SolClient

sol = SolClient()
rows = sol.query("brottstyp-manad-region", crime_ids=["14024"],        # befogenhetsbedrägeri
                 regions=["Hela landet", "Region Stockholm"], periods="2023-01..2026-12")
# -> [{'brott': 'Befogenhetsbedrägeri', 'omrade': 'Hela landet', 'period': '2023-01',
#      'preliminar': False, 'antal': 946.0, 'per_100k': 9.0, ...}, ...]
```

### Egen bevakningslista

Kopiera `config/watchlist_aml_fraud.json` och ändra serierna. Varje serie anger `meny` och `ids` eller `koder`, och kan också ange `perioder` och `regioner`. Kör sedan:

```bash
python scripts/sol_watchlist.py --config config/min_lista.json
```

---

## Utdata

```
data/
├── sol/
│   ├── watchlist_samlad.csv        alla bevakningsserier, långt format (semikolon, UTF-8 med BOM -> öppnas rätt i Excel)
│   ├── watchlist/<serie>.csv
│   ├── uttag_<meny>_<tid>.csv      egna uttag
│   └── katalog/                    brottstyper, brottskoder, områden, perioder per meny
├── raw/                            Brås Excel-tabeller (anmalda_brott, misstankta, lagforda, handlagda, malsagare, ntu, …)
├── docs/                           rapporter och metoddokument (PDF)
├── dashboard/                      Bra_trendbevakning_dashboard.xlsx / .html
├── manifest.csv                    URL, status, storlek och sha256 för varje hämtad fil
└── logs/                           loggar från schemalagda körningar
```

Datakatalogen styrs med `--out` eller miljövariabeln `BRA_DATA_DIR`. `data/` checkas inte in.

**Kolumner i SOL-uttagen:** `meny, brott_id, brottskod, brott, sokvag, omrade, period, ar, manad, kvartal, periodtyp, preliminar, antal, per_100k`. Tomt `antal` betyder att brottet inte fanns under perioden, t.ex. innan en kod infördes.

---

## Dokumentation

| Dokument | Innehåll |
|---|---|
| [docs/01-datakallor.md](docs/01-datakallor.md) | Vad som finns i SOL och på bra.se: täckning, aktualitet, sekretess, tabellgrupper och förbehåll |
| [docs/02-brottskoder-aml-ctf-bedrageri.md](docs/02-brottskoder-aml-ctf-bedrageri.md) | **Kodkatalog:** penningtvätt, terrorfinansiering, sanktioner, bedrägerimodus (2019–), identitet och dataintrång, företag som brottsverktyg, predikatbrott och rekommenderade serier |
| [docs/03-teknik-hamtning.md](docs/03-teknik-hamtning.md) | Hur SOL och bra.se fungerar tekniskt (endpoints, sessioner, format) och TLS |
| [reference/brottskoder_sol.csv](reference/brottskoder_sol.csv) | Alla 1 361 brottskoder, inklusive upphörda (SOL 2026-09-24) |
| [reference/brottstyper_sol.csv](reference/brottstyper_sol.csv) | Brottstypsträdet med SOL-id och sökväg |

## Schemaläggning

Brå uppdaterar den preliminära månadsstatistiken cirka 10 dagar efter varje månadsskifte. Standardschemat kör därför **den 15:e varje månad kl. 07:00** med `--no-pdf`.

- **macOS:** `./run/mac-linux/schedule_macos.sh`. launchd får inte läsa `~/Desktop`, `~/Documents` eller `~/Downloads`, så lägg repot t.ex. i `~/code/`.
- **Linux:** `./run/mac-linux/schedule_cron.sh`
- **Windows:** `run\windows\schedule_task.bat`, eller `schedule_task.ps1 -Day 15 -Time 07:00`

Alla tre tas bort med `--remove` respektive `-Remove`.

## Felsökning

| Problem | Lösning |
|---|---|
| `CERTIFICATE_VERIFY_FAILED` | `pip install truststore` (ingår i requirements). Klienten faller annars automatiskt tillbaka på systemets `curl`. Det kan också tvingas med `BRASTAT_HTTP=curl`. |
| `SOL-fel: …` / "obefintlig menyrad" | SOL:s sessionsflöde har ändrats eller servern är nere. Försök igen senare, och se docs/03. |
| `saknas` i manifest.csv | Tabellen är inte publicerad ännu (t.ex. årstabell före mars) eller Brå har ändrat URL-mönstret. Kör `scripts/inspect_forms.py`. |
| Skript blockeras i Windows | Använd `.bat`-filerna eller `-ExecutionPolicy Bypass` enligt ovan. |
| Konstiga tecken (Ã¤) i Excel | CSV-filerna är UTF-8 med BOM och semikolonseparerade. Öppna med Data → Från text/CSV om Excel ändå gissar fel. |

## Förbehåll

- Statistiken visar **anmälda brott**, inte faktisk brottslighet. Bedrägeri räknas som seriebrott och kan ge stora toppar.
- **Brottskoder anger inte betalmedel.** Kopplingar till typologier (i kodkatalogen och dashboarden) är analytiska antaganden.
- Månadsdata är **preliminär** och revideras i den slutliga årsstatistiken.
- Koder ändras över tid och bryter serier. Läs Brås *Klassificering av brott* och kvalitetsdeklarationerna (`--groups metod`).

## Licens och källa

Koden är licensierad under MIT, se [LICENSE](LICENSE). Datan kommer från **Brottsförebyggande rådet (Brå)** och får vidareutnyttjas fritt med Brå angiven som källa. Repot är inte framtaget av Brå. Var snäll mot Brås servrar: skripten väntar mellan anropen, och det räcker att schemalägga en körning i månaden.

## Utveckling

```bash
python -m unittest discover -s tests     # offline-tester (körs i CI på Linux, macOS och Windows)
```

Bidrag är välkomna. Nya serier läggs lättast till i bevakningslistan, och nya bra.se-tabeller som en metod i `brastat/tabeller.py`.
