// Small static file server for the local copy. Listens on 127.0.0.1 only (this Mac).
// Usage: node scripts/serve.mjs <folder> <port> [--spa]
//   --spa: unknown paths without a file extension get index.html (like Cloudflare Pages).
import http from "node:http";
import { readFile, stat } from "node:fs/promises";
import { extname, join, normalize, resolve, sep } from "node:path";

const root = resolve(process.argv[2] || "docs");
const port = Number(process.argv[3] || 4174);
const spa = process.argv.includes("--spa");
const types = { ".html": "text/html; charset=utf-8", ".js": "text/javascript", ".mjs": "text/javascript", ".css": "text/css",
  ".json": "application/json", ".webmanifest": "application/manifest+json", ".png": "image/png", ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg", ".svg": "image/svg+xml", ".webp": "image/webp", ".gif": "image/gif", ".ico": "image/x-icon",
  ".woff2": "font/woff2", ".woff": "font/woff", ".ttf": "font/ttf", ".mp4": "video/mp4", ".pdf": "application/pdf",
  ".wasm": "application/wasm", ".txt": "text/plain; charset=utf-8" };

async function isFile(f) { return (await stat(f).catch(() => null))?.isFile() ?? false; }

http.createServer(async (req, res) => {
  try {
    const p = decodeURIComponent(new URL(req.url, "http://x").pathname);
    let file = normalize(join(root, p));
    if (file !== root && !file.startsWith(root + sep)) { res.writeHead(403).end(); return; }
    if (!(await isFile(file)) && (await isFile(join(file, "index.html")))) file = join(file, "index.html");
    if (!(await isFile(file)) && spa && !extname(p)) file = join(root, "index.html");
    const body = await readFile(file);
    res.writeHead(200, { "Content-Type": types[extname(file).toLowerCase()] || "application/octet-stream", "Cache-Control": "no-cache" });
    res.end(body);
  } catch { res.writeHead(404, { "Content-Type": "text/plain" }).end("Not found"); }
}).listen(port, "127.0.0.1", () => console.log(`Serving ${root} on http://127.0.0.1:${port}/`));
