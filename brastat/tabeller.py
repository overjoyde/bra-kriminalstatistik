"""Hämta Brås färdiga tabeller (Excel), diagramdata, rapporter och metoddokument från bra.se.

Brå har inget publikt API för de färdiga tabellerna. Tabellerna nås via sidans
"StatSelector"-formulär, som i JavaScript bygger en URL
``/statistik_sidor/<kategori>/<år>/<prefix><område>-<period>.html``. Den sidan
innehåller i sin tur en länk till Excel-filen. Modulen återskapar den logiken
(motsvarar ``submitFormAnmaldaPrel`` / ``submitformPeriodRegion`` i bra.se:s
webapp-assets.js) och laddar ned filerna.

Resultatet loggas i ``manifest.csv`` (URL, status, storlek, sha256). Om Brå byter
webbplattform syns det som ``saknas`` i manifestet.
"""
from __future__ import annotations

import csv
import datetime as dt
import hashlib
import json
import re
import urllib.parse
from pathlib import Path

from .http import Client

BASE = "https://bra.se"
REGIONS = ["La", "Rn01", "Rn02", "Rn03", "Rn04", "Rn05", "Rn06", "Rn07"]  # La = hela landet
POLIS_REGIONS = REGIONS[1:]
REGION_NAMES = {"La": "Hela landet", "Rn01": "Nord", "Rn02": "Mitt", "Rn03": "Öst", "Rn04": "Väst",
                "Rn05": "Syd", "Rn06": "Stockholm", "Rn07": "Bergslagen"}

GROUPS = ["anmalda", "misstankta", "lagforda", "handlagda", "malsagare", "enkater", "amnessidor",
          "rapporter", "metod"]

REPORT_PAGES = [
    "rapporter/arkiv/2025-12-11-foretag-som-brottsverktyg",
    "rapporter/arkiv/2026-02-26-brottsutvecklingen-i-sverige-2006-2024",
    "rapporter/arkiv/2026-03-19-bostadsrattsforeningars-utsatthet-och-sarbarhet-for-ekonomisk-brottslighet",
    "rapporter/arkiv/2025-10-15-nationella-trygghetsundersokningen-2025",
    "rapporter/arkiv/2025-04-25-brottsutvecklingen-till-och-med-2024",
    "rapporter/arkiv/2019-12-10-penningtvattsbrott",
    "rapporter/arkiv/2021-04-28-finansiering-av-terrorism",
    "rapporter/arkiv/2015-12-15-penningtvatt-och-annan-penninghantering",
]
EXTRA_REPORTS = [
    "/download/18.3808406a192bd2f0b727c8f/1730736409029/2023_11_Bedragerier-mot-privatpersoner.pdf",
]

ANM = "statistik/statistik-fran-rattsvasendet/anmalda-brott"
MISST = "statistik/statistik-fran-rattsvasendet/misstankta-personer"
LAGF = "statistik/statistik-fran-rattsvasendet/personer-lagforda-for-brott"
HANDL = "statistik/statistik-fran-rattsvasendet/handlagda-brott"


def default_last_full_year(today: dt.date | None = None) -> int:
    """Slutlig årsstatistik för år X publiceras i mars–april år X+1."""
    today = today or dt.date.today()
    return today.year - 1 if today.month >= 4 else today.year - 2


