// iPhone remote for the local deck.
//   node scripts/remote.mjs serve <port> <key>   run the remote server
//   node scripts/remote.mjs qr <port> <key>      print the phone link and a QR code, then exit
// The phone page and commands need the secret key. Only next / back / go to slide / black screen exist.
// The deck (on this Mac) listens on /deck-events and reports its state on /deck-state; both accept loopback only.
// The app and the deck are NOT served here: they stay on 127.0.0.1.
import http from "node:http";
import os from "node:os";
import { createRequire } from "node:module";

const [mode = "serve", portArg = "4175", key = ""] = process.argv.slice(2);
const port = Number(portArg);
if (!/^[A-Za-z0-9]{6,}$/.test(key)) { console.error("Usage: node scripts/remote.mjs serve|qr <port> <key>  (key: 6+ letters or digits)"); process.exit(1); }

function lanAddresses() {
  const out = [];
  for (const list of Object.values(os.networkInterfaces())) for (const a of list || [])
    if (a.family === "IPv4" && !a.internal) out.push(a.address);
  // iPhone Personal Hotspot first (172.20.10.x), then home/office ranges.
  const rank = ip => ip.startsWith("172.20.10.") ? 0 : ip.startsWith("192.168.") ? 1 : ip.startsWith("10.") ? 2 : 3;
  return out.sort((a, b) => rank(a) - rank(b));
}

if (mode === "qr") {
  const ips = lanAddresses();
  if (!ips.length) { console.log("No network found. Turn on Personal Hotspot on the iPhone and join it from this Mac, then run present.command again."); process.exit(0); }
  const url = ip => `http://${ip}:${port}/?k=${key}`;
  const qrcode = createRequire(import.meta.url)("./vendor/qrcode/qrcode.cjs");
  const qr = qrcode(0, "M"); qr.addData(url(ips[0])); qr.make();
  const n = qr.getModuleCount(), dark = (r, c) => r >= 0 && c >= 0 && r < n && c < n && qr.isDark(r, c);
  let s = "";
  for (let r = -2; r < n + 2; r += 2) {   // two QR rows per text line; light-on-dark terminals print it inverted, which iPhone still reads
    let line = "";
    for (let c = -2; c < n + 2; c++) { const t = dark(r, c), b = dark(r + 1, c); line += t && b ? " " : t ? "▄" : b ? "▀" : "█"; }
    s += "  " + line + "\n";
  }
  console.log(s);
  console.log("  Scan with the iPhone camera, or open: " + url(ips[0]));
  if (ips.length > 1) console.log("  Other networks on this Mac: " + ips.slice(1).map(url).join("  "));
  if (!ips[0].startsWith("172.20.10.")) console.log("  Tip: join the iPhone's Personal Hotspot. Venue wifi often blocks phone-to-laptop links.");
  process.exit(0);
}

const isLoop = req => ["127.0.0.1", "::1", "::ffff:127.0.0.1"].includes(req.socket.remoteAddress);
const okKey = u => u.searchParams.get("k") === key;
let state = { cur: 0, total: 0, title: "", next: "", live: false, black: false };
const decks = new Set();
const CORS = { "Access-Control-Allow-Origin": "*", "Cache-Control": "no-store" };

http.createServer((req, res) => {
  const u = new URL(req.url, "http://x");
  if (u.pathname === "/deck-events" && isLoop(req)) {          // deck on this Mac subscribes to commands
    res.writeHead(200, { ...CORS, "Content-Type": "text/event-stream", Connection: "keep-alive" });
    res.write("retry: 1000\n\n"); decks.add(res);
    const ping = setInterval(() => res.write(": ping\n\n"), 15000);
    req.on("close", () => { clearInterval(ping); decks.delete(res); });
    return;
  }
  if (u.pathname === "/deck-state" && req.method === "POST" && isLoop(req)) {
    let b = ""; req.on("data", d => { if ((b += d).length > 4000) req.destroy(); });
    req.on("end", () => { try { state = { ...state, ...JSON.parse(b) }; } catch {} res.writeHead(204, CORS).end(); });
    return;
  }
  if (!okKey(u)) { res.writeHead(403, { "Content-Type": "text/plain" }).end("Scan the QR code in the Terminal window again."); return; }
  if (u.pathname === "/cmd" && req.method === "POST") {
    const c = u.searchParams.get("c") || "";
    if (/^(next|prev|black|go:\d{1,3})$/.test(c)) for (const d of decks) d.write(`data: ${c}\n\n`);
    res.writeHead(204, CORS).end(); return;
  }
  if (u.pathname === "/state") { res.writeHead(200, { ...CORS, "Content-Type": "application/json" }).end(JSON.stringify({ ...state, deck: decks.size > 0 })); return; }
  if (u.pathname === "/") { res.writeHead(200, { "Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-store" }).end(PAGE); return; }
  res.writeHead(404).end();
}).listen(port, "0.0.0.0", () => console.log(`Remote on port ${port}`));

