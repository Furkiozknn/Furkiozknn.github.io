# -*- coding: utf-8 -*-
"""Oyun merkezi: furkiozknn.github.io kök sayfasını (index.html) üretir.

Tek kaynak bu dosyadaki OYUNLAR listesidir. Görseller merkez/img/<slug>-s.webp
(480 px) ve -l.webp (960/760 px). Çalıştır:  python merkez/olustur.py
"""
import html
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SITE = "https://furkiozknn.github.io/"

# motif: (genişlik, yükseklik, SVG içeriği) — renkler kartın CSS değişkenlerinden.
A = "style='fill:var(--acc)'"
AS = "style='fill:none;stroke:var(--acc)'"
I = "style='fill:var(--ink)'"
MOTIF = {
    "ag": (32, 28, f"<path d='M0 14H32' {AS} stroke-width='1.5'/><circle cx='16' cy='14' r='5' {A}/>"),
    "kemer": (36, 28, f"<rect width='36' height='28' {A}/><circle cx='9' cy='14' r='3' style='fill:var(--bg)'/><path d='M27 6l6 8-6 8-6-8z' style='fill:var(--bg)'/>"),
    "zikzak": (24, 28, f"<path d='M0 5L12 23L24 5' {AS} stroke-width='3'/>"),
    "dalga": (48, 28, f"<path d='M0 18Q12 6 24 18T48 18' {AS} stroke-width='3'/>"),
    "simit": (40, 28, f"<circle cx='20' cy='14' r='8.5' {AS} stroke-width='4.5'/><ellipse cx='17' cy='9' rx='1.6' ry='.9' {I}/><ellipse cx='24' cy='12' rx='1.6' ry='.9' {I}/><ellipse cx='19' cy='19' rx='1.6' ry='.9' {I}/>"),
    "dama": (28, 28, f"<rect width='14' height='14' {I}/><rect x='14' y='14' width='14' height='14' {I}/>"),
    "sekme": (48, 28, f"<circle cx='6' cy='20' r='2.4' {A}/><circle cx='18' cy='10' r='2.4' {A}/><circle cx='30' cy='7' r='2.4' {A}/><circle cx='42' cy='12' r='2.4' {A}/>"),
    "tente": (32, 28, f"<rect width='16' height='17' {A}/><circle cx='8' cy='17' r='8' {A}/><rect x='16' width='16' height='17' {I}/><circle cx='24' cy='17' r='8' {I}/>"),
    "yol": (40, 28, f"<rect y='13' width='14' height='2.5' {A}/><rect x='20' y='13' width='14' height='2.5' {A}/><path d='M37 9l4 5-4 5-4-5z' {A}/>"),
    "mazgal": (32, 28, f"<rect y='6' width='18' height='22' {A}/>"),
    "susam": (30, 28, f"<ellipse cx='6' cy='7' rx='3.2' ry='1.7' {A} transform='rotate(-30 6 7)'/><ellipse cx='21' cy='19' rx='3.2' ry='1.7' {A} transform='rotate(25 21 19)'/><ellipse cx='16' cy='5' rx='3.2' ry='1.7' {A} transform='rotate(60 16 5)'/><ellipse cx='8' cy='22' rx='3.2' ry='1.7' {A}/>"),
    "balon": (44, 28, f"<circle cx='22' cy='11' r='8' {A}/><rect x='20' y='21' width='4' height='4' rx='1' {A}/>"),
    "kafes": (28, 28, f"<path d='M14 2l12 12-12 12L2 14z' {AS} stroke-width='2'/>"),
    "yildiz": (64, 28, f"<path d='M14 4l2 6 6 2-6 2-2 6-2-6-6-2 6-2z' {A}/><path d='M46 14l1.4 4 4 1.4-4 1.4-1.4 4-1.4-4-4-1.4 4-1.4z' {A}/><circle cx='34' cy='7' r='1.3' {A}/>"),
    "kubbe": (40, 28, f"<path d='M5 28A15 15 0 0 1 35 28z' {A}/><rect x='19' y='6' width='2' height='8' {A}/>"),
    "ebru": (64, 28, "<path d='M0 8Q16 0 32 8T64 8' style='fill:none;stroke:#b8342a' stroke-width='2.5'/><path d='M0 15Q16 7 32 15T64 15' style='fill:none;stroke:#2a3f7a' stroke-width='2.5'/><path d='M0 22Q16 14 32 22T64 22' style='fill:none;stroke:#d9a21b' stroke-width='2.5'/>"),
    "cini": (28, 28, "<rect width='28' height='28' style='fill:#1d3f9e'/><rect x='8' y='8' width='12' height='12' style='fill:#1aa3a3'/><rect x='8' y='8' width='12' height='12' style='fill:#1aa3a3' transform='rotate(45 14 14)'/>"),
    "kemerli": (40, 28, f"<path d='M5 28V15A15 15 0 0 1 35 15V28' {AS} stroke-width='2'/>"),
    "teras": (48, 28, f"<path d='M0 9Q12 17 24 9T48 9' {AS} stroke-width='3'/><path d='M0 20Q12 28 24 20T48 20' {AS} stroke-width='3'/>"),
    "lale": (32, 28, f"<path d='M10 6l3 4 3-6 3 6 3-4-1 8q-5 4-10 0z' {A}/><rect x='15.2' y='16' width='1.6' height='12' style='fill:#3d7a2c'/>"),
    "fay": (40, 28, f"<path d='M0 14L8 7L14 19L22 9L28 20L34 11L40 14' {AS} stroke-width='2.5'/>"),
}

