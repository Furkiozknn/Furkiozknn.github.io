#!/usr/bin/env python3
"""Build the project directory from the project-meta.json file in every
repository on the account.

Nothing on the page is typed by hand: the generator fetches each repository's
metadata over the GitHub raw endpoint, writes the snapshot to veri/projeler.json
and renders index.html from it. A field that is null in the metadata is left out
of the page rather than filled in.

    python3 uret.py              # fetch, then render
    python3 uret.py --yerel      # render from the snapshot already in veri/
    python3 uret.py --onizleme   # refresh only the card previews, then render
"""

import argparse
import datetime
import html
import json
import os
import re
import sys
import urllib.error
import urllib.request

OWNER = "Furkiozknn"
RAW = "https://raw.githubusercontent.com/{owner}/{repo}/{branch}/project-meta.json"
API = "https://api.github.com/users/{owner}/repos?per_page=100&type=owner"
RELEASES = "https://api.github.com/repos/{owner}/{repo}/releases?per_page=5"
SITE = "https://furkiozknn.github.io/"
HERE = os.path.dirname(os.path.abspath(__file__))
SNAPSHOT = os.path.join(HERE, "veri", "projeler.json")
RAW_FILE = "https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}"
# Card previews are local copies, so the page still asks no other host for anything.
PREVIEW_DIR = os.path.join(HERE, "assets", "onizleme")
PREVIEW_URL = "assets/onizleme/"
MAX_PREVIEW_BYTES = 400_000
PREVIEW_EXT = (".png", ".jpg", ".jpeg", ".webp", ".svg")
# A screenshot says more than a banner for something a visitor can look at.
VISUAL_CATEGORIES = {"game", "web-app", "template"}

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
    """One HTTP GET. A token is optional and only raises the rate limit."""
    req = urllib.request.Request(url, headers={"User-Agent": "furkiozknn-hub"})
    if token:
        req.add_header("Authorization", "Bearer " + token)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8")


def repo_names(token=None):
    """Every public, non-fork repository on the account, straight from GitHub."""
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
    """Read each repository's own project-meta.json, main first, then master.

    A repository with no metadata is reported by name rather than guessed at:
    the page says it is missing instead of inventing a card for it.
    """
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


def collect_releases(names, token=None):
    """Real releases, read from the GitHub API. A repository that has none, or
    that the API will not answer for, simply contributes no entries."""
    out = []
    for name in names:
        try:
            data = json.loads(fetch(RELEASES.format(owner=OWNER, repo=name), token))
        except Exception:
            continue
        for r in data:
            if r.get("draft") or not r.get("published_at"):
                continue
            out.append({
                "repo": name,
                "tag": r.get("tag_name") or "",
                "title": (r.get("name") or "").strip() or f'{name} {r.get("tag_name") or ""}'.strip(),
                "url": r.get("html_url") or f"https://github.com/{OWNER}/{name}/releases",
                "published": r["published_at"],
                "prerelease": bool(r.get("prerelease")),
            })
    out.sort(key=lambda r: r["published"], reverse=True)
    return out


# --- card previews ----------------------------------------------------------

SAFE_PATH = re.compile(r"^[\w][\w./-]*$")
SVG_ACTIVE = re.compile(rb"<script|<foreignobject|javascript:|\son\w+\s*=|<!entity", re.I)


def preview_candidates(m):
    """The images a card may show, in order: only what the repository's own
    media block lists, never a guess. Something a visitor can look at (a game,
    a web app, a template) leads with a screenshot; a tool leads with its hero."""
    media = m.get("media") or {}
    hero = [media["hero"]] if media.get("hero") else []
    shots = list(media.get("screenshots") or [])
    order = shots + hero if m.get("category") in VISUAL_CATEGORIES else hero + shots
    out = []
    for p in order:
        if (isinstance(p, str) and SAFE_PATH.match(p) and ".." not in p
                and p.lower().endswith(PREVIEW_EXT) and p not in out):
            out.append(p)
    return out


