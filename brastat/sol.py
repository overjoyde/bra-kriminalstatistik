"""Client for Brå's interactive statistics database SOL ("Gör din egen sökning").

    https://statistik.bra.se/solwebb/action/index

SOL has no official API. It is an old Struts/JSP frameset application:

1. ``start?menykatalogid=1`` opens a session (JSESSIONID cookie).
2. ``anmalda/urval/urval?menyid=<N>`` selects a menu (year/month, crime type/code,
   country/municipality). The page embeds all selectable values as JavaScript
   arrays: ``arrayNivaett`` (tree), ``arrayNivatva`` (selectable crimes),
   ``arrayRegionNivaTva`` (areas), ``arrayPeriod`` (periods).
3. ``anmalda/urval/vantapopup`` (POST) receives the selection as ``*``-separated
   id strings, ``anmalda/urval/sok`` runs the query and
   ``anmalda/resultat/dbfil`` (POST) returns the result as a long-format
   semicolon-separated "database file".

This module re-implements that flow. The session is bound to one menu at a time,
so a new menu selection is made whenever you switch menu.
"""
from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass, field

from .http import Client

BASE = "https://statistik.bra.se/solwebb/action"
SEP = "*"
MAX_CELLS = 10_000  # SOL refuses larger queries

# menyid per (klassificering, periodicitet, områdesnivå) – from start?menykatalogid=1
MENUS: dict[str, dict] = {
    "brottstyp-ar-region": {"id": 98, "desc": "Brottstyp, årsvis – land och län 1975–2014, land och polisregion 2015–"},
    "brottstyp-ar-kommun": {"id": 101, "desc": "Brottstyp, årsvis – kommun och storstädernas stadsområden 1996–"},
    "brottstyp-manad-region": {"id": 34, "desc": "Brottstyp, månads- och kvartalsvis – land och län 1975–2014, land och region 2015–"},
    "brottstyp-manad-kommun": {"id": 90, "desc": "Brottstyp, månads- och kvartalsvis – kommun och stadsområden 1996– (sekretessbegränsad)"},
    "brottskod-ar-region": {"id": 104, "desc": "Brottskod, årsvis – land och län 1975–2014, land och region 2015–"},
    "brottskod-ar-kommun": {"id": 107, "desc": "Brottskod, årsvis – kommun och storstädernas stadsområden 1996–"},
    "brottskod-manad-region": {"id": 46, "desc": "Brottskod, månads- och kvartalsvis – land och län 1975–2014, land och region 2015–"},
}

