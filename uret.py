#!/usr/bin/env python3
"""Build the project directory from the project-meta.json file in every
repository on the account.

Nothing on the page is typed by hand: the generator fetches each repository's
metadata over the GitHub raw endpoint, writes the snapshot to veri/projeler.json
and renders index.html from it. A field that is null in the metadata is left out
of the page rather than filled in.

    python3 uret.py            # fetch, then render
    python3 uret.py --yerel    # render from the snapshot already in veri/
"""

import argparse
import datetime
import html
import json
import os
import sys
import urllib.error
import urllib.request

OWNER = "Furkiozknn"
RAW = "https://raw.githubusercontent.com/{owner}/{repo}/{branch}/project-meta.json"
API = "https://api.github.com/users/{owner}/repos?per_page=100&type=owner"
HERE = os.path.dirname(os.path.abspath(__file__))
SNAPSHOT = os.path.join(HERE, "veri", "projeler.json")

GROUPS = [
    ("security-tool", "Security"),
    ("developer-tool", "Developer tools"),
    ("observability", "Observability"),
    ("mcp-server", "MCP servers"),
    ("agent-infrastructure", "Agent infrastructure"),
    ("backend-service", "Backend services"),
    ("web-app", "Web apps"),
    ("game", "Games"),
    ("template", "Templates"),
    ("research", "Research"),
    ("profile", "This account"),
]


def fetch(url, token=None):
    req = urllib.request.Request(url, headers={"User-Agent": "furkiozknn-hub"})
    if token:
        req.add_header("Authorization", "Bearer " + token)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8")


def repo_names(token=None):
    out, page = [], 1
    while True:
        try:
            data = json.loads(fetch(API.format(owner=OWNER) + f"&page={page}", token))
        except urllib.error.HTTPError as e:
            sys.exit(f"github said {e.code} while listing repositories")
        if not data:
            break
        out += [r["name"] for r in data if not r["fork"] and not r["private"]]
        if len(data) < 100:
            break
        page += 1
    return sorted(out)


def collect(token=None):
    rows, missing = [], []
    for name in repo_names(token):
        meta = None
        for branch in ("main", "master"):
            try:
                meta = json.loads(fetch(RAW.format(owner=OWNER, repo=name, branch=branch)))
                break
            except urllib.error.HTTPError:
                continue
        if meta is None:
            missing.append(name)
            continue
        rows.append(meta)
    return rows, missing


# --- rendering ------------------------------------------------------------

def e(x):
    return html.escape(str(x), quote=True)


def chip(text, kind=""):
    return f'<span class="chip {kind}">{e(text)}</span>'


def card(m):
    pid = m["id"]
    tests = (m.get("tests") or {}).get("count")
    links = [(m["repository"], "Repository")]
    if m.get("homepage"):
        links.append((m["homepage"], "Live"))
    if m.get("releases"):
        links.append((m["releases"], "Releases"))
    feats = (m.get("key_features") or [])[:2]
    search = " ".join(
        [pid, m.get("summary", ""), " ".join(m.get("topics") or []),
         " ".join(m.get("technologies") or []), m.get("primary_language") or "",
         " ".join(m.get("platform") or []), m.get("category") or ""]
    ).lower()
    out = [f'<article class="card" id="{e(pid)}" data-search="{e(search)}" '
           f'data-cat="{e(m.get("category") or "")}" data-lang="{e(m.get("primary_language") or "")}">']
    out.append('<header>')
    out.append(f'<h3><a href="{e(m["repository"])}">{e(pid)}</a></h3>')
    meta_bits = []
    if m.get("primary_language"):
        meta_bits.append(chip(m["primary_language"], "lang"))
    if m.get("version"):
        meta_bits.append(chip("v" + m["version"], "ver"))
    if tests:
        meta_bits.append(chip(f"{tests:,} tests".replace(",", " "), "tests"))
    if m.get("status") == "archived":
        meta_bits.append(chip("archived", "arch"))
    out.append('<div class="meta">' + "".join(meta_bits) + "</div>")
    out.append("</header>")
    out.append(f'<p class="sum">{e(m.get("summary") or "")}</p>')
    if feats:
        out.append("<ul class=\"feats\">" + "".join(f"<li>{e(f)}</li>" for f in feats) + "</ul>")
    if m.get("topics"):
        out.append('<div class="topics">' + "".join(
            f'<span class="topic">{e(t)}</span>' for t in m["topics"][:8]) + "</div>")
    out.append('<div class="links">' + "".join(
        f'<a href="{e(u)}">{e(t)}</a>' for u, t in links) + "</div>")
    out.append("</article>")
    return "\n".join(out)


