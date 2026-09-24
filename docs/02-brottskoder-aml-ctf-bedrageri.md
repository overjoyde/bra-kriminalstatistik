# Brottstyper & brottskoder – AML/CTF & bedrägeri

> **Syfte**  
> Sidan samlar de brottstyper och fyrsiffriga brottskoder i Brås SOL-databas som rör **penningtvätt, terrorfinansiering, sanktioner, bedrägeri och närliggande predikatbrott**. Den ska fungera som uppslagsverk när Brå-statistik ska kopplas till typologier för penningtvätt, terrorfinansiering och bedrägeri, t.ex. i transaktionsövervakning. Alla koder är hämtade från SOL:s kodlista 2026-09-24. Se [01-datakallor.md](01-datakallor.md) för dataunderlaget och [`reference/brottskoder_sol.csv`](../reference/brottskoder_sol.csv) för alla koder. Uppdatera listorna med `python scripts/sol_catalog.py`.

## Så läser du tabellerna

- **Brottstyp** är den aggregerade nivån, t.ex. "9 kap. Bedrägeri". Den bygger på en eller flera brottskoder, och vilka koder som ingår kan ändras mellan år. Använd brottstyp för tidsserier.
- **Brottskod** är Polisens fyrsiffriga klassificering. Koden kan också ange offer, plats och modus. Använd koder när du behöver en finare uppdelning än brottstypen ger, och kontrollera då kodens giltighetsår.
- **SOL-id** är SOL:s interna id för brottstypsnoden. Det är bara användbart för automatiserade uttag och kan ändras.
- *Upphörd* betyder att koden eller typen finns kvar historiskt men inte används för nya anmälningar.
- Modusrutnätet för bedrägeri från 2019 följer ett fast mönster med fyra koder i följd:
  1. internationell anknytning, mot äldre/funktionsnedsatt
  2. ej internationell anknytning, mot äldre/funktionsnedsatt
  3. internationell anknytning, ej mot äldre/funktionsnedsatt
  4. ej internationell anknytning, ej mot äldre/funktionsnedsatt

> **Viktigt**  
> Koderna säger **inget om betalmedel**. "Befogenhetsbedrägeri" kan ha gått via direktbetalning, kort eller kontanter. Kopplingen till en viss betaltjänst är alltid en **hypotes om modus**, inte en observation. Typologikolumnerna i tabellerna är analytiska antaganden och ska inte läsas som fastställda samband.

---

## 1. Penningtvätt (AML – kärnbrott)

Lag (2014:307) om straff för penningtvättsbrott. Brottstyp **"Lag om straff för penningtvättsbrott"** (SOL-id 13092).

| Kod | Brott | Brottstyp (SOL-id) | Typologi (hypotes) |
|---|---|---|---|
| 5121 | Penningtvättsbrott (3–4 §) | 13093 | Penningflöden via målvaktskonton (money mules) |
| 5122 | Grovt penningtvättsbrott (5 §) | 13094 | Money mules, organiserad penningtvätt |
| 5123 | Penningtvättsförseelse (6 §) | 13095 | Målvakter och unga som lånar ut konton |
| 5124 | Näringspenningtvätt (7 §) | 13096 | Företag som brottsverktyg (tar emot och slussar vidare) |
| 5125 | Grov näringspenningtvätt | 13096 | Företag som brottsverktyg |
| 5126 | Ringa näringspenningtvätt | 13096 | Företag som brottsverktyg |

**Historiskt och närliggande (9 kap. BrB)**

| Kod | Brott | Kommentar |
|---|---|---|
| 0933 / 0934 | Penninghäleri / penninghäleriförseelse | Upphörde 2014. Ersattes av penningtvättslagen. Behövs för serier före 2014-07 (brottstyp 13098). |
| 0930 / 0931 | Häleri: tillfälligt / vanemässigt eller stor omfattning | Brottstyp 11577 och 11579 |
| 0999 | Utförselhäleri inkl. grovt (9:6 a) | Brottstyp 14899. Stöldgods som förs ut ur landet. |
| 0996 | **Olovlig befattning med betalningsverktyg** (9:3 c) | Brottstyp 14598. Handel med kortuppgifter och inloggningar. Nära mule- och kontoövertagande. |

