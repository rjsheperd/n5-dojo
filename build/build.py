# Builds the offline, installable N5 Renshū Dōjō from the artifact's files in ../src
#   dist/            static site: pages, audio, fonts, icons, manifest, service worker
import os, re, json, shutil, hashlib, glob
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "src")
OUT = os.path.join(HERE, "..", "site")
NM = os.path.join(HERE, "node_modules", "@fontsource")
shutil.rmtree(OUT, ignore_errors=True)
for d in ("audio", "fonts", "icons"):
    os.makedirs(os.path.join(OUT, d))

pages = sorted(os.path.basename(p) for p in glob.glob(os.path.join(SRC, "*.html")))
texts = {p: open(os.path.join(SRC, p), encoding="utf-8").read() for p in pages}

# ---------- fonts: keep only the woff2 chunks that cover characters the pages use ----------
chars = set(ord(c) for t in texts.values() for c in t)
chars |= set(range(0x20, 0x7f)) | set(range(0x3040, 0x3100)) | set(range(0x30a0, 0x3100))  # all kana
FONTS = [("klee-one", "Klee One", ["400", "600"]),
         ("zen-kaku-gothic-new", "Zen Kaku Gothic New", ["400", "500", "700"]),
         ("shippori-mincho-b1", "Shippori Mincho B1", ["600", "800"])]

def ranges(spec):
    out = []
    for part in spec.split(","):
        part = part.strip().replace("U+", "")
        if "-" in part:
            a, b = part.split("-"); out.append((int(a, 16), int(b, 16)))
        elif "?" in part:
            out.append((int(part.replace("?", "0"), 16), int(part.replace("?", "f"), 16)))
        else:
            out.append((int(part, 16),) * 2)
    return out

css, nfiles = ["/* Klee One, Zen Kaku Gothic New, Shippori Mincho B1: SIL Open Font License 1.1, bundled from @fontsource */"], 0
for pkg, fam, weights in FONTS:
    for w in weights:
        src = open(os.path.join(NM, pkg, f"{w}.css"), encoding="utf-8").read()
        for block in re.findall(r"@font-face\s*{[^}]*}", src):
            m = re.search(r"unicode-range:\s*([^;]+);", block)
            if m and not any(a <= c <= b for a, b in ranges(m.group(1)) for c in chars if a <= c <= b):
                continue
            f = re.search(r"url\(\./files/([^)]+\.woff2)\)", block).group(1)
            shutil.copy(os.path.join(NM, pkg, "files", f), os.path.join(OUT, "fonts", f)); nfiles += 1
            block = re.sub(r"src:[^;]+;", f"src: url(./{f}) format('woff2');", block)
            css.append(block)
open(os.path.join(OUT, "fonts", "fonts.css"), "w", encoding="utf-8").write("\n".join(css))

# ---------- icons: red hanko stamp with 道 ----------
cjk = [p for p in glob.glob("/usr/share/fonts/**/*CJK*", recursive=True) if re.search(r"Serif.*(Bold|Black)", p)]
cjk = sorted(cjk, key=lambda p: ("Black" in p, p))[0]
def icon(size, maskable=False, bg_full=True):
    img = Image.new("RGB", (size, size), "#f5f6f3")
    d = ImageDraw.Draw(img)
    pad = int(size * (0.18 if maskable else 0.08))
    r = int(size * 0.14)
    d.rounded_rectangle([pad, pad, size - pad, size - pad], radius=r, fill="#c43d2b")
    inset = pad + int(size * 0.045)
    d.rounded_rectangle([inset, inset, size - inset, size - inset], radius=int(r * .7), outline="#ffffff", width=max(2, size // 90))
    font = ImageFont.truetype(cjk, int((size - 2 * pad) * 0.62), index=0)
    d.text((size / 2, size / 2 + size * 0.01), "道", font=font, fill="#ffffff", anchor="mm")
    return img
icon(192).save(os.path.join(OUT, "icons", "icon-192.png"))
icon(512).save(os.path.join(OUT, "icons", "icon-512.png"))
icon(512, maskable=True).save(os.path.join(OUT, "icons", "maskable-512.png"))
icon(180).save(os.path.join(OUT, "icons", "apple-touch-icon.png"))
icon(64).save(os.path.join(OUT, "favicon.png"))

manifest = {
    "name": "N5 Renshū Dōjō", "short_name": "N5 Dōjō", "lang": "ja",
    "description": "JLPT N5 practice: kanji, words, adjectives, counters, dates and listening. Works offline.",
    "start_url": "./index.html", "scope": "./", "display": "standalone",
    "background_color": "#f5f6f3", "theme_color": "#f5f6f3",
    "icons": [
        {"src": "icons/icon-192.png", "sizes": "192x192", "type": "image/png"},
        {"src": "icons/icon-512.png", "sizes": "512x512", "type": "image/png"},
        {"src": "icons/maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"}],
}
json.dump(manifest, open(os.path.join(OUT, "manifest.webmanifest"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)

# ---------- pages ----------
HEAD = """<meta name="theme-color" content="#f5f6f3" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#141816" media="(prefers-color-scheme: dark)">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<meta name="apple-mobile-web-app-title" content="N5 Dōjō">
<link rel="manifest" href="manifest.webmanifest">
<link rel="icon" type="image/png" href="favicon.png">
<link rel="apple-touch-icon" href="icons/apple-touch-icon.png">
<link rel="stylesheet" href="fonts/fonts.css">
<script>if ("serviceWorker" in navigator) addEventListener("load", () => navigator.serviceWorker.register("./sw.js").catch(() => {}));</script>
"""
for p, s in texts.items():
    s = re.sub(r'<link rel="preconnect"[^>]*>\s*', "", s)
    s = re.sub(r'<link rel="stylesheet" href="https://fonts\.googleapis\.com[^>]*>\s*', "", s)
    s = re.sub(r'<meta name="claude:[^>]*>\s*', "", s)
    assert "googleapis" not in s and "gstatic" not in s, p
    n = s.count("/*PWA*/false")
    s = s.replace("/*PWA*/false", "true")
    if not s.lower().startswith("<!doctype"):
        s = "<!doctype html>" + s
    s = s.replace("<html>", '<html lang="ja">', 1)
    s = s.replace("</head>", HEAD + "</head>", 1)
    assert HEAD in s, p
    open(os.path.join(OUT, p), "w", encoding="utf-8").write(s)
    print(f"{p:18} PWA switch: {n}")
for f in glob.glob(os.path.join(SRC, "audio", "*.mp3")):
    shutil.copy(f, os.path.join(OUT, "audio"))

# ---------- service worker: precache everything, versioned by content hash ----------
assets = sorted(os.path.relpath(p, OUT).replace(os.sep, "/") for p in glob.glob(os.path.join(OUT, "**", "*"), recursive=True)
                if os.path.isfile(p))
h = hashlib.sha256()
for a in assets:
    h.update(a.encode()); h.update(open(os.path.join(OUT, a), "rb").read())
VERSION = h.hexdigest()[:10]
sw = open(os.path.join(HERE, "sw.template.js"), encoding="utf-8").read()
sw = sw.replace("__VERSION__", VERSION).replace("__ASSETS__", json.dumps(["./"] + assets, indent=1))
open(os.path.join(OUT, "sw.js"), "w", encoding="utf-8").write(sw)

size = sum(os.path.getsize(os.path.join(OUT, a)) for a in assets)
print(f"{len(assets)} files, {size/1e6:.1f} MB, {nfiles} font chunks, cache version {VERSION}")