def render(rows, missing, when):
    by_cat = {}
    for m in rows:
        by_cat.setdefault(m.get("category") or "other", []).append(m)
    for v in by_cat.values():
        v.sort(key=lambda m: (-((m.get("tests") or {}).get("count") or 0), m["id"]))

    # Archived projects keep their own card and their own count, but they are
    # left out of the headline so this page and TESTLER.md say the same number.
    live = [m for m in rows if m.get("status") != "archived"]
    total_tests = sum((m.get("tests") or {}).get("count") or 0 for m in live)
    suites = sum(1 for m in live if (m.get("tests") or {}).get("count"))
    langs = sorted({m.get("primary_language") for m in rows if m.get("primary_language")})

    sections = []
    for key, label in GROUPS:
        items = by_cat.pop(key, [])
        if not items:
            continue
        sections.append(
            f'<section class="group" data-group="{e(key)}"><h2>{e(label)}'
            f'<span class="count">{len(items)}</span></h2>'
            f'<div class="grid">' + "\n".join(card(m) for m in items) + "</div></section>")
    for key, items in sorted(by_cat.items()):
        sections.append(
            f'<section class="group" data-group="{e(key)}"><h2>{e(key)}'
            f'<span class="count">{len(items)}</span></h2>'
            f'<div class="grid">' + "\n".join(card(m) for m in items) + "</div></section>")

    filters = "".join(
        f'<button class="f" data-cat="{e(k)}">{e(l)}</button>'
        for k, l in GROUPS if by_cat.get(k) is not None or any(m.get("category") == k for m in rows))
    langfilters = "".join(f'<button class="f" data-lang="{e(l)}">{e(l)}</button>' for l in langs)

    note = ""
    if missing:
        note = ('<p class="warn">No project-meta.json found in: '
                + ", ".join(e(x) for x in missing) + "</p>")

    return TEMPLATE.format(
        owner=OWNER,
        count=len(rows),
        tests=f"{total_tests:,}".replace(",", ","),
        suites=suites,
        when=e(when),
        filters=filters,
        langfilters=langfilters,
        sections="\n".join(sections),
        note=note,
    )


TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Furki Özkan — {count} projects</title>
<meta name="description" content="Every public repository on the account, generated from the project-meta.json file each one carries: {count} projects, {tests} tests across {suites} suites.">
<meta property="og:title" content="Furki Özkan — {count} projects">
<meta property="og:description" content="Agent infrastructure, MCP servers, developer tooling and games. {tests} tests across {suites} suites, every count traced to the run that printed it.">
<meta property="og:type" content="website">
<meta property="og:url" content="https://furkiozknn.github.io/">
<meta property="og:image" content="https://furkiozknn.github.io/assets/og.png">
<meta name="twitter:card" content="summary_large_image">
<meta name="author" content="Furki Özkan">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'><rect width='16' height='16' rx='3' fill='%230b0b0f'/><text x='8' y='12' font-size='11' text-anchor='middle' fill='%23c9a961' font-family='monospace'>F</text></svg>">
<style>
:root {{
  --bg:#0b0b0f; --panel:#101016; --line:#242430; --text:#d8d8e0; --dim:#8a8a97;
  --gold:#c9a961; --green:#4ade9e; --blue:#6cb6ff; --pink:#e19bd0;
}}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--bg); color:var(--text);
  font:15px/1.6 'Segoe UI',-apple-system,Verdana,Helvetica,sans-serif; }}
a {{ color:var(--blue); text-decoration:none; }}
a:hover {{ text-decoration:underline; }}
.wrap {{ max-width:1180px; margin:0 auto; padding:0 20px 80px; }}
header.top {{ padding:56px 0 24px; }}
h1 {{ font:700 40px/1.1 'Cascadia Code','JetBrains Mono',Consolas,monospace;
  margin:0 0 10px; color:var(--gold); letter-spacing:-1px; }}
