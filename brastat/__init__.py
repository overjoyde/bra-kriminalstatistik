"""brastat – hämta och tolka offentlig kriminalstatistik från Brå (Brottsförebyggande rådet) och Domstolsverket.

Moduler:
    brastat.http     – enkel HTTP-klient (stdlib, cookies, artig fördröjning)
    brastat.sol      – klient för statistikdatabasen SOL (statistik.bra.se/solwebb)
    brastat.tabeller – hämtning av Brås färdiga Excel-tabeller, rapporter och metoddokument från bra.se
    brastat.domstat  – klient för Domstolsverkets statistikdatabas DOMstat (PxWeb-API)
"""
__version__ = "0.1.0"
