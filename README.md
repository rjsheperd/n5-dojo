# N5 Renshū Dōjō

Offline, installable JLPT N5 practice app: kanji, vocabulary, adjectives, counters, dates and listening.

**Use it:** open https://rjsheperd.github.io/n5-dojo/ in Safari on iPhone, then Share → **Add to Home Screen**.
Open it once online so it downloads everything (about 8 MB); after that it works with no connection.

## Layout
- `site/` – the published app (pages, audio, bundled fonts, icons, manifest, service worker). Deployed by `.github/workflows/pages.yml` on every push to `main`.
- `build/` – how `site/` is made. `build/src/` holds the pages exported from the claude.ai artifact; `build.py` swaps Google Fonts for bundled ones, turns on each app's offline mode, adds the manifest and icons, and writes a service worker that precaches everything.

`build/jukugo/` makes the Jukugo page: `extra.py` holds the exam sentences and look-alike kanji, and `gen.py` combines them with the compound list in `src/asobiba.html` into `src/jukugo.html`.

To rebuild after changing `build/src/`:
```
cd build && python3 jukugo/gen.py && npm ci && python3 build.py
```

## Progress
Saved on the device, per app. Kanji, Kotoba and Keiyōshi Renshū have Settings → Back up / Restore for moving progress between devices or from the claude.ai version.

## Credits
Fonts: Klee One, Zen Kaku Gothic New, Shippori Mincho B1 (SIL Open Font License 1.1). Listening voices: VOICEVOX もち子さん, 青山龍星.
