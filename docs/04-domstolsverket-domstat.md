# Domstolsverkets statistikdatabas (DOMstat)

[DOMstat](https://pxweb.etjanst.domstol.se/PxWeb/pxweb/sv/DOMstat/) är Sveriges Domstolars officiella statistik (SOS) över mål och ärenden. Den kompletterar Brå: Brå beskriver **anmälda, misstänkta och lagförda brott**, DOMstat beskriver **domstolsledet**, alltså hur många brottmål som kommer in till och avgörs i domstolarna, hur lång tid det tar och hur ofta domar ändras. Dessutom finns **konkurser, företagsrekonstruktioner och skuldsaneringar**, som är relevanta för *företag som brottsverktyg* och för ekonomisk utsatthet.

## Vad finns – och vad finns inte?

Genomgång 2026-09-25: **69 tabeller i 15 mappar**, alla med **årsdata** (som längst 2002–2025) och uppdelade per domstol.

| Mapp | Innehåll | Relevans för bedrägeri/AML |
|---|---|---|
| Antal mål (`AntalMal`) | Inkomna, avgjorda och balanserade mål per domstolsslag och per domstol och målkategori (tingsrätt, hovrätt, HD, förvaltningsdomstolar, hyresnämnder). **Tabell 02b: konkursärenden, företagsrekonstruktioner, skuldsanering, utsökning. Tabell 09: konkurser per tingsrätt.** | ⭐⭐⭐ Brottmålsvolymer och insolvens |
| Mark- och miljö, Patent- och marknad, Migration | Motsvarande för specialdomstolarna | – |
| Avgörandetyp, Bemanning | Dom/beslut/tredskodom, nämnd/ensam domare | ⭐ |
| Snabbare lagföring (`Snabbspar`) | Mål inom snabbspåret och tider brott→dom (2024–) | ⭐⭐ |
| Ungdomsmål | Avgjorda mål med tilltalade 15–17 och 18–20 år, handläggningstider | ⭐⭐ Unga som målvakter/money mules |
| Familjemål | Äktenskapsskillnad, vårdnad | – |
| Förhandling | Huvudförhandlingar (även >18 h), häktningsförhandlingar, inställda förhandlingar med orsak | ⭐⭐ Långa förhandlingar ≈ komplexa mål, t.ex. ekobrott och organiserad brottslighet |
| Förtursmål | Mål med häktad eller minderårig | ⭐ |
| Prövningstillstånd (PT) | Beviljade/ej beviljade PT per domstol och kategori | ⭐ |
| Verksamhetsmål | Handläggningstid (75/90-percentil i månader) | ⭐⭐ Hur lång tid lagföringen tar |
| Ålder i balanserade mål | Mål i balans äldre än 6/12/24 månader | ⭐⭐ |
| Överklagande | Överklagande- och ändringsfrekvens, även per part (åklagare/tilltalad) i brottmål | ⭐ |

**Begränsningar att känna till**

- **Ingen uppdelning per brottstyp eller brottskod.** Brottmål är en enda målkategori. För penningtvätt, bedrägeri etc. per brott används Brås lagföringsstatistik (`fetch_tables.py --groups lagforda`) och SOL.
- **Bara årsdata**, uppdaterad en gång per år (februari–mars). Månadsbevakning är inte möjlig.
- Uppdelning per **domstol**, inte per kommun eller polisregion. Domstolsområden följer inte polisregionerna.
- Symboler: `-` = noll (sparas som 0), `.` = kan inte förekomma, t.ex. när en tingsrätt inte fanns (sparas som tomt). Tingsrättssammanslagningar bryter serierna per domstol – använd "Alla tingsrätter" för långa tidsserier.

## Så används den tillsammans med Brå

| Fråga | Kombination |
|---|---|
| Hinner rättsväsendet med? | Brå: anmälda/lagförda brott → DOMstat: inkomna vs avgjorda brottmål, balans och balansålder |
| Hur lång tid tar det från brott till dom? | DOMstat: `Verksamhetsmal` + `Snabbspar` (brottsdatum→dom) |
| Ökar konkurser i samma regioner som fakturabedrägeri och näringspenningtvätt? | DOMstat: konkurser per tingsrätt + Brå/SOL: kod 5124–5126 och fakturabedrägeri per region |
| Ekonomisk utsatthet hos privatpersoner | DOMstat: skuldsanering (tabell 02b) + Brå: bedrägerier mot äldre |
| Unga i lagföringen | DOMstat: ungdomsmål 15–20 år + Brå tabell 220: misstänkta 15–24 år för penningtvätt |

## Hämtning

DOMstat har ett öppet **PxWeb-API** (v1), så här behövs ingen skrapning som för SOL:

```bash
# Bevakningslistan (17 serier, ~40 s) -> data/domstat/watchlist_samlad.csv
python scripts/domstat_watchlist.py

# Sök tabeller och visa variabler/värden
python scripts/domstat_catalog.py --search konkurs
python scripts/domstat_catalog.py --table AntalMal/02b_Malutveckling_per_malkategori_arenden_TR

# Exportera hela katalogen -> data/domstat/katalog/tabeller.csv + variabler.csv (~2 min)
python scripts/domstat_catalog.py

# Eget uttag
python scripts/domstat_query.py --table AntalMal/09_Konkurser_TR --years 2015-
python scripts/domstat_query.py --table AntalMal/02a_Malutveckling_per_malkategori_TR \
    --select "Domstol=Alla tingsrätter" "Målkategori=Brottmål" --years senaste:5 --out -
```

`--select` anges med DOMstat:s **svenska texter** (skiftlägesokänsligt, ett unikt delord räcker, t.ex. `Domstol=Attunda`). Variabler som inte väljs hämtas i sin helhet. `domstat_watchlist.py` körs också av `fetch_all.py` (hoppa över med `--no-domstat`).

**Format** (CSV, semikolon, UTF-8 med BOM), samma långa format oavsett tabell:

```text
serie;kategori;tabell;tabell_titel;domstol;dimension;dimensionsvarde;variabel;ar;varde;symbol
konkurser_tingsratt;Insolvens – företag som brottsverktyg;AntalMal/09_Konkurser_TR;09. Inkomna, …;Alla tingsrätter;;;Antal inkomna konkursärenden;2025;14632.0;
```

`dimension`/`dimensionsvarde` är tabellens eventuella extra indelning (t.ex. *Målkategori = Brottmål* eller *Ungdomskategori = varav 15-17 år*). För tabeller utan variabeldimension (t.ex. verksamhetsmål) står tabellens titel i `variabel`.

### Teknik (`brastat/domstat.py`)

- `GET  …/api/v1/sv/DOMstat/<mapp>` listar mappar och tabeller, `GET …/<tabell>.px` ger metadata, `POST …/<tabell>.px` med `{"query": [...], "response": {"format": "json"}}` ger data.
- Värdekoderna i just denna databas är **engelska etiketter** (t.ex. `All district courts`) och årskoderna är **löpnummer** (`"0"` = 2002). Klienten översätter alltid via metadatan, så använd de svenska texterna och lita inte på koderna.
- Anropsgräns enligt `…/api/v1/sv/?config`: **10 anrop per 10 sekunder** och högst 100 000 celler per uttag. Klienten väntar 1,1 s mellan anrop och respekterar `Retry-After` vid HTTP 429. Största tabellen är ca 39 000 celler, så ett uttag räcker alltid.

## Licens och källa

Statistiken ingår i Sveriges officiella statistik och får vidareutnyttjas. Ange *Källa: Domstolsverket* när du publicerar.
