"""Hälsokontroll av hämtad data: fångar när Brå/Domstolsverket ändrat något innan det tyst ger luckor.

Läser ``manifest.csv`` (från ``brastat.tabeller``) och bevakningslistornas samlade CSV:er och
rapporterar fynd med nivå ``error`` eller ``warning``:

- poster med status ``FEL: …`` (error) eller ``saknas`` (warning – årstabeller publiceras mars–april)
- okänd status, 0 byte eller en fil som står i manifestet men saknas på disk (error)
- sha256 som inte stämmer med filen på disk (error, bara med ``verify=True``)
- en grupp där *ingen* post lyckades – typiskt att Brå bytt URL-mönster (error)
- förväntade grupper som saknas helt i manifestet (warning)
- manifestet är äldre än ``max_age_days`` – den schemalagda körningen har inte gått (warning)
- senaste månaden i SOL-bevakningslistan ligger mer än ``max_lag_months`` bakåt (warning)
- senaste året i DOMstat-bevakningslistan ligger mer än två år bakåt (warning)
- jämfört med förra körningen (``watchlist_samlad.prev.csv``): serier som försvunnit eller tappat
  många rader, och *slutliga* värden som reviderats kraftigt (warning)
- det medföljande mellancertifikatet för statistik.bra.se går ut inom ``cert_warn_days`` (warning)

Bara standardbiblioteket används.
"""

from __future__ import annotations

import csv
import datetime as dt
import hashlib
import logging
import ssl
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path

from .http import EXTRA_CA
from .watchlist import COMBINED, PREVIOUS, read_csv

log = logging.getLogger(__name__)

OK_STATUSES = {"ok", "uppdaterad", "cached", "extraherad"}
# Grupper som hämtas i en vanlig körning (rapporter/metod hoppas över med --no-pdf).
EXPECTED_GROUPS = ("anmalda", "misstankta", "lagforda", "handlagda", "malsagare", "enkater", "amnessidor")


@dataclass
class Finding:
    level: str  # "error" | "warning"
    check: str
    message: str
    group: str = ""
    file: str = ""

    def as_dict(self) -> dict:
        return asdict(self)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def check_manifest(
    data: Path,
    *,
    verify: bool = False,
    max_age_days: int = 40,
    expected_groups: tuple[str, ...] = EXPECTED_GROUPS,
    now: dt.datetime | None = None,
) -> list[Finding]:
    path = Path(data) / "manifest.csv"
    if not path.exists():
        return [Finding("error", "manifest", f"{path} saknas – kör fetch_tables.py först")]
    now = now or dt.datetime.now()
    out: list[Finding] = []
    age = now - dt.datetime.fromtimestamp(path.stat().st_mtime)
    if age > dt.timedelta(days=max_age_days):
        out.append(
            Finding(
                "warning",
                "manifest_age",
                f"manifest.csv är {age.days} dagar gammal (gräns {max_age_days}) – har den schemalagda körningen gått?",
            )
        )
    with path.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    ok_per_group: Counter[str] = Counter()
    rows_per_group: Counter[str] = Counter()
    for r in rows:
        g, status, file = r.get("group", ""), (r.get("status") or "").strip(), r.get("file", "")
        where = file or r.get("url", "")
        rows_per_group[g] += 1
        if status.startswith("FEL"):
            out.append(Finding("error", "status", f"{where}: {status}", g, file))
            continue
        if status == "saknas":
            out.append(
                Finding("warning", "status", f"{where}: saknas (inte publicerad ännu, eller nytt URL-mönster)", g, file)
            )
            continue
        if status not in OK_STATUSES:
            out.append(Finding("error", "status", f"{where}: okänd status '{status}'", g, file))
            continue
        try:
            size = int(r.get("bytes") or 0)
        except ValueError:
            size = 0
        if size <= 0:
            out.append(Finding("error", "empty", f"{where}: 0 byte", g, file))
            continue
        if file:
            p = Path(data) / file
            if not p.exists():
                out.append(
                    Finding("error", "missing_file", f"{file} står i manifestet men finns inte på disk", g, file)
                )
                continue
            if verify and r.get("sha256") and _sha256(p) != r["sha256"]:
                out.append(Finding("error", "checksum", f"{file}: sha256 stämmer inte med manifestet", g, file))
                continue
        ok_per_group[g] += 1
    for g, n in sorted(rows_per_group.items()):
        if n and not ok_per_group[g]:
            out.append(
                Finding(
                    "error", "group_failed", f"gruppen '{g}': 0 av {n} poster lyckades – har Brå ändrat webbplatsen?", g
                )
            )
    for g in expected_groups:
        if g not in rows_per_group:
            out.append(Finding("warning", "group_missing", f"gruppen '{g}' finns inte i manifestet", g))
    return out