MONTHS = ["Jan", "Feb", "Mar", "Apr", "Maj", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dec"]
_NBSP = "\u00a0"
_ARRAY_RE = re.compile(r'(array\w+)\[(\d+)\]\s*=\s*"((?:[^"\\]|\\.)*)"')


def _clean(s: str) -> str:
    return s.replace("\\xA0", _NBSP).replace('\\"', '"')


def _depth(name: str) -> int:
    n = len(name) - len(name.lstrip(_NBSP + " "))
    return n // 2


@dataclass
class Crime:
    id: str
    name: str          # label as shown (trimmed)
    parent_id: str     # id of the node in arrayNivaett
    path: str          # full path as given by SOL
    depth: int         # indentation level inside the parent node
    code: str = ""     # 4-digit brottskod (brottskod menus only)

    @property
    def label(self) -> str:
        """Label as it appears in result files ("X totalt" is reported as "X")."""
        n = self.name
        return n[: -len(" totalt")] if n.endswith(" totalt") else n


@dataclass
class Period:
    id: str
    name: str
    year: int
    prel: bool
    kind: str          # "ar", "helar", "kvartal", "manad"
    month: int | None = None
    quarter: int | None = None

    @property
    def key(self) -> str:
        if self.kind == "manad":
            return f"{self.year}-{self.month:02d}"
        if self.kind == "kvartal":
            return f"{self.year}-K{self.quarter}"
        return str(self.year)


@dataclass
class Catalog:
    menu: str
    tree: list[tuple[str, str, int]] = field(default_factory=list)   # (id, name, depth)
    crimes: list[Crime] = field(default_factory=list)
    regions: dict[str, str] = field(default_factory=dict)            # name -> id
    periods: list[Period] = field(default_factory=list)

    # ---- lookups -------------------------------------------------------
    def crime_by_id(self, cid: str) -> Crime:
        for c in self.crimes:
            if c.id == str(cid):
                return c
        raise KeyError(f"Okänt brotts-id {cid} i meny {self.menu}")

    def crime_by_code(self, code: str) -> Crime:
        code = str(code).zfill(4)
        for c in self.crimes:
            if c.code == code:
                return c
        raise KeyError(f"Okänd brottskod {code} i meny {self.menu}")

    def region_id(self, name: str) -> str:
        if name in self.regions:
            return self.regions[name]
        low = {k.lower(): v for k, v in self.regions.items()}
        for cand in (name.lower(), f"region {name.lower()}", f"{name.lower()} län", f"{name.lower()} kommun"):
            if cand in low:
                return low[cand]
        raise KeyError(f"Okänt område '{name}'. Kör sol_catalog.py för att se giltiga namn.")

    def select_periods(self, spec: str) -> list[Period]:
        """Period spec examples: 'senaste', '2015-2025', '2024,2025', '2024-01..2026-08', 'alla'."""
        spec = spec.strip().lower()
        yearly = [p for p in self.periods if p.kind == "ar"]
        monthly = [p for p in self.periods if p.kind == "manad"]
        pool = yearly or monthly
        if spec in ("alla", "all"):
            return pool
        if spec in ("senaste", "latest"):
            return [max(pool, key=lambda p: (p.year, p.month or 0))]
        m = re.fullmatch(r"(\d{4})-(\d{2})\.\.(\d{4})-(\d{2})", spec)
        if m:
            lo, hi = (int(m[1]), int(m[2])), (int(m[3]), int(m[4]))
            return sorted((p for p in monthly if lo <= (p.year, p.month) <= hi), key=lambda p: (p.year, p.month))
        m = re.fullmatch(r"(\d{4})-(\d{4})", spec)
        if m:
            lo, hi = int(m[1]), int(m[2])
            if yearly:
                return sorted((p for p in yearly if lo <= p.year <= hi), key=lambda p: p.year)
            return sorted((p for p in monthly if lo <= p.year <= hi), key=lambda p: (p.year, p.month))
        years = {int(y) for y in re.split(r"[,\s]+", spec) if y}
        if yearly:
            return sorted((p for p in yearly if p.year in years), key=lambda p: p.year)
        return sorted((p for p in monthly if p.year in years), key=lambda p: (p.year, p.month))


def parse_catalog(html: str, menu: str) -> Catalog:
    cat = Catalog(menu=menu)
    arrays: dict[str, list[str]] = {}
    for name, _, val in _ARRAY_RE.findall(html):
        arrays.setdefault(name, []).append(_clean(val))

    for v in arrays.get("arrayNivaett", []):
        cid, name = v.split(SEP, 1)
        cat.tree.append((cid, name.strip(_NBSP + " "), _depth(name)))

    for v in arrays.get("arrayNivatva", []):
        p = v.split(SEP)
        if len(p) < 4:
            continue
        raw = p[1]
        name = raw.strip(_NBSP + " ")
        m = re.match(r"(\d{4}) - ", name)
        cat.crimes.append(Crime(id=p[0], name=name, parent_id=p[2], path=p[3].strip(),
                                depth=_depth(raw), code=m.group(1) if m else ""))

    for v in arrays.get("arrayRegionNivaTva", []):
        p = v.split(SEP)
        name = p[1].strip(_NBSP + " ")
        cat.regions.setdefault(name, p[0])
    if not cat.regions:
        for v in arrays.get("arrayRegionNivaEtt", []):
            rid, name = v.split(SEP, 1)
            cat.regions.setdefault(name.strip(_NBSP + " "), rid)

    for v in arrays.get("arrayPeriod", []):
        p = v.split(SEP)
        pid, name, full = p[0], p[1], p[3] if len(p) > 3 else p[1]
        typ = p[4] if len(p) > 4 else "-1"
        ym = re.search(r"(\d{4})", full if typ != "-1" else name)
        if not ym:
            continue
        year, prel = int(ym.group(1)), "prel" in full
        if typ == "-1":
            cat.periods.append(Period(pid, name, year, prel, "ar"))
        elif typ == "0":
            cat.periods.append(Period(pid, name, year, prel, "helar"))
        elif typ == "1":
            q = re.search(r"Kvartal (\d)", name)
            cat.periods.append(Period(pid, name, year, prel, "kvartal", quarter=int(q.group(1)) if q else None))
        elif typ == "2" and name[:3] in MONTHS:
            cat.periods.append(Period(pid, name, year, prel, "manad", month=MONTHS.index(name[:3]) + 1))
    return cat


def parse_dbfil(text: str) -> list[dict]:
    """Parse the semicolon 'Databasfil.txt' export into dict rows."""
    rows = []
    reader = csv.reader(io.StringIO(text.replace("&nbsp;", " ")), delimiter=";")
    header = None
    for rec in reader:
        if not rec or not any(x.strip() for x in rec):
            continue
        if header is None:
            header = [h.strip() for h in rec]
            continue
        rec = [x.strip() for x in rec]
        rows.append(dict(zip(header, rec)))
    return rows


def _num(v: str | None) -> float | None:
    if v is None:
        return None
    v = v.replace(" ", "").replace("\u00a0", "").replace(",", ".")
    if v in ("", "..", "-"):
        return None
    try:
        return float(v)
    except ValueError:
        return None


class SolClient:
    """Session-aware SOL client.

    >>> sol = SolClient()
    >>> rows = sol.query("brottskod-manad-region", codes=["0950", "0951"],
    ...                  regions=["Hela landet"], periods="2025-01..2026-08")
    """

    def __init__(self, client: Client | None = None):
        self.http = client or Client()
        self._menu: str | None = None
        self._catalogs: dict[str, Catalog] = {}

    # ---- session / catalog --------------------------------------------
    def _select_menu(self, menu: str) -> str:
        if menu not in MENUS:
            raise KeyError(f"Okänd meny '{menu}'. Välj en av: {', '.join(MENUS)}")
        start = f"{BASE}/start?menykatalogid=1"
        self.http.get(start)
        html = self.http.get(f"{BASE}/anmalda/urval/urval?menyid={MENUS[menu]['id']}", referer=start)
        text = html.decode("latin-1", "replace")
        if "obefintlig menyrad" in text or "arrayNivatva" not in text:
            raise RuntimeError(f"SOL returnerade inget urval för meny {menu}; strukturen kan ha ändrats.")
        self._menu = menu
        return text

    def catalog(self, menu: str) -> Catalog:
        if menu not in self._catalogs:
            self._catalogs[menu] = parse_catalog(self._select_menu(menu), menu)
        elif self._menu != menu:
            self._select_menu(menu)
        return self._catalogs[menu]

    # ---- query --------------------------------------------------------
    def _run(self, crime_ids: list[str], region_ids: list[str], period_ids: list[str],
             per_100k: bool) -> list[dict]:
        urval = f"{BASE}/anmalda/urval"
        self.http.post(f"{urval}/vantapopup", {
            "brottstyp_id_string": SEP.join(crime_ids),
            "region_id_string": SEP.join(region_ids),
            "period_id_string": SEP.join(period_ids),
            "fordelning_id_string": "",
            "antal": "1",
            "antal_100k": "1" if per_100k else "0",
        }, referer=f"{urval}/minaval")
        page = self.http.get(f"{urval}/sok", referer=f"{urval}/vantapopup").decode("latin-1", "replace")
        if "Fel/Error" in page:
            msg = re.search(r"Felmeddelande:\s*([^<]+)", page)
            raise RuntimeError(f"SOL-fel: {msg.group(1).strip() if msg else 'okänt'}")
        data = self.http.post(f"{BASE}/anmalda/resultat/dbfil", {}, referer=f"{urval}/sok")
        return parse_dbfil(data.decode("latin-1", "replace"))

    def query(self, menu: str, *, crime_ids: list[str] | None = None, codes: list[str] | None = None,
              regions: list[str] | None = None, periods: str | list[str] = "senaste",
              per_100k: bool = True) -> list[dict]:
        """Return tidy rows: meny, brott_id, brottskod, brott, sokvag, omrade, period, ar, manad,
        kvartal, periodtyp, preliminar, antal, per_100k.

        ``periods`` is a spec string (see ``Catalog.select_periods``) or a list of SOL period ids.
        ``regions`` accepts names such as "Hela landet", "Stockholm" (→ Region Stockholm),
        "Skåne län" or municipality names in the kommun menus."""
        cat = self.catalog(menu)
        crimes = [cat.crime_by_id(i) for i in (crime_ids or [])] + [cat.crime_by_code(c) for c in (codes or [])]
        if not crimes:
            raise ValueError("Ange minst ett brotts-id eller en brottskod.")
        region_names = regions or ["Hela landet"]
        region_ids = [cat.region_id(r) for r in region_names]
        pers = cat.select_periods(periods) if isinstance(periods, str) else [
            p for p in cat.periods if p.id in set(periods)]
        if not pers:
            raise ValueError(f"Inga perioder matchade '{periods}'.")

        # Split crimes so that no batch contains two crimes with the same label
        batches: list[list[Crime]] = []
        for c in crimes:
            for b in batches:
                if all(x.label != c.label for x in b):
                    b.append(c)
                    break
            else:
                batches.append([c])

        out: list[dict] = []
        units = 2 if per_100k else 1
        for batch in batches:
            per_chunk = max(1, MAX_CELLS // (len(batch) * len(region_ids) * units))
            for i in range(0, len(pers), per_chunk):
                chunk = pers[i:i + per_chunk]
                rows = self._run([c.id for c in batch], region_ids, [p.id for p in chunk], per_100k)
                wanted = {c.label: c for c in batch}
                found: dict[tuple, dict] = {}
                for r in rows:
                    c = wanted.get(r.get("Brott", ""))
                    if not c:
                        continue
                    yr_raw, per_raw = r.get("År", ""), r.get("Period", "")
                    prel = "prel" in yr_raw or "prel" in per_raw
                    year_m = re.search(r"\d{4}", yr_raw) or re.search(r"\d{4}", per_raw)
                    year = int(year_m.group(0)) if year_m else None
                    p = next((cand for cand in chunk if cand.year == year
                              and (cand.kind == "ar" or cand.name == per_raw)), None)
                    rec = {
                        "meny": menu,
                        "brott_id": c.id,
                        "brottskod": c.code,
                        "brott": c.label,
                        "sokvag": c.path,
                        "omrade": r.get("Region"),
                        "period": p.key if p else f"{year}",
                        "ar": year,
                        "manad": p.month if p else None,
                        "kvartal": p.quarter if p else None,
                        "periodtyp": p.kind if p else "",
                        "preliminar": prel,
                        "antal": _num(r.get("Antal")),
                        "per_100k": _num(r.get("/100 000 inv")) if per_100k else None,
                    }
                    key = (c.id, rec["omrade"], per_raw, yr_raw)
                    # ancestors of a selected crime are echoed with ".." – keep the row with values
                    if key not in found or (found[key]["antal"] is None and rec["antal"] is not None):
                        found[key] = rec
                out.extend(found.values())
        return out