class TableFetcher:
    def __init__(self, out: Path, force: bool = False, last_full_year: int | None = None,
                 years: int = 10, client: Client | None = None):
        self.out = Path(out)
        self.raw = self.out / "raw"
        self.docs = self.out / "docs"
        self.force = force
        self.http = client or Client()
        self.last = last_full_year or default_last_full_year()
        self.years = list(range(self.last - years + 1, self.last + 1))
        self.manifest: list[dict] = []
        self.prev_urls = self._read_prev_urls()

    # ---- helpers -------------------------------------------------------
    def _read_prev_urls(self) -> dict[str, str]:
        """fil -> URL från förra körningens manifest."""
        path = self.out / "manifest.csv"
        if not path.exists():
            return {}
        with path.open(encoding="utf-8") as f:
            return {r["file"]: r["url"] for r in csv.DictReader(f) if r.get("file") and r.get("url")}

    def _log(self, **kw):
        self.manifest.append({k: kw.get(k, "") for k in ("group", "file", "url", "status", "bytes", "sha256", "note")})

    def _rel(self, p: Path) -> str:
        return p.relative_to(self.out).as_posix()

    def save(self, url: str, dest: Path, group: str, note: str = "") -> None:
        dest.parent.mkdir(parents=True, exist_ok=True)
        status = "cached"
        # Brås nedladdningslänkar innehåller id och tidsstämpel (/download/18.x/<ms>/fil.xlsx).
        # Ny länk till samma filnamn = ny version, t.ex. när preliminär statistik fryses.
        prev = self.prev_urls.get(self._rel(dest))
        changed = dest.exists() and prev is not None and prev != url
        if self.force or not dest.exists() or changed:
            try:
                dest.write_bytes(self.http.get(url))
                status = "uppdaterad" if changed else "ok"
            except Exception as e:  # noqa: BLE001 – logga och fortsätt
                self._log(group=group, url=url, status=f"FEL: {e}", bytes=0, note=note)
                print(f"  x {url}  ({e})")
                return
        data = dest.read_bytes()
        self._log(group=group, file=self._rel(dest), url=url, status=status, bytes=len(data),
                  sha256=hashlib.sha256(data).hexdigest(), note=note)
        print(f"  {'.' if status == 'cached' else '+'} {self._rel(dest)}")

    def resolve_statpage(self, divurl: str) -> str | None:
        try:
            html = self.http.text(f"{BASE}/statistik_sidor/{divurl}.html")
        except Exception:  # noqa: BLE001
            return None
        m = re.search(r'href="(/download/[^"]+\.(?:xlsx|xls))"', html)
        return BASE + m.group(1) if m else None

    def stat_table(self, divurl: str, folder: str, group: str, note: str = "") -> None:
        url = self.resolve_statpage(divurl)
        if not url:
            self._log(group=group, url=f"{BASE}/statistik_sidor/{divurl}.html", status="saknas", bytes=0, note=note)
            print(f"  - saknas: {divurl}")
            return
        fname = urllib.parse.unquote(url.rsplit("/", 1)[1])
        self.save(url, self.raw / folder / fname, group, note)

    def page_files(self, page: str, dest: Path, group: str, pattern: str = r"\.(?:xlsx|xls|csv)$",
                   exclude: str | None = None) -> None:
        html = self.http.text(f"{BASE}/{page}")
        for link in sorted(set(re.findall(r'(?:https://bra\.se)?(/download/[^"\'\s]+)', html))):
            name = urllib.parse.unquote(link.rsplit("/", 1)[1])
            if not re.search(pattern, name, re.I) or (exclude and re.search(exclude, name, re.I)):
                continue
            self.save(BASE + link, dest / name, group)

    def chart_data(self, page: str, out: Path, group: str) -> None:
        """Extrahera diagramdata (bra-charts ``chartData``) från en ämnessida till CSV."""
        html = self.http.text(f"{BASE}/{page}")
        dec = json.JSONDecoder()
        rows = []
        for m in re.finditer(r"registerInitialState\('[^']+',", html):
            try:
                obj, _ = dec.raw_decode(html, m.end())
            except json.JSONDecodeError:
                continue
            cd = obj.get("chartData") if isinstance(obj, dict) else None
            if not cd:
                continue
            for q in cd.get("questions", []):
                for s in q.get("series", []):
                    for label, val in zip(q.get("labels", []), s.get("data", [])):
                        rows.append(dict(chart=cd.get("chartTitle"), question=q.get("customName") or q.get("name"),
                                         series=s.get("title"), label=label, value=val,
                                         description=cd.get("chartDescription")))
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["chart", "question", "series", "label", "value", "description"])
            w.writeheader()
            w.writerows(rows)
        data = out.read_bytes()
        self._log(group=group, file=self._rel(out), url=f"{BASE}/{page}", status="extraherad", bytes=len(data),
                  sha256=hashlib.sha256(data).hexdigest(), note=f"{len(rows)} rader diagramdata")
        print(f"  + {self._rel(out)} ({len(rows)} rader)")

    def latest_options(self, page: str, form_prefix: str) -> list[str]:
        html = self.http.text(f"{BASE}/{page}")
        m = re.search(rf'id="period_{form_prefix}"[^>]*>(.*?)</select>', html, re.S)
        return re.findall(r'<option value="([^"-][^"]*)"', m.group(1)) if m else []

    # ---- groups --------------------------------------------------------
    def anmalda(self) -> None:
        print("\n[anmalda] Anmälda brott – preliminär månads-/kvartalsstatistik")
        p1 = self.latest_options(ANM, "P1")
        if p1:
            latest_month = p1[0]  # t.ex. "Aug-2026"
            year = latest_month.split("-")[1]
            for r in REGIONS:
                self.stat_table(f"P1/{year}/P1{r}{latest_month}", "anmalda_brott/prel_P1M_manad", "anmalda",
                                f"P1M {latest_month} {r}")
                self.stat_table(f"P3/{year}/P3{r}{latest_month}", "anmalda_brott/prel_P3_utveckling", "anmalda",
                                f"P3 {latest_month} {r}")
        p2 = self.latest_options(ANM, "P2")
        if p2:
            q, qy = p2[0], p2[0].split("-")[1]
            for reg in ("P1", "P2"):  # P1 = hela landet, P2 = alla områden
                self.stat_table(f"{reg}/{qy}/{reg}{q}", "anmalda_brott/prel_kvartal", "anmalda", f"kvartal {q} {reg}")

        print("\n[anmalda] Tidsserier per månad (landet 2015–, regioner 2022–)")
        for opt in self.latest_options(ANM, "P4"):
            y = opt.split("/")[1]
            if opt.startswith("P4", 8):  # regionversion (>= 2022)
                for r in REGIONS:
                    self.stat_table(opt.replace("Region", r), "anmalda_brott/tidsserie_manad", "anmalda", f"{y} {r}")
            else:
                self.stat_table(opt, "anmalda_brott/tidsserie_manad", "anmalda", f"{y} La")

        print("\n[anmalda] Slutlig årsstatistik")
        for y in self.years:
            self.stat_table(f"100/{y}/100La-{y}", "anmalda_brott/ar_100_landet", "anmalda", f"tabell 100 {y}")
            self.stat_table(f"110/{y}/110La-{y}", "anmalda_brott/ar_110_regioner", "anmalda", f"tabell 110 {y}")
        for y in self.years[-3:]:
            for r in POLIS_REGIONS:
                self.stat_table(f"120/{y}/120{r}-{y}", "anmalda_brott/ar_120_kommuner", "anmalda", f"tabell 120 {y} {r}")
        self.page_files(ANM, self.raw / "anmalda_brott/tidsserier_och_kommun", "anmalda")

    def misstankta(self) -> None:
        print("\n[misstankta] Misstänkta personer (brottstyp x ålder x kön, lagföringsbeslut)")
        for y in self.years:
            self.stat_table(f"220/{y}/220La-{y}", "misstankta/220_brottstyp_alder_kon", "misstankta", f"220 {y}")
            self.stat_table(f"230/{y}/230aLa-{y}", "misstankta/230a_lagforingsbeslut_brottstyp", "misstankta", f"230a {y}")
            self.stat_table(f"230/{y}/230bLa-{y}", "misstankta/230b_lagforingsbeslut_alder", "misstankta", f"230b {y}")
        self.page_files(MISST, self.raw / "misstankta/tidsserier", "misstankta")

    def lagforda(self) -> None:
        print("\n[lagforda] Personer lagförda för brott")
        for y in self.years:
            self.stat_table(f"420/{y}/420La-{y}", "lagforda/420_lagforingsbeslut_brott", "lagforda", f"420 {y}")
            self.stat_table(f"450/{y}/450La-{y}", "lagforda/450_huvudbrott_alder", "lagforda", f"450 {y}")
            self.stat_table(f"460/{y}/460La-{y}", "lagforda/460_huvudbrott_region", "lagforda", f"460 {y}")
        self.page_files(LAGF, self.raw / "lagforda/tidsserier", "lagforda")

    def handlagda(self) -> None:
        print("\n[handlagda] Handlagda brott och uppklaring")
        for y in self.years:
            for t in ("300", "310", "320"):
                self.stat_table(f"{t}/{y}/{t}La-{y}", f"handlagda/{t}", "handlagda", f"{t} {y}")
        cur = self.last + 1
        for t in ("301", "311"):  # halvår innevarande år
            self.stat_table(f"{t}/{cur}/{t}La-{cur}", f"handlagda/{t}_halvar", "handlagda", f"{t} {cur} halvår")
        self.page_files(HANDL, self.raw / "handlagda/tidsserier", "handlagda")
        self.page_files("statistik/statistik-fran-rattsvasendet/handlaggningsresultat",
                        self.raw / "handlaggningsresultat", "handlagda")

    def malsagare(self) -> None:
        print("\n[malsagare] Målsägare vid brottsanmälan")
        for y in self.years:
            self.stat_table(f"malsagare/{y}/malsagare_vid_brottsanmalan_{y}", "malsagare/tabellverk", "malsagare", str(y))
        self.page_files("statistik/statistik-fran-rattsvasendet/malsagare-vid-brottsanmalan",
                        self.raw / "malsagare", "malsagare")

    def enkater(self) -> None:
        print("\n[enkater] NTU och Skolundersökningen om brott")
        self.page_files("statistik/statistik-fran-enkatundersokningar/nationella-trygghetsundersokningen",
                        self.raw / "ntu", "enkater")
        self.page_files("statistik/statistik-fran-enkatundersokningar/skolundersokningen-om-brott",
                        self.raw / "skolundersokningen", "enkater")

    def amnessidor(self) -> None:
        print("\n[amnessidor] Diagramdata från ämnessidor")
        self.chart_data("amnen/bedrageri", self.raw / "amnessidor/bedrageri_diagramdata.csv", "amnessidor")
        self.chart_data("amnen/penningtvatt-och-finansiering-av-terrorism",
                        self.raw / "amnessidor/penningtvatt_terrorfinansiering_diagramdata.csv", "amnessidor")

    def rapporter(self) -> None:
        print("\n[rapporter] Rapporter (PDF)")
        for page in REPORT_PAGES:
            self.page_files(page, self.docs / "rapporter", "rapporter", pattern=r"\.pdf$",
                            exclude=r"(Money_Laundering|Financing_of_terrorism|Swedish Crime Survey|Begrepp)")
        for link in EXTRA_REPORTS:
            self.save(BASE + link, self.docs / "rapporter" / link.rsplit("/", 1)[1], "rapporter")

    def metod(self) -> None:
        print("\n[metod] Begrepp, kvalitetsdeklarationer, statistikrapporter")
        for page in (ANM, MISST, LAGF, HANDL):
            self.page_files(page, self.docs / "metod", "metod", pattern=r"\.pdf$")

    # ---- run -----------------------------------------------------------
    def run(self, groups: list[str] | None = None) -> Path:
        for g in groups or GROUPS:
            try:
                getattr(self, g)()
            except Exception as e:  # noqa: BLE001 – en grupp får inte stoppa resten
                self._log(group=g, status=f"FEL: {e}")
                print(f"  x grupp {g} misslyckades: {e}")
        return self.write_manifest()

    def write_manifest(self) -> Path:
        self.out.mkdir(parents=True, exist_ok=True)
        path = self.out / "manifest.csv"
        old: list[dict] = []
        if path.exists():  # behåll poster för grupper som inte kördes nu
            groups_now = {m["group"] for m in self.manifest}
            with path.open(encoding="utf-8") as f:
                old = [r for r in csv.DictReader(f) if r.get("group") not in groups_now]
        with path.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["group", "file", "url", "status", "bytes", "sha256", "note"])
            w.writeheader()
            w.writerows(old + self.manifest)
        ok = sum(1 for m in self.manifest if m["status"] in ("ok", "uppdaterad", "cached", "extraherad"))
        print(f"\nKlart {dt.datetime.now():%Y-%m-%d %H:%M}: {ok}/{len(self.manifest)} poster OK -> {path}")
        return path
