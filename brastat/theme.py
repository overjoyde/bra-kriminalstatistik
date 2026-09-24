"""Färgteman för matplotlib, samma paletter som HTML-dashboarden.

Används av scripts/make_charts.py och fungerar direkt i en notebook
(Jupyter, Colab, BigQuery Studio):

    from brastat import theme
    theme.apply("dark")     # alla grafer efter detta blir mörka
    theme.apply("light")    # tillbaka till ljust

Modulen byter aldrig matplotlib-backend, så grafer fortsätter att visas
i notebookens celler. matplotlib importeras först när apply() anropas.
"""
from __future__ import annotations

# Serieordning: blå, orange, grön, röd, lila, brun, rosa, grå.
# Den mörka paletten har samma färgtoner som den ljusa, bara ljusare.
PALETTES = {
    "light": ["#3b75af", "#ef8636", "#519e3e", "#c53a32", "#8d69b8", "#84584e", "#d57dbf", "#7f7f7f"],
    "dark": ["#6d9bf7", "#f5a255", "#6cc36a", "#ff8a80", "#b39ddb", "#c9a393", "#e57ad0", "#9aa3b2"],
}

# Bakgrund och förgrund (text, nollinjer).
COLORS = {
    "light": {"bg": "white", "fg": "black", "muted": "black", "edge": "black", "grid": "#b0b0b0",
              "legend_bg": "white", "legend_edge": "#cccccc"},
    "dark": {"bg": "#171c25", "fg": "#e3e6eb", "muted": "#9aa3b2", "edge": "#5c6677", "grid": "#5c6677",
             "legend_bg": "#141922", "legend_edge": "#394254"},
}

# Grundstil som gäller oavsett tema.
BASE = {
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.alpha": 0.3, "axes.titlesize": 12,
    "legend.frameon": True, "legend.fontsize": 9, "axes.formatter.use_locale": False,
}


def rc(name: str = "dark", base: bool = True) -> dict:
    """rcParams för ett tema: bakgrund, text, rutnät och seriepalett."""
    if name not in COLORS:
        raise ValueError(f"okänt tema {name!r}, välj bland {sorted(COLORS)}")
    from cycler import cycler

    c = COLORS[name]
    params = {
        "figure.facecolor": c["bg"], "axes.facecolor": c["bg"], "savefig.facecolor": c["bg"],
        "axes.edgecolor": c["edge"], "axes.labelcolor": c["fg"], "axes.titlecolor": c["fg"],
        "text.color": c["fg"], "xtick.color": c["muted"], "ytick.color": c["muted"],
        "grid.color": c["grid"], "legend.facecolor": c["legend_bg"], "legend.edgecolor": c["legend_edge"],
        "legend.labelcolor": c["fg"], "axes.prop_cycle": cycler(color=PALETTES[name]),
    }
    return {**BASE, **params} if base else params


def apply(name: str = "dark", base: bool = True) -> None:
    """Sätt temat globalt för alla grafer som ritas efter anropet."""
    import matplotlib as mpl

    mpl.rcParams.update(rc(name, base))