const PAGE = `<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no,viewport-fit=cover">
<meta name="apple-mobile-web-app-capable" content="yes"><meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<title>Deck remote</title>
<style>
*{box-sizing:border-box;margin:0;-webkit-tap-highlight-color:transparent;-webkit-user-select:none;user-select:none}
html,body{height:100%;background:#111;color:#eee;font:16px/1.35 -apple-system,system-ui,sans-serif;touch-action:manipulation}
body{display:flex;flex-direction:column;padding:max(14px,env(safe-area-inset-top)) 14px max(14px,env(safe-area-inset-bottom));gap:10px}
.top{display:flex;justify-content:space-between;align-items:center;font-weight:700}
#dot{display:inline-block;width:10px;height:10px;border-radius:5px;background:#e54b4b;margin-right:6px}
#dot.ok{background:#2fbf71}
#pos{font-size:28px}#tm{font-size:22px;color:#e54b4b;padding:4px 8px}
#title{font-size:20px;font-weight:700;min-height:2.7em}#nxt{color:#999;font-size:15px;min-height:1.4em}
#live{display:none;background:#5a1d1d;color:#ffd7d7;padding:8px 10px;border-radius:10px;font-weight:600}
button{border:0;border-radius:18px;font:700 22px -apple-system,system-ui,sans-serif;color:#fff}
#next{flex:1;background:#e54b4b;font-size:40px}
.row{display:flex;gap:10px;height:96px}#prev{flex:2;background:#333}#black{flex:1;background:#222;border:2px solid #444;font-size:17px}
button:active{filter:brightness(1.3)}#black.on{background:#eee;color:#111}
</style></head><body>
<div class="top"><span><span id="dot"></span><span id="pos">– / –</span></span><span id="tm" title="Tap to reset">0:00</span></div>
<div id="title">Connecting…</div><div id="nxt"></div>
<div id="live">Live demo slide. Next still moves the deck.</div>
<button id="next">Next ›</button>
<div class="row"><button id="prev">‹ Back</button><button id="black">Black</button></div>
<script>
var K=new URLSearchParams(location.search).get("k"),t0=0,st={};
function cmd(c){ fetch("/cmd?k="+K+"&c="+c,{method:"POST"}).catch(function(){}); if(!t0)t0=Date.now(); }
function poll(){ fetch("/state?k="+K,{cache:"no-store"}).then(function(r){return r.json()}).then(function(s){ st=s;
  document.getElementById("dot").className=s.deck?"ok":"";
  document.getElementById("pos").textContent=s.total?(s.cur+1)+" / "+s.total:"– / –";
  document.getElementById("title").textContent=s.deck?(s.title||""):"Deck not connected. Open the deck on the Mac.";
  document.getElementById("nxt").textContent=s.next?"Next: "+s.next:"";
  document.getElementById("live").style.display=s.live?"block":"none";
  document.getElementById("black").className=s.black?"on":"";
 }).catch(function(){ document.getElementById("dot").className=""; document.getElementById("title").textContent="No link to the Mac. Check the hotspot."; }); }
setInterval(poll,700); poll();
setInterval(function(){ if(!t0)return; var s=Math.floor((Date.now()-t0)/1000); document.getElementById("tm").textContent=Math.floor(s/60)+":"+("0"+s%60).slice(-2); },1000);
document.getElementById("tm").onclick=function(){ t0=0; this.textContent="0:00"; };
document.getElementById("next").onclick=function(){ cmd("next"); };
document.getElementById("prev").onclick=function(){ cmd("prev"); };
document.getElementById("black").onclick=function(){ cmd("black"); };
var wl=null; function wake(){ if(navigator.wakeLock&&!wl) navigator.wakeLock.request("screen").then(function(l){ wl=l; l.addEventListener("release",function(){ wl=null; }); }).catch(function(){}); }
document.addEventListener("click",wake); document.addEventListener("visibilitychange",function(){ if(!document.hidden) wake(); });
</script></body></html>`;
