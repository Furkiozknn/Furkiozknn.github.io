"""The generator has one promise: nothing on the page is written by hand.

Everything the page says comes from a repository's own project-meta.json, and
a field that is null there is left off rather than filled in with something
plausible. That promise is only worth anything if it is checked, so these tests
exist mainly to catch the two ways it breaks:

* a null leaking onto the page as the string "None", which reads like a fact;
* a feed, sitemap or JSON-LD block that is malformed, which fails silently
  because nobody looks at them with a browser.
"""

import json
import re
import sys
import xml.dom.minidom
from html.parser import HTMLParser
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import uret  # noqa: E402


# --------------------------------------------------------------------------
# fixtures
# --------------------------------------------------------------------------


def meta(**over):
    """A complete project-meta.json, so a test can null exactly one field."""
    base = {
        "id": "thing",
        "repository": "https://github.com/Furkiozknn/thing",
        "homepage": "https://example.invalid/thing",
        "releases": "https://github.com/Furkiozknn/thing/releases",
        "status": "active",
        "category": "developer-tool",
        "primary_language": "Python",
        "version": "1.2.3",
        "license": "MIT",
        "topics": ["alpha", "beta"],
        "technologies": ["stdlib"],
        "platform": ["linux"],
        "summary": "Does a thing.",
        "key_features": ["first", "second", "third"],
        "tests": {"count": 42},
    }
    base.update(over)
    return base


def release(**over):
    base = {
        "repo": "thing", "tag": "v1.0.0", "title": "thing v1.0.0",
        "url": "https://github.com/Furkiozknn/thing/releases/tag/v1.0.0",
        "published": "2026-01-02T03:04:05Z", "prerelease": False,
    }
    base.update(over)
    return base