# Veri merkez/oyunlar.json'da (tek kaynak). Her oyun: depo adı (çapa), ad, renkler,
# motif, görsel biçimi (w 16:9 · p 4:5 · s 1:1), tür, kanca, nasıl oynanır, şarkı, sarki_youtube.
VERI = os.path.join(HERE, "oyunlar.json")


def yukle():
    doc = json.load(open(VERI, encoding="utf-8"))
    oyunlar = []
    for g in doc["oyunlar"]:
        r = g["renk"]
        yt = (g.get("sarki_youtube") or "").strip()
        if yt and not yt.startswith(("https://www.youtube.com/", "https://youtube.com/", "https://youtu.be/", "https://m.youtube.com/")):
            raise SystemExit(f"{g['id']}: sarki_youtube bir YouTube linki değil: {yt}")
        oyunlar.append(dict(
            id=g["id"], ad=g["ad"], m=g["motif"], g=g["gorsel"],
            c=(r["zemin"], r["metin"], r["vurgu"], r["dugme"], r["dugme_metin"], r["bant"]),
            tur=(g["tur"]["tr"], g["tur"]["en"]), kanca=(g["kanca"]["tr"], g["kanca"]["en"]),
            nasil=(g["nasil"]["tr"], g["nasil"]["en"]), alt=(g["alt"]["tr"], g["alt"]["en"]),
            sarki=(g["sarki"]["tr"], g["sarki"]["en"]) if g.get("sarki") else None, yt=yt,
            surum=g.get("surum", ""), yenilik=(g["yenilik"]["tr"], g["yenilik"]["en"]) if g.get("yenilik") else None))
    return oyunlar


OYUNLAR = yukle()
SON_GUNCELLEME = json.load(open(VERI, encoding="utf-8")).get("son_guncelleme", "")
AYLAR_TR = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
AYLAR_EN = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]


def tarih(iso):
    y, m, d = (int(x) for x in iso.split("-"))
    return f"{d} {AYLAR_TR[m - 1]} {y}", f"{AYLAR_EN[m - 1]} {d}, {y}"

e = html.escape


def tt(tr, en, tag="span", cls=""):
    """Both languages in the markup; CSS shows one (Turkish without JS)."""
    c = f" {cls}" if cls else ""
    return (f'<{tag} class="tr{c}" lang="tr">{e(tr)}</{tag}>'
            f'<{tag} class="en{c}" lang="en">{e(en)}</{tag}>')


def band(o):
    w, h, inner = MOTIF[o["m"]]
    pid = "p-" + o["id"]
    return (f'<svg class="band" aria-hidden="true" focusable="false" width="100%" height="{h}">'
            f'<defs><pattern id="{pid}" width="{w}" height="{h}" patternUnits="userSpaceOnUse">{inner}'
            f'<animateTransform attributeName="patternTransform" type="translate" from="0 0" to="{w} 0" dur="{max(3, w // 6)}s" repeatCount="indefinite"/></pattern></defs>'
            f'<rect width="100%" height="{h}" fill="url(#{pid})"/></svg>')


def _lum(h):
    c = [int(h.lstrip("#")[k:k + 2], 16) / 255 for k in (0, 2, 4)]
    c = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def kontrast(a, b):
    a, b = _lum(a), _lum(b)
    return (max(a, b) + 0.05) / (min(a, b) + 0.05)