def _months_between(a: dt.date, b: dt.date) -> int:
    return (b.year - a.year) * 12 + (b.month - a.month)


def check_sol(data: Path, *, max_lag_months: int = 3, today: dt.date | None = None) -> list[Finding]:
    path = Path(data) / "sol" / "watchlist_samlad.csv"
    if not path.exists():
        return [Finding("warning", "sol", f"{path} saknas – kör sol_watchlist.py")]
    today = today or dt.date.today()
    latest: dt.date | None = None
    with path.open(encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f, delimiter=";"):
            if r.get("periodtyp") != "manad" or not r.get("antal"):
                continue
            try:
                y, m = (int(x) for x in r["period"].split("-")[:2])
            except (ValueError, KeyError):
                continue
            d = dt.date(y, m, 1)
            latest = d if latest is None or d > latest else latest
    if latest is None:
        return [Finding("error", "sol", f"{path}: inga månadsvärden")]
    lag = _months_between(latest, today)
    if lag > max_lag_months:
        return [
            Finding(
                "warning", "sol_lag", f"senaste SOL-månad är {latest:%Y-%m} ({lag} mån sedan, gräns {max_lag_months})"
            )
        ]
    return []


def check_domstat(data: Path, *, max_lag_years: int = 2, today: dt.date | None = None) -> list[Finding]:
    path = Path(data) / "domstat" / "watchlist_samlad.csv"
    if not path.exists():
        return []  # DOMstat är valfritt (--no-domstat)
    today = today or dt.date.today()
    years = set()
    with path.open(encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f, delimiter=";"):
            if (r.get("ar") or "").isdigit():
                years.add(int(r["ar"]))
    if not years:
        return [Finding("error", "domstat", f"{path}: inga årsvärden")]
    if today.year - max(years) > max_lag_years:
        return [Finding("warning", "domstat_lag", f"senaste DOMstat-år är {max(years)}")]
    return []


# Nycklar och värdekolumn per källa för jämförelsen mellan körningar.
_REVISION_KEYS = {
    "sol": (("serie", "brott_id", "brottskod", "omrade", "period", "periodtyp"), "antal"),
    "domstat": (("serie", "tabell", "domstol", "dimension", "dimensionsvarde", "variabel", "ar"), "varde"),
}


def _float(v: str | None) -> float | None:
    if not v:
        return None
    try:
        return float(v)
    except ValueError:
        return None


