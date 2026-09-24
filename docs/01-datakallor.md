# Datakällor hos Brå

Brottsförebyggande rådet (Brå) publicerar Sveriges officiella kriminalstatistik. Repot hämtar från två ställen:

1. **Statistikdatabasen SOL**, "Gör din egen sökning", på <https://statistik.bra.se/solwebb/action/index>. Här gör man egna uttag av **anmälda brott** per brottstyp eller brottskod, område och period.
2. **bra.se**: färdiga Excel-tabeller, diagramdata på ämnessidor, rapporter och metoddokument.

All data är offentlig och aggregerad och innehåller inga personuppgifter. Den får vidareutnyttjas fritt enligt Brås villkor, men **Brå ska anges som källa**.

---

## 1. SOL – statistikdatabasen över anmälda brott

| Dimension | Innehåll |
|---|---|
| **Statistikområde** | Endast **anmälda brott**. Det är brott som anmälts till och registrerats av Polismyndigheten, Tullverket, Åklagarmyndigheten eller Ekobrottsmyndigheten. Underlaget kommer från databasen för officiell kriminalstatistik. |
| **Finns inte i SOL** | Handlagda brott, brottsmisstankar, misstänkta personer, lagförda personer och återfall. Dessa finns som färdiga tabeller på bra.se (avsnitt 2). |
| **Klassificering** | **Brottstyp:** hierarki med brottsbalkens kapitel först och sedan specialstraffrättsliga lagar. Rekommenderas för tidsserier. **Brottskod:** Polisens fyrsiffriga kod, som kan ange offer, plats och modus. Kräver att man vet vilka koder en brottstyp bygger på under olika perioder. |
| **Område** | Hela landet från 1975. Län 1975–2014. De **7 polisregionerna** från 2015. Kommuner från 1996. Stadsområden i Stockholm, Göteborg och Malmö från 2002. |
| **Period** | År från 1975. **Månad och kvartal från 1995.** |
| **Enhet** | Antal anmälda brott eller antal per 100 000 invånare |
| **Aktualitet** | Preliminär månadsstatistik publiceras med cirka **10 dagars fördröjning** och uppdateras varje månad. Den fryses och blir slutlig i **februari** året därpå. Skillnaden mellan preliminär och slutlig statistik har varit under 0,5 % totalt. |
| **Sekretess** | För kommuner och stadsområden redovisas bara ett fåtal brottstyper per månad eller kvartal. Månadsstatistik per brottskod visas inte på kommunnivå. |
| **Uttagsgräns** | Högst **10 000 dataceller** per sökning (brott × område × period × enhet). `brastat.sol` delar upp stora uttag automatiskt. |
| **Kommunstatistik** | Kommunsiffrorna bygger på brottsplats, medan regionsiffrorna bygger på var brottet handlagts. **Bedrägerier saknar ofta brottsplats** och har därför stort bortfall på kommunnivå. |

### Menyer (ingångar) i SOL

| Meny i `brastat` | menyid | Innehåll |
|---|---|---|
| `brottstyp-ar-region` | 98 | Brottstyp, år: land och län 1975–2014, land och polisregion 2015– |
| `brottstyp-ar-kommun` | 101 | Brottstyp, år: kommun och stadsområde 1996– |
| `brottstyp-manad-region` | 34 | Brottstyp, månad/kvartal: land och region |
| `brottstyp-manad-kommun` | 90 | Brottstyp, månad/kvartal: kommun (sekretessbegränsad) |
| `brottskod-ar-region` | 104 | Brottskod, år: land och region |
| `brottskod-ar-kommun` | 107 | Brottskod, år: kommun och stadsområde |
| `brottskod-manad-region` | 46 | Brottskod, månad/kvartal: land och region |

### Omfattning (uttag 2026-09-24)

- **Brottstyp-trädet** har 117 grupper och cirka 1 360 valbara brottstyper. Dessa kan vara uppdelade efter ålder, kön, relation, internetrelaterat, internationell anknytning och "mot äldre/funktionsnedsatt". Se [`reference/brottstyper_sol.csv`](../reference/brottstyper_sol.csv).
- **Brottskoder:** 1 361 koder, inklusive upphörda koder. Se [`reference/brottskoder_sol.csv`](../reference/brottskoder_sol.csv). Kodgrupperna är 03, 04, 05–07, 08, **09 (bedrägeri)**, **10–19 (bl.a. förskingring, borgenärsbrott och förfalskning)**, 20–51, 61–69 och **70–98 (bl.a. penningtvätt, terrorism, sanktioner och dataintrång)**.
- Urval för AML/CTF och bedrägeri: se [02-brottskoder-aml-ctf-bedrageri.md](02-brottskoder-aml-ctf-bedrageri.md).