.lede {{ color:var(--dim); max-width:70ch; margin:0 0 22px; }}
.stats {{ display:flex; gap:10px; flex-wrap:wrap; margin-bottom:26px; }}
.stat {{ background:var(--panel); border:1px solid var(--line); border-radius:10px;
  padding:10px 16px; }}
.stat b {{ display:block; font:700 21px/1.2 'Cascadia Code',monospace; color:var(--green); }}
.stat span {{ color:var(--dim); font-size:12px; }}
.tools {{ position:sticky; top:0; background:rgba(11,11,15,.94); backdrop-filter:blur(6px);
  padding:14px 0; border-bottom:1px solid var(--line); z-index:9; margin-bottom:8px; }}
#q {{ width:100%; padding:12px 14px; border-radius:10px; border:1px solid var(--line);
  background:var(--panel); color:var(--text); font-size:15px; }}
#q:focus {{ outline:2px solid var(--gold); outline-offset:1px; }}
.fs {{ display:flex; gap:7px; flex-wrap:wrap; margin-top:10px; }}
button.f {{ background:var(--panel); border:1px solid var(--line); color:var(--dim);
  border-radius:99px; padding:5px 12px; font-size:12px; cursor:pointer; }}
button.f:hover {{ color:var(--text); }}
button.f.on {{ border-color:var(--gold); color:var(--gold); }}
.group h2 {{ font:600 15px/1 'Segoe UI',sans-serif; color:var(--gold);
  text-transform:uppercase; letter-spacing:.09em; margin:36px 0 14px; }}
.group h2 .count {{ color:var(--dim); font-weight:400; margin-left:8px;
  text-transform:none; letter-spacing:0; }}
.grid {{ display:grid; gap:14px; grid-template-columns:repeat(auto-fill,minmax(330px,1fr)); }}
.card {{ background:var(--panel); border:1px solid var(--line); border-radius:14px;
  padding:18px; display:flex; flex-direction:column; }}
.card h3 {{ margin:0; font:600 17px/1.2 'Cascadia Code','JetBrains Mono',monospace; }}
.card h3 a {{ color:var(--text); }}
.meta {{ display:flex; gap:6px; flex-wrap:wrap; margin:9px 0 2px; }}
.chip {{ font:12px/1 'Cascadia Code',monospace; border:1px solid var(--line);
  border-radius:99px; padding:4px 9px; color:var(--dim); }}