## 2. Terrorism och terrorfinansiering (CTF)

Terroristbrottslag (2022:666), gäller **från 2023**. Brottstyp **"Terroristbrottslag (fr.o.m. 2023)"** (SOL-id 14612).

| Kod | Brott | Typologi |
|---|---|---|
| **7035** | **Finansiering för att begå eller medverka till terroristbrott** | CTF, direkt relevant |
| **7036** | **Finansiering av annan särskilt allvarlig brottslighet** | CTF |
| **7037** | **Finansiering av terroristorganisation, eller person/sammanslutning som begår terroristbrott eller särskilt allvarlig brottslighet** | CTF, t.ex. insamlingar via betalnummer eller konton |
| 7029–7033 | Terroristbrott, försök, förberedelse, stämpling, underlåtenhet att avslöja | Kontext |
| 7034 | Samröre med en terroristorganisation | Kontext |
| 7038–7042 | Offentlig uppmaning, rekrytering, ge eller ta del av utbildning, resa för terrorism | Kontext. Resor kan förekomma i transaktionsmönster. |
| 7043 | Deltagande i en terroristorganisation | Kontext |

**Upphörda koder (för serier före 2023)**

| Kod | Brott | Upphörde |
|---|---|---|
| 7002–7007 | Terroristbrott, försök, förberedelse (7004 = **genom finansiering**), stämpling, underlåtenhet | 2023 |
| 7008–7010, 7020–7021 | Uppmaning, rekrytering, utbildning, resa | 2023 |
| 7011, 7013 | Insamling av medel för terroristbrott / annan särskilt allvarlig brottslighet | 2016 |
| 7012, 7022–7025, 7027 | Insamling, tillhandahållande och mottagande av medel (olika syften) | 2023 |
| 7026 | Samröre med terroristorganisation | 2023 |
| 5050 | Insamling av medel för att finansiera särskilt allvarlig brottslighet | 2016 |

Äldre brottstyper: 13175 (terroristbrott t.o.m. 2022), 13176 (uppmaning/rekrytering/utbildning t.o.m. 2022-06) och 11850 (lag om straff för finansiering av särskilt allvarlig brottslighet t.o.m. 2022).

> **Volymer**  
> CTF-koderna har mycket få anmälningar per år. De fungerar som kontext för riskbedömning och är för små för trendsignaler eller modellkalibrering.

## 3. Sanktioner

| Kod | Brott | Brottstyp (SOL-id) | Kommentar |
|---|---|---|---|
| 7045 | Sanktionsbrott inkl. grovt | 14903 (lag om internationella sanktioner 3–5, 8 §§) | Ny lag 2025 |
| 7046 | Sanktionsförseelse | 14903 | |
| 7047 | Upprepat sanktionsbrott | 14903 | |
| 7014–7016 | Brott mot föreskrift som genomför internationella sanktioner | 13177 (t.o.m. 2025) | Upphörde 2025. Serien bryts. |

## 4. Bedrägeri (9 kap. BrB) – fraud

Brottstyp **"9 kap. Bedrägeri och annan oredlighet"** (SOL-id 11096) → **"Bedrägeri inkl. grovt, bedrägligt beteende (1–3 §)"** (11563).

### 4a. Modusindelning från 2019 (huvudnivå för trendbevakning)

