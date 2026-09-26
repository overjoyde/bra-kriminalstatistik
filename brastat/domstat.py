"""Klient för Domstolsverkets statistikdatabas DOMstat (PxWeb).

    Webb: https://pxweb.etjanst.domstol.se/PxWeb/pxweb/sv/DOMstat/
    API:  https://pxweb.etjanst.domstol.se/PxWeb/api/v1/sv/DOMstat

Till skillnad från Brås SOL har DOMstat ett riktigt API (standard-PxWeb v1):

- ``GET  <API>/<mapp>``             -> lista med mappar (type "l") och tabeller (type "t")
- ``GET  <API>/<mapp>/<tabell>.px`` -> metadata: variabler med ``values`` (koder) och ``valueTexts``
- ``POST <API>/<mapp>/<tabell>.px`` -> data, body ``{"query": [...], "response": {"format": "json"}}``

Egenheter i just denna databas:

- Värdekoderna är inte stabila id:n utan engelska etiketter (t.ex. ``"All district courts"``) och
  årskoderna är löpnummer (``"0"`` = första året). Klienten översätter därför alltid via metadatan
  och låter användaren välja med de svenska texterna.
- All statistik är **årsvis** och per domstol. Brottmål redovisas som en målkategori – det finns
  ingen uppdelning per brottstyp eller brottskod.
- Symboler: ``"."`` = uppgift kan inte förekomma (t.ex. domstolen fanns inte), ``"-"`` = noll,
  ``".."`` = uppgift saknas. ``"-"`` blir 0, övriga blir tomt värde; symbolen sparas i kolumnen ``symbol``.
- Anropsgräns (``?config``): 10 anrop per 10 sekunder och högst 100 000 celler per uttag.
"""

from __future__ import annotations

import builtins
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from .http import Client

API = "https://pxweb.etjanst.domstol.se/PxWeb/api/v1/{lang}/DOMstat"
WEB = "https://pxweb.etjanst.domstol.se/PxWeb/pxweb/sv/DOMstat"
MAX_CELLS = 100_000
DELAY = 1.1  # sekunder mellan anrop -> håller oss under 10 anrop / 10 s

FIELDS = ["tabell", "tabell_titel", "domstol", "dimension", "dimensionsvarde", "variabel", "ar", "varde", "symbol"]

_SYMBOLS_ZERO = {"-"}
_ALL = {"*", "alla", "all"}


def _num(s: str) -> float | None:
    try:
        return float(s.replace(",", ".").replace(" ", ""))
    except (ValueError, AttributeError):
        return None


def norm_table(path: str) -> str:
    """'AntalMal/09_Konkurser_TR' -> '/AntalMal/09_Konkurser_TR.px' (tolerant för '.px' och snedstreck)."""
    p = "/" + path.strip().strip("/")
    return p if p.endswith(".px") else p + ".px"


@dataclass
class Variable:
    code: str
    text: str
    values: list[str]
    texts: list[str]
    time: bool = False
    elimination: bool = False

    @property
    def is_court(self) -> bool:
        return self.code.lower().startswith("domstol")

    @property
    def is_variable(self) -> bool:
        return self.code == "Variabel"

    def text_of(self, code: str) -> str:
        try:
            return self.texts[self.values.index(code)]
        except ValueError:
            return code

    def resolve(self, wanted: str) -> str:
        """Svensk text (skiftlägesokänsligt, även unikt delord) eller kod -> kod."""
        if wanted in self.values:
            return wanted
        w = wanted.strip().lower()
        exact = [c for c, t in zip(self.values, self.texts) if t.lower() == w]
        if exact:
            return exact[0]
        part = [c for c, t in zip(self.values, self.texts) if w in t.lower()]
        if len(part) == 1:
            return part[0]
        hint = f"flera träffar: {[self.text_of(c) for c in part]}" if part else f"välj bland: {self.texts}"
        raise KeyError(f"{self.text}: '{wanted}' matchar inte entydigt ({hint})")


@dataclass
class Table:
    path: str
    title: str
    variables: list[Variable] = field(default_factory=list)

    def var(self, code_or_text: str) -> Variable:
        q = code_or_text.lower()
        for v in self.variables:
            if v.code.lower() == q or v.text.lower() == q:
                return v
        # Tillåt "Domstol" även när variabeln heter t.ex. "Domstolsslag (migration separat)"
        for v in self.variables:
            if v.code.lower().startswith(q):
                return v
        raise KeyError(f"{self.path}: variabeln '{code_or_text}' finns inte ({[v.code for v in self.variables]})")

    @property
    def time_var(self) -> Variable | None:
        return next((v for v in self.variables if v.time), None)


def parse_metadata(path: str, meta: dict) -> Table:
    return Table(
        path=norm_table(path),
        title=meta.get("title", ""),
        variables=[
            Variable(
                v["code"],
                v["text"],
                list(v["values"]),
                list(v["valueTexts"]),
                bool(v.get("time")),
                bool(v.get("elimination")),
            )
            for v in meta["variables"]
        ],
    )


