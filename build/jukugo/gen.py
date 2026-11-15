# Builds jukugo.html (for the Dōjō) from app.src.html, Asobiba's compound data and extra.py
import json, re, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from extra import CORE, EXTRA_COMPOUNDS, LOOK

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
aso = open(f"{SRC}/asobiba.html", encoding="utf-8").read()
i = aso.find("const DATA = ") + len("const DATA = ")
d, _ = json.JSONDecoder().raw_decode(aso[i:])
kanji = [{"k": k["k"], "m": k["m"], "m1": k["m1"], "snd": k["snd"]} for k in d["kanji"]]

comps = [c for c in d["compounds"] if c["w"] not in {"出来る", "電話する", "一人で"}]  # not compounds as such
have = {c["w"] for c in comps}
for c in EXTRA_COMPOUNDS:
    if c["w"] not in have: comps.append(c)
missing = [w for w in CORE if w not in {c["w"] for c in comps}]
assert not missing, missing
for c in comps:
    c.pop("src", None)
    if c["w"] in CORE:
        s, e = CORE[c["w"]]
        assert s.count("{}") == 1, c["w"]
        c["core"] = 1; c["sentence"] = s; c["en"] = e
    else:
        c["core"] = 0
# sanity: every part's reading joins up to the word's reading
for c in comps:
    if c.get("parts") and not c.get("special"):
        joined = "".join(p.get("kana") or p["r"] for p in c["parts"])
        assert joined == c["r"], (c["w"], joined, c["r"])
data = json.dumps({"kanji": kanji, "compounds": comps, "look": LOOK}, ensure_ascii=False, separators=(",", ":"))

kj = open(f"{SRC}/kanji.html", encoding="utf-8").read()
skeleton = kj[:kj.index("<body>") + len("<body>")]
css = re.search(r"<style>\s*(/\* Layout: practice-paper.*?)</style>", kj, re.S).group(1)
hub = kj[kj.rindex("<style>", 0, kj.index(".n5hub-back")):kj.index("</a>", kj.index('class="n5hub-back"')) + 4]

page = open(os.path.join(os.path.dirname(__file__), "app.src.html"), encoding="utf-8").read()
page = page.replace("/*KANJI_CSS*/", css).replace("/*JUKUGO_DATA*/null", data).replace("/*HUB_BACK*/", hub)
out = skeleton + "\n" + page + "\n</body></html>"
open(f"{SRC}/jukugo.html", "w", encoding="utf-8").write(out)
print(f"{len(comps)} compounds, {sum(c['core'] for c in comps)} core, {len(out)//1024} KB")
