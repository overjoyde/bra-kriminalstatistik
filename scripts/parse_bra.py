"""Parse Brå raw Excel/CSV files into tidy tables for the Excel dashboard.

Outputs (DataFrames) are consumed by build_excel_dashboard.py.
Only public, aggregated Brå statistics — no personal data.
"""
from __future__ import annotations

import glob
import os
import re

import pandas as pd

import _bootstrap  # noqa: F401,E402
from brastat.paths import data_dir  # noqa: E402

# Datakatalog med raw/ (från fetch_tables.py). Styrs med BRA_DATA_DIR.
ROOT = str(data_dir())

REGIONS = {
    "La": "Hela landet",
    "Rn01": "Nord",
    "Rn02": "Mitt",
    "Rn03": "Öst",
    "Rn04": "Väst",
    "Rn05": "Syd",
    "Rn06": "Stockholm",
    "Rn07": "Bergslagen",
}

# Canonical series -> accepted labels (P4M format first, older formats after).
# Labels are compared after whitespace normalisation.
SERIES = {
    "Samtliga brott": ["SAMTLIGA BROTT"],
    "Bedrägeri och annan oredlighet": [
        "Bedrägeri och annan oredlighet, totalt",
        "9 kap. Bedrägeri och annan oredlighet",
    ],
    "Social manipulation, totalt": [
        "Genom social manipulation, totalt",
        "Bedrägeri genom social manipulation",
    ],
    "Befogenhetsbedrägeri": ["Befogenhetsbedrägeri, totalt", "Befogenhetsbedrägeri"],
    "Social manipulation av annan typ": [
        "Genom social manipulation av annan typ, totalt",
        "Av annan typ",
    ],
    "Romansbedrägeri": ["Romansbedrägeri, totalt", "Romansbedrägeri"],
    "Investeringsbedrägeri": ["Investeringsbedrägeri, totalt", "Investeringsbedrägeri"],
    "Identitetsbedrägeri": ["Identitetsbedrägeri, totalt", "Identitetsbedrägeri"],
    "Fakturabedrägeri": ["Fakturabedrägeri, totalt", "Fakturabedrägeri"],
    "Annonsbedrägeri": ["Annonsbedrägeri, totalt", "Annonsbedrägeri"],
    "Kortbedrägeri, totalt": [
        "Kortbedrägeri (bank, betal- och kreditkort), totalt",
        "Kortbedrägeri (bank, betal- och kreditkort)",
    ],
    "Kortbedrägeri utan fysiskt kort": [
        "Kortbedrägeri utan fysiskt kort, totalt",
        "Utan fysiskt kort",
    ],
    "Olovlig identitetsanvändning": [
        "Olovlig identitetsanvändning, totalt",
        "Olovlig identitetsanvändning",
        "Olovlig identitetsanvändning (6 b §)",
    ],
    "Penningtvättsbrott, totalt": [
        "Penningtvättsbrott, totalt",
        "Lag om straff för penningtvättsbrott",
    ],
}

# Modus series that have a "mot äldre/funktionsnedsatt" split.
ELDER_PARENTS = {
    "Befogenhetsbedrägeri",
    "Social manipulation av annan typ",
    "Romansbedrägeri",
    "Investeringsbedrägeri",
    "Identitetsbedrägeri",
    "Fakturabedrägeri",
    "Annonsbedrägeri",
}
ELDER_SUFFIX = " – mot äldre/funktionsnedsatt"

# Modus categories (social manipulation etc.) are only comparable from the year
# they were introduced; before that the same words can mean something else
# (e.g. "Investeringsbedrägeri" under datorbedrägeri 2015–2016).
MODUS_SERIES = set(SERIES) - {"Samtliga brott", "Bedrägeri och annan oredlighet", "Penningtvättsbrott, totalt", "Olovlig identitetsanvändning"}
IN_9KAP = MODUS_SERIES  # labels searched only inside the 9 kap. section
MODUS_FROM_YEAR = 2019  # first year with the social-manipulation breakdown


def norm(s) -> str:
    s = re.sub(r"\s+", " ", str(s)).strip()
    return re.sub(r"(?<=[A-Za-zÅÄÖåäö])\d$", "", s)  # footnote digit, e.g. "SAMTLIGA BROTT2"