| Brottstyp (SOL-id) | Koder | Modus | Typologi (hypotes) |
|---|---|---|---|
| **Bedrägeri genom social manipulation** (14021) | | | |
| ↳ Romansbedrägeri (14022) | 0942–0945 | Relation byggs upp och offret förmås betala | Offer → målvakt → vidare; upprepade betalningar |
| ↳ Investeringsbedrägeri (14023) | 0946–0949 | Falska investeringar och krypto | Företag som brottsverktyg, money mules |
| ↳ **Befogenhetsbedrägeri** (14024) | 0950–0953 | Gärningspersonen utger sig för att vara bank eller polis, ofta mot äldre | **Money mules**. Klassiskt APP-modus (e-legitimation och "säkert konto"). |
| ↳ Annan typ (14025) | 0954–0957 | Övrig social manipulation | Money mules |
| **Identitetsbedrägeri** (14026) | | | |
| ↳ Köp (14038) | 0958–0961 | Köp i annans namn | Identitetsmissbruk |
| ↳ Lån (14040) | 0962–0965 | Lån och kredit i annans namn | Identitetsmissbruk, företag |
| ↳ Annan typ (14042) | 0966–0969 | | Identitetsmissbruk |
| **Fakturabedrägeri** (14027) | | | |
| ↳ Med kontakt (14039) | 0970–0973 | Bluffaktura efter kontakt | Företag som mottagare |
| ↳ Utan kontakt (14045) | 0974–0977 | Bluffaktura utan kontakt | Företag som brottsverktyg |
| **Kortbedrägeri** (14028) | | | |
| ↳ Med fysiskt kort (14048) | 0978–0981 | | Förflyttning mellan betalmetoder |
| ↳ Utan fysiskt kort (14050) | 0982 (int.), 0983 (ej int.) | Kortuppgifter online (ingen uppdelning på äldre) | Jämförelse: kort vs social manipulation |
| **Annonsbedrägeri** (14029) | 0984–0987 | Blocket/Marketplace m.m. | **Identitetsmissbruk**, money mules (många små mottagna betalningar) |
| Försäkringsbedrägeri (14030) | 0988 | | Låg |
| Snyltningsbrott (14031) | 0989 | | Låg |
| Grovt fordringsbedrägeri (14032) | 0990 (int.), 0991 (ej int.) | | Företag som brottsverktyg |
| Övrigt bedrägeri (14033) | 0992–0995 | | Kontext |
| Lönegarantibedrägeri (14716) | 0997 | | Företag som brottsverktyg (konkursbolag) |
| Bedrägeri mot EU:s finansiella intressen (14717) | 0998 | | Låg |

### 4b. Äldre indelning (brottstyperna redovisas t.o.m. 2018)

| Kod | Brott | Brottstyp (SOL-id) |
|---|---|---|
| 0901 | Datorbedrägeri | 11565 |
| 0902 | Automatmissbruk | 11564 |
| 0904 | Bedrägeri med kontokort | 11566 |
| 0913 | Bedrägeri med hjälp av internet | 11567 |
| 0935 | Investeringsbedrägeri | 11568 |
| 0912 | Bedrägeri/bedrägligt beteende avseende bluffakturor | 11574 |
| 0932 | Överskridit eget konto | 11569 |
| 0929 | Mot försäkringsbolag | 11570 |
| 0903 | Mot hotell, restaurang, transport | 11573 |
| 0905 | Mot funktionsnedsatt | – |
| 0906 | Övrigt bedrägeri | 11576 |
| 0914 | Mot EU:s finansiella intressen | 11571 |
| 0922 | Annan checkbedrägeri | – |

> **Serier över 2019**  
> Det finns ingen exakt nyckel mellan den gamla och den nya indelningen. En rimlig uppskattning är: 0913 + 0901 ≈ social manipulation + annonsbedrägeri + kort utan fysiskt kort, och 0904 ≈ kort med fysiskt kort. Använd hellre toppnivån 11563 för långa serier och modusnivån från 2019 och framåt.

### 4c. Övriga brott i 9 kap. med AML-relevans

| Kod | Brott | Brottstyp (SOL-id) | Kommentar |
|---|---|---|---|
| 0940 | Utpressning (9:4) | 13060 | T.ex. sextortion och ransom. Se även 9465. |
| 0941 | Ocker (9:5) | 13061 | |
| 0996 | Olovlig befattning med betalningsverktyg (9:3 c) | 14598 | Se avsnitt 1 |
| 0916 | Subventionsmissbruk | 12987 | Upphörde 2026, ersatt av subventionsbrottslagen (se 6) |
| 0915 | Övriga brott mot 9 kap. | 11581 | |