def card(i, o):
    bg, ink, acc, btn, bink, bandbg = o["c"]
    n = f"{i:02d}"
    # number badge: whichever text colour reads best on the accent
    nofg = max((bg, ink, "#ffffff", "#15120f"), key=lambda x: kontrast(x, acc))
    shape = o["g"]
    if shape == "w":
        wl, hl, ws = 960, 540, 480
    elif shape == "p":
        wl, hl, ws = 760, 950, 480
    else:
        wl, hl, ws = 760, 760, 480
    img = (f'<img src="merkez/img/{o["id"]}-l.webp" srcset="merkez/img/{o["id"]}-s.webp {ws}w, merkez/img/{o["id"]}-l.webp {wl}w" '
           f'sizes="(min-width: 860px) 560px, calc(100vw - 32px)" width="{wl}" height="{hl}" '
           f'loading="{"eager" if i <= 1 else "lazy"}" decoding="async" '
           f'alt="{e(o["alt"][0])}" data-alt-en="{e(o["alt"][1])}">')
    song = ""
    if o["sarki"]:
        song = (f'<p class="song"><span aria-hidden="true">🎵</span> '
                + tt("Şarkısı var: " + o["sarki"][0], "Has its own song: " + o["sarki"][1]) + "</p>")
    if o["yt"]:
        song += (f'<p class="listen"><a href="{e(o["yt"])}"><span aria-hidden="true">🎵</span> '
                 + tt("Şarkıyı dinle", "Listen to the song") + f'<span class="vh"> ({e(o["ad"])})</span></a></p>')
    url = f"{SITE}{o['id']}/"
    news = ""
    if o["yenilik"]:
        v = f" v{o['surum']}" if o["surum"] else ""
        news = (f'<p class="news"><span class="badge">{tt("Güncellendi · Kasım 2026", "Updated · Nov 2026")}</span> '
                f'<span class="ver">{e(v.strip())}</span> ' + tt(*o["yenilik"]) + "</p>")
    return f'''<article class="g g-{shape} m-{o["m"]}" id="{o["id"]}" style="--bg:{bg};--ink:{ink};--acc:{acc};--btn:{btn};--bink:{bink};--bandbg:{bandbg};--nofg:{nofg}" aria-labelledby="h-{o["id"]}">
{band(o)}
<div class="g-in">
<figure class="shot">{img}</figure>
<div class="body">
<p class="kick"><span class="no">{n}</span> {tt(*o["tur"])}</p>
<h2 id="h-{o["id"]}" lang="tr">{e(o["ad"])}</h2>
<p class="hook">{tt(*o["kanca"])}</p>
{news}
<p class="how"><span class="lbl">{tt("Nasıl oynanır", "How to play")}</span> {tt(*o["nasil"])}</p>
<a class="play" href="{url}" data-ad="{e(o["ad"])}"><span aria-hidden="true">▶</span> {tt("Oyna", "Play")}<span class="vh"> {e(o["ad"])}</span></a>
{song}
<p class="src"><a href="https://github.com/Furkiozknn/{o["id"]}">{tt("Kaynak kodu", "Source code")}</a></p>
</div>
</div>
</article>'''


def jump():
    """Each game's own animated banner (the docs/banner.svg the profile README shows)."""
    items = []
    for i, o in enumerate(OYUNLAR, 1):
        bg, ink, acc = o["c"][0], o["c"][1], o["c"][2]
        nofg = max((bg, ink, "#ffffff", "#15120f"), key=lambda x: kontrast(x, acc))
        items.append(
            f'<li style="--bg:{bg};--ink:{ink};--acc:{acc};--nofg:{nofg};--d:{(i - 1) * 45}ms"><a href="#{o["id"]}">'
            f'<img src="/{o["id"]}/docs/banner.svg" width="1280" height="320" loading="{"eager" if i <= 6 else "lazy"}" decoding="async" alt="">'
            f'<span class="cap"><b class="no">{i:02d}</b><span class="nm" lang="tr">{e(o["ad"])}</span>'
            f'<span class="tu">{tt(*o["tur"])}</span><span class="go" aria-hidden="true">→</span></span></a></li>')
    return "\n".join(items)