def select_years(var: Variable, spec: str | int | list | None) -> list[str]:
    """Årsurval: None/'alla', 'senaste', 'senaste:3', '2015-2025', '2015-', '-2005', '2024,2025' eller lista.

    Ett urval som inte matchar något år ger ValueError (i stället för en tom fråga mot API:et).
    """
    years = var.texts
    if spec is None or (isinstance(spec, str) and spec.strip().lower() in _ALL):
        return list(var.values)
    s = str(spec).strip().lower()
    if isinstance(spec, (list, tuple)):
        wanted = {str(x).strip() for x in spec}
        out = [c for c, t in zip(var.values, years) if t in wanted]
    elif m := re.fullmatch(r"senaste(?::(\d+))?", s):
        n = int(m.group(1) or 1)
        if n < 1:
            raise ValueError(f"'{spec}': antalet år måste vara minst 1")
        out = list(var.values[-n:])
    elif (m := re.fullmatch(r"(\d{4})?\s*-\s*(\d{4})?", s)) and (m.group(1) or m.group(2)):
        lo, hi = int(m.group(1) or 0), int(m.group(2) or 9999)
        out = [c for c, t in zip(var.values, years) if t.isdigit() and lo <= int(t) <= hi]
    else:
        wanted = {x.strip() for x in s.split(",")}
        out = [c for c, t in zip(var.values, years) if t in wanted]
    if not out:
        raise ValueError(f"Inga år matchar '{spec}' (finns: {years[0]}–{years[-1]})")
    return out


def build_query(table: Table, selections: Mapping[str, Any] | None = None, years: Any = None) -> dict:
    """Bygg PxWeb-frågan. Ovalda variabler tas med i sin helhet (DOMstat saknar eliminering)."""
    selections = {k.lower(): v for k, v in (selections or {}).items()}
    query = []
    cells = 1
    for v in table.variables:
        if v.time:
            codes = select_years(v, years if years is not None else selections.get(v.code.lower()))
        else:
            want = None
            for key in (v.code.lower(), v.text.lower(), "domstol" if v.is_court else None):
                if key and key in selections:
                    want = selections[key]
                    break
            if want is None or (isinstance(want, str) and want.lower() in _ALL):
                codes = list(v.values)
            else:
                items = [want] if isinstance(want, str) else list(want)
                codes = [v.resolve(str(x)) for x in items]
        cells *= max(len(codes), 1)
        query.append({"code": v.code, "selection": {"filter": "item", "values": codes}})
    if cells > MAX_CELLS:
        raise ValueError(f"Uttaget blir {cells} celler (max {MAX_CELLS}). Begränsa domstolar, kategorier eller år.")
    return {"query": query, "response": {"format": "json"}}


def parse_result(table: Table, result: dict) -> list[dict]:
    """PxWeb 'json'-svar -> rader i långt format (se FIELDS)."""
    cols = [c for c in result["columns"] if c.get("type") != "c"]
    content = [c for c in result["columns"] if c.get("type") == "c"]
    vars_ = [table.var(c["code"]) for c in cols]
    table_id = table.path.lstrip("/").removesuffix(".px")
    fallback_var = table.title or (content[0]["text"] if content else "")
    rows = []
    for rec in result["data"]:
        r = {
            "tabell": table_id,
            "tabell_titel": table.title,
            "domstol": "",
            "dimension": "",
            "dimensionsvarde": "",
            "variabel": fallback_var,
            "ar": "",
        }
        extra_dim, extra_val = [], []
        for v, code in zip(vars_, rec["key"]):
            text = v.text_of(code)
            if v.time:
                r["ar"] = int(text) if text.isdigit() else text
            elif v.is_court:
                r["domstol"] = text
            elif v.is_variable:
                r["variabel"] = text
            else:
                extra_dim.append(v.text)
                extra_val.append(text)
        r["dimension"] = " | ".join(extra_dim)
        r["dimensionsvarde"] = " | ".join(extra_val)
        raw = (rec.get("values") or [""])[0].strip()
        val = _num(raw)
        if val is None and raw in _SYMBOLS_ZERO:
            val = 0.0
        r["varde"] = val
        r["symbol"] = "" if _num(raw) is not None else raw
        rows.append(r)
    return rows


class DomstatClient:
    """Liten klient mot DOMstat:s PxWeb-API.

    >>> dom = DomstatClient()
    >>> rows = dom.query("AntalMal/09_Konkurser_TR", {"Domstol": "Alla tingsrätter"}, years="2015-")
    """

    def __init__(self, client: Client | None = None, lang: str = "sv"):
        self.http = client or Client(delay=DELAY)
        self.base = API.format(lang=lang)
        self._meta: dict[str, Table] = {}

    def _get_json(self, url: str):
        return json.loads(self.http.get(url).decode("utf-8-sig"))

    def list(self, folder: str = "") -> builtins.list[dict]:
        f = "/" + folder.strip("/") if folder.strip("/") else ""
        return self._get_json(self.base + f)

    def tree(self, folder: str = "") -> builtins.list[dict]:
        """Alla tabeller rekursivt: [{'path', 'mapp', 'mapp_text', 'text', 'updated'}]."""
        out = []

        def walk(prefix: str, folder_text: str) -> None:
            for n in self.list(prefix):
                p = f"{prefix}/{n['id']}".lstrip("/")
                if n.get("type") == "l":
                    walk(p, n.get("text", ""))
                elif n.get("type") == "t":
                    out.append(
                        {
                            "path": p.removesuffix(".px"),
                            "mapp": prefix,
                            "mapp_text": folder_text,
                            "text": n.get("text", ""),
                            "updated": n.get("updated", ""),
                        }
                    )

        walk(folder.strip("/"), "")
        return out

    def table(self, path: str) -> Table:
        p = norm_table(path)
        if p not in self._meta:
            self._meta[p] = parse_metadata(p, self._get_json(self.base + p))
        return self._meta[p]

    def query(self, path: str, selections: Mapping[str, Any] | None = None, years: Any = None) -> builtins.list[dict]:
        t = self.table(path)
        payload = build_query(t, selections, years)
        result = json.loads(self.http.post_json(self.base + t.path, payload).decode("utf-8-sig"))
        return parse_result(t, result)
