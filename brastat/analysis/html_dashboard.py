"""Build a self-contained HTML dashboard: dashboard/Bra_trendbevakning_dashboard.html

Usage:
    python scripts/build_html_dashboard.py

No external dependencies at view time (no CDN) — charts are drawn as inline SVG
by vanilla JS, data is embedded as JSON. Source: Brå (public statistics, PSI).
"""
from __future__ import annotations

import json
import logging
import os
from datetime import date
from importlib import resources

from brastat.analysis import parse_bra as pb
from brastat.analysis.excel_dashboard import REGION_ORDER, TYPOLOGY_MAP

log = logging.getLogger(__name__)
FILENAME = "Bra_trendbevakning_dashboard.html"


def default_out() -> str:
    return os.path.join(pb.root(), "dashboard", FILENAME)


def template() -> str:
    """HTML/CSS/JS-mallen i brastat/analysis/templates/dashboard.html."""
    return (resources.files("brastat.analysis") / "templates" / "dashboard.html").read_text(encoding="utf-8")


def build(out: str | None = None) -> str:
    out = out or default_out()
    m = pb.monthly()
    a = pb.annual()
    s = pb.suspects()
    bed, pt = pb.amnessidor()

    monthly: dict = {}
    for r in m.itertuples(index=False):
        monthly.setdefault(r.Region, {}).setdefault(r.Serie, {})[f"{r.År}-{r.Månad:02d}"] = r.Antal
    annual: dict = {}
    for r in a.itertuples(index=False):
        annual.setdefault(r.Serie, {})[int(r.År)] = {"n": _num(r.Antal), "p": _num(r[3])}
    groups = {"15–17": ["15", "16", "17"], "18–20": ["18", "19", "20"], "21–24": ["21-24"], "25–29": ["25-29"],
              "30–39": ["30-39"], "40+": ["40-49", "50-59", "60-"]}
    suspects: dict = {}
    for r in s.to_dict("records"):
        suspects.setdefault(r["Serie"], {})[int(r["År"])] = {
            "tot": _num(r["Samtliga"]), "kv": _num(r["Kvinnor"]),
            **{g: sum(_num(r[c]) or 0 for c in cols) for g, cols in groups.items()},
        }
    ntu: dict = {}
    for r in bed[bed.chart.str.startswith("Andel")].itertuples(index=False):
        key = "Försäljningsbedrägeri" if "försäljning" in r.chart else "Kort- och kreditbedrägeri"
        ntu.setdefault(key, {}).setdefault(r.series, {})[int(r.label)] = round(float(r.value), 2)
    ptcsv: dict = {}
    for r in pt.itertuples(index=False):
        ptcsv.setdefault(r.series, {})[int(r.label)] = _num(r.value)

    data = {
        "generated": date.today().isoformat(),
        "monthly": monthly, "annual": annual, "suspects": suspects, "ntu": ntu, "ptcsv": ptcsv,
        "tm": TYPOLOGY_MAP, "regions": ["Hela landet"] + REGION_ORDER,
        "elder": sorted(pb.ELDER_PARENTS), "elderSuffix": pb.ELDER_SUFFIX,
        "domstat": domstat_data(),
    }
    html = render(data)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    log.info("%s %.0f KB", out, len(html) / 1024)
    return out


def render(data: dict) -> str:
    """Fyll mallen med data (JSON) och mörkt tema."""
    return (template().replace("/*__DARK__*/", DARK_THEME)
            .replace("/*__DATA__*/null", json.dumps(data, ensure_ascii=False, separators=(",", ":"))))


# Serier i DOMstat-panelen: namn -> (serie, variabel, dimensionsvärde). Alla tingsrätter.
DOMSTAT_PANEL = {
    "Konkursärenden": ("konkurser_tingsratt", "Antal inkomna konkursärenden", ""),
    "Företagsrekonstruktioner": ("insolvensarenden_tingsratt", "Antal inkomna mål", "Företagsrekonstruktioner"),
    "Skuldsanering": ("insolvensarenden_tingsratt", "Antal inkomna mål", "Skuldsanering"),
    "Inkomna brottmål": ("brottmal_tingsratt", "Antal inkomna mål", "Brottmål"),
    "Avgjorda brottmål": ("brottmal_tingsratt", "Antal avgjorda mål", "Brottmål"),
}


def domstat_data(path: str | None = None) -> dict:
    """DOMstat-bevakningslistan -> {namn: {år: värde}} för panelen. Tomt om den inte hämtats."""
    import csv

    path = path or os.path.join(pb.root(), "domstat", "watchlist_samlad.csv")
    if not os.path.exists(path):
        return {}
    wanted = {v: k for k, v in DOMSTAT_PANEL.items()}
    out: dict = {}
    with open(path, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f, delimiter=";"):
            key = (r.get("serie"), r.get("variabel"), r.get("dimensionsvarde") or "")
            if key in wanted and r.get("domstol") == "Alla tingsrätter" and (r.get("ar") or "").isdigit():
                v = _num(r.get("varde"))
                if v is not None:
                    out.setdefault(wanted[key], {})[int(r["ar"])] = v
    return out


def _num(v):
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return None if f != f else f


# Mörk palett. Samma nyanser som den ljusa men ljusare, så att serier, rött/grönt och
# typologitaggar betyder samma sak i båda temana. Injiceras både för prefers-color-scheme
# och för manuellt valt mörkt tema.
DARK_THEME = (
    "color-scheme:dark;"
    "--navy:#16264a;--onnavy:#e6ebf5;--accent:#9db8ec;--ink:#e3e6eb;--muted:#9aa3b2;--line:#2a3140;"
    "--bg:#0f131a;--card:#171c25;--surface:#141922;--field:#394254;--soft:#223152;--hover:#1d2430;"
    "--flatbg:#232a36;--warnbg:#221c14;--tipbg:#0a0d12;--tipfg:#e3e6eb;--grid:#242b37;--axis:#5c6677;"
    "--label:#e3e6eb;--barlbl:#c3c9d3;--heatup:229,83,70;--heatdown:52,168,100;"
    "--up:#ff8a80;--upbg:rgba(255,138,128,.14);--down:#6fd39a;--downbg:rgba(111,211,154,.13);"
    "--c1:#6d9bf7;--c2:#f5a255;--c3:#4fcdbd;--c4:#e57ad0;--c5:#bcc8dc;--c6:#c9a393;--c7:#8a94a3"
)


def main() -> None:
    import argparse

    from brastat import log as blog

    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", help=f"Utfil (standard: <data>/dashboard/{FILENAME})")
    blog.add_arguments(ap)
    a = ap.parse_args()
    blog.setup_from_args(a)
    build(a.out)


if __name__ == "__main__":
    main()
