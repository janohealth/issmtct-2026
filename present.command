#!/bin/bash
# ISSMTCT 2026 · start the local show on this Mac.
# 1. Gets the latest deck (this repo) and the latest DEPLOYED app build, if there is internet.
#    The deployed app build is the "publish-therapy" branch of the app repo (folder public/),
#    the same files that jano-functional.pages.dev serves. No npm install or build is needed.
# 2. Runs the app on http://127.0.0.1:4173 and the deck on http://127.0.0.1:4174 (this Mac only).
# 3. Opens the deck full screen in its own Chrome window. Quit that window with Cmd+Q.
# Double-click this file in Finder, or run: ./present.command
# Settings: present.config (next to this file).

DECK_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_REPO="$HOME/Jano Health/ehr-prototype"
APP_BRANCH="publish-therapy"
APP_SUBDIR="public"
APP_CACHE="$HOME/Jano Health/.issmtct-app"
APP_PORT=4173
DECK_PORT=4174
REMOTE_PORT=4175
REMOTE=1
[ -f "$DECK_DIR/present.config" ] && source "$DECK_DIR/present.config"
export GIT_TERMINAL_PROMPT=0   # never stop to ask for a password on stage

say_step() { printf "\n\033[1m%s\033[0m\n" "$1"; }
up() { curl -s -o /dev/null --max-time 1 "$1"; }
PIDS=(); STARTED_PORTS=()
cleanup() {
  for p in "${PIDS[@]}"; do pkill -TERM -P "$p" 2>/dev/null; kill "$p" 2>/dev/null; done
  for port in "${STARTED_PORTS[@]}"; do lsof -ti "tcp:$port" -sTCP:LISTEN 2>/dev/null | xargs kill 2>/dev/null; done
  echo; echo "Stopped."
}
trap cleanup EXIT INT TERM

say_step "1/5 Get the latest deck"
git -C "$DECK_DIR" pull --ff-only 2>/dev/null && echo "Deck is up to date." || echo "No update (no internet or local changes). Using the deck on this Mac."

say_step "2/5 Get the latest deployed app"
if [ ! -d "$APP_REPO/.git" ] && [ ! -f "$APP_REPO/.git" ]; then echo "App repo not found: $APP_REPO. Set APP_REPO in present.config."; exit 1; fi
git -C "$APP_REPO" fetch origin "$APP_BRANCH" 2>/dev/null && echo "Fetched the latest $APP_BRANCH." || echo "No update (no internet). Using the last $APP_BRANCH on this Mac."
if git -C "$APP_REPO" rev-parse --verify -q "origin/$APP_BRANCH" >/dev/null; then
  rm -rf "$APP_CACHE.new" && mkdir -p "$APP_CACHE.new"
  if git -C "$APP_REPO" archive "origin/$APP_BRANCH" "$APP_SUBDIR" | tar -x -C "$APP_CACHE.new"; then
    rm -rf "$APP_CACHE" && mv "$APP_CACHE.new" "$APP_CACHE"
  else
    rm -rf "$APP_CACHE.new"; echo "Could not unpack $APP_BRANCH. Using the last copy."
  fi
fi
if [ ! -f "$APP_CACHE/$APP_SUBDIR/index.html" ]; then echo "No app build found in $APP_CACHE. Connect to the internet once and run this again."; exit 1; fi
VERSION="$(grep -o '"tag": *"[^"]*"' "$APP_CACHE/$APP_SUBDIR/build.json" 2>/dev/null | sed 's/.*"\([^"]*\)"$/\1/')"
echo "App build: ${VERSION:-unknown}"

say_step "3/5 Start the app and the deck"
if up "http://127.0.0.1:$APP_PORT/"; then echo "Port $APP_PORT is already in use. Stop that server, or the deck shows it instead."; else
  node "$DECK_DIR/scripts/serve.mjs" "$APP_CACHE/$APP_SUBDIR" "$APP_PORT" --spa > /tmp/jano-app.log 2>&1 & PIDS+=($!); STARTED_PORTS+=("$APP_PORT")
fi
if up "http://127.0.0.1:$DECK_PORT/"; then echo "The deck is already running on port $DECK_PORT."; else
  node "$DECK_DIR/scripts/serve.mjs" "$DECK_DIR/docs" "$DECK_PORT" > /tmp/jano-deck.log 2>&1 & PIDS+=($!); STARTED_PORTS+=("$DECK_PORT")
fi
for i in $(seq 1 20); do up "http://127.0.0.1:$APP_PORT/" && up "http://127.0.0.1:$DECK_PORT/" && break; sleep 0.5; done
up "http://127.0.0.1:$APP_PORT/" && echo "App:  http://127.0.0.1:$APP_PORT/  OK" || echo "App did not start. See /tmp/jano-app.log"
up "http://127.0.0.1:$DECK_PORT/" && echo "Deck: http://127.0.0.1:$DECK_PORT/  OK" || echo "Deck did not start. See /tmp/jano-deck.log"

say_step "4/5 iPhone remote"
if [ "${REMOTE:-1}" = "0" ]; then echo "Remote is off (REMOTE=0 in present.config)."
elif up "http://127.0.0.1:$REMOTE_PORT/"; then echo "Port $REMOTE_PORT is in use. Stop that server to use the iPhone remote."
else
  KEY="$(LC_ALL=C tr -dc 'A-Za-z0-9' </dev/urandom | head -c 10)"
  node "$DECK_DIR/scripts/remote.mjs" serve "$REMOTE_PORT" "$KEY" > /tmp/jano-remote.log 2>&1 & PIDS+=($!); STARTED_PORTS+=("$REMOTE_PORT")
  sleep 0.5
  node "$DECK_DIR/scripts/remote.mjs" qr "$REMOTE_PORT" "$KEY"
  echo "  If macOS asks to allow incoming connections for node, click Allow."
fi

say_step "5/5 Open the deck full screen"
URL="http://127.0.0.1:$DECK_PORT/"
if [ "${OPEN_BROWSER:-1}" = "0" ]; then echo "Open $URL yourself."
elif [ -d "/Applications/Google Chrome.app" ]; then
  open -na "Google Chrome" --args --user-data-dir="$HOME/.jano-present-chrome" --no-first-run --kiosk "$URL"
  echo "Chrome opened in full screen. Quit it with Cmd+Q."
else
  open "$URL"; echo "Opened in your default browser. Press F on the deck for full screen."
fi
echo "Keep this window open during the talk. Press Ctrl+C here to stop."
wait