def _label_col(df: pd.DataFrame) -> int:
    """P4M files have Lagrum in col 0 and Brottstyp in col 1."""
    head = " ".join(norm(x) for x in df.iloc[:3, 0].tolist())
    return 1 if "P4M" in head or norm(df.iloc[1, 0]) == "Lagrum" else 0


def find_rows(labels: pd.Series) -> dict[str, int]:
    """Map canonical series -> row index in a Brå table."""
    sec = labels[labels.str.contains("Bedrägeri och annan oredlighet", regex=False)]
    sec_start = sec.index[0] if len(sec) else 0
    ends = labels[(labels.index > sec_start) & labels.str.contains(r"^(?:10 kap|Förskingring och annan trolöshet)", regex=True)]
    sec_end = ends.index[0] if len(ends) else len(labels)

    found: dict[str, int] = {}
    for canon, alts in SERIES.items():
        for alt in alts:
            mask = labels == alt
            if canon in IN_9KAP:
                mask &= (labels.index >= sec_start) & (labels.index < sec_end)
            hits = labels[mask].index
            if len(hits):
                found[canon] = hits[0]
                break
    # Elder split: explicit label (P4M) or "Mot äldre/funktionsnedsatt" row right under the parent.
    for parent in ELDER_PARENTS:
        if parent in found and found[parent] + 1 < len(labels):
            nxt = labels.iloc[found[parent] + 1].lower()
            if "mot äldre" in nxt and not nxt.startswith("ej") and " ej " not in f" {nxt} ":
                found[parent + ELDER_SUFFIX] = found[parent] + 1
    return found


MONTHS_EN = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def file_period(path: str) -> tuple[int, int]:
    """(year, last month) of a monthly file, e.g. P4LaAug-2026.xlsx -> (2026, 8).
    Files without a month in the name (P1xLa-2020) count as a full year."""
    fn = os.path.basename(path)
    m = re.search(r"(?:(" + "|".join(MONTHS_EN) + r"))?-(\d{4})", fn)
    if not m:
        return (0, 0)
    return int(m.group(2)), (MONTHS_EN.index(m.group(1)) + 1 if m.group(1) else 12)


def parse_monthly_file(path: str) -> list[dict]:
    fn = os.path.basename(path)
    m = re.match(r"(P4|P1x)(La|Rn0\d)(?:[A-Za-z]{3})?-(\d{4})", fn)
    if not m:
        return []
    region = REGIONS[m.group(2)]
    year, last_month = file_period(fn)

    df = pd.read_excel(path, sheet_name=0, header=None)
    lc = _label_col(df)
    found = find_rows(df.iloc[:, lc].map(norm))
    rows = []

    for canon, r in found.items():
        vals = df.iloc[r, lc + 1 : lc + 13].tolist()
        for i, v in enumerate(vals, start=1):
            if i > last_month:
                continue
            try:
                v = float(v)
            except (TypeError, ValueError):
                continue
            rows.append({"År": year, "Månad": i, "Region": region, "Serie": canon, "Antal": v, "Källfil": fn})
    return rows


def monthly() -> pd.DataFrame:
    # Each run saves a new file for the current year (P4LaJul-2026, P4LaAug-2026 …).
    # Sort chronologically, not alphabetically, so drop_duplicates(keep="last") below
    # keeps the latest publication (alphabetically Sep sorts after Dec).
    files = sorted(glob.glob(os.path.join(ROOT, "raw/anmalda_brott/tidsserie_manad/*.xls*")), key=file_period)
    rows = [r for f in files for r in parse_monthly_file(f)]
    df = pd.DataFrame(rows)
    df = _drop_early_modus(df)
    df = df.drop_duplicates(["År", "Månad", "Region", "Serie"], keep="last")
    df["Datum"] = pd.to_datetime(dict(year=df["År"], month=df["Månad"], day=1))
    return df.sort_values(["Region", "Serie", "Datum"]).reset_index(drop=True)


def _drop_early_modus(df: pd.DataFrame) -> pd.DataFrame:
    is_modus = df["Serie"].str.replace(ELDER_SUFFIX, "", regex=False).isin(MODUS_SERIES)
    return df[~is_modus | (df["År"] >= MODUS_FROM_YEAR)]