class Tags(HTMLParser):
    """Enough of a parser to prove the page is well-formed and to count cards."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.cards = 0
        self.unclosed_error = None
        self.void = {"meta", "link", "img", "br", "hr", "input", "source", "path", "rect", "text"}

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag == "article" and "card" in (d.get("class") or ""):
            self.cards += 1
        if tag not in self.void:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag in self.void:
            return
        if self.stack and self.stack[-1] == tag:
            self.stack.pop()
        elif tag in self.stack:
            while self.stack and self.stack.pop() != tag:
                pass


# --------------------------------------------------------------------------
# the null rule
# --------------------------------------------------------------------------


@pytest.mark.parametrize("field", ["version", "homepage", "releases", "primary_language", "summary"])
def test_a_null_field_never_reaches_the_page_as_a_word(field):
    html_out = uret.card(meta(**{field: None}))
    assert "None" not in html_out
    assert "null" not in html_out


def test_a_null_version_drops_the_version_chip_rather_than_showing_v_none():
    assert "v1.2.3" in uret.card(meta())
    assert 'class="chip ver"' not in uret.card(meta(version=None))


def test_a_null_homepage_drops_the_live_link_instead_of_linking_nowhere():
    assert ">Live<" in uret.card(meta())
    assert ">Live<" not in uret.card(meta(homepage=None))


def test_a_null_test_count_drops_the_tests_chip():
    assert "42 tests" in uret.card(meta())
    assert "tests" not in uret.card(meta(tests=None)).split('class="links"')[0]


def test_a_missing_tests_block_is_not_an_error():
    m = meta()
    del m["tests"]
    assert "thing" in uret.card(m)


def test_an_archived_project_is_marked_as_archived():
    assert "archived" in uret.card(meta(status="archived"))
    assert "archived" not in uret.card(meta()).replace("data-search", "")


# --------------------------------------------------------------------------
# escaping - the page is generated from data it does not control
# --------------------------------------------------------------------------


def test_a_summary_with_html_in_it_is_escaped_not_rendered():
    out = uret.card(meta(summary='<script>alert("x")</script>'))
    assert "<script>" not in out
    assert "&lt;script&gt;" in out


def test_a_quote_in_a_field_cannot_break_out_of_an_attribute():
    out = uret.card(meta(id='a" onmouseover="evil()'))
    assert 'onmouseover="evil()"' not in out
    assert "&quot;" in out


def test_an_ampersand_in_a_url_is_escaped():
    assert "&amp;" in uret.card(meta(homepage="https://e.invalid/?a=1&b=2"))


# --------------------------------------------------------------------------
# the page as a whole
# --------------------------------------------------------------------------


def test_the_page_renders_one_card_per_project():
    rows = [meta(id="a"), meta(id="b"), meta(id="c", category="game")]
    page = uret.render(rows, [], "2026-01-01")
    p = Tags()
    p.feed(page)
    assert p.cards == 3


def test_the_page_is_balanced_html():
    page = uret.render([meta(id="a")], [], "2026-01-01")
    p = Tags()
    p.feed(page)
    assert p.stack == [], "unclosed tags: %s" % p.stack


def test_the_headline_totals_leave_archived_projects_out():
    """The page and TESTLER.md have to agree, and TESTLER.md counts live work."""
    live_only = uret.render([meta(id="a", tests={"count": 10})], [], "2026-01-01")
    with_archived = uret.render(
        [meta(id="a", tests={"count": 10}),
         meta(id="b", status="archived", tests={"count": 999})],
        [], "2026-01-01")
    assert ">10<" in live_only
    assert "999" not in with_archived.split('class="stats"')[1].split("</div>")[0]


def test_a_repository_with_no_metadata_is_named_rather_than_hidden():
    page = uret.render([meta(id="a")], ["mystery-repo"], "2026-01-01")
    assert "mystery-repo" in page


def test_the_page_carries_the_feed_link_and_a_canonical_url():
    page = uret.render([meta()], [], "2026-01-01")
    assert 'type="application/atom+xml"' in page
    assert 'rel="canonical"' in page


def test_every_project_lands_in_a_section():
    rows = [meta(id="a", category="game"), meta(id="b", category="not-a-known-group")]
    page = uret.render(rows, [], "2026-01-01")
    assert 'data-group="game"' in page
    assert 'data-group="not-a-known-group"' in page


# --------------------------------------------------------------------------
# JSON-LD
# --------------------------------------------------------------------------


def test_the_jsonld_block_is_valid_json_and_an_itemlist():
    d = json.loads(uret.jsonld([meta(id="a"), meta(id="b")], "2026-01-01"))
    assert d["@type"] == "ItemList"
    assert d["numberOfItems"] == 2
    assert [i["position"] for i in d["itemListElement"]] == [1, 2]


def test_the_jsonld_block_omits_fields_that_are_null():
    d = json.loads(uret.jsonld([meta(version=None, license=None)], "2026-01-01"))
    node = d["itemListElement"][0]["item"]
    assert "version" not in node
    assert "license" not in node
    assert node["name"] == "thing"


def test_the_jsonld_block_embedded_in_the_page_still_parses():
    page = uret.render([meta(id="a")], [], "2026-01-01")
    m = re.search(r'<script type="application/ld\+json">\s*(\{.*?\})\s*</script>', page, re.S)
    assert m, "the page has no JSON-LD block"
    assert json.loads(m.group(1))["numberOfItems"] == 1


def test_the_jsonld_is_sorted_so_the_diff_is_stable():
    d = json.loads(uret.jsonld([meta(id="z"), meta(id="a")], "2026-01-01"))
    assert [i["item"]["name"] for i in d["itemListElement"]] == ["a", "z"]


# --------------------------------------------------------------------------
# the feed, the sitemap and robots.txt
# --------------------------------------------------------------------------


def test_the_feed_is_well_formed_xml_with_one_entry_per_release():
    feed = uret.atom([release(tag="v1"), release(tag="v2", url="https://e.invalid/2")], "2026-01-01")
    xml.dom.minidom.parseString(feed.encode("utf-8"))
    assert feed.count("<entry>") == 2


def test_a_feed_with_no_releases_is_still_valid_and_empty():
    feed = uret.atom([], "2026-01-01")
    xml.dom.minidom.parseString(feed.encode("utf-8"))
    assert "<entry>" not in feed


def test_the_feeds_updated_time_is_the_newest_release():
    feed = uret.atom([release(published="2026-05-05T00:00:00Z"),
                      release(published="2026-01-01T00:00:00Z")], "2026-09-09")
    assert "<updated>2026-05-05T00:00:00Z</updated>" in feed.split("<entry>")[0]


def test_a_release_title_with_an_ampersand_cannot_break_the_feed():
    feed = uret.atom([release(title="a & b <c>")], "2026-01-01")
    xml.dom.minidom.parseString(feed.encode("utf-8"))
    assert "a &amp; b &lt;c&gt;" in feed


def test_a_prerelease_says_so_in_its_summary():
    assert "(pre-release)" in uret.atom([release(prerelease=True)], "2026-01-01")


def test_the_feed_is_capped_so_it_cannot_grow_without_bound():
    many = [release(tag="v%d" % i, url="https://e.invalid/%d" % i) for i in range(200)]
    assert uret.atom(many, "2026-01-01").count("<entry>") == 60


def test_the_sitemap_is_well_formed_and_carries_the_date():
    sm = uret.sitemap("2026-03-04")
    xml.dom.minidom.parseString(sm.encode("utf-8"))
    assert "<lastmod>2026-03-04</lastmod>" in sm


def test_robots_points_at_the_sitemap_and_allows_crawling():
    r = uret.robots()
    assert "Allow: /" in r
    assert r.strip().endswith("sitemap.xml")


# --------------------------------------------------------------------------
# fetching - stubbed, so the suite never needs the network
# --------------------------------------------------------------------------


def test_repo_names_skips_forks_and_private_repositories(monkeypatch):
    payload = [
        {"name": "mine", "fork": False, "private": False},
        {"name": "forked", "fork": True, "private": False},
        {"name": "secret", "fork": False, "private": True},
    ]
    monkeypatch.setattr(uret, "fetch", lambda url, token=None: json.dumps(payload))
    assert uret.repo_names() == ["mine"]


def test_collect_falls_back_to_master_when_main_has_no_metadata(monkeypatch):
    import urllib.error

    monkeypatch.setattr(uret, "repo_names", lambda token=None: ["old"])

    def fake(url, token=None):
        if "/main/" in url:
            raise urllib.error.HTTPError(url, 404, "no", None, None)
        return json.dumps(meta(id="old"))

    monkeypatch.setattr(uret, "fetch", fake)
    rows, missing = uret.collect()
    assert missing == []
    assert rows[0]["id"] == "old"


def test_collect_reports_a_repository_with_no_metadata_instead_of_inventing_one(monkeypatch):
    import urllib.error

    monkeypatch.setattr(uret, "repo_names", lambda token=None: ["bare"])

    def fake(url, token=None):
        raise urllib.error.HTTPError(url, 404, "no", None, None)

    monkeypatch.setattr(uret, "fetch", fake)
    rows, missing = uret.collect()
    assert rows == []
    assert missing == ["bare"]


def test_collect_releases_ignores_drafts_and_sorts_newest_first(monkeypatch):
    payload = [
        {"tag_name": "v1", "name": "one", "html_url": "u1", "published_at": "2026-01-01T00:00:00Z",
         "draft": False, "prerelease": False},
        {"tag_name": "v2", "name": "two", "html_url": "u2", "published_at": "2026-02-01T00:00:00Z",
         "draft": False, "prerelease": True},
        {"tag_name": "v3", "name": "draft", "html_url": "u3", "published_at": None, "draft": True},
    ]
    monkeypatch.setattr(uret, "fetch", lambda url, token=None: json.dumps(payload))
    got = uret.collect_releases(["thing"])
    assert [r["tag"] for r in got] == ["v2", "v1"]
    assert got[0]["prerelease"] is True


def test_a_repository_the_api_will_not_answer_for_contributes_no_entries(monkeypatch):
    def boom(url, token=None):
        raise OSError("network down")

    monkeypatch.setattr(uret, "fetch", boom)
    assert uret.collect_releases(["thing"]) == []


# --------------------------------------------------------------------------
# the real snapshot, if it is checked in
# --------------------------------------------------------------------------


def test_the_checked_in_snapshot_still_renders():
    snap = Path(__file__).resolve().parents[1] / "veri" / "projeler.json"
    if not snap.is_file():
        pytest.skip("no snapshot checked in")
    d = json.loads(snap.read_text(encoding="utf-8"))
    page = uret.render(d["projects"], d.get("missing", []), d["generated"])
    p = Tags()
    p.feed(page)
    assert p.cards == len(d["projects"])
    assert p.stack == []
    assert "None" not in page or ">None<" not in page


# --------------------------------------------------------------------------
# linking to a card - every repository's homepage is one of these anchors
# --------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]


def snapshot():
    snap = ROOT / "veri" / "projeler.json"
    if not snap.is_file():
        pytest.skip("no snapshot checked in")
    return json.loads(snap.read_text(encoding="utf-8"))


def test_every_homepage_that_points_at_a_card_here_finds_that_card():
    """A repository whose homepage is https://furkiozknn.github.io/#name sends
    its visitors to that id; a card that renamed or vanished strands them."""
    d = snapshot()
    page = uret.render(d["projects"], d.get("missing", []), d["generated"])
    ids = re.findall(r'<article class="card" id="([^"]+)"', page)
    assert len(ids) == len(set(ids)), "two cards share an id"
    for m in d["projects"]:
        home = m.get("homepage") or ""
        if home.startswith(uret.SITE + "#"):
            assert home.split("#", 1)[1] in ids, home


def test_a_linked_card_lands_below_the_sticky_toolbar_not_under_it():
    page = uret.render([meta()], [], "2026-01-01")
    assert "scroll-margin-top:calc(var(--tools-h)" in page
    assert "setProperty('--tools-h'" in page


def test_a_homepage_that_is_this_directory_gets_no_live_link_to_itself():
    assert ">Live<" not in uret.card(meta(homepage=uret.SITE + "#thing"))
    assert ">Live<" not in uret.card(meta(homepage=uret.SITE))
    assert ">Live<" in uret.card(meta(homepage=uret.SITE + "masal/"))


# --------------------------------------------------------------------------
# accessibility and reader preferences
# --------------------------------------------------------------------------


def test_the_page_has_a_main_landmark_and_a_labelled_search():
    page = uret.render([meta()], [], "2026-01-01")
    assert '<main id="main">' in page and "</main>" in page
    assert '<label for="q"' in page
    assert 'role="status"' in page


def test_every_filter_button_is_a_button_that_announces_its_state():
    page = uret.render([meta(), meta(id="g", category="game", primary_language="Rust")], [], "2026-01-01")
    buttons = re.findall(r'<button[^>]*class="f"[^>]*>', page)
    assert len(buttons) == 4
    for b in buttons:
        assert 'type="button"' in b and 'aria-pressed="false"' in b


def test_the_page_follows_the_readers_light_or_dark_preference():
    page = uret.render([meta()], [], "2026-01-01")
    assert '<meta name="color-scheme" content="dark light">' in page
    assert "@media (prefers-color-scheme: light)" in page


def test_link_previews_carry_size_alt_text_and_a_twitter_image():
    page = uret.render([meta()], [], "2026-01-01")
    for tag in ('property="og:image:width" content="1200"', 'property="og:image:height" content="630"',
                'property="og:image:alt"', 'name="twitter:image"', 'name="twitter:title"'):
        assert tag in page, tag


def test_the_social_card_states_no_number_that_could_go_stale():
    """The card is an image nobody regenerates; it said "26 repositories,
    4,700 tests" long after both had changed."""
    svg = (ROOT / "assets" / "og.svg").read_text(encoding="utf-8")
    texts = re.findall(r"<text[^>]*>([^<]*)</text>", svg)
    assert texts
    assert not [t for t in texts if re.search(r"\d", t)]