def check_revisions(
    data: Path, source: str, *, max_drop: float = 0.2, max_revision: float = 0.05, min_abs: float = 5, examples: int = 3
) -> list[Finding]:
    """Jämför bevakningslistan med förra körningen.

    - en serie som fanns förra gången men saknas nu, eller har tappat mer än ``max_drop`` av raderna
    - slutliga värden (SOL: ``preliminar=False``; DOMstat: alla år utom det senaste) som ändrats mer än
      ``max_revision`` och minst ``min_abs`` – slutlig statistik ska inte ändras
    """
    folder = Path(data) / source
    prev_path, cur_path = folder / PREVIOUS, folder / COMBINED
    if not (prev_path.exists() and cur_path.exists()):
        return []
    keys, value = _REVISION_KEYS[source]
    prev, cur = read_csv(prev_path), read_csv(cur_path)
    out: list[Finding] = []
    n_prev, n_cur = Counter(r.get("serie", "") for r in prev), Counter(r.get("serie", "") for r in cur)
    for serie, n in sorted(n_prev.items()):
        if not n_cur[serie]:
            out.append(
                Finding(
                    "warning",
                    f"{source}_series_gone",
                    f"{source}: serien '{serie}' fanns förra körningen ({n} rader) men saknas nu",
                    serie,
                )
            )
        elif n_cur[serie] < n * (1 - max_drop):
            out.append(
                Finding(
                    "warning",
                    f"{source}_rows_dropped",
                    f"{source}: serien '{serie}' har {n_cur[serie]} rader mot {n} förra körningen",
                    serie,
                )
            )

    def final(r: dict, latest_year: int) -> bool:
        if source == "sol":
            return r.get("preliminar") == "False"
        return (r.get("ar") or "").isdigit() and int(r["ar"]) < latest_year

    years = [int(r["ar"]) for r in cur if (r.get("ar") or "").isdigit()]
    latest = max(years) if years else 0
    before = {tuple(r.get(k, "") for k in keys): r for r in prev if final(r, latest)}
    revised: dict[str, list[str]] = defaultdict(list)
    for r in cur:
        if not final(r, latest):
            continue
        old = before.get(tuple(r.get(k, "") for k in keys))
        a, b = _float(old.get(value)) if old else None, _float(r.get(value))
        if a is None or b is None:
            continue
        if abs(b - a) >= min_abs and abs(b - a) / max(abs(a), 1) > max_revision:
            where = " ".join(str(r.get(k, "")) for k in keys[1:] if r.get(k))
            revised[r.get("serie", "")].append(f"{where}: {a:g} -> {b:g}")
    for serie, items in sorted(revised.items()):
        out.append(
            Finding(
                "warning",
                f"{source}_revised",
                f"{source}: {len(items)} slutliga värden i '{serie}' ändrades mer än {max_revision:.0%} "
                f"sedan förra körningen, t.ex. {'; '.join(items[:examples])}",
                serie,
            )
        )
    return out


def check_certificate(path: Path = EXTRA_CA, *, warn_days: int = 180, today: dt.date | None = None) -> list[Finding]:
    """Varnar när det medföljande mellancertifikatet (se brastat.http) närmar sig utgångsdatum."""
    if not Path(path).exists():
        return [Finding("warning", "certificate", f"{path} saknas – Linux kan få TLS-fel mot statistik.bra.se")]
    try:
        not_after = ssl._ssl._test_decode_cert(str(path))["notAfter"]  # type: ignore[attr-defined]
        expires = dt.datetime.fromtimestamp(ssl.cert_time_to_seconds(not_after), dt.timezone.utc).date()
    except (AttributeError, KeyError, ValueError, ssl.SSLError) as e:
        log.debug("kunde inte läsa certifikatet: %s", e)
        return []
    left = (expires - (today or dt.date.today())).days
    if left <= warn_days:
        return [
            Finding(
                "warning" if left > 0 else "error",
                "certificate",
                f"mellancertifikatet {Path(path).name} går ut {expires} ({left} dagar kvar) – byt det i "
                "brastat/ (se brastat/http.py)",
            )
        ]
    return []


def run_all(
    data: Path, *, verify: bool = False, max_age_days: int = 40, max_lag_months: int = 3, today: dt.date | None = None
) -> list[Finding]:
    now = dt.datetime.combine(today, dt.time()) if today else None
    return (
        check_manifest(data, verify=verify, max_age_days=max_age_days, now=now)
        + check_sol(data, max_lag_months=max_lag_months, today=today)
        + check_domstat(data, today=today)
        + check_revisions(data, "sol")
        + check_revisions(data, "domstat")
        + check_certificate(today=today)
    )


def summarize(findings: list[Finding]) -> dict[str, list[Finding]]:
    by: dict[str, list[Finding]] = defaultdict(list)
    for f in findings:
        by[f.level].append(f)
    return by