def annual() -> pd.DataFrame:
    """Final annual statistics (tabell 100, hela landet): total and per 100 000 inv."""
    rows = []
    for f in sorted(glob.glob(os.path.join(ROOT, "raw/anmalda_brott/ar_100_landet/100La-*.xls*"))):
        year = int(re.search(r"-(\d{4})", f).group(1))
        df = pd.read_excel(f, header=None)
        new = norm(df.iloc[1, 0]) == "Lagrum"
        lc, tc = (1, 2) if new else (0, 13)
        pc = df.shape[1] - 1
        for canon, r in find_rows(df.iloc[:, lc].map(norm)).items():
            rows.append({
                "År": year, "Serie": canon,
                "Antal": pd.to_numeric(df.iloc[r, tc], errors="coerce"),
                "Per 100 000 inv": pd.to_numeric(df.iloc[r, pc], errors="coerce"),
                "Källfil": os.path.basename(f),
            })
    return _drop_early_modus(pd.DataFrame(rows)).sort_values(["Serie", "År"]).reset_index(drop=True)


AGE_COLS = ["Samtliga", "15", "16", "17", "18", "19", "20", "21-24", "25-29", "30-39", "40-49", "50-59", "60-", "Okänd ålder", "Kvinnor", "Män", "Kön okänt"]
SUSPECT_SERIES = {
    "Bedrägeri och annan oredlighet": ["Bedrägeri och annan oredlighet, totalt", "9 kap. Bedrägeri och annan oredlighet"],
    "Penningtvättsbrott, totalt": ["Penningtvättsbrott, totalt", "Lag om straff för penningtvättsbrott"],
    "Social manipulation, totalt": ["Genom social manipulation, totalt", "Bedrägeri genom social manipulation"],
    "Befogenhetsbedrägeri": ["Befogenhetsbedrägeri, totalt", "Befogenhetsbedrägeri"],
}


def suspects() -> pd.DataFrame:
    rows = []
    for f in sorted(glob.glob(os.path.join(ROOT, "raw/misstankta/220_brottstyp_alder_kon/*.xls*"))):
        year = int(re.search(r"-(\d{4})", f).group(1))
        df = pd.read_excel(f, header=None)
        lc = 1 if norm(df.iloc[1, 0]) == "Lagrum" else 0
        labels = df.iloc[:, lc].map(norm)
        for canon, alts in SUSPECT_SERIES.items():
            for alt in alts:
                hits = labels[labels == alt].index
                if len(hits):
                    vals = df.iloc[hits[0], lc + 1 : lc + 1 + len(AGE_COLS)].tolist()
                    rec = {"År": year, "Serie": canon}
                    for k, v in zip(AGE_COLS, vals):
                        rec[k] = pd.to_numeric(v, errors="coerce")
                    rows.append(rec)
                    break
    return pd.DataFrame(rows).sort_values(["Serie", "År"]).reset_index(drop=True)


def amnessidor() -> tuple[pd.DataFrame, pd.DataFrame]:
    b = pd.read_csv(os.path.join(ROOT, "raw/amnessidor/bedrageri_diagramdata.csv"))
    p = pd.read_csv(os.path.join(ROOT, "raw/amnessidor/penningtvatt_terrorfinansiering_diagramdata.csv"))
    for d in (b, p):
        for c in ("chart", "question", "series", "label"):
            d[c] = d[c].astype(str).str.strip()
    return b, p


if __name__ == "__main__":
    m = monthly()
    print(m.pivot_table(index="Serie", columns=["Region"], values="År", aggfunc="min").to_string())
    print(m[m.Region == "Hela landet"].pivot_table(index="Serie", columns="År", values="Antal", aggfunc="sum").round(0).to_string())
    a = annual()
    print(a.pivot_table(index="Serie", columns="År", values="Antal").round(0).to_string())
    print(a.pivot_table(index="Serie", columns="År", values="Per 100 000 inv").round(1).to_string())
    s = suspects()
    print(s[["År", "Serie", "Samtliga", "18", "19", "20"]].to_string())
