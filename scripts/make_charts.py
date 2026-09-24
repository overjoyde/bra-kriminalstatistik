#!/usr/bin/env python3
"""Skapa exempelgrafer (PNG) och en årstabell (Markdown) från hämtad data.

Kräver att dessa körts först:
    python scripts/sol_watchlist.py                    # SOL-serier (månad/region)
    python scripts/fetch_tables.py --groups anmalda misstankta   # för årstabell och misstänkta

    python scripts/make_charts.py                      # -> data/charts/*.png + arstabell.md
    python scripts/make_charts.py --out docs/img       # (används för README-graferna)
    python scripts/make_charts.py --theme dark         # bara mörka grafer (*_dark.png); standard är båda

Graferna är exempel på analyser – se README-avsnittet "Vad kan man göra med datan?".
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.ticker as mtick  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import _bootstrap  # noqa: F401,E402
from brastat.paths import data_dir  # noqa: E402

BLUE, ORANGE, GREEN, RED, PURPLE, GREY = "#3b75af", "#ef8636", "#519e3e", "#c53a32", "#8d69b8", "#7f7f7f"
PALETTE = [BLUE, ORANGE, GREEN, RED, PURPLE, "#84584e", "#d57dbf", GREY]
REGIONS = ["Stockholm", "Öst", "Väst", "Syd", "Mitt", "Bergslagen", "Nord"]
SOURCE = "Källa: Brå, anmälda brott (SOL). Bearbetning: bra-kriminalstatistik."

plt.rcParams.update({
    "figure.dpi": 110, "savefig.dpi": 150, "font.size": 10,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.alpha": 0.3, "axes.titlesize": 12, "legend.frameon": True,
    "legend.fontsize": 9, "axes.formatter.use_locale": False,
})

# Teman. Mörkt följer HTML-dashboardens mörka palett, så att samma serie har samma
# färg i båda. Mörka filer får suffixet _dark; de ljusa behåller sina namn.
THEMES = {
    "light": {"colors": ("#3b75af", "#ef8636", "#519e3e", "#c53a32", "#8d69b8", "#7f7f7f"),
              "extra": ("#84584e", "#d57dbf"), "bg": "white", "fg": "black", "suffix": "", "rc": {}},
    "dark": {"colors": ("#6d9bf7", "#f5a255", "#6cc36a", "#ff8a80", "#b39ddb", "#9aa3b2"),
             "extra": ("#c9a393", "#e57ad0"), "bg": "#171c25", "fg": "#e3e6eb", "suffix": "_dark",
             "rc": {"figure.facecolor": "#171c25", "axes.facecolor": "#171c25", "savefig.facecolor": "#171c25",
                    "axes.edgecolor": "#5c6677", "axes.labelcolor": "#e3e6eb", "text.color": "#e3e6eb",
                    "xtick.color": "#9aa3b2", "ytick.color": "#9aa3b2", "grid.color": "#5c6677",
                    "legend.facecolor": "#141922", "legend.edgecolor": "#394254", "legend.labelcolor": "#e3e6eb"}},
}
FG, BG, SUFFIX = "black", "white", ""


def use_theme(name: str) -> None:
    """Sätt färgkonstanterna för ett tema. Diagramfunktionerna läser dem vid anropet."""
    global BLUE, ORANGE, GREEN, RED, PURPLE, GREY, PALETTE, FG, BG, SUFFIX
    t = THEMES[name]
    BLUE, ORANGE, GREEN, RED, PURPLE, GREY = t["colors"]
    PALETTE = [BLUE, ORANGE, GREEN, RED, PURPLE, *t["extra"], GREY]
    FG, BG, SUFFIX = t["fg"], t["bg"], t["suffix"]


def thousands(ax, axis="y"):
    fmt = mtick.FuncFormatter(lambda x, _: f"{x:,.0f}".replace(",", " "))
    (ax.yaxis if axis == "y" else ax.xaxis).set_major_formatter(fmt)


def save(fig, out: Path, name: str, source: str = SOURCE):
    fig.text(0.01, 0.005, source, fontsize=7.5, color=GREY, ha="left", va="bottom")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    p = out / name.replace(".png", f"{SUFFIX}.png")
    fig.savefig(p, bbox_inches="tight", facecolor=BG)
    plt.close(fig)
    print("  +", p)


# ---------------------------------------------------------------- data
def load_sol(d: Path) -> pd.DataFrame:
    df = pd.read_csv(d / "sol" / "watchlist_samlad.csv", sep=";", dtype={"brottskod": str})
    df = df[df.periodtyp.isin(["manad", "ar"])].copy()
    m = df.periodtyp == "manad"
    df.loc[m, "datum"] = pd.to_datetime(df.loc[m, "period"] + "-01")
    df["omrade"] = df["omrade"].str.replace("Region ", "", regex=False)
    return df


def monthly(sol: pd.DataFrame, serie: str, omrade: str = "Hela landet") -> pd.Series:
    x = sol[(sol.serie == serie) & (sol.omrade == omrade) & (sol.periodtyp == "manad")]
    s = x.groupby("datum").antal.sum(min_count=1).dropna().sort_index()
    return s


def prel_start(sol: pd.DataFrame) -> pd.Timestamp | None:
    x = sol[(sol.periodtyp == "manad") & (sol.preliminar)]
    return x.datum.min() if len(x) else None


# ---------------------------------------------------------------- charts
def chart_monthly(sol, out):
    s = monthly(sol, "penningtvatt_totalt")
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(s.index, s.values, color=BLUE, lw=1.6, label="Penningtvättsbrott, totalt")
    r12 = s.rolling(12).mean()
    ax.plot(r12.index, r12.values, color=ORANGE, lw=2, ls="--", label="Glidande 12-månadersmedel")
    ps = prel_start(sol)
    if ps is not None:
        ax.axvspan(ps, s.index.max(), color=GREY, alpha=0.12, lw=0)
        ax.text(ps, ax.get_ylim()[1] * 0.97, " preliminärt", color=GREY, fontsize=8, va="top")
    ax.set_title("Anmälda penningtvättsbrott per månad, hela landet")
    ax.text(0.99, 0.02, "Penningtvätt har långa registreringstider – de senaste\npreliminära månaderna underskattar ofta nivån.",
            transform=ax.transAxes, ha="right", va="bottom", fontsize=8, color=GREY)
    ax.legend(loc="upper left")
    thousands(ax)
    save(fig, out, "01_penningtvatt_manad.png")


def chart_modus_r12(sol, out):
    series = {"befogenhetsbedrageri": "Befogenhetsbedrägeri", "annonsbedrageri": "Annonsbedrägeri",
              "fakturabedrageri": "Fakturabedrägeri", "identitetsbedrageri": "Identitetsbedrägeri",
              "investeringsbedrageri": "Investeringsbedrägeri", "romansbedrageri": "Romansbedrägeri"}
    fig, ax = plt.subplots(figsize=(10, 4.4))
    for (k, label), c in zip(series.items(), PALETTE):
        s = monthly(sol, k).rolling(12).sum().dropna()
        ax.plot(s.index, s.values, color=c, lw=2, label=label)
    ax.set_title("Bedrägerimodus – rullande 12 månader (R12), hela landet")
    ax.set_ylabel("Anmälda brott senaste 12 mån")
    ax.legend(ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.08), frameon=False)
    thousands(ax)
    save(fig, out, "02_modus_r12.png")


def chart_region_ytd(sol, out):
    x = sol[(sol.periodtyp == "manad") & sol.omrade.isin(REGIONS)]
    last = x.datum.max()
    y, mth = last.year, last.month
    res = {}
    for k, label in (("social_manipulation", "Social manipulation, totalt"),
                     ("penningtvatt_totalt", "Penningtvättsbrott, totalt")):
        z = x[x.serie == k]
        cur = z[(z.datum.dt.year == y) & (z.datum.dt.month <= mth)].groupby("omrade").antal.sum()
        prev = z[(z.datum.dt.year == y - 1) & (z.datum.dt.month <= mth)].groupby("omrade").antal.sum()
        res[label] = (cur / prev - 1).reindex(REGIONS)
    df = pd.DataFrame(res)
    fig, ax = plt.subplots(figsize=(10, 4.2))
    w = 0.38
    xs = np.arange(len(df))
    for i, (col, c) in enumerate(zip(df.columns, (BLUE, ORANGE))):
        bars = ax.bar(xs + (i - 0.5) * w, df[col].values, w, color=c, label=col)
        ax.bar_label(bars, labels=[f"{v:+.0%}" for v in df[col].values], fontsize=7.5, padding=2)
    ax.axhline(0, color=FG, lw=0.8)
    ax.set_xticks(xs, df.index)
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0, decimals=0))
    months = ["jan", "feb", "mar", "apr", "maj", "jun", "jul", "aug", "sep", "okt", "nov", "dec"]
    ax.set_title(f"Förändring jan–{months[mth - 1]} {y} jämfört med samma period {y - 1}, per polisregion")
    ax.legend(loc="upper right")
    save(fig, out, "03_region_hittills_i_ar.png",
         SOURCE + " Preliminära månader – penningtvätt registreras med fördröjning och underskattas ofta.")


def chart_region_per100k(sol, out):
    x = sol[(sol.serie == "social_manipulation") & (sol.periodtyp == "manad") & sol.omrade.isin(REGIONS)]
    last = x.datum.max()
    win = x[x.datum > last - pd.DateOffset(months=12)]
    v = win.groupby("omrade").per_100k.sum().reindex(REGIONS).sort_values()
    nat = sol[(sol.serie == "social_manipulation") & (sol.omrade == "Hela landet") & (sol.periodtyp == "manad")]
    natv = nat[nat.datum > last - pd.DateOffset(months=12)].per_100k.sum()
    fig, ax = plt.subplots(figsize=(10, 3.8))
    bars = ax.barh(v.index, v.values, color=BLUE)
    ax.bar_label(bars, labels=[f"{b:.0f}" for b in v.values], padding=3, fontsize=8)
    ax.axvline(natv, color=RED, ls="--", lw=1.2, label=f"Hela landet ({natv:.0f})")
    ax.set_title("Social manipulation per 100 000 invånare, senaste 12 månaderna")
    ax.legend(loc="lower right")
    ax.grid(axis="y", visible=False)
    save(fig, out, "04_region_per_100k.png",
         SOURCE + " Summa av avrundade månadsvärden per 100 000 inv. – ungefärlig nivå.")


def chart_elderly(annual, out):
    mod = ["Befogenhetsbedrägeri", "Social manipulation av annan typ", "Investeringsbedrägeri",
           "Romansbedrägeri", "Fakturabedrägeri", "Annonsbedrägeri"]
    fig, ax = plt.subplots(figsize=(10, 4.2))
    for m, c in zip(mod, PALETTE):
        tot = annual[annual.Serie == m].set_index("År").Antal
        eld = annual[annual.Serie == m + " – mot äldre/funktionsnedsatt"].set_index("År").Antal
        share = (eld / tot).dropna()
        if len(share):
            ax.plot(share.index, share.values, marker="o", color=c, lw=2, label=m)
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0, decimals=0))
    ax.set_title("Andel av anmälda bedrägerier som riktas mot äldre/funktionsnedsatta")
    ax.legend(ncol=2, loc="upper left", fontsize=8)
    ax.xaxis.set_major_locator(mtick.MaxNLocator(integer=True))
    save(fig, out, "05_andel_mot_aldre.png", "Källa: Brå, anmälda brott tabell 100 (slutlig årsstatistik).")


def chart_suspects(susp, out):
    young = ["15", "16", "17", "18", "19", "20", "21-24"]
    fig, ax = plt.subplots(figsize=(10, 4.2))
    for serie, c in (("Penningtvättsbrott, totalt", BLUE), ("Social manipulation, totalt", ORANGE),
                     ("Bedrägeri och annan oredlighet", GREEN)):
        z = susp[susp.Serie == serie].set_index("År")
        known = z["Samtliga"] - z["Okänd ålder"].fillna(0)
        share = (z[young].fillna(0).sum(axis=1) / known).dropna()
        ax.plot(share.index, share.values, marker="o", color=c, lw=2, label=serie)
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0, decimals=0))
    ax.set_title("Andel misstänkta personer som är 15–24 år")
    ax.legend(loc="upper right")
    ax.xaxis.set_major_locator(mtick.MaxNLocator(integer=True))
    save(fig, out, "06_misstankta_15_24.png",
         "Källa: Brå, misstänkta personer tabell 220. En person kan vara misstänkt för flera brottstyper; "
         "okänd ålder exkluderad.")


def seasonal_forecast(s: pd.Series, h: int = 6, q: float = 0.90):
    """Enkel, beroendefri prognos: multiplikativ säsong + linjär trend på senaste 36 mån.
    Intervall från historiska prognosfel i procent, skalat med sqrt(h)."""
    s = s.dropna().astype(float)
    hist = s[-60:]
    idx = hist.rolling(12, center=True).mean()
    ratio = (hist / idx).dropna()
    season = ratio.groupby(ratio.index.month).mean()
    season = season / season.mean()
    des = s / s.index.month.map(season).values
    tail = des[-36:]
    t = np.arange(len(tail))
    b, a = np.polyfit(t, tail.values, 1)
    fit = (a + b * t) * tail.index.month.map(season).values
    err = np.log(s[-36:].values / fit)
    lo_q, hi_q = np.quantile(err, [(1 - q) / 2, 1 - (1 - q) / 2])
    fidx = pd.date_range(s.index[-1] + pd.offsets.MonthBegin(1), periods=h, freq="MS")
    tf = np.arange(len(tail), len(tail) + h)
    f = (a + b * tf) * fidx.month.map(season).values
    scale = np.sqrt(np.arange(1, h + 1))
    return (pd.Series(f, fidx), pd.Series(f * np.exp(lo_q * scale), fidx),
            pd.Series(f * np.exp(hi_q * scale), fidx))


def chart_forecast(sol, out):
    series = {"social_manipulation": "Social manipulation, totalt", "befogenhetsbedrageri": "Befogenhetsbedrägeri",
              "annonsbedrageri": "Annonsbedrägeri", "romansbedrageri": "Romansbedrägeri",
              "investeringsbedrageri": "Investeringsbedrägeri", "fakturabedrageri": "Fakturabedrägeri"}
    fig, axes = plt.subplots(2, 3, figsize=(14, 6.5))
    for ax, (k, label) in zip(axes.flat, series.items()):
        s = monthly(sol, k)
        f, lo, hi = seasonal_forecast(s)
        show = s[-36:]
        ax.plot(show.index, show.values, color=BLUE, lw=1.5, label="utfall")
        ax.plot([show.index[-1], *f.index], [show.values[-1], *f.values], color=RED, ls="--", lw=1.6,
                label="prognos")
        ax.fill_between(f.index, lo.values, hi.values, color=RED, alpha=0.15, lw=0, label="90 %-intervall")
        ax.set_title(label, fontsize=10)
        thousands(ax)
        ax.tick_params(axis="x", labelsize=8)
        ax.xaxis.set_major_locator(matplotlib.dates.YearLocator())
        ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%Y"))
    axes.flat[0].legend(loc="upper left", fontsize=8)
    fig.suptitle("Prognos 6 månader framåt, hela landet (enkel säsongs- och trendmodell)", fontsize=13)
    save(fig, out, "07_prognos.png",
         SOURCE + " Illustration – inte en officiell prognos. Byt gärna modell (t.ex. TimesFM, Prophet, ETS).")


def annual_table(sol, annual, out):
    order = ["Bedrägeri och annan oredlighet", "Social manipulation, totalt", "Befogenhetsbedrägeri",
             "Romansbedrägeri", "Investeringsbedrägeri", "Fakturabedrägeri", "Identitetsbedrägeri",
             "Annonsbedrägeri", "Kortbedrägeri utan fysiskt kort", "Olovlig identitetsanvändning",
             "Penningtvättsbrott, totalt"]
    a = annual[annual.Serie.isin(order)].pivot_table(index="Serie", columns="År", values="Antal").reindex(order)
    years = [c for c in a.columns if c >= a.columns.max() - 6]
    lines = ["| Brottstyp | " + " | ".join(str(y) for y in years) + " | Förändring |",
             "|---|" + "---:|" * (len(years) + 1)]
    for serie, r in a[years].iterrows():
        vals = ["–" if pd.isna(v) else f"{v:,.0f}".replace(",", "\u202f") for v in r.values]
        first = r.dropna()
        chg = f"{r.iloc[-1] / first.iloc[0] - 1:+.0%}" if len(first) > 1 else ""
        lines.append(f"| {serie} | " + " | ".join(vals) + f" | {chg} ({first.index[0]}–{years[-1]}) |")
    # CTF / sanktioner (små tal) från SOL
    ctf = sol[(sol.serie.isin(["terrorfinansiering", "sanktionsbrott", "naringspenningtvatt"]))
              & (sol.omrade == "Hela landet") & (sol.periodtyp == "ar")]
    ct = ctf.pivot_table(index=["brottskod", "brott"], columns="ar", values="antal", aggfunc="sum")
    ct = ct[[c for c in ct.columns if c >= 2019]].dropna(how="all")
    lines += ["", "| Kod | Brott | " + " | ".join(str(int(c)) for c in ct.columns) + " |",
              "|---|---|" + "---:|" * len(ct.columns)]
    for (kod, brott), r in ct.iterrows():
        name = brott.split(" - ", 1)[-1]
        name = name if len(name) <= 80 else name[:77].rstrip(" ,") + "…"
        lines.append(f"| {kod} | {name} | " + " | ".join("–" if pd.isna(v) else f"{v:,.0f}".replace(",", "\u202f")
                                                     for v in r.values) + " |")
    p = out / "arstabell.md"
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("  +", p)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", help="Katalog för PNG-filer (standard: data/charts)")
    ap.add_argument("--theme", choices=["light", "dark", "both"], default="both",
                    help="Ljusa grafer, mörka (filnamn *_dark.png) eller båda (standard)")
    a = ap.parse_args()
    d = data_dir()
    out = Path(a.out) if a.out else d / "charts"
    out.mkdir(parents=True, exist_ok=True)

    sol = load_sol(d)
    try:
        import parse_bra as pb
        annual, susp = pb.annual(), pb.suspects()
    except (FileNotFoundError, ValueError, KeyError, IndexError) as e:
        annual = susp = None
        print(f"  (hoppar över årstabell/misstänkta – kör fetch_tables.py först: {e})")

    for theme in (["light", "dark"] if a.theme == "both" else [a.theme]):
        use_theme(theme)
        with plt.rc_context(THEMES[theme]["rc"]):
            chart_monthly(sol, out)
            chart_modus_r12(sol, out)
            chart_region_ytd(sol, out)
            chart_region_per100k(sol, out)
            chart_forecast(sol, out)
            if annual is not None:
                try:
                    chart_elderly(annual, out)
                    chart_suspects(susp, out)
                except (ValueError, KeyError, IndexError) as e:
                    print(f"  (hoppar över äldre/misstänkta: {e})")
    if annual is not None:
        annual_table(sol, annual, out)


if __name__ == "__main__":
    main()