def image_kind(data):
    """The extension the bytes really are, or None. The file name is not trusted:
    a preview is written only if its content is a raster image, or an SVG with
    nothing in it that could run when the file is opened on this origin."""
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return ".png"
    if data[:3] == b"\xff\xd8\xff":
        return ".jpg"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return ".webp"
    head = data[:2048].lstrip().lower()
    if (head.startswith(b"<svg") or head.startswith(b"<?xml")) and b"<svg" in data[:4096].lower():
        return None if SVG_ACTIVE.search(data) else ".svg"
    return None


def fetch_bytes(url, token=None):
    req = urllib.request.Request(url, headers={"User-Agent": "furkiozknn-hub"})
    if token:
        req.add_header("Authorization", "Bearer " + token)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read(MAX_PREVIEW_BYTES + 1)


def collect_previews(rows, token=None, get=None):
    """Copy one preview per project into assets/onizleme/<id>.<ext>.

    The first candidate that downloads, is small enough and is really an image
    wins. A project with none keeps a card without a picture - the page is
    shorter rather than decorated with something the repository never showed.
    Returns the provenance map written into the snapshot."""
    get = get or (lambda url: fetch_bytes(url, token))
    os.makedirs(PREVIEW_DIR, exist_ok=True)
    found = {}
    for m in rows:
        for path in preview_candidates(m):
            data = None
            for branch in ("main", "master"):
                url = RAW_FILE.format(owner=OWNER, repo=m["id"], branch=branch, path=path)
                try:
                    data = get(url)
                    break
                except Exception:
                    continue
            if not data or len(data) > MAX_PREVIEW_BYTES:
                continue
            kind = image_kind(data)
            if not kind:
                continue
            name = m["id"] + kind
            with open(os.path.join(PREVIEW_DIR, name), "wb") as f:
                f.write(data)
            found[m["id"]] = {"file": PREVIEW_URL + name, "source": url, "bytes": len(data)}
            break
    # A preview whose project is gone, or that changed type, must not linger.
    keep = {os.path.basename(v["file"]) for v in found.values()}
    for name in os.listdir(PREVIEW_DIR):
        if name not in keep and name.lower().endswith(PREVIEW_EXT):
            os.remove(os.path.join(PREVIEW_DIR, name))
    return dict(sorted(found.items()))


def preview_file(pid):
    """The local preview of a project, if one was copied; the page links nothing else."""
    for ext in PREVIEW_EXT:
        if os.path.isfile(os.path.join(PREVIEW_DIR, pid + ext)):
            return PREVIEW_URL + pid + ext
    return None


def atom(releases, when):
    """One Atom entry per real release. Nothing is written for a release that
    does not exist, and an entry's date is the date GitHub published it."""
    newest = releases[0]["published"] if releases else when + "T00:00:00Z"
    parts = ['<?xml version="1.0" encoding="utf-8"?>',
             '<feed xmlns="http://www.w3.org/2005/Atom">',
             f'<title>{OWNER} - releases</title>',
             f'<subtitle>Every release across the repositories on this account.</subtitle>',
             f'<link href="{SITE}feed.xml" rel="self"/>',
             f'<link href="{SITE}"/>',
             f'<id>{SITE}</id>',
             f'<updated>{newest}</updated>',
             f'<author><name>{OWNER}</name></author>']
    for r in releases[:60]:
        summary = f'{r["repo"]} {r["tag"]}'.strip()
        if r["prerelease"]:
            summary += " (pre-release)"
        parts += ['<entry>',
                  f'<title>{e(r["title"])}</title>',
                  f'<link href="{e(r["url"])}"/>',
                  f'<id>{e(r["url"])}</id>',
                  f'<updated>{e(r["published"])}</updated>',
                  f'<category term="{e(r["repo"])}"/>',
                  f'<summary>{e(summary)}</summary>',
                  '</entry>']
    parts.append('</feed>')
    return "\n".join(parts) + "\n"