.chip.tests {{ color:var(--green); border-color:rgba(74,222,158,.4); }}
.chip.lang {{ color:var(--blue); border-color:rgba(108,182,255,.35); }}
.chip.ver {{ color:var(--gold); border-color:rgba(201,169,97,.35); }}
.chip.arch {{ color:var(--pink); border-color:rgba(225,155,208,.35); }}
.sum {{ font-size:14px; margin:12px 0 0; }}
.feats {{ margin:12px 0 0; padding-left:18px; color:var(--dim); font-size:13px; }}
.feats li {{ margin-bottom:5px; }}
.topics {{ margin-top:12px; display:flex; gap:5px; flex-wrap:wrap; }}
.topic {{ font-size:11px; color:var(--dim); background:#15151c; border-radius:5px; padding:2px 7px; }}
.links {{ margin-top:auto; padding-top:14px; display:flex; gap:14px; font-size:13px; }}
footer {{ margin-top:60px; padding-top:22px; border-top:1px solid var(--line);
  color:var(--dim); font-size:13px; }}
.warn {{ color:var(--pink); }}
.empty {{ color:var(--dim); padding:40px 0; display:none; }}
@media (max-width:600px) {{ h1 {{ font-size:30px; }} .wrap {{ padding:0 14px 60px; }} }}
</style>
</head>
<body>
<div class="wrap">
<header class="top">
  <h1>Furki Özkan</h1>
  <p class="lede">Agent infrastructure, MCP servers and developer tooling &mdash; and the tooling
  that checks whether any of it actually works. Every card below is generated from the
  <code>project-meta.json</code> file that repository carries, so a number here is a number
  that repository can defend.</p>
  <div class="stats">
    <div class="stat"><b>{count}</b><span>public repositories</span></div>
    <div class="stat"><b>{tests}</b><span>tests across {suites} active suites</span></div>
    <div class="stat"><b>{when}</b><span>generated</span></div>
  </div>
  <p><a href="https://github.com/{owner}">GitHub profile</a> &middot;
     <a href="https://github.com/{owner}/{owner}/blob/main/TESTLER.md">Where the test numbers come from</a> &middot;
     <a href="https://github.com/{owner}/{owner}/blob/main/schema/README.md">The metadata schema</a></p>
</header>

<div class="tools">
  <input id="q" type="search" placeholder="Search projects, topics, technologies&hellip;  (press / to focus)" autocomplete="off">
  <div class="fs">{filters}</div>
  <div class="fs">{langfilters}</div>
</div>

{note}
<p class="empty" id="empty">Nothing matches that.</p>
{sections}

<footer>
  <p>This page is generated by <a href="https://github.com/{owner}/{owner}.github.io/blob/main/uret.py"><code>uret.py</code></a>
  from the <code>project-meta.json</code> in every repository, and refreshed by a scheduled
  workflow. A field that is <code>null</code> in the metadata is left off the page rather than
  filled in with a guess.</p>
  <p>Source for this page: <a href="https://github.com/{owner}/{owner}.github.io">{owner}/{owner}.github.io</a></p>
</footer>
</div>
<script>
const q = document.getElementById('q');
const cards = [...document.querySelectorAll('.card')];
const groups = [...document.querySelectorAll('.group')];
let cat = null, lang = null;
function apply() {{
  const t = q.value.trim().toLowerCase();
  let shown = 0;
  for (const c of cards) {{
    const okText = !t || c.dataset.search.includes(t);
    const okCat = !cat || c.dataset.cat === cat;
    const okLang = !lang || c.dataset.lang === lang;
    const on = okText && okCat && okLang;
    c.style.display = on ? '' : 'none';
    if (on) shown++;
  }}
  for (const g of groups) {{
    g.style.display = [...g.querySelectorAll('.card')].some(c => c.style.display !== 'none') ? '' : 'none';
  }}
  document.getElementById('empty').style.display = shown ? 'none' : 'block';
}}
q.addEventListener('input', apply);
q.addEventListener('keydown', ev => {{
  if (ev.key === 'Enter') {{
    const first = cards.find(c => c.style.display !== 'none');
    if (first) window.location.href = first.querySelector('h3 a').href;
  }}
  if (ev.key === 'Escape') {{ q.value = ''; apply(); }}
}});
document.addEventListener('keydown', ev => {{
  if (ev.key === '/' && document.activeElement !== q) {{ ev.preventDefault(); q.focus(); }}
}});
for (const b of document.querySelectorAll('button.f')) {{
  b.addEventListener('click', () => {{
    const isCat = b.dataset.cat !== undefined;
    const val = isCat ? b.dataset.cat : b.dataset.lang;
    if (isCat) cat = (cat === val) ? null : val; else lang = (lang === val) ? null : val;
    for (const o of document.querySelectorAll('button.f')) {{
      const ov = o.dataset.cat !== undefined ? o.dataset.cat : o.dataset.lang;
      const active = (o.dataset.cat !== undefined) ? (cat === ov) : (lang === ov);
      o.classList.toggle('on', !!active);
    }}
    apply();
  }});
}}
</script>
</body>
</html>
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--yerel", action="store_true", help="render from veri/projeler.json")
    ap.add_argument("--cikti", default=os.path.join(HERE, "index.html"))
    args = ap.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if args.yerel:
        snap = json.load(open(SNAPSHOT, encoding="utf-8"))
        rows, missing, when = snap["projects"], snap.get("missing", []), snap["generated"]
    else:
        rows, missing = collect(token)
        when = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
        os.makedirs(os.path.dirname(SNAPSHOT), exist_ok=True)
        json.dump({"generated": when, "missing": missing, "projects": rows},
                  open(SNAPSHOT, "w", encoding="utf-8"), indent=2, ensure_ascii=False)

    page = render(rows, missing, when)
    open(args.cikti, "w", encoding="utf-8").write(page)
    print(f"{len(rows)} projects rendered to {args.cikti}")
    if missing:
        print("no metadata in:", ", ".join(missing))


if __name__ == "__main__":
    main()