## 5. Identitet, dataintrång och förfalskning (möjliggörare för bedrägeri)

| Kod | Brott | Brottstyp (SOL-id) | Typologi |
|---|---|---|---|
| 0480–0483 | **Olovlig identitetsanvändning** (4:6 b), per kön/ålder | 13184 | Identitetsmissbruk |
| 0415 | Dataintrång (4:9 c) | 11337 | Kontoövertagande |
| 9464 | Dataintrång genom överbelastningsattack | 14492 | |
| 9465 | Dataintrång med skadlig kod i utpressningssyfte | 14493 | Ransomware-betalningar |
| 9466 | Dataintrång genom olovlig registerslagning | 14494 | Insiderläckage |
| 9467 | **Dataintrång i sociala medier eller e-tjänster** | 14495 | Kontoövertagande (e-legitimation/e-tjänst) |
| 9468 | Övrigt dataintrång | 14496 | |
| 1404 / 1405 | Förfalskning av tjänste-/id-kort respektive annan legitimationshandling | 11610, 11612 | Identitetsmissbruk, falska identiteter |
| 1406 | Övrig urkundsförfalskning | 11613 | Falska fakturor och intyg (företag som brottsverktyg) |
| 1407 | Signaturförfalskning | 11614 | |
| 1408 | Penningförfalskning | 11615 | |
| 1401 | Förfalskning av check | 11609 | Låg |
| 1410 | Förfalskade handlingar för illegal invandring | 11611 | Människosmuggling |

## 6. Ekonomisk brottslighet och företag som brottsverktyg

| Kod | Brott | Brottstyp (SOL-id) | Kommentar |
|---|---|---|---|
| — | **Brott mot bulvan- och målvaktsbestämmelser** (ABL 30:1 3 st.) | **13118** | Finns bara som brottstyp. Direkt kopplat till målvaktsbolag. |
| 5038 | Övriga brott mot aktiebolagslagen | 13115 | (5031 upphörde 2011) |
| 5030 | Överträdelse av näringsförbud | 13113 | Företrädare som kör vidare via bulvan |
| 1111 | Oredlighet mot borgenärer inkl. grov | 11588 | Konkursbolag och tömning av bolag |
| 1112 / 1113 / 1115 | Vårdslöshet mot, mannamån mot borgenärer respektive försvårande av konkurs | 11590, 11591, 11589 | |
| 1122 / 1125 | Grovt bokföringsbrott, konkurs / ej konkurs | 11592 | |
| 1126–1133 | Bokföringsbrott (ringa/normal × konkurs/ej konkurs × årsredovisning/övrigt) | 11592 | Ny indelning. 1114 och 1120–1124 har upphört. |
| 1001 | Förskingring inkl. grov, undandräkt | 11582 | |
| 1007 | Trolöshet mot huvudman | 11584 | |
| 1010 | Behörighetsmissbruk | 11587 | |
| 1012–1015 | Tagande och givande av muta inkl. grov (utländska tjänstemän eller ej) | 13031, 13032 | Korruption som predikatbrott. 1708 och 2003 upphörde 2025. |
| 1011 | Handel med inflytande, vårdslös finansiering av mutbrott | 13033 | |
| 5020–5026 | Skattebrottslagen: moms, övrigt, vårdslös uppgift, försvårande av kontroll, skatteavdrag, grovt | 13105 | Predikatbrott |
| 5088–5099 | Skattebrott och grovt skattebrott: moms inom landet/gränsöverskridande, oriktig uppgift m.m. | 13107, 13106 | Ny indelning 2024/2025 (5090 och 5093 upphörde 2025) |
| 5060–5075 | Bidragsbrott mot Försäkringskassan, kommuner, a-kassor och övriga myndigheter (ringa/normal/grovt/vårdslöst) | 11689 (11690–11693) | Välfärdsbrott, utbetalningar som slussas vidare |
| 5131–5133 | Subventionsbrott och subventionsmissbruk med företagsstöd / EU-stöd | 14963 (14964–14966) | Ny lag (2025:1267) |
| 5083 | Folkbokföringsbrott inkl. grovt | 13926 | Falska adresser och identiteter |
| 5078–5080 | Insiderbrott, grovt insiderbrott, obehörigt röjande | 5066 (5067–5069 inkl. marknadsmanipulation) | Låg relevans för betalflöden |

