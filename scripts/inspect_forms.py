#!/usr/bin/env python3
"""Lista StatSelector-formulär (kategori/prefix/period/område) på Brås statistiksidor.

Används för att upptäcka vilka tabell-id som finns innan man bygger ut fetch_tables.py.

    python scripts/inspect_forms.py                     # standardsidorna
    python scripts/inspect_forms.py anmalda-brott       # en sida
"""
import re
import sys
from html.parser import HTMLParser

import _bootstrap  # noqa: F401
from brastat.http import Client

PAGES = sys.argv[1:] or [
    "anmalda-brott",
    "misstankta-personer",
    "personer-lagforda-for-brott",
    "handlagda-brott",
    "handlaggningsresultat",
    "malsagare-vid-brottsanmalan",
]


class FormParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.forms, self.cur, self.sel, self.heading, self.in_head = [], None, None, "", False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "div" and "statisticheadline" in (a.get("class") or "") and "modulexlinkxstatistics" in (a.get("class") or ""):
            self.in_head, self.heading = True, ""
        if tag == "form" and "statform" in (a.get("class") or ""):
            self.cur = {"name": a.get("name"), "id": a.get("id"), "heading": self.heading.strip(), "hidden": {}, "selects": {}}
        elif self.cur is not None:
            if tag == "input" and a.get("type") == "hidden":
                self.cur["hidden"][a.get("name")] = a.get("value")
            elif tag == "select":
                self.sel = a.get("name")
                self.cur["selects"][self.sel] = []
            elif tag == "option" and self.sel:
                v = a.get("value")
                if v not in ("-", "0", None):
                    self.cur["selects"][self.sel].append(v)

    def handle_endtag(self, tag):
        if tag == "div" and self.in_head:
            self.in_head = False
        if tag == "select":
            self.sel = None
        if tag == "form" and self.cur is not None:
            self.forms.append(self.cur)
            self.cur = None

    def handle_data(self, data):
        if self.in_head:
            self.heading += data


http = Client()
for page in PAGES:
    url = f"https://bra.se/statistik/statistik-fran-rattsvasendet/{page}"
    html = http.text(url)
    p = FormParser()
    p.feed(html)
    print(f"\n##### {page}")
    for f in p.forms:
        sel = {k: (v[:3] + ["…"] + v[-2:] if len(v) > 6 else v) for k, v in f["selects"].items()}
        print(f"- [{f['name']}] {f['heading'][:90]!r} hidden={f['hidden']} selects={sel}")
    for m in sorted(set(re.findall(r'href="(/download/[^"]+\.(?:xlsx|xls|csv|pdf))"', html))):
        print("   file:", m)
