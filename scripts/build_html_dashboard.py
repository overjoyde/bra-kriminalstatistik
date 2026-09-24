"""Build a self-contained HTML dashboard: dashboard/Bra_trendbevakning_dashboard.html

Usage:
    python scripts/build_html_dashboard.py

No external dependencies at view time (no CDN) — charts are drawn as inline SVG
by vanilla JS, data is embedded as JSON. Source: Brå (public statistics, PSI).
"""
from __future__ import annotations

import json
import os
from datetime import date

import parse_bra as pb
from build_excel_dashboard import TYPOLOGY_MAP, REGION_ORDER

OUT = os.path.join(pb.ROOT, "dashboard", "Bra_trendbevakning_dashboard.html")


def build():
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
    }
    html = (TEMPLATE.replace("/*__DARK__*/", DARK_THEME)
            .replace("/*__DATA__*/null", json.dumps(data, ensure_ascii=False, separators=(",", ":"))))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html)
    print(OUT, f"{len(html)/1024:.0f} KB")


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

TEMPLATE = r"""<!doctype html>
<html lang="sv">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Brå-trendbevakning – bedrägeri och penningtvätt</title>
<style>
  :root{color-scheme:light;
        --navy:#1F3864;--onnavy:#fff;--accent:#1F3864;--ink:#1d1d1f;--muted:#6b7280;--line:#e5e7eb;--bg:#f6f7f9;--card:#fff;
        --surface:#fff;--field:#cbd2d9;--soft:#eef2f8;--hover:#f8fafc;--flatbg:#f1f3f5;--warnbg:#fff8f0;
        --tipbg:#111827;--tipfg:#fff;--grid:#eef0f3;--axis:#9ca3af;--label:#1d1d1f;--barlbl:#374151;
        --heatup:192,57,43;--heatdown:30,123,69;
        --up:#c0392b;--upbg:#fdecea;--down:#1e7b45;--downbg:#e7f5ec;
        --c1:#1F3864;--c2:#e07a1f;--c3:#2a9d8f;--c4:#b5179e;--c5:#6c8ebf;--c6:#8d6e63;--c7:#9aa5b1}
  @media (prefers-color-scheme: dark){:root:not([data-theme="light"]){/*__DARK__*/}}
  :root[data-theme="dark"]{/*__DARK__*/}
  *{box-sizing:border-box}
  body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif;color:var(--ink);background:var(--bg);font-size:14px}
  header{background:var(--navy);color:var(--onnavy);padding:20px 32px}
  header h1{margin:0;font-size:22px;font-weight:650}
  header p{margin:6px 0 0;opacity:.8;font-size:13px}
  .controls{display:flex;gap:18px;align-items:center;flex-wrap:wrap;padding:14px 32px;background:var(--surface);border-bottom:1px solid var(--line);position:sticky;top:0;z-index:5}
  .controls label{font-size:12px;color:var(--muted);display:flex;gap:8px;align-items:center}
  select{font:inherit;padding:5px 8px;border:1px solid var(--field);border-radius:6px;background:var(--surface);color:var(--ink)}
  .pill{background:var(--soft);color:var(--accent);border-radius:999px;padding:4px 10px;font-size:12px;font-weight:600}
  .theme{margin-left:auto;font:inherit;font-size:12px;border:1px solid var(--field);background:var(--surface);color:var(--ink);border-radius:6px;padding:4px 10px;cursor:pointer}
  main{padding:24px 32px;max-width:1500px;margin:0 auto}
  .grid{display:grid;gap:18px}
  .kpis{grid-template-columns:repeat(auto-fit,minmax(210px,1fr))}
  .two{grid-template-columns:repeat(auto-fit,minmax(520px,1fr))}
  .card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:16px 18px}
  .card h2{font-size:15px;margin:0 0 4px;color:var(--accent)}
  .card .sub{font-size:12px;color:var(--muted);margin:0 0 10px}
  .kpi .lbl{font-size:12px;color:var(--muted)}
  .kpi .tm{font-size:11px;color:var(--accent);font-weight:600;text-transform:uppercase;letter-spacing:.04em}
  .kpi .val{font-size:28px;font-weight:700;margin:4px 0}
  .kpi .cmp{font-size:12px;color:var(--muted)}
  .chg{font-weight:700;border-radius:5px;padding:1px 6px;font-size:12px;white-space:nowrap}
  .chg.up{color:var(--up);background:var(--upbg)} .chg.down{color:var(--down);background:var(--downbg)} .chg.flat{color:var(--muted);background:var(--flatbg)}
  section{margin-top:22px}
  table{border-collapse:collapse;width:100%;font-size:13px}
  th{background:var(--navy);color:var(--onnavy);font-weight:600;text-align:right;padding:8px;font-size:12px;position:sticky;top:0}
  th:first-child,th:nth-child(2){text-align:left}
  td{padding:7px 8px;border-bottom:1px solid var(--line);text-align:right;white-space:nowrap}
  td:first-child{text-align:left;font-weight:600} td:nth-child(2){text-align:left;color:var(--muted)}
  tr:hover td{background:var(--hover)}
  .heat tr:hover td.hc{filter:brightness(1.08)}
  .tag{display:inline-block;font-size:11px;padding:2px 7px;border-radius:4px;background:var(--soft);color:var(--accent);font-weight:600}
  .chart{width:100%;height:300px;position:relative}
  .chart svg{width:100%;height:100%;overflow:visible}
  .legend{display:flex;flex-wrap:wrap;gap:6px 14px;font-size:12px;margin-top:6px}
  .legend span{display:flex;align-items:center;gap:6px;cursor:pointer;user-select:none}
  .legend span.off{opacity:.35}
  .legend i{width:12px;height:3px;border-radius:2px;display:inline-block}
  .tip{position:fixed;left:0;top:0;pointer-events:none;background:var(--tipbg);color:var(--tipfg);border:1px solid var(--line);font-size:12px;padding:7px 9px;border-radius:6px;opacity:0;transition:opacity .1s;white-space:nowrap;z-index:10}
  .note{font-size:12px;color:var(--muted);line-height:1.5}
  .warn{border-left:4px solid var(--c2);background:var(--warnbg)}
  code{color:var(--ink)}
  .heat td.hc{font-weight:600}
  footer{padding:24px 32px 40px;color:var(--muted);font-size:12px;max-width:1500px;margin:0 auto}
  .tabs{display:flex;gap:6px;margin-bottom:8px;flex-wrap:wrap}
  .tabs button{font:inherit;font-size:12px;border:1px solid var(--field);background:var(--surface);color:var(--ink);border-radius:6px;padding:4px 10px;cursor:pointer}
  .tabs button.on{background:var(--navy);color:var(--onnavy);border-color:var(--navy)}
  .chart .gl{stroke:var(--grid)} .chart .ax{fill:var(--muted)} .chart .zl{stroke:var(--axis)}
  .chart .bl{fill:var(--label)} .chart .bv{fill:var(--barlbl)}
  @media print{.controls{position:static}.card{break-inside:avoid}}
</style>
</head>
<body>
<header>
  <h1>Brå-trendbevakning – bedrägeri och penningtvätt</h1>
  <p>Offentlig, aggregerad statistik från Brottsförebyggande rådet (Brå). Anmälda brott, inte faktisk brottslighet. Brottskoderna anger inte betalmedel – kopplingen till en viss betaltjänst är indirekt, via modus.</p>
</header>
<div class="controls">
  <label>Region <select id="region"></select></label>
  <label>Jämförelsemånad <select id="month"></select></label>
  <span class="pill" id="asof"></span>
  <span class="pill" id="final"></span>
  <button class="theme" id="theme" type="button"></button>
</div>
<main>
  <div class="grid kpis" id="kpis"></div>

  <section class="card">
    <h2>Brottstyper och modus per typologi</h2>
    <p class="sub" id="tblsub"></p>
    <div style="overflow-x:auto"><table id="kpitable"></table></div>
    <p class="note">Rött betyder en ökning över 5 % och grönt en minskning över 5 %. Det beskriver förändringen, inte risken. Månadssiffrorna är preliminära och jämförs med preliminära siffror för föregående år, så som Brå gör. Siffrorna för senaste slutliga år gäller alltid hela landet.</p>
  </section>

  <section class="grid two">
    <div class="card"><h2>Social manipulation jämfört med kortbedrägeri</h2><p class="sub">Rullande 12 månader (R12). Förflyttning mellan betalmetoder.</p>
      <div class="chart" id="ch-shift"></div><div class="legend" id="lg-shift"></div></div>
    <div class="card"><h2>Social manipulation och företagsrelaterade modus</h2><p class="sub">Rullande 12 månader (R12). Klicka i förklaringen för att dölja eller visa en serie.</p>
      <div class="chart" id="ch-modus"></div><div class="legend" id="lg-modus"></div></div>
  </section>

  <section class="grid two">
    <div class="card"><h2>Penningtvättsbrott per år</h2><p class="sub">Slutlig statistik, hela landet (tabell 100)</p>
      <div class="chart" id="ch-pt"></div></div>
    <div class="card"><h2>Förändring per polisregion</h2><p class="sub" id="regsub"></p>
      <div class="tabs" id="regtabs"></div><div class="chart" id="ch-reg"></div></div>
  </section>

  <section class="grid two">
    <div class="card"><h2>Andel misstänkta i åldern 15–24 år</h2><p class="sub">Tabell 220, slutlig statistik. Ett mått som kan antyda rekrytering av unga som målvakter (money mules).</p>
      <div class="chart" id="ch-young"></div><div class="legend" id="lg-young"></div></div>
    <div class="card"><h2>Självrapporterad utsatthet (NTU)</h2><p class="sub">Andel av befolkningen 16–84 år. Inkluderar brott som inte anmälts.</p>
      <div class="chart" id="ch-ntu"></div><div class="legend" id="lg-ntu"></div></div>
  </section>

  <section class="card">
    <h2>Anmälda brott per polisregion, hittills i år</h2><p class="sub" id="heatsub"></p>
    <div style="overflow-x:auto"><table id="heat" class="heat"></table></div>
    <p class="note">Summan av regionerna kan avvika något från hela landet, eftersom en del brott saknar känd region.</p>
  </section>

  <section class="card warn">
    <h2>Förbehåll</h2>
    <ul class="note">
      <li><b>Penningtvätt:</b> den preliminära månadsstatistiken ligger långt under den slutliga (2025: <span id="ptgap"></span>). Använd de slutliga årssiffrorna för nivåer.</li>
      <li>Uppdelningen på modus, till exempel social manipulation, befogenhets- och annonsbedrägeri, finns i datat från 2019. Polisregioner finns från 2022.</li>
      <li>Identitetsbedrägeri minskar kraftigt 2021–2023, delvis på grund av ändrad registrering. Förändringen över 5 år går därför inte att tolka rakt av.</li>
      <li>Bedrägeri är ett seriebrott. Enskilda stora ärenden kan ge toppar i statistiken. Brottskoderna anger inte vilket betalmedel som använts.</li>
      <li>Läs <code>docs/metod/</code> (begrepp och kvalitetsdeklarationer) innan du tolkar siffrorna.</li>
    </ul>
  </section>
</main>
<footer>
  Källa: Brottsförebyggande rådet (Brå). Offentlig statistik som får vidareutnyttjas fritt (PSI). Genererad <span id="gen"></span> av <code>scripts/build_html_dashboard.py</code>.
  Uppdatera så här: <code>python scripts/fetch_tables.py</code> och sedan <code>python scripts/build_html_dashboard.py</code>.
</footer>

<script>
const D = /*__DATA__*/null;
const COLORS = ["var(--c1)","var(--c2)","var(--c3)","var(--c4)","var(--c5)","var(--c6)","var(--c7)"];
const fmt = n => n==null||isNaN(n) ? "–" : Math.round(n).toLocaleString("sv-SE");
const fmt1 = n => n==null||isNaN(n) ? "–" : n.toLocaleString("sv-SE",{maximumFractionDigits:1,minimumFractionDigits:1});
const pct = n => n==null||!isFinite(n) ? "–" : (n>0?"+":"")+(n*100).toLocaleString("sv-SE",{maximumFractionDigits:1,minimumFractionDigits:1})+" %";
const pctPlain = n => n==null||!isFinite(n) ? "–" : (n*100).toLocaleString("sv-SE",{maximumFractionDigits:1,minimumFractionDigits:1})+" %";
const chg = (n) => { if(n==null||!isFinite(n)) return '<span class="chg flat">–</span>';
  const c = n>0.05?"up":n<-0.05?"down":"flat"; return `<span class="chg ${c}">${pct(n)}</span>`; };
const MONTHS = ["jan","feb","mar","apr","maj","jun","jul","aug","sep","okt","nov","dec"];
const ym = (y,m) => `${y}-${String(m).padStart(2,"0")}`;

// ---------- data helpers ----------
const nat = D.monthly["Hela landet"];
const allKeys = Object.keys(nat["Samtliga brott"]).sort();
const latestKey = allKeys[allKeys.length-1];
const finalYear = Math.max(...Object.keys(D.annual["Samtliga brott"]).map(Number));
function mv(region, serie, y, m){ const s=(D.monthly[region]||{})[serie]; return s? s[ym(y,m)] : undefined; }
function ytd(region, serie, y, m){ const s=(D.monthly[region]||{})[serie]; if(!s) return null;
  let t=0, any=false; for(let i=1;i<=m;i++){ const v=s[ym(y,i)]; if(v!=null){t+=v;any=true;} } return any?t:null; }
function r12(serie, region="Hela landet"){ const s=D.monthly[region][serie]||{}; const ks=Object.keys(s).sort(); const out=[];
  for(let i=11;i<ks.length;i++){ let t=0; for(let j=i-11;j<=i;j++) t+=s[ks[j]]; out.push([ks[i],t]); } return out; }
const ratio = (a,b) => (a==null||b==null||b===0) ? null : a/b-1;

// ---------- controls ----------
const regSel=document.getElementById("region"), monSel=document.getElementById("month");
D.regions.forEach(r=>regSel.add(new Option(r,r)));
allKeys.filter(k=>k>="2023-01").reverse().forEach(k=>{const [y,m]=k.split("-").map(Number); monSel.add(new Option(`${MONTHS[m-1]} ${y}`,k));});
document.getElementById("asof").textContent = `Senaste preliminära månad: ${MONTHS[+latestKey.slice(5)-1]} ${latestKey.slice(0,4)}`;
document.getElementById("final").textContent = `Senaste slutliga år: ${finalYear}`;
document.getElementById("gen").textContent = D.generated;
regSel.onchange = monSel.onchange = renderAll;

// ---------- theme: auto (följer systemet) → mörkt → ljust ----------
const THEMES = {auto:"Tema: auto", dark:"Tema: mörkt", light:"Tema: ljust"};
const themeBtn = document.getElementById("theme");
function applyTheme(t){ if(t==="auto") delete document.documentElement.dataset.theme; else document.documentElement.dataset.theme=t;
  themeBtn.textContent = THEMES[t]; }
let theme = "auto"; try { theme = localStorage.getItem("bra-theme") || "auto"; } catch(e) {}
if(!THEMES[theme]) theme = "auto";
applyTheme(theme);
themeBtn.onclick = () => { const order=["auto","dark","light"]; theme=order[(order.indexOf(theme)+1)%3]; applyTheme(theme);
  try { localStorage.setItem("bra-theme", theme); } catch(e) {} };

// ---------- KPI cards + table ----------
const SERIES = Object.keys(D.tm);
function renderKpis(){
  const region=regSel.value, [Y,M]=monSel.value.split("-").map(Number);
  const cards = ["Social manipulation, totalt","Befogenhetsbedrägeri","Kortbedrägeri utan fysiskt kort","Penningtvättsbrott, totalt"];
  document.getElementById("kpis").innerHTML = cards.map(s=>{
    const cur=ytd(region,s,Y,M), prev=ytd(region,s,Y-1,M);
    return `<div class="card kpi"><div class="tm">${D.tm[s]}</div><div class="lbl">${s}, jan–${MONTHS[M-1]} ${Y}</div>
      <div class="val">${fmt(cur)}</div><div class="cmp">${chg(ratio(cur,prev))} jämfört med jan–${MONTHS[M-1]} ${Y-1} (${fmt(prev)})</div></div>`;
  }).join("");
  document.getElementById("tblsub").textContent = `${region} · ${MONTHS[M-1]} ${Y} · slutlig statistik ${finalYear} gäller hela landet`;
  const head = `<tr><th>Brottstyp / modus</th><th>Typologi</th><th>${MONTHS[M-1]} ${Y}</th><th>${MONTHS[M-1]} ${Y-1}</th><th>Förändring</th>
    <th>Jan–${MONTHS[M-1]} ${Y}</th><th>Jan–${MONTHS[M-1]} ${Y-1}</th><th>Förändring</th><th>Andel mot äldre</th>
    <th>${finalYear} (slutligt)</th><th>Per 100 000 inv</th><th>Förändring 5 år</th></tr>`;
  const rows = SERIES.map(s=>{
    const c=mv(region,s,Y,M), p=mv(region,s,Y-1,M), cy=ytd(region,s,Y,M), py=ytd(region,s,Y-1,M);
    const eld = D.elder.includes(s) ? ytd(region,s+D.elderSuffix,Y,M) : null;
    const A=D.annual[s]||{}, fy=A[finalYear]||{}, f5=A[finalYear-5]||{};
    return `<tr><td>${s}</td><td><span class="tag">${D.tm[s]}</span></td><td>${fmt(c)}</td><td>${fmt(p)}</td><td>${chg(ratio(c,p))}</td>
      <td>${fmt(cy)}</td><td>${fmt(py)}</td><td>${chg(ratio(cy,py))}</td><td>${eld!=null&&cy?pctPlain(eld/cy):"–"}</td>
      <td>${fmt(fy.n)}</td><td>${fmt1(fy.p)}</td><td>${chg(ratio(fy.n,f5.n))}</td></tr>`;
  }).join("");
  document.getElementById("kpitable").innerHTML = head+rows;
}

// ---------- SVG chart engine ----------
const tipEl = () => { let t=document.querySelector("body > .tip"); if(!t){t=document.createElement("div");t.className="tip";document.body.appendChild(t);} return t; };
// position:fixed + viewport-koordinater: tipset kan aldrig vidga sidan, och det byter sida vid kanterna.
function showTip(tip,e){ tip.style.opacity=1; const w=tip.offsetWidth, h=tip.offsetHeight;
  const x = e.clientX+14+w > innerWidth-8 ? e.clientX-14-w : e.clientX+14;
  const y = Math.min(Math.max(8, e.clientY-10), innerHeight-h-8);
  tip.style.left=Math.max(8,x)+"px"; tip.style.top=y+"px"; }
function niceStep(v){ const e=Math.pow(10,Math.floor(Math.log10(v))); const f=v/e; return (f<=1?1:f<=2?2:f<=5?5:10)*e; }
function niceAxis(v){ if(v<=0) return {max:1,step:0.25}; const step=niceStep(v/4); return {max:Math.ceil(v/step-1e-9)*step, step}; }  // gridlines at 1/2/5×10^n
function axisFmt(v,isPct){ if(isPct) return Math.round(v*1000)/10+" %"; return v>=1000? (v/1000).toLocaleString("sv-SE")+" k" : v.toLocaleString("sv-SE"); }

function lineChart(id, series, {isPct=false, legendId=null, xLabel=k=>k}={}){
  const el=document.getElementById(id); const W=el.clientWidth||600, H=el.clientHeight||300, P={l:52,r:12,t:10,b:28};
  const hidden = el._hidden || (el._hidden=new Set());
  const vis = series.filter(s=>!hidden.has(s.name));
  const xs = [...new Set(series.flatMap(s=>s.data.map(d=>d[0])))].sort((a,b)=>a<b?-1:a>b?1:0);
  const {max:ymax, step:ystep} = niceAxis(Math.max(0,...vis.flatMap(s=>s.data.map(d=>d[1]))));
  const X = k => P.l + (xs.length<2?0:xs.indexOf(k)/(xs.length-1))*(W-P.l-P.r);
  const Y = v => H-P.b - (v/ymax)*(H-P.t-P.b);
  let g = "";
  for(let v=0;v<=ymax+ystep/1e6;v+=ystep){ const y=Y(v); g+=`<line x1="${P.l}" x2="${W-P.r}" y1="${y}" y2="${y}" class="gl"/><text class="ax" x="${P.l-6}" y="${y+4}" font-size="11" text-anchor="end">${axisFmt(v,isPct)}</text>`; }
  const step = Math.max(1, Math.ceil(xs.length/8));
  xs.forEach((k,i)=>{ const last=i===xs.length-1; if((i%step===0 && xs.length-1-i >= step/2) || last) g+=`<text class="ax" x="${X(k)}" y="${H-8}" font-size="11" text-anchor="middle">${xLabel(k)}</text>`; });
  series.forEach((s,i)=>{ if(hidden.has(s.name)) return; const col=s.color||COLORS[i%COLORS.length];
    const d=s.data.map((p,j)=>`${j?"L":"M"}${X(p[0]).toFixed(1)},${Y(p[1]).toFixed(1)}`).join("");
    g+=`<path d="${d}" fill="none" style="stroke:${col}" stroke-width="2.2" stroke-linejoin="round"/>`;
    if(s.data.length<=15) s.data.forEach(p=>g+=`<circle cx="${X(p[0])}" cy="${Y(p[1])}" r="3" style="fill:${col}"/>`); });
  g+=`<line id="${id}-cur" y1="${P.t}" y2="${H-P.b}" class="zl" stroke-dasharray="3 3" opacity="0"/>`;
  el.innerHTML = `<svg viewBox="0 0 ${W} ${H}">${g}<rect x="${P.l}" y="${P.t}" width="${W-P.l-P.r}" height="${H-P.t-P.b}" fill="transparent"/></svg>`;
  const svg=el.querySelector("svg"), cur=svg.querySelector(`#${id}-cur`), tip=tipEl();
  svg.onmousemove = e => { const r=svg.getBoundingClientRect(); const x=(e.clientX-r.left)*W/r.width;
    let bi=0,bd=1e9; xs.forEach((k,i)=>{const dd=Math.abs(X(k)-x); if(dd<bd){bd=dd;bi=i;}}); const k=xs[bi];
    cur.setAttribute("x1",X(k)); cur.setAttribute("x2",X(k)); cur.setAttribute("opacity",1);
    tip.innerHTML = `<b>${xLabel(k,true)}</b><br>`+series.map((s,i)=>{ if(hidden.has(s.name)) return ""; const p=s.data.find(d=>d[0]===k);
      return p?`<span style="color:${getComputedStyle(document.documentElement).getPropertyValue((s.color||COLORS[i%COLORS.length]).slice(4,-1))}">●</span> ${s.name}: ${isPct?pctPlain(p[1]):fmt(p[1])}<br>`:""; }).join("");
    showTip(tip,e); };
  svg.onmouseleave = ()=>{ tip.style.opacity=0; cur.setAttribute("opacity",0); };
  if(legendId){ const lg=document.getElementById(legendId);
    lg.innerHTML = series.map((s,i)=>`<span data-n="${s.name}" class="${hidden.has(s.name)?"off":""}"><i style="background:${s.color||COLORS[i%COLORS.length]}"></i>${s.name}</span>`).join("");
    lg.querySelectorAll("span").forEach(sp=>sp.onclick=()=>{ const n=sp.dataset.n; hidden.has(n)?hidden.delete(n):hidden.add(n); lineChart(id,series,{isPct,legendId,xLabel}); }); }
}

function barChart(id, items, {horizontal=false, isPct=false, color="var(--c1)"}={}){
  const el=document.getElementById(id); const W=el.clientWidth||600, H=el.clientHeight||300;
  const tip=tipEl(); let g="";
  if(!horizontal){
    const P={l:52,r:12,t:16,b:28}, {max:ymax, step:ystep}=niceAxis(Math.max(...items.map(d=>d[1]||0)));
    const bw=(W-P.l-P.r)/items.length;
    for(let v=0;v<=ymax+ystep/1e6;v+=ystep){ const y=H-P.b-(v/ymax)*(H-P.t-P.b); g+=`<line x1="${P.l}" x2="${W-P.r}" y1="${y}" y2="${y}" class="gl"/><text class="ax" x="${P.l-6}" y="${y+4}" font-size="11" text-anchor="end">${axisFmt(v,isPct)}</text>`; }
    items.forEach((d,i)=>{ const h=(d[1]||0)/ymax*(H-P.t-P.b), x=P.l+i*bw+bw*0.15, y=H-P.b-h;
      g+=`<rect class="b" data-i="${i}" x="${x}" y="${y}" width="${bw*0.7}" height="${h}" rx="3" style="fill:${color}"/>
          <text class="ax" x="${x+bw*0.35}" y="${H-8}" font-size="11" text-anchor="middle">${d[0]}</text>`; });
  } else {
    const P={l:96,r:60,t:6,b:6}, lim=Math.max(0.05,...items.map(d=>Math.abs(d[1]||0))), bh=(H-P.t-P.b)/items.length;
    const X0=P.l+(W-P.l-P.r)/2, sc=(W-P.l-P.r)/2/lim;
    g+=`<line x1="${X0}" x2="${X0}" y1="${P.t}" y2="${H-P.b}" class="zl"/>`;
    items.forEach((d,i)=>{ const v=d[1]; const y=P.t+i*bh+bh*0.18, w=Math.abs(v||0)*sc, x=v>=0?X0:X0-w;
      const col = v>0.05?"var(--up)":v<-0.05?"var(--down)":"var(--c7)";
      g+=`<text x="${P.l-8}" y="${y+bh*0.42}" font-size="12" class="bl" text-anchor="end">${d[0]}</text>
          <rect class="b" data-i="${i}" x="${x}" y="${y}" width="${w}" height="${bh*0.64}" rx="3" style="fill:${col}"/>
          <text x="${v>=0?X0+w+5:X0-w-5}" y="${y+bh*0.42}" font-size="11" class="bv" text-anchor="${v>=0?"start":"end"}">${pct(v)}</text>`; });
  }
  el.innerHTML=`<svg viewBox="0 0 ${W} ${H}">${g}</svg>`;
  el.querySelectorAll(".b").forEach(b=>{ b.onmousemove=e=>{ const d=items[+b.dataset.i]; tip.innerHTML=`<b>${d[0]}</b><br>${isPct||horizontal?pct(d[1]):fmt(d[1])}${d[2]?"<br>"+d[2]:""}`;
      showTip(tip,e); }; b.onmouseleave=()=>tip.style.opacity=0; });
}

// ---------- charts ----------
const monthLabel = (k,long) => long ? `${MONTHS[+k.slice(5)-1]} ${k.slice(0,4)}` : (k.slice(5)==="01"||k===undefined ? k.slice(0,4) : `${MONTHS[+k.slice(5)-1]} ${k.slice(2,4)}`);
function renderTrends(){
  lineChart("ch-shift", ["Social manipulation, totalt","Kortbedrägeri utan fysiskt kort","Annonsbedrägeri"].map(s=>({name:s,data:r12(s)})), {legendId:"lg-shift", xLabel:monthLabel});
  lineChart("ch-modus", ["Befogenhetsbedrägeri","Social manipulation av annan typ","Identitetsbedrägeri","Fakturabedrägeri","Investeringsbedrägeri","Romansbedrägeri"].map(s=>({name:s,data:r12(s)})), {legendId:"lg-modus", xLabel:monthLabel});
  const pt=D.annual["Penningtvättsbrott, totalt"];
  barChart("ch-pt", Object.keys(pt).sort().map(y=>[y, pt[y].n, `${fmt1(pt[y].p)} per 100 000 inv`]));
  const young = ["Penningtvättsbrott, totalt","Social manipulation, totalt","Befogenhetsbedrägeri","Bedrägeri och annan oredlighet"].map(s=>({name:s,
    data:Object.keys(D.suspects[s]).sort().map(y=>{const r=D.suspects[s][y]; return [y,(r["15–17"]+r["18–20"]+r["21–24"])/r.tot];})}));
  lineChart("ch-young", young, {isPct:true, legendId:"lg-young"});
  const ntu=[]; for(const [k,v] of Object.entries(D.ntu)) for(const sx of ["Samtliga","Män","Kvinnor"]) if(v[sx])
    ntu.push({name:`${k} – ${sx}`, data:Object.keys(v[sx]).sort().map(y=>[y,v[sx][y]/100])});
  const ntuEl=document.getElementById("ch-ntu"); if(!ntuEl._hidden) ntuEl._hidden=new Set(ntu.filter(s=>!s.name.endsWith("Samtliga")).map(s=>s.name));
  lineChart("ch-ntu", ntu, {isPct:true, legendId:"lg-ntu"});
}

const REG_SERIES = ["Social manipulation, totalt","Befogenhetsbedrägeri","Kortbedrägeri utan fysiskt kort","Annonsbedrägeri","Penningtvättsbrott, totalt","Bedrägeri och annan oredlighet"];
let regSerie = REG_SERIES[0];
function renderRegions(){
  const [Y,M]=monSel.value.split("-").map(Number);
  document.getElementById("regsub").textContent = `Jan–${MONTHS[M-1]} ${Y} jämfört med jan–${MONTHS[M-1]} ${Y-1}, preliminärt`;
  const tabs=document.getElementById("regtabs");
  tabs.innerHTML = REG_SERIES.map(s=>`<button class="${s===regSerie?"on":""}">${s.replace(", totalt","")}</button>`).join("");
  tabs.querySelectorAll("button").forEach((b,i)=>b.onclick=()=>{regSerie=REG_SERIES[i]; renderRegions();});
  barChart("ch-reg", D.regions.map(r=>{ const c=ytd(r,regSerie,Y,M), p=ytd(r,regSerie,Y-1,M); return [r, ratio(c,p), `${fmt(c)} mot ${fmt(p)}`]; }), {horizontal:true});

  document.getElementById("heatsub").textContent = `Jan–${MONTHS[M-1]} ${Y}. Cellfärgen visar förändringen mot samma period ${Y-1}.`;
  const HS = SERIES;
  let h = `<tr><th>Region</th>${HS.map(s=>`<th>${s.replace(", totalt","")}</th>`).join("")}</tr>`;
  D.regions.forEach(r=>{ h+=`<tr><td>${r}</td>`+HS.map(s=>{ const c=ytd(r,s,Y,M), p=ytd(r,s,Y-1,M), ch=ratio(c,p);
      const a=ch==null?0:Math.min(1,Math.abs(ch)/0.5), bg=ch==null?"transparent":ch>0?`rgba(var(--heatup),${0.08+0.5*a})`:`rgba(var(--heatdown),${0.08+0.5*a})`;
      return `<td class="hc" style="background:${bg}" title="${pct(ch)} jämfört med ${Y-1} (${fmt(p)})">${fmt(c)}</td>`; }).join("")+`</tr>`; });
  const t=document.getElementById("heat"); t.innerHTML=h; t.querySelectorAll("th:nth-child(2)").forEach(th=>th.style.textAlign="right");
  t.querySelectorAll("td:nth-child(2)").forEach(td=>{td.style.color="inherit";td.style.textAlign="right";});
}

function renderAll(){ renderKpis(); renderRegions(); }
(function init(){
  const prelimPT = Object.entries(nat["Penningtvättsbrott, totalt"]).filter(([k])=>k.startsWith("2025")).reduce((a,[,v])=>a+v,0);
  const finalPT = (D.annual["Penningtvättsbrott, totalt"][2025]||{}).n;
  document.getElementById("ptgap").textContent = `${fmt(prelimPT)} preliminärt mot ${fmt(finalPT)} slutligt`;
  renderAll(); renderTrends();
  let rt; window.addEventListener("resize",()=>{clearTimeout(rt); rt=setTimeout(()=>{renderTrends(); renderRegions();},150);});
})();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    build()
