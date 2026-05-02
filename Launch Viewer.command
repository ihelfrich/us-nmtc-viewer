#!/bin/bash
# =============================================================
#  NMTC Viewer — double-click this file in Finder to launch.
#  Starts a local web server and opens the viewer in your
#  default browser automatically.
#
#  To stop:  close this Terminal window, or press Ctrl+C here.
# =============================================================

# Move to the folder this script lives in (us_nmtc/).
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PORT=8765
URL="http://localhost:$PORT/viewer/"

echo ""
echo "  NMTC Blended-Finance Viewer"
echo "  ==========================="
echo ""

# ── check for Python 3 ──────────────────────────────────────
if ! command -v python3 &>/dev/null; then
    echo "  ERROR: python3 is not installed."
    echo "  Install it from https://www.python.org/downloads/"
    echo ""
    read -rp "  Press Enter to close..."
    exit 1
fi

# ── free the port if it was left open from a previous run ───
lsof -ti tcp:$PORT 2>/dev/null | xargs kill -9 2>/dev/null
sleep 0.2

# ── start the server ────────────────────────────────────────
cd "$DIR"
python3 -m http.server $PORT --bind 127.0.0.1 \
    > /tmp/nmtc_server.log 2>&1 &
SERVER_PID=$!

# ── wait for it to be ready ─────────────────────────────────
echo "  Starting server on port $PORT..."
for i in 1 2 3 4 5; do
    sleep 0.4
    if curl -s --max-time 1 "http://localhost:$PORT/" > /dev/null 2>&1; then
        break
    fi
done

# ── open the browser ────────────────────────────────────────
echo "  Opening $URL"
echo ""
open "$URL"

echo "  ✔  Viewer is running at $URL"
echo "  ✔  Close this window (or press Ctrl+C) to stop the server."
echo ""
echo "  Tip: if the page loads but the map stays black, give it"
echo "  a few extra seconds — Cesium is fetching the satellite"
echo "  imagery from the internet."
echo ""

# ── keep alive until window is closed ───────────────────────
trap "kill $SERVER_PID 2>/dev/null; echo '  Server stopped.'; exit 0" INT TERM
wait $SERVER_PID