# --------------------------------------------------------------------------
# prose that disagrees with the tests chip on the same card
# --------------------------------------------------------------------------


def test_a_summary_that_states_an_old_test_count_is_named():
    got = uret.stale_counts([meta(summary="Zero dependencies, 289 tests.", tests={"count": 319})])
    assert got == ["thing: the text says 289 tests, tests.count is 319"]


def test_a_summary_that_agrees_with_the_count_is_not_named():
    assert uret.stale_counts([meta(summary="1,234 tests and counting.", tests={"count": 1234})]) == []
    assert uret.stale_counts([meta(summary="12 tests", tests=None)]) == []


# --------------------------------------------------------------------------
# the committed output is the generator's output
# --------------------------------------------------------------------------


def test_the_committed_page_feed_and_sitemap_are_what_the_snapshot_renders():
    """A hand edit to index.html would be overwritten by the next rebuild, and
    a template change committed without re-rendering would ship the old page."""
    d = snapshot()
    assert (ROOT / "index.html").read_text(encoding="utf-8") == uret.render(
        d["projects"], d.get("missing", []), d["generated"])
    assert (ROOT / "feed.xml").read_text(encoding="utf-8") == uret.atom(d.get("releases", []), d["generated"])
    assert (ROOT / "sitemap.xml").read_text(encoding="utf-8") == uret.sitemap(d["generated"])
