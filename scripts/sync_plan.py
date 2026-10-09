#!/usr/bin/env python3
"""Plan the Artifact reads for a deck sync. Prints JSON for the agent.

Step 1:  python3 scripts/sync_plan.py
         -> the paths for ONE Artifact read (deck.json + every known slide)
Step 2:  python3 scripts/sync_plan.py --after-read
         -> new slides still to read, and image ids still to download
"""
import glob, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG = json.load(open(f"{ROOT}/scripts/site.json"))
SYNC = f"{ROOT}/.sync"

if "--after-read" not in sys.argv:
    order = json.load(open(f"{ROOT}/source/deck.json"))["order"] if os.path.exists(f"{ROOT}/source/deck.json") else []
    print(json.dumps({"action": "read", "url": CFG["artifact"], "out_dir": SYNC,
                      "paths": ["project/deck.json"] + [f"project/slides/{s}.html" for s in order]}, indent=1))
    sys.exit(0)

deck = json.load(open(f"{SYNC}/project/deck.json"))
missing_slides = [f"project/slides/{s}.html" for s in deck["order"] if not os.path.exists(f"{SYNC}/project/slides/{s}.html")]
have = {os.path.splitext(os.path.basename(f))[0] for f in glob.glob(f"{ROOT}/source/assets/*")}
have |= {os.path.splitext(os.path.basename(f))[0] for f in glob.glob(f"{SYNC}/*.*")}
used = set()
for s in deck["order"]:
    f = f"{SYNC}/project/slides/{s}.html"
    if os.path.exists(f):
        used |= set(re.findall(r"/_blob/([0-9a-f]{32})", open(f).read()))
print(json.dumps({"read_slides_first": missing_slides,
                  "read_assets": sorted(used - have),
                  "note": "Read each asset id with action read, path=<id>, out_dir=" + SYNC + ". Then run scripts/sync_apply.py."}, indent=1))
