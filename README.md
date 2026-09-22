# furkiozknn.github.io

The project directory for [this account](https://github.com/Furkiozknn): every public
repository, in one searchable page.

**→ [furkiozknn.github.io](https://furkiozknn.github.io/)**

Nothing on the page is written here. `uret.py` reads the `project-meta.json` that every
repository carries — identity, version, status, platform, key features, and the test count
together with the runner line it came from — writes the snapshot to
[`veri/projeler.json`](veri/projeler.json) and renders `index.html` from it. A field that is
`null` in the metadata is left off the page rather than filled in with a plausible-looking
string, which is the same rule the
[schema](https://github.com/Furkiozknn/Furkiozknn/blob/main/schema/README.md) follows.

A scheduled workflow rebuilds it every Monday and commits only when the output actually
changes, so the page cannot quietly fall behind the repositories it describes.

```sh
python3 uret.py            # fetch every repository's metadata, then render
python3 uret.py --yerel    # render from the snapshot already in veri/
python3 -m pytest tests -q # 37 tests over the generator
```

No build step, no dependencies, one HTML file.

## What the tests are for

The page is generated, so the generator is the only thing here that can break — and
it breaks quietly. A malformed feed, a sitemap that does not parse, a JSON-LD block
with a trailing comma: a browser shows the page regardless and nobody notices for
weeks.

So the suite checks the two failure modes that actually happen. First, the null rule:
a field that is `null` in a repository's metadata has to leave the page *shorter*,
never print the word `None` where a reader would take it for a fact. Every optional
field is tested for that individually. Second, well-formedness: the feed and the
sitemap are parsed as XML, the JSON-LD block is parsed out of the rendered page and
validated, and the page itself is walked for unbalanced tags. The suite also renders
the real snapshot in [`veri/`](veri/), so a change that works on fixtures but breaks
on the actual 27 projects fails in CI rather than on the live site.

Writing them found a real one: a repository whose `summary` was `null` crashed the
whole build, because `.get("summary", "")` returns `None` when the key is present
and null. Every repository happened to have a summary, so nothing had failed yet.

## Following it without opening it

The same run writes three things a machine can read, so the account can be followed without
anyone polling the page:

| File | What it is |
| --- | --- |
| [`veri/projeler.json`](veri/projeler.json) | the snapshot the page is rendered from — every repository's metadata, one JSON document |
| [`feed.xml`](https://furkiozknn.github.io/feed.xml) | an Atom feed of every release across the repositories, read from the GitHub API, newest first |
| [`sitemap.xml`](https://furkiozknn.github.io/sitemap.xml) + `robots.txt` | so search engines index the directory rather than guess at it |

The page itself also carries a `schema.org` `ItemList` in JSON-LD, built from the same
metadata, so a crawler sees the project list rather than a wall of markup. A release that does
not exist contributes no feed entry, and a repository the API will not answer for contributes
none either — the feed is short rather than invented.

## Licence

MIT — see [LICENSE](LICENSE).
