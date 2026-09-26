"""brastat – hämta och tolka offentlig kriminalstatistik från Brå (Brottsförebyggande rådet) och Domstolsverket.

Moduler:
    brastat.http     – enkel HTTP-klient (stdlib, cookies, artig fördröjning)
    brastat.sol      – klient för statistikdatabasen SOL (statistik.bra.se/solwebb)
    brastat.tabeller – hämtning av Brås färdiga Excel-tabeller, rapporter och metoddokument från bra.se
    brastat.domstat  – klient för Domstolsverkets statistikdatabas DOMstat (PxWeb-API)
    brastat.health   – hälsokontroll av hämtad data (fel, luckor, revideringar, certifikat)
    brastat.watchlist – gemensamt för bevakningslistorna (CSV, ögonblicksbilder)
    brastat.notify   – aviseringar (skrivbord, webhook, e-post)
    brastat.theme    – färgteman för matplotlib (samma paletter som HTML-dashboarden)
    brastat.cli      – kommandoradsverktygen (scripts/*.py och brastat-…-kommandona)
    brastat.analysis – tolkning av Brås Excel-tabeller, grafer och dashboards (kräver pandas)
"""

__version__ = "0.2.0"