def sitemap(when):
    """One URL, because the directory is one page. Valid is what matters here."""
    return ('<?xml version="1.0" encoding="utf-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            f'  <url><loc>{SITE}</loc><lastmod>{when}</lastmod>'
            '<changefreq>weekly</changefreq><priority>1.0</priority></url>\n'
            '</urlset>\n')


def robots():
    """Allow everything and point at the sitemap - there is nothing here to hide."""
    return ("User-agent: *\n"
            "Allow: /\n"
            f"Sitemap: {SITE}sitemap.xml\n")


def jsonld(rows, when):
    """A machine-readable description of the directory, in the vocabulary search
    engines already read. Every field comes from a repository's own metadata."""
    items = []
    for i, m in enumerate(sorted(rows, key=lambda x: x["id"]), start=1):
        node = {
            "@type": "SoftwareSourceCode",
            "name": m["id"],
            "codeRepository": m["repository"],
        }
        if m.get("summary"):
            node["description"] = m["summary"]
        if m.get("primary_language"):
            node["programmingLanguage"] = m["primary_language"]
        if m.get("license"):
            node["license"] = m["license"]
        if m.get("version"):
            node["version"] = m["version"]
        if m.get("topics"):
            node["keywords"] = ", ".join(m["topics"])
        if m.get("homepage"):
            node["url"] = m["homepage"]
        items.append({"@type": "ListItem", "position": i, "item": node})
    doc = {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": f"{OWNER} - project directory",
        "url": SITE,
        "dateModified": when,
        "numberOfItems": len(items),
        "itemListElement": items,
    }
    return json.dumps(doc, ensure_ascii=False, indent=1)


# --- rendering ------------------------------------------------------------

def gid(key):
    """A category key as a dictionary key the page's script can look up."""
    return key.replace("-", "_")


def e(x):
    """Escape for HTML, attributes included. Everything on the page goes through this."""
    return html.escape(str(x), quote=True)


def chip(text, kind="", i18n=""):
    """One small labelled pill - a language, a version, a test count.

    i18n is the interface-shell key the page's script translates; the English
    text stays in the markup, so the page reads correctly without the script."""
    return f'<span class="chip {kind}"{i18n}>{e(text)}</span>'


def points_here(url):
    """True when a homepage is this directory itself - its root or a card on it.

    Most repositories use their own card here (#repo-name) as their homepage;
    a "Live" link on that card would only link the card to itself.
    """
    return url.split("#", 1)[0].rstrip("/") == SITE.rstrip("/")


STATED_TESTS = re.compile(r"\b(\d[\d,]*) (?:passing )?tests\b")


def stale_counts(rows):
    """Prose that states a test count the tests block no longer agrees with.

    The page shows a repository's summary next to its tests chip, so a summary
    written when the suite was smaller puts two different numbers on one card.
    The fix belongs in that repository's project-meta.json; this only names it.
    """
    out = []
    for m in rows:
        count = (m.get("tests") or {}).get("count")
        if not count:
            continue
        texts = [m.get("summary") or ""] + list(m.get("key_features") or [])
        for text in texts:
            for n in STATED_TESTS.findall(text):
                if int(n.replace(",", "")) != count:
                    out.append(f'{m["id"]}: the text says {n} tests, tests.count is {count}')
    return out