TILE = ("<svg class=\"tiles\" aria-hidden=\"true\" focusable=\"false\" width=\"100%\" height=\"48\"><defs><pattern id=\"{id}\" width=\"48\" height=\"48\" patternUnits=\"userSpaceOnUse\">"
        "<rect width=\"48\" height=\"48\" fill=\"#1d3f9e\"/><rect x=\"15\" y=\"15\" width=\"18\" height=\"18\" fill=\"#1aa3a3\"/>"
        "<rect x=\"15\" y=\"15\" width=\"18\" height=\"18\" fill=\"#1aa3a3\" transform=\"rotate(45 24 24)\"/>"
        "<animateTransform attributeName=\"patternTransform\" type=\"translate\" from=\"0 0\" to=\"{dx} 0\" dur=\"4s\" repeatCount=\"indefinite\"/></pattern></defs>"
        "<rect width=\"100%\" height=\"48\" fill=\"url(#{id})\"/></svg>")

CSS = r"""
:root{--siyah:#15120f;--siyah2:#1f1b16;--kurk:#f1efea;--gumus:#b8bcc3;--tugra:#c9a227;--kehribar:#e0a01c;--dim:#8f877b;
--poster:"Archivo Black","Arial Black",Impact,sans-serif;--sans:"Nunito",system-ui,-apple-system,"Segoe UI",sans-serif;
--mono:"JetBrains Mono",ui-monospace,Consolas,monospace;--display:"Cinzel",Georgia,serif;color-scheme:dark}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%;scroll-padding-top:12px}
body{margin:0;background:var(--siyah);color:var(--kurk);font:400 16px/1.5 var(--sans)}
a{color:inherit}
img{max-width:100%;display:block}
.vh{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
.en{display:none}
html[data-l=en] .en{display:revert}
html[data-l=en] .tr{display:none}
.skip{position:absolute;left:-999px;top:8px;background:var(--tugra);color:var(--siyah);padding:12px 16px;border-radius:8px;z-index:9;font-weight:800}
.skip:focus{left:16px}
:focus-visible{outline:3px solid var(--kehribar);outline-offset:3px}
.wrap{max-width:1080px;margin:0 auto;padding:0 16px}
.tiles{display:block}
header.top{padding:20px 0 8px}
.bar{display:flex;align-items:center;justify-content:space-between;gap:12px}
.brand{font:700 16px/1 var(--display);letter-spacing:.1em;color:var(--gumus);margin:0}
.lang{display:flex;border:1.5px solid #5e5649;border-radius:999px;overflow:hidden}
.lang button{all:unset;cursor:pointer;font:600 13px/1 var(--mono);letter-spacing:.08em;min-width:48px;min-height:44px;display:grid;place-items:center;color:var(--gumus)}
.lang button[aria-pressed=true]{background:var(--tugra);color:var(--siyah)}
.lang button:focus-visible{outline:3px solid var(--kehribar);outline-offset:-3px}
h1{font:400 clamp(64px,22vw,148px)/.92 var(--poster);color:var(--tugra);margin:28px 0 10px;letter-spacing:-.01em;text-transform:uppercase}
h1 small{display:block;font:600 clamp(14px,3.6vw,18px)/1.3 var(--mono);letter-spacing:.14em;color:var(--kurk);margin-top:10px}
.lead{font:600 clamp(18px,4.6vw,22px)/1.45 var(--sans);max-width:36em;margin:14px 0 22px;color:var(--kurk)}
.jump h2{font:600 13px/1 var(--mono);letter-spacing:.14em;color:var(--gumus);margin:0 0 12px;text-transform:uppercase}
.jump ol{list-style:none;margin:0 0 40px;padding:0;display:grid;grid-template-columns:minmax(0,1fr);gap:12px}
.jump li{animation:in .6s cubic-bezier(.2,.8,.2,1) var(--d) both}
.jump a{display:block;border-radius:12px;overflow:hidden;background:var(--bg);color:var(--ink);text-decoration:none;
 box-shadow:0 0 0 1px #ffffff1a;transition:transform .2s cubic-bezier(.2,.8,.2,1),box-shadow .2s}
.jump a:hover,.jump a:focus-visible{transform:translateY(-4px);box-shadow:0 0 0 2px var(--acc),0 12px 28px -10px var(--acc)}
.jump img{width:100%;height:auto;aspect-ratio:4/1;background:var(--bg)}
.jump .cap{display:flex;align-items:center;gap:10px;min-height:44px;padding:6px 12px;border-top:3px solid var(--acc)}
.jump .no{font:600 12px/1 var(--mono);background:var(--acc);color:var(--nofg);padding:4px 6px;border-radius:4px}
.jump .nm{font:800 16px/1.2 var(--sans)}
.jump .tu{font:600 11.5px/1.2 var(--mono);letter-spacing:.1em;text-transform:uppercase;opacity:.8;margin-left:auto;text-align:right}
.jump .go{font:800 18px/1 var(--sans);color:var(--acc);transition:transform .2s}
.jump a:hover .go{transform:translateX(4px)}
@media (min-width:600px){.jump ol{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media (min-width:960px){.jump ol{grid-template-columns:repeat(3,minmax(0,1fr))}}
@keyframes in{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:none}}
h1>.tr,h1>.en{background:linear-gradient(90deg,#c9a227,#e0a01c,#d94f30,#b8342a,#1aa3a3,#2f6fd6,#c9a227) 0 0/300% 100%;-webkit-background-clip:text;background-clip:text;color:transparent;animation:sheen 9s linear infinite}
@keyframes sheen{to{background-position:300% 0}}
.g.rv{opacity:0;transform:translateY(24px);transition:opacity .7s cubic-bezier(.2,.8,.2,1),transform .7s cubic-bezier(.2,.8,.2,1)}
.g.rv.on{opacity:1;transform:none}
.shot{overflow:hidden}
.shot img{transition:transform 1.2s cubic-bezier(.2,.8,.2,1)}
.g:hover .shot img{transform:scale(1.04)}
.play{position:relative;overflow:hidden}
.play::after{content:"";position:absolute;inset:0;pointer-events:none;background:linear-gradient(100deg,transparent 30%,#ffffff55 50%,transparent 70%);transform:translateX(-120%);animation:glint 4.5s ease-in-out infinite}
@keyframes glint{0%,60%{transform:translateX(-120%)}100%{transform:translateX(120%)}}
main{padding-bottom:24px}
.listen{margin:10px 0 0}
.listen a{display:inline-flex;align-items:center;gap:8px;min-height:44px;padding:0 16px;border-radius:999px;border:2px solid currentColor;font:800 15px/1 var(--sans);text-decoration:none}
.g{background:var(--bg);color:var(--ink);border-radius:16px;overflow:hidden;margin:0 0 28px;scroll-margin-top:12px}
.g:target{box-shadow:0 0 0 4px var(--tugra)}
.band{display:block;background:var(--bandbg)}
.g-in{display:grid}
.shot{margin:0;background:#00000022}
.shot img{width:100%;height:auto;aspect-ratio:16/9;object-fit:cover}
.g-p .shot img{aspect-ratio:4/5}
.g-s .shot img{aspect-ratio:1/1}
.body{padding:20px 18px 22px}
.kick{font:600 12.5px/1.2 var(--mono);letter-spacing:.14em;margin:0 0 8px;text-transform:uppercase}
.kick .no{display:inline-block;background:var(--acc);color:var(--nofg);padding:3px 6px;border-radius:4px;margin-right:6px}
.g h2{font:400 clamp(36px,11vw,60px)/1.05 var(--poster);text-transform:uppercase;margin:0 0 12px;letter-spacing:-.005em;overflow-wrap:anywhere}
.hook{font:700 clamp(18px,4.8vw,21px)/1.4 var(--sans);margin:0 0 14px}
.how{font:500 15px/1.5 var(--sans);margin:0 0 18px}
.how .lbl{display:block;font:600 12px/1.4 var(--mono);letter-spacing:.14em;text-transform:uppercase;opacity:.86;margin-bottom:2px}
.play{display:flex;align-items:center;justify-content:center;gap:10px;min-height:58px;padding:0 28px;border-radius:999px;background:var(--btn);color:var(--bink);
 font:400 22px/1 var(--poster);text-transform:uppercase;text-decoration:none;letter-spacing:.02em;box-shadow:0 4px 0 0 #00000040;transition:transform .12s}
.play:hover{transform:translateY(-2px)}
.play:active{transform:translateY(2px);box-shadow:0 1px 0 0 #00000040}
.play:focus-visible{outline:3px solid var(--ink);outline-offset:3px}
.news{font:600 14px/1.45 var(--sans);margin:0 0 14px}
.news .badge{display:inline-block;background:var(--acc);color:var(--nofg);font:600 11.5px/1 var(--mono);letter-spacing:.08em;text-transform:uppercase;padding:5px 8px;border-radius:999px;margin-right:6px}
.news .ver{font:600 12px/1 var(--mono);opacity:.85;margin-right:4px}
.song{font:700 14.5px/1.4 var(--sans);margin:14px 0 0}
.src{margin:6px 0 0}
.src a{display:inline-flex;align-items:center;min-height:44px;font:600 13px/1 var(--mono);letter-spacing:.06em;opacity:.9}
@media (min-width:860px){
 .g-in{grid-template-columns:minmax(0,1.15fr) minmax(0,1fr);align-items:center}
 .g:nth-of-type(even) .shot{order:2}
 .g-p .g-in{grid-template-columns:minmax(0,.72fr) minmax(0,1fr)}
 .g-s .g-in{grid-template-columns:minmax(0,.8fr) minmax(0,1fr)}
 .shot{height:100%}
 .shot img{height:100%;aspect-ratio:auto;min-height:100%}
 .g-w .shot img{aspect-ratio:16/9}
 .body{padding:28px 34px}
 .play{display:inline-flex;min-width:240px}
}
/* each card's own touch */
.m-dama .g-in{border-top:0}
.m-dama h2{background:var(--ink);color:var(--bg);display:inline-block;padding:4px 10px 2px;border-radius:6px}
.m-kafes .shot{box-shadow:inset 0 0 0 6px #f2b33d33}
.m-yildiz h2{letter-spacing:.04em}
.m-mazgal .band{background:var(--siyah)}
.m-kemer .play,.m-mazgal .play{box-shadow:0 0 0 3px var(--acc),0 4px 0 3px #00000040}
.m-ebru h2{color:#b8342a}
.m-lale h2{color:var(--acc)}
.m-tente .band{background:var(--bandbg)}
footer{padding:8px 0 40px;color:var(--gumus)}
footer nav{display:flex;flex-wrap:wrap;gap:8px 20px;margin:20px 0 8px}
footer nav a{display:inline-flex;align-items:center;min-height:44px;font:700 16px/1 var(--sans);color:var(--kurk)}
.fine{font-size:12.5px;color:var(--dim);margin:12px 0 0}
@media (prefers-reduced-motion:reduce){*,*::before,*::after{animation:none!important;transition:none!important}.g.rv{opacity:1;transform:none}.g:hover .shot img,.jump a:hover{transform:none}}
"""

