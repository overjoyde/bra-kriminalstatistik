# Ändringslogg

Formatet följer [Keep a Changelog](https://keepachangelog.com/sv/1.1.0/) och versionerna [semantisk versionering](https://semver.org/lang/sv/). Versionsnumret finns i `brastat/__init__.py` och varje version taggas `vX.Y.Z` i git.

## [0.2.0] – 2026-09-26

### Tillagt
- `pyproject.toml`: paketet installeras med `pip install -e .`. Beroenden finns som extras (`analysis`, `export`, `dev`) och verktygen som kommandon (`brastat-fetch-all`, `brastat-health`, `brastat-sol-query` m.fl.).
- `requirements.lock`: låsta versioner för alla plattformar och Python 3.10+ (`uv pip compile --universal`), som setup-skripten och CI installerar.
- **Hälsokontroll** (`check_health.py`, körs sist i `fetch_all`):
  - fel i manifestet, saknade eller tomma filer och grupper där allt misslyckats
  - inaktuell data
  - serier som försvunnit sedan förra körningen, och slutliga värden som reviderats
  - mellancertifikat som snart går ut
- **Aviseringar** vid fel (`--notify`, används av de schemalagda körningarna): skrivbord, webhook och e-post, konfigurerat med miljövariabler.
- **Ögonblicksbilder** av bevakningslistorna (`watchlist_samlad.prev.csv` och `snapshots/*.csv.gz`), för att följa revideringar.
- **Livetest** mot SOL, DOMstat och bra.se (`smoke_live.py`), som körs varje vecka i GitHub Actions.
- **DOMstat i grafer och dashboard**: graf 08 (insolvensärenden och brottmål i tingsrätt jämfört med anmäld penningtvätt) och en DOMstat-panel i HTML-dashboarden.
- **Export** till Parquet och DuckDB (`export_data.py`).
- Loggning via `logging`: tidsstämplar i schemalagda körningar, `-v`/`-q`.
- CI:
  - ruff (lint + format av kärnbiblioteket) och mypy
  - Python 3.10–3.14
  - körskripten testas på Windows, macOS och Linux, inklusive setup från låsfilen
  - veckovis test mot de senaste beroendena
  - månatlig PR med uppdaterad låsfil
  - Dependabot för actions
  - `.pre-commit-config.yaml`
- Tester: från 20 till över 80, bland annat dashboardbyggen från fixturer, hälsokontroll, aviseringar och kommandon.

### Ändrat
- Koden har flyttat in i paketet: `brastat/cli/` (kommandon), `brastat/analysis/` (tolkning, grafer, dashboards, HTML-mall i `templates/`) och `brastat/config/` (bevakningslistor). `scripts/*.py` finns kvar som tunna skal, så befintliga kommandon och körskript fungerar som förut. `sys.path`-hacket (`_bootstrap.py`) är borttaget.
- Datakatalogen läses först när den behövs. Vid vanlig installation (inte `-e`) används användarens datakatalog i stället för site-packages.
- Beroendena har övre versionsgränser, och numpy är nu uttryckligen deklarerat.
- curl-reserven skickar anropskroppen via en temporär fil i stället för stdin, och städar sina temporära filer.
- Actions är pinnade till commit-SHA, och arbetsflödena har minsta möjliga rättigheter.
- Om en serie misslyckas i en bevakningslista behålls dess rader från förra körningen, i stället för att den samlade filen tappar serien.

### Rättat
- `annual_table` kraschade när en serie saknades i datan.
- `select_years("senaste:0")` gav alla år, och ett årsurval utan träff gav en tom fråga. Båda ger nu `ValueError`.

## [0.1.0] – 2026-09-25

Första versionen: SOL-klient, tabellhämtare för bra.se, AML/CTF-kodkatalog, DOMstat-klient och bevakningslistor, exempelgrafer, Excel- och HTML-dashboard (med mörkt tema) samt körskript och schemaläggning för macOS, Linux och Windows. Färgteman för grafer, även i notebooks (`brastat.theme`, PR #4).

[0.2.0]: https://github.com/overjoyde/bra-kriminalstatistik/compare/021a823...v0.2.0
[0.1.0]: https://github.com/overjoyde/bra-kriminalstatistik/tree/021a823