def card(m):
    """One project, rendered from its own metadata.

    Every optional field is guarded, because a null in the metadata has to
    leave the page shorter rather than print the word "None" as if it were a
    fact about the project.
    """
    pid = m["id"]
    tests = (m.get("tests") or {}).get("count")
    links = [(m["repository"], "Repository", "l_repo")]
    if m.get("homepage") and not points_here(m["homepage"]):
        # A game's homepage is the game itself, so the link says so.
        play = m.get("category") == "game"
        links.append((m["homepage"], "Play" if play else "Live", "l_play" if play else "l_live"))
    if m.get("releases"):
        links.append((m["releases"], "Releases", "l_rel"))
    feats = (m.get("key_features") or [])[:2]
    search = " ".join(
        [pid, m.get("summary") or "", " ".join(m.get("topics") or []),
         " ".join(m.get("technologies") or []), m.get("primary_language") or "",
         " ".join(m.get("platform") or []), m.get("category") or ""]
    ).lower()
    out = [f'<article class="card" id="{e(pid)}" data-search="{e(search)}" '
           f'data-cat="{e(m.get("category") or "")}" data-lang="{e(m.get("primary_language") or "")}">']
    thumb = preview_file(pid)
    if thumb:
        # Decorative: the name, summary and links below say everything the
        # picture does, so it is hidden from screen readers and from the tab order.
        fit = " contain" if thumb.endswith(".svg") else ""
        out.append(f'<a class="thumb{fit}" href="{e(m["repository"])}" tabindex="-1" aria-hidden="true">'
                   f'<img src="{e(thumb)}" alt="" width="640" height="360" loading="lazy" decoding="async"></a>')
    out.append('<header>')
    out.append(f'<h3><a href="{e(m["repository"])}">{e(pid)}</a></h3>')
    meta_bits = []
    if m.get("primary_language"):
        meta_bits.append(chip(m["primary_language"], "lang"))
    if m.get("version"):
        meta_bits.append(chip("v" + m["version"], "ver"))
    if tests:
        meta_bits.append(chip(f"{tests:,} tests", "tests", f' data-i="tests" data-n="{tests}"'))
    if m.get("status") == "archived":
        meta_bits.append(chip("archived", "arch", ' data-i="archived"'))
    out.append('<div class="meta">' + "".join(meta_bits) + "</div>")
    out.append("</header>")
    out.append(f'<p class="sum">{e(m.get("summary") or "")}</p>')
    if feats:
        out.append("<ul class=\"feats\">" + "".join(f"<li>{e(f)}</li>" for f in feats) + "</ul>")
    if m.get("topics"):
        out.append('<div class="topics">' + "".join(
            f'<span class="topic">{e(t)}</span>' for t in m["topics"][:8]) + "</div>")
    out.append('<div class="links">' + "".join(
        f'<a href="{e(u)}" data-i="{k}">{e(t)}</a>' for u, t, k in links) + "</div>")
    out.append("</article>")
    return "\n".join(out)


def render(rows, missing, when):
    """The whole page: headline totals, filters, one section per category.

    Archived projects keep their card but stay out of the headline, so this
    page and TESTLER.md report the same number.
    """
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
            f'<section class="group" data-group="{e(key)}"><h2><span data-i="g_{gid(key)}">{e(label)}</span>'
            f'<span class="count">{len(items)}</span></h2>'
            f'<div class="grid">' + "\n".join(card(m) for m in items) + "</div></section>")
    for key, items in sorted(by_cat.items()):
        sections.append(
            f'<section class="group" data-group="{e(key)}"><h2>{e(key)}'
            f'<span class="count">{len(items)}</span></h2>'
            f'<div class="grid">' + "\n".join(card(m) for m in items) + "</div></section>")

    filters = "".join(
        f'<button type="button" class="f" data-cat="{e(k)}" aria-pressed="false" data-i="g_{gid(k)}">{e(l)}</button>'
        for k, l in GROUPS if by_cat.get(k) is not None or any(m.get("category") == k for m in rows))
    langfilters = "".join(
        f'<button type="button" class="f" data-lang="{e(l)}" aria-pressed="false">{e(l)}</button>'
        for l in langs)

    note = ""
    if missing:
        note = ('<p class="warn">No project-meta.json found in: '
                + ", ".join(e(x) for x in missing) + "</p>")

    template = open(TEMPLATE_FILE, encoding="utf-8").read()
    return fill(template, dict(
        owner=OWNER,
        count=len(rows),
        tests=f"{total_tests:,}",
        tests_raw=total_tests,
        suites=suites,
        when=e(when),
        filters=filters,
        langfilters=langfilters,
        sections="\n".join(sections),
        note=note,
        jsonld=jsonld(rows, when),
        groups_en=js_labels(dict(GROUPS)),
        groups_tr=js_labels(GROUPS_TR),
    ))