JS = r"""
(function(){
var d=document,h=d.documentElement,K='merkez-dil';
function set(l,save){h.setAttribute('data-l',l);h.lang=l;
 d.querySelectorAll('.lang button').forEach(function(b){b.setAttribute('aria-pressed',b.dataset.l===l)});
 d.querySelectorAll('img[data-alt-en]').forEach(function(i){if(!i.dataset.altTr)i.dataset.altTr=i.alt;i.alt=l==='en'?i.dataset.altEn:i.dataset.altTr});
 d.title=l==='en'?'Furki Ozkan · 21 free browser games':'Furki Ozkan · 21 ücretsiz tarayıcı oyunu';
 if(save){try{localStorage.setItem(K,l)}catch(e){}}}
var q=new URLSearchParams(location.search).get('lang'),s=null;
try{s=localStorage.getItem(K)}catch(e){}
set(q==='en'||q==='tr'?q:(s||'tr'),false);
d.querySelectorAll('.lang button').forEach(function(b){b.addEventListener('click',function(){set(b.dataset.l,true)})});
var calm=matchMedia('(prefers-reduced-motion: reduce)').matches;
if(calm){d.querySelectorAll('svg').forEach(function(s){s.pauseAnimations&&s.pauseAnimations()})}
else if('IntersectionObserver' in window){
 var io=new IntersectionObserver(function(es){es.forEach(function(x){if(x.isIntersecting){x.target.classList.add('on');io.unobserve(x.target)}})},{rootMargin:'0px 0px -8% 0px'});
 d.querySelectorAll('.g').forEach(function(g){if(g.getBoundingClientRect().top>innerHeight){g.classList.add('rv');io.observe(g)}})}
})();
"""


