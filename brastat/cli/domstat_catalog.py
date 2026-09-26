#!/usr/bin/env python3
"""Lista tabeller och variabler i Domstolsverkets statistikdatabas DOMstat (PxWeb-API).

Exempel:
    python scripts/domstat_catalog.py                      # exportera katalogen -> data/domstat/katalog/
    python scripts/domstat_catalog.py --search brottmål    # sök i tabellnamn (skriver inga filer)
    python scripts/domstat_catalog.py --table AntalMal/09_Konkurser_TR   # visa variabler och värden

Exporten ger två CSV:er: tabeller.csv (en rad per tabell) och variabler.csv (en rad per
variabelvärde, dvs. exakt de svenska texter som kan användas i domstat_query.py/--select).
"""
import argparse
import csv
import logging

from brastat import log as blog
from brastat.domstat import DomstatClient
from brastat.paths import data_dir

log = logging.getLogger("brastat.domstat_catalog")


def write_csv(path, header, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(header)
        w.writerows(rows)
    log.info("  + %s (%d rader)", path, len(rows))


def show(dom: DomstatClient, path: str) -> None:
    t = dom.table(path)
    print(f"{t.path.lstrip('/')}\n  {t.title}")
    for v in t.variables:
        kind = " (tid)" if v.time else ""
        print(f"\n  {v.code}{kind} – {len(v.texts)} värden")
        for txt in v.texts:
            print(f"    {txt}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--search", help="Skriv ut tabeller vars namn eller sökväg innehåller texten")
    ap.add_argument("--table", help="Visa variabler och värden för en tabell, t.ex. AntalMal/09_Konkurser_TR")
    ap.add_argument("--out", help="Datakatalog (standard: ./data eller BRA_DATA_DIR)")
    blog.add_arguments(ap)
    a = ap.parse_args()
    blog.setup_from_args(a)

    dom = DomstatClient()
    if a.table:
        show(dom, a.table)
        return
    log.info("Läser tabellträdet från DOMstat …")
    tables = dom.tree()
    if a.search:
        q = a.search.lower()
        for t in tables:
            if q in t["text"].lower() or q in t["path"].lower() or q in t["mapp_text"].lower():
                print(f"  {t['path']:60} {t['text']}")
        return

    out = data_dir(a.out) / "domstat" / "katalog"
    trows, vrows = [], []
    for i, t in enumerate(tables, 1):
        log.info("  [%d/%d] %s", i, len(tables), t["path"])
        meta = dom.table(t["path"])
        years = meta.time_var.texts if meta.time_var else []
        trows.append([t["path"], t["mapp"], t["mapp_text"], meta.title or t["text"], t["updated"],
                      years[0] if years else "", years[-1] if years else "",
                      ", ".join(v.code for v in meta.variables)])
        for v in meta.variables:
            for code, txt in zip(v.values, v.texts):
                vrows.append([t["path"], v.code, "ja" if v.time else "", txt, code])
    write_csv(out / "tabeller.csv", ["tabell", "mapp", "mapp_namn", "titel", "uppdaterad", "forsta_ar",
                                     "sista_ar", "variabler"], trows)
    write_csv(out / "variabler.csv", ["tabell", "variabel", "tid", "varde_text", "varde_kod"], vrows)


if __name__ == "__main__":
    main()
