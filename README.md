# ISSMTCT 2026 · Jano Health talk website

This repo holds the talk deck as a website, with the live Jano app inside the "Live demo" slide (slide 8).

- **Edit the slides in Claude**, not here: https://claude.ai/artifact/HhxHYNWPUyPjFbev7hQnjb
- **Online copy (iPad, backup):** https://janohealth.github.io/issmtct-2026/ — the demo uses https://jano-functional.pages.dev/
- **Local copy (MacBook on stage, no internet):** `present.command` — the demo uses the app built on the Mac, at http://127.0.0.1:4173/

## Folders

| Folder | What it holds | Who changes it |
|---|---|---|
| `source/` | The slides exported from the Claude deck | The sync (an agent), not people |
| `docs/` | The built website. GitHub Pages publishes this folder. | `scripts/build.py` |
| `scripts/` | Build, sync and local server scripts, fonts, icons | Developers |
| `brief/` | The demo-mode brief for the app team | Sudarshan |

Speaker notes are removed from `source/` and `docs/`, because this repo is public. To keep them, set `"notes": "keep"` in `scripts/site.json`.

## Sync the deck after you edit it in Claude

Ask Claude: **"Sync the ISSMTCT deck to GitHub."** The agent follows `.claude/skills/sync-issmtct-deck/SKILL.md`.

Manual steps for an agent:
1. `python3 scripts/sync_plan.py` — the paths for one Artifact read into `.sync/`.
2. `python3 scripts/sync_plan.py --after-read` — new slides and images to read.
3. `python3 scripts/sync_apply.py` — copies `.sync/` into `source/` and prints the changes.
4. `python3 scripts/build.py` — builds `docs/`.
5. Commit and push. GitHub Pages publishes in about 1 minute.

## Present on the MacBook (local, no internet)

1. Before the talk, with internet: double-click `present.command`. It gets the latest deck and the latest deployed app build (branch `publish-therapy` of `ehr-prototype`, folder `public/`). Then it serves both on this Mac. There is no npm install and no build.
2. The deck opens full screen in its own Chrome window. Leave it open.
3. With no internet, `present.command` still works. It uses the last copies on the Mac.
4. To stop: press Cmd+Q in the deck window, then Ctrl+C in the Terminal window.

The first time only: right-click `present.command` › Open (macOS asks to confirm). The Mac needs Node.js and git access to `janohealth/jano-ehr-prototype`. Settings are in `present.config`.

## Present on the iPad (online)

1. Open https://janohealth.github.io/issmtct-2026/ in Safari.
2. Tap Share › Add to Home Screen. Open the deck from the home screen for full screen.
3. Swipe left or right, or use a Bluetooth clicker. The demo needs internet on the iPad.

## Keys

| Key | Action |
|---|---|
| Clicker, →, Space, PageDown | Next step or slide. On the Live demo slide: the next demo step (when the app has demo mode) |
| ←, PageUp | Back |
| B or . | Black screen |
| A number, then Enter | Go to that slide |
| F | Full screen (desktop browsers) |
| P | Presenter window with timer |
| S | Settings: app address, demo scene, clicker drive on or off |
| R | Reload the demo |

With a trackpad: click in the demo to use the app. Click the slide margin once, or use ‹ › at the bottom right, to take control back.

## Settings for the live demo

`scripts/site.json`:
- `appOnline`, `appLocal` — the app addresses. The deck uses `appLocal` when it runs on 127.0.0.1, else `appOnline`.
- `live` — the slides with a live demo, the demo scene, and the position of the frame (`panel`: left and top of the white box on the slide, in px).

The message contract with the app is in `brief/demo-mode-brief.md`, section 5.
