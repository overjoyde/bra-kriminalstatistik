# Teknik: hur hämtningen fungerar

Brå har **inget officiellt API**. Båda hämtarna återskapar det som webbläsaren gör. De är därför känsliga för ändringar på Brås webbplats. När något slutar fungera syns det i loggen, i `data/manifest.csv` (status `saknas`/`FEL`) eller som ett SOL-fel.

## SOL (`brastat/sol.py`)

SOL är en äldre Struts/JSP-applikation med ramar (frameset) och teckenkodning ISO-8859-1. Sessionen styrs av cookien `JSESSIONID`, och **en session är låst till en meny åt gången**.

```
GET  /solwebb/action/start?menykatalogid=1            -> öppnar session (cookie)
GET  /solwebb/action/anmalda/urval/urval?menyid=<N>   -> väljer meny; sidan innehåller urvalslistor som JS-arrayer
POST /solwebb/action/anmalda/urval/vantapopup         -> skickar urvalet
GET  /solwebb/action/anmalda/urval/sok                -> kör frågan
POST /solwebb/action/anmalda/resultat/dbfil           -> resultat som "Databasfil.txt" (semikolon, långt format)
```

**Urvalslistor i menysidan** (fälten är `*`-separerade):

| Array | Format | Innehåll |
|---|---|---|
| `arrayNivaett` | `id*namn` | Grupper och trädnoder (indrag med `\xA0`) |
| `arrayNivatva` | `id*namn*grupp_id*sökväg` | Valbara brottstyper/brottskoder. `"X totalt"` redovisas som `"X"` i resultatet. |
| `arrayRegionNivaTva` | `id*namn*förälder*fullständigt namn` | Områden |
| `arrayPeriod` | `id*namn*år_id*fullständigt namn*typ` | Typ `-1` = år (årsmenyer), `0` = helår, `1` = kvartal, `2` = månad |

**POST till `vantapopup`:**

```
brottstyp_id_string = 13092*14024        (brotts-id, *-separerade)
region_id_string    = 8291*8338          (8291 = Hela landet)
period_id_string    = 2874*2878          (period-id; unika per år och månad)
fordelning_id_string=
antal               = 1
antal_100k          = 1                  (1 = även per 100 000 invånare)
```

**Resultat (`dbfil`):**

```
Region;Brott;År;Period;Antal;/100 000 inv
Hela landet;Befogenhetsbedrägeri;År;2025;14278;135;
Hela landet;0950 - Befogenhetsbedrägeri, …;2026 prel.;Aug;498;5;
```

- `..` betyder att uppgift inte är tillämplig. Resultatet ekar även **föräldranoderna** till valda brottstyper, och de har `..` som värde. `brastat` filtrerar bort dem och behåller bara valda brott.
- Samma etikett kan förekomma under flera föräldrar, t.ex. "Internationell anknytning". `brastat` lägger därför brott med samma etikett i **olika anrop**.
- Kolumnen `sokvag` i utdata anger var i trädet brottet ligger.
- Uttag över 10 000 celler delas upp per period.

Om urvalssidan svarar "En obefintlig menyrad har valts" saknas sessionen eller menyvalet. Klienten gör då om `start` och `urval`.

## bra.se – färdiga tabeller (`brastat/tabeller.py`)

Statistiksidorna har "StatSelector"-formulär. JavaScript bygger en URL:

```
/statistik_sidor/<kategori>/<år>/<prefix><område>-<period>.html   ->  innehåller länk /download/…/<fil>.xlsx
```

Exempel: `P4/2026/P4RegionAug-2026` (månadsserie per region), `100/2025/100La-2025` (årstabell hela landet), `220/2025/220La-2025` (misstänkta). Områdeskoder: `La` = hela landet, `Rn01`–`Rn07` = polisregionerna Nord, Mitt, Öst, Väst, Syd, Stockholm och Bergslagen.

Senaste tillgängliga månad och kvartal läses från formulärens `<select id="period_P1">` med flera. `scripts/inspect_forms.py` listar alla formulär och deras värden. Det behövs när nya tabeller ska läggas till.

Diagramdata på ämnessidorna ligger som JSON i `registerInitialState('…', {...chartData...})` och extraheras till CSV.

## TLS och certifikat

`brastat.http` använder operativsystemets certifikatlager via `truststore` om det är installerat, annars `certifi` eller Pythons standard. Om verifieringen ändå misslyckas, t.ex. med Homebrew- eller python.org-Python utan certifikat eller bakom en TLS-inspekterande proxy, går klienten automatiskt över till systemets `curl`. Det kan också tvingas med `BRASTAT_HTTP=curl`.

## Artighet

Klienten väntar 0,3 sekunder mellan anrop och identifierar sig med en tydlig User-Agent. En full hämtning av tabellerna tar cirka 4 minuter och en körning av bevakningslistan cirka 30 sekunder. Schemalägg inte oftare än en gång per dygn, eftersom månadsdata uppdateras en gång i månaden.
