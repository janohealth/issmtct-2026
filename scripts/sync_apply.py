#!/usr/bin/env python3
"""Copy a fresh Artifact read (.sync/) into source/. Prints what changed.

- Writes source/deck.json and source/slides/<id>.html for every slide in the order.
- Removes slide files that are no longer in the order.
- Adds new images to source/assets/ and removes images that no slide uses.
- If scripts/site.json has "notes": "strip", speaker notes are removed (the repo is public).
"""
import glob, hashlib, json, os, re, shutil, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG = json.load(open(f"{ROOT}/scripts/site.json"))
SYNC, SRC = f"{ROOT}/.sync", f"{ROOT}/source"
if not os.path.exists(f"{SYNC}/project/deck.json"):
    print("ERROR: .sync/project/deck.json not found. Run the Artifact read first."); sys.exit(1)

def h(p): return hashlib.sha1(open(p, "rb").read()).hexdigest() if os.path.exists(p) else None
os.makedirs(f"{SRC}/slides", exist_ok=True); os.makedirs(f"{SRC}/assets", exist_ok=True)
deck = json.load(open(f"{SYNC}/project/deck.json"))
changed, used = [], set()

for sid in deck["order"]:
    src = f"{SYNC}/project/slides/{sid}.html"
    if not os.path.exists(src):
        print(f"ERROR: {sid} is in the order but was not read. Read project/slides/{sid}.html."); sys.exit(1)
    s = open(src).read()
    used |= set(re.findall(r"/_blob/([0-9a-f]{32})", s))
    if CFG.get("notes") == "strip":
        s = re.sub(r"<aside>.*?</aside>", "<aside></aside>", s, flags=re.S)
    dst = f"{SRC}/slides/{sid}.html"
    old = open(dst).read() if os.path.exists(dst) else None
    if old != s:
        open(dst, "w").write(s); changed.append(("new" if old is None else "changed") + f" slide {sid}")

for f in glob.glob(f"{SRC}/slides/*.html"):
    sid = os.path.basename(f)[:-5]
    if sid not in deck["order"]:
        os.remove(f); changed.append(f"removed slide {sid}")

for f in glob.glob(f"{SYNC}/*.*"):
    bid = os.path.splitext(os.path.basename(f))[0]
    if re.fullmatch(r"[0-9a-f]{32}", bid) and not glob.glob(f"{SRC}/assets/{bid}.*"):
        shutil.copy(f, f"{SRC}/assets/"); changed.append(f"new image {bid}")
for f in glob.glob(f"{SRC}/assets/*"):
    bid = os.path.splitext(os.path.basename(f))[0]
    if bid not in used:
        os.remove(f); changed.append(f"removed unused image {bid}")
missing = [b for b in used if not glob.glob(f"{SRC}/assets/{b}.*")]
if missing:
    print("ERROR: images not downloaded:", ", ".join(missing)); sys.exit(1)

old_deck = open(f"{SRC}/deck.json").read() if os.path.exists(f"{SRC}/deck.json") else None
new_deck = json.dumps(deck, ensure_ascii=False, indent=1)
if old_deck != new_deck:
    open(f"{SRC}/deck.json", "w").write(new_deck); changed.append("changed deck.json (order, sections or title)")

shutil.rmtree(SYNC)
print("\n".join(changed) if changed else "No changes.")