---

## 2. bra.se – färdiga tabeller, diagramdata och rapporter

Hämtas med `scripts/fetch_tables.py`. Filerna hamnar i `data/raw/`, PDF:erna i `data/docs/` och varje fil loggas i `data/manifest.csv`.

| Grupp (`--groups`) | Katalog i `data/raw/` | Innehåll | Typisk användning |
|---|---|---|---|
| `anmalda` | `anmalda_brott/tidsserie_manad/` | P4: anmälda brott per månad. Landet 2015–, polisregioner 2022– | **Huvudindikator.** Annons-, befogenhets-, romans-, investerings-, faktura- och identitetsbedrägeri, social manipulation, kort utan fysiskt kort, penningtvättsbrott. Ofta uppdelat på "mot äldre/funktionsnedsatt". |
| `anmalda` | `anmalda_brott/prel_P1M_manad/`, `prel_P3_utveckling/`, `prel_kvartal/` | Senaste månad eller kvartal, förändring mot föregående år och brott per 100 000 invånare per region | Månadsuppföljning |
| `anmalda` | `anmalda_brott/ar_100_landet/`, `ar_110_regioner/` | Slutlig årsstatistik de senaste 10 åren | Nivåer och säsongsbaslinje |
| `anmalda` | `anmalda_brott/ar_120_kommuner/` | Kommunnivå de senaste 3 åren per polisregion | Geografiska hotspots |
| `anmalda` | `anmalda_brott/tidsserier_och_kommun/` | 10-årsserier, serier från 1950, kommun-CSV | Lång trend |
| `misstankta` | `misstankta/` | Tabell 220 (brottstyp × ålder × kön), 230a/b (lagföringsbeslut) samt 10-årsserier | Åldersprofil, t.ex. unga som målvakter (money mules) |
| `lagforda` | `lagforda/` | Tabell 420/450/460 samt serier från 1975 | Hur penningtvätts- och bedrägeriärenden slutar |
| `handlagda` | `handlagda/`, `handlaggningsresultat/` | Tabell 300/310/320, halvår innevarande år, uppklaring | Låg uppklaring som motiv för förebyggande kontroller |
| `malsagare` | `malsagare/` | Målsägare per år och tidsserie | Offrens ålder och kön |
| `enkater` | `ntu/`, `skolundersokningen/` | NTU-tabellsamling 2007– (län, socioekonomiska områden) och Skolundersökningen om brott | Utsatthet inklusive oanmälda brott (försäljnings-, kort- och kreditbedrägeri) |
| `amnessidor` | `amnessidor/` | Diagramdata från ämnessidorna *Bedrägeri* och *Penningtvätt och finansiering av terrorism* (extraherad till CSV) | Snabböversikt, bl.a. finansiering av terrorism |
| `rapporter` | `data/docs/rapporter/` | *Företag som brottsverktyg* (2025), *Brottsutvecklingen i Sverige 2006–2024*, *Bedrägerier mot privatpersoner* (2023:11), *Penningtvättsbrott* (2019:17), *Finansiering av terrorism* (2021:6), *Penningtvätt och annan penninghantering* (2015), *Bostadsrättsföreningars utsatthet* (2026), NTU 2025 | Modus och kvalitativ kontext |
| `metod` | `data/docs/metod/` | Begrepp och definitioner, kvalitetsdeklarationer och statistikrapporter | **Läs innan tolkning**, eftersom brottskoder ändras och bryter serier |

Övriga källor som **inte** automatiseras: NTU:s "Skapa din egen tabell" och specialbeställningar via statistik@bra.se.

Domstolsledet (brottmål, handläggningstider, konkurser, skuldsanering) hämtas från Domstolsverkets DOMstat, se [04-domstolsverket-domstat.md](04-domstolsverket-domstat.md).

---

## 3. Förbehåll vid tolkning

- **Anmälningar är inte faktisk brottslighet.** Bedrägeri räknas som seriebrott, så ett enda ärende kan ge stora toppar i en månad eller region.
- **Brottskoderna anger inte betalmedel.** Kopplingen till en viss betaltjänst är alltid indirekt, via modus.
- **Månadsdata är preliminär** (märkt "prel") och revideras i den slutliga årsstatistiken i februari.
- **Serierna bryts när koder ändras.** Exempel: ny bedrägeriindelning 2019, penninghäleri ersatt av penningtvättslagen 2014, ny terroristbrottslag 2023, ny sanktionslag och subventionsbrottslag 2025/2026, ny indelning av människohandel 2025.
- Jämför bara med egen data på **aggregerad nivå**.