GROUPS_TR = {
    "security-tool": "Güvenlik",
    "developer-tool": "Geliştirici araçları",
    "observability": "Gözlemlenebilirlik",
    "mcp-server": "MCP sunucuları",
    "agent-infrastructure": "Ajan altyapısı",
    "backend-service": "Arka uç servisleri",
    "web-app": "Web uygulamaları",
    "game": "Oyunlar",
    "template": "Şablonlar",
    "research": "Araştırma",
    "profile": "Bu hesap",
}

TEMPLATE_FILE = os.path.join(HERE, "sablon.html")


def js_labels(labels):
    """Group names as extra JS dictionary entries: ,g_key:'Label' ... (escaped for a JS string)."""
    return "".join(",g_%s:%s" % (k.replace("-", "_"), json.dumps(v, ensure_ascii=False))
                   for k, v in labels.items())


def fill(template, values):
    """One pass over @@name@@ tokens, so a value that happens to contain a token is left alone."""
    return re.sub(r"@@(\w+)@@", lambda m: str(values[m.group(1)]), template)


def write_snapshot(snap):
    """One key order whichever path wrote it, so a rebuild diff shows data, not reshuffling."""
    order = ("generated", "missing", "releases", "previews", "projects")
    snap = {k: snap[k] for k in order if k in snap}
    os.makedirs(os.path.dirname(SNAPSHOT), exist_ok=True)
    with open(SNAPSHOT, "w", encoding="utf-8", newline="\n") as f:
        json.dump(snap, f, indent=2, ensure_ascii=False)


def main():
    """Fetch, or read the snapshot, then write the page and the machine-readable files."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--yerel", action="store_true", help="render from veri/projeler.json")
    ap.add_argument("--onizleme", action="store_true",
                    help="refresh only the card previews for the snapshot's projects, then render")
    ap.add_argument("--cikti", default=os.path.join(HERE, "index.html"))
    args = ap.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if args.yerel or args.onizleme:
        snap = json.load(open(SNAPSHOT, encoding="utf-8"))
        rows, missing, when = snap["projects"], snap.get("missing", []), snap["generated"]
        releases = snap.get("releases", [])
        if args.onizleme:
            # Raw file downloads only - no API call, so no rate limit to spend.
            snap["previews"] = collect_previews(rows, token)
            write_snapshot(snap)
    else:
        rows, missing = collect(token)
        releases = collect_releases([m["id"] for m in rows], token)
        when = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
        write_snapshot({"generated": when, "missing": missing, "releases": releases,
                        "previews": collect_previews(rows, token), "projects": rows})

    page = render(rows, missing, when)
    # newline="\n": the same bytes on every OS, so a Windows rebuild is not a diff.
    open(args.cikti, "w", encoding="utf-8", newline="\n").write(page)

    out = os.path.dirname(os.path.abspath(args.cikti)) or HERE
    open(os.path.join(out, "feed.xml"), "w", encoding="utf-8", newline="\n").write(atom(releases, when))
    open(os.path.join(out, "sitemap.xml"), "w", encoding="utf-8", newline="\n").write(sitemap(when))
    open(os.path.join(out, "robots.txt"), "w", encoding="utf-8", newline="\n").write(robots())

    print(f"{len(rows)} projects rendered to {args.cikti}")
    print(f"{len(releases)} releases in feed.xml; sitemap.xml and robots.txt written")
    if missing:
        print("no metadata in:", ", ".join(missing))
    # A GitHub Actions annotation, not a failure: the stale number lives in
    # another repository, and the rebuild should not stop because of it.
    for line in stale_counts(rows):
        print(f"::warning title=stale test count::{line}")


if __name__ == "__main__":
    main()