## 7. Predikatbrott med AML-relevans (utöver ovan)

| Område | Koder | Brottstyp (SOL-id) | Typologi |
|---|---|---|---|
| **Olovligt spel** | 4082 olovlig spelverksamhet, 4083 främjande av olovligt spel, 4084 spelfusk | 13922 (13923–13925) | Flöden till spelbolag |
| **Människohandel** | 9512–9551 (ändamål × offer: sexuella, tvångsarbete, tiggeri, organ, krigstjänst, brottslig verksamhet, surrogat, tvångsäktenskap, adoption, övrigt) | 11298 | Ny indelning 2025. Äldre koder 0416–0421 och 0470–0479 har upphört. |
| **Människoexploatering** | 0493–0496 (tvångsarbete/orimliga villkor, tiggeri) | 5225 | Arbetskraftsexploatering |
| **Koppleri** | 0609 | 11779 | Sexköpsflöden |
| **Utnyttjande av barn** (köp av sexuell handling, sexuell posering) | 0610, 6153/6154 | 11771, 11770 | Betalningar för sexuella övergrepp mot barn |
| **Människosmuggling** | 4025, 4026 (organiserande) | 11720 (utlänningslagen) | |
| **Smuggling** | 4055–4060 (alkohol/tobak, vapen, övrigt), 4101–4106, 4133–4142 (vapen och grov narkotikasmuggling), 4046 | 11694 | Predikatbrott |
| **Narkotika** | (narkotikastrafflagen, många koder) | 11650 | Största predikatbrottet i volym. Hämtas vid behov från fullständiga listan. |

---

## Snabbval: rekommenderade serier för trendbevakning (finns i `config/watchlist_aml_fraud.json`)

| Signal | Välj i SOL | Nivå |
|---|---|---|
| Social manipulation totalt | Brottstyp 14021 | Månad, land och region |
| Befogenhetsbedrägeri mot äldre | Koder 0950 + 0951 | Månad, land och region |
| Romansbedrägeri | Brottstyp 14022 | Månad |
| Annonsbedrägeri | Brottstyp 14029 | Månad |
| Identitetsbedrägeri | Brottstyp 14026, samt olovlig identitetsanvändning 13184 | Månad |
| Fakturabedrägeri | Brottstyp 14027 | Månad |
| Kort utan fysiskt kort | Brottstyp 14050 | Månad (jämförelse med betalmetodsförflyttning) |
| Penningtvätt totalt | Brottstyp 13092 | Månad och år |
| Näringspenningtvätt | Koder 5124–5126 | År |
| Olovlig befattning med betalningsverktyg | Kod 0996 | År och månad |
| Terrorfinansiering | Koder 7035–7037 (+ 7004, 7011–7013, 7022–7025 före 2023) | År, land |
| Sanktionsbrott | 7045–7047 (+ 7014–7016 före 2025) | År, land |
| Målvakts- och bulvanbolag | Brottstyp 13118 + näringsförbud 13113 | År |

## Källor
- Brå SOL, "Gör din egen sökning": <https://statistik.bra.se/solwebb/action/index>. Kodlista och brottstypsträd hämtade 2026-09-24.
- Brå, *Klassificering av brott* (regler för brottskoderna) och *Kvalitetsdeklaration anmälda brott* (RV0102). Hämtas till `data/docs/metod/` med `python scripts/fetch_tables.py --groups metod`.
- Brå-rapporter (hämtas till `data/docs/rapporter/` med `--groups rapporter`): *Penningtvättsbrott* (2019:17), *Finansiering av terrorism* (2021:6), *Bedrägerier mot privatpersoner* (2023:11), *Företag som brottsverktyg* (2025:20).