def page():
    cards = "\n".join(card(i, o) for i, o in enumerate(OYUNLAR, 1))
    n = len(OYUNLAR)
    desc_tr = f"Türk kültüründen {n} ücretsiz tarayıcı oyunu: Hamsi, Kırkpınar, Mehter, Boğaz Vapuru ve daha fazlası. İndirme yok, üyelik yok."
    return f'''<!doctype html>
<html lang="tr" data-l="tr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>Furki Ozkan · {n} ücretsiz tarayıcı oyunu</title>
<meta name="description" content="{e(desc_tr)}">
<meta name="theme-color" content="#15120f">
<link rel="canonical" href="{SITE}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Furki Ozkan">
<meta property="og:title" content="{n} oyun · tarayıcıda ücretsiz oyna">
<meta property="og:description" content="{e(desc_tr)}">
<meta property="og:url" content="{SITE}">
<meta property="og:image" content="{SITE}merkez/og.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Furki Ozkan: {n} oyun. Oyunlardan kareler, İznik çini şeridi.">
<meta property="og:locale" content="tr_TR">
<meta property="og:locale:alternate" content="en_US">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="Furki Ozkan · {n} free browser games">
<meta name="twitter:description" content="Turkish-culture games you play in the browser: Hamsi, Kırkpınar, Mehter, Bosphorus Ferry and more. No download, no sign-up.">
<meta name="twitter:image" content="{SITE}merkez/og.jpg">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'%3E%3Crect width='16' height='16' rx='3' fill='%231d3f9e'/%3E%3Crect x='5' y='5' width='6' height='6' fill='%231aa3a3'/%3E%3Crect x='5' y='5' width='6' height='6' fill='%231aa3a3' transform='rotate(45 8 8)'/%3E%3C/svg%3E">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo+Black&family=Cinzel:wght@700&family=JetBrains+Mono:wght@600&family=Nunito:wght@500;600;700;800&display=swap">
<link rel="preload" as="image" href="merkez/img/hamsi-s.webp" imagesrcset="merkez/img/hamsi-s.webp 480w, merkez/img/hamsi-l.webp 960w" imagesizes="(min-width: 860px) 560px, calc(100vw - 32px)">
<style>{CSS}</style>
</head>
<body>
<a class="skip" href="#oyunlar">{tt("Oyunlara geç", "Skip to the games")}</a>
{TILE.format(id="t1", dx=48)}
<div class="wrap">
<header class="top">
<div class="bar"><p class="brand">Furki Ozkan</p>
<div class="lang" role="group" aria-label="Dil / Language"><button type="button" data-l="tr" aria-pressed="true" lang="tr">TR</button><button type="button" data-l="en" aria-pressed="false" lang="en">EN</button></div></div>
<h1><span class="tr" lang="tr">{n} oyun</span><span class="en" lang="en">{n} games</span><small>{tt("TARAYICIDA · ÜCRETSİZ · ÜYELİK YOK", "IN THE BROWSER · FREE · NO SIGN‑UP")}</small></h1>
<p class="lead">{tt("Türk kültüründen oyunlar: Karadeniz'de hamsi avı, Kırkpınar'da yağlı güreş, Boğaz'da vapur. Birini seç, dokun, oyna.", "Games from Turkish culture: anchovy fishing on the Black Sea, oil wrestling at Kırkpınar, a ferry on the Bosphorus. Pick one, tap, play.")}</p>
<nav class="jump" aria-labelledby="j-h"><h2 id="j-h">{tt("Hepsi bir bakışta", "All at a glance")}</h2>
<ol>
{jump()}
</ol></nav>
</header>
<main id="oyunlar" tabindex="-1">
<h2 class="vh">{tt("Oyunlar", "Games")}</h2>
{cards}
</main>
</div>
{TILE.format(id="t2", dx=-48)}
<footer>
<div class="wrap">
<nav aria-label="Bağlantılar / Links">
<a href="https://github.com/Furkiozknn">GitHub</a>
</nav>
<p>{tt("Hepsi ücretsiz, reklamsız; sayfa sizi izlemez.", "All free, no ads; this page doesn't track you.")}</p>
<p class="fine">{tt("Müzik ve görseller yapay zekâ ile üretildi.", "Music and artwork generated with AI.")}</p>
<p class="fine">{tt("Son güncelleme: " + tarih(SON_GUNCELLEME)[0], "Last updated: " + tarih(SON_GUNCELLEME)[1]) if SON_GUNCELLEME else ""}</p>
</div>
</footer>
<script>{JS}</script>
</body>
</html>
'''


if __name__ == "__main__":
    out = os.path.join(ROOT, "index.html")
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write(page())
    print(out, os.path.getsize(out), "bytes,", len(OYUNLAR), "oyun")
