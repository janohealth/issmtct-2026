#!/bin/bash
# ISSMTCT 2026 · start the local show on this Mac.
# 1. Gets the latest deck and app (if there is internet).
# 2. Builds the app and runs it on http://127.0.0.1:4173 (this Mac only).
# 3. Runs the deck on http://127.0.0.1:4174 (this Mac only).
# 4. Opens the deck full screen in its own Chrome window. Quit that window with Cmd+Q.
# Double-click this file in Finder, or run: ./present.command
# Settings: present.config (next to this file).

DECK_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_DIR="$HOME/Jano Health/ehr-prototype"
APP_PORT=4173
DECK_PORT=4174
APP_BUILD="npm run build"
APP_SERVE="npm run preview -- --host 127.0.0.1 --port $APP_PORT --strictPort"
[ -f "$DECK_DIR/present.config" ] && source "$DECK_DIR/present.config"

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

say_step "2/5 Get the latest app"
if [ ! -d "$APP_DIR" ]; then echo "App folder not found: $APP_DIR. Set APP_DIR in present.config."; exit 1; fi
git -C "$APP_DIR" pull --ff-only 2>/dev/null && echo "App is up to date." || echo "No update (no internet or local changes). Using the app on this Mac."
LOCK_HASH="$(shasum "$APP_DIR/package-lock.json" 2>/dev/null | cut -c1-40)"
if [ ! -d "$APP_DIR/node_modules" ] || [ "$(cat "$APP_DIR/node_modules/.jano-lock-hash" 2>/dev/null)" != "$LOCK_HASH" ]; then
  echo "Installing app packages..."
  (cd "$APP_DIR" && npm ci) && echo "$LOCK_HASH" > "$APP_DIR/node_modules/.jano-lock-hash" || echo "Install failed. Trying with the packages on this Mac."
fi

say_step "3/5 Build the app"
(cd "$APP_DIR" && eval "$APP_BUILD") || echo "Build failed. Using the last build, if there is one."

say_step "4/5 Start the app and the deck"
if up "http://127.0.0.1:$APP_PORT/"; then echo "The app is already running on port $APP_PORT."; else
  (cd "$APP_DIR" && eval "$APP_SERVE" > /tmp/jano-app.log 2>&1) & PIDS+=($!); STARTED_PORTS+=("$APP_PORT")
fi
if up "http://127.0.0.1:$DECK_PORT/"; then echo "The deck is already running on port $DECK_PORT."; else
  node "$DECK_DIR/scripts/serve.mjs" "$DECK_DIR/docs" "$DECK_PORT" > /tmp/jano-deck.log 2>&1 & PIDS+=($!); STARTED_PORTS+=("$DECK_PORT")
fi
for i in $(seq 1 40); do up "http://127.0.0.1:$APP_PORT/" && up "http://127.0.0.1:$DECK_PORT/" && break; sleep 0.5; done
up "http://127.0.0.1:$APP_PORT/" && echo "App:  http://127.0.0.1:$APP_PORT/  OK" || echo "App did not start. See /tmp/jano-app.log"
up "http://127.0.0.1:$DECK_PORT/" && echo "Deck: http://127.0.0.1:$DECK_PORT/  OK" || echo "Deck did not start. See /tmp/jano-deck.log"

say_step "5/5 Open the deck full screen"
URL="http://127.0.0.1:$DECK_PORT/"
if [ -d "/Applications/Google Chrome.app" ]; then
  open -na "Google Chrome" --args --user-data-dir="$HOME/.jano-present-chrome" --no-first-run --kiosk "$URL"
  echo "Chrome opened in full screen. Quit it with Cmd+Q."
else
  open "$URL"; echo "Opened in your default browser. Press F on the deck for full screen."
fi
echo "Keep this window open during the talk. Press Ctrl+C here to stop."
wait
