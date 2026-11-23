# furkiozknn.github.io

**→ [furkiozknn.github.io](https://furkiozknn.github.io/)** is the games hub: all 21 browser games on one
mobile-first page, the link that goes in a profile bio.

## Oyun merkezi (games hub)

`index.html` at the root is rendered by [`merkez/olustur.py`](merkez/olustur.py) from one data file,
[`merkez/oyunlar.json`](merkez/oyunlar.json). Every game has its own card: its own colours and motif strip,
a real screenshot (or a song-reel still), a one-line hook, how to play, a big "▶ Oyna" button to the
live game, and an anchor `#<repo-name>` (`https://furkiozknn.github.io/#hamsi`). Turkish by default,
English with the TR/EN switch or `?lang=en`. No trackers, no scripts from other hosts; only the fonts
come from Google Fonts. Images are WebP in `merkez/img/` (480 px and 960 px), lazy-loaded.

The old project directory at `/projeler/` was removed on 2026-11-23; that address now forwards to this page.

### Şarkı linki ekleme (adding a song link)

Each card has a hidden "🎵 Şarkıyı dinle" button. To show it, open
[`merkez/oyunlar.json`](merkez/oyunlar.json) on GitHub (pencil icon), find the game by its `"id"` and
fill its `"sarki_youtube"` with the YouTube link, for example:

```json
"id": "hamsi",
...
"sarki_youtube": "https://www.youtube.com/watch?v=XXXXXXXXXXX"
```

Commit. The `Merkez` workflow re-renders `index.html` and the button appears within a minute or two.
An empty string hides it again. Only `youtube.com` / `youtu.be` links are accepted; anything else
fails the run instead of publishing a wrong link. Locally: `python3 merkez/olustur.py`.

## Licence

MIT — see [LICENSE](LICENSE).
