#!/usr/bin/env python3
import http.server
import socketserver
import os
import sys
from pathlib import Path
from datetime import date
from urllib.parse import unquote

PORT = 8000
ROOT = Path(os.environ.get("GIF_DIR", ".")).resolve()
TODAY = date.today().isoformat()
EXTS = [".gif", ".mp4", ".webm", ".mov"]
MIME = {
    ".gif":  "image/gif",
    ".mp4":  "video/mp4",
    ".webm": "video/webm",
    ".mov":  "video/quicktime",
}


def collect():
    buckets = {}

    # arquivos soltos na raiz
    for f in ROOT.iterdir():
        if f.is_file() and f.suffix.lower() in EXTS:
            buckets.setdefault("", []).append(f)

    # subpastas de data
    for sub in ROOT.iterdir():
        if sub.is_dir():
            files = [f for f in sub.iterdir() if f.is_file() and f.suffix.lower() in EXTS]
            if files:
                buckets[sub.name] = files

    for key in buckets:
        buckets[key].sort(key=lambda f: f.stat().st_mtime, reverse=True)

    ordered = sorted(buckets.keys(), key=lambda k: "9999" if k == TODAY else k, reverse=True)
    return [(k, k == TODAY, buckets[k]) for k in ordered]


def fmt_size(p):
    kb = p.stat().st_size / 1024
    return f"{kb:.0f} KB" if kb < 1024 else f"{kb/1024:.1f} MB"


def make_card(label, f):
    url = (f"{label}/{f.name}" if label else f.name).replace("'", "%27")
    name_js = f.stem.replace("'", "\\'").replace("\\", "\\\\")
    sz = fmt_size(f)
    ext = f.suffix.lower()
    if ext == ".gif":
        media = f'<img src="{url}" loading="lazy">'
    else:
        media = f'<video src="{url}" muted autoplay loop playsinline></video>'
    return f"""<div class="card" onclick="open_lb('{url}','{name_js}')">
<div class="thumb">{media}<div class="ov">&#9654;</div></div>
<div class="meta"><span class="n">{f.stem}</span><span class="s">{sz}</span></div>
</div>"""


def make_html():
    sections = collect()
    total = sum(len(gifs) for _, _, gifs in sections)

    body = ""
    for label, is_today, files in sections:
        badge = '<span class="badge">hoje</span>' if is_today else ""
        title = label or "raiz"
        cards = "".join(make_card(label, f) for f in files)
        cls = "today" if is_today else "past"
        body += f'<section class="{cls}"><h2>{title}{badge}</h2><div class="grid">{cards}</div></section>'

    if not body:
        body = '<div class="empty"><p>&#127902;</p><h2>Nenhum arquivo encontrado</h2><small>Rode gifs-fix primeiro.</small></div>'

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>GIF Gallery</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@700&family=Syne:wght@400;800&display=swap');
*{{box-sizing:border-box;margin:0;padding:0}}
:root{{--bg:#0a0a0f;--card:#14141e;--border:#1e1e2e;--accent:#c8ff57;--text:#e8e8f0;--muted:#55556a}}
body{{background:var(--bg);color:var(--text);font-family:'Syne',sans-serif;min-height:100vh}}
header{{position:sticky;top:0;z-index:9;background:rgba(10,10,15,.9);backdrop-filter:blur(10px);border-bottom:1px solid var(--border);padding:14px 18px;display:flex;align-items:center;gap:12px}}
header h1{{font-size:1.4rem;font-weight:800;flex:1}}header h1 span{{color:var(--accent)}}
.count{{font-family:'Space Mono',monospace;font-size:.7rem;color:var(--muted);border:1px solid var(--border);padding:3px 10px;border-radius:20px}}
main{{padding:22px 16px 60px;max-width:1400px;margin:0 auto}}
section{{margin-bottom:32px}}
h2{{font-family:'Space Mono',monospace;font-size:.72rem;letter-spacing:1.5px;text-transform:uppercase;color:var(--muted);margin-bottom:12px;display:flex;align-items:center;gap:8px}}
.today h2{{color:var(--accent)}}
.badge{{background:var(--accent);color:#000;font-size:.6rem;font-weight:700;padding:2px 8px;border-radius:20px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:10px}}
@media(min-width:480px){{.grid{{grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:12px}}}}
@media(min-width:900px){{.grid{{grid-template-columns:repeat(auto-fill,minmax(220px,1fr))}}}}
.card{{background:var(--card);border:1px solid var(--border);border-radius:10px;overflow:hidden;cursor:pointer;transition:transform .18s,border-color .18s,box-shadow .18s}}
.card:hover{{transform:translateY(-3px);border-color:var(--accent);box-shadow:0 0 18px rgba(200,255,87,.15)}}
.thumb{{position:relative;aspect-ratio:1;overflow:hidden;background:#0d0d14}}
.thumb img,.thumb video{{width:100%;height:100%;object-fit:cover;display:block;transition:transform .25s}}
.card:hover .thumb img,.card:hover .thumb video{{transform:scale(1.05)}}
.ov{{position:absolute;inset:0;background:rgba(0,0,0,.45);display:flex;align-items:center;justify-content:center;opacity:0;transition:opacity .18s;font-size:1.4rem;color:var(--accent)}}
.card:hover .ov{{opacity:1}}
.meta{{padding:7px 9px;display:flex;justify-content:space-between;align-items:center;gap:4px}}
.n{{font-size:.7rem;font-weight:700;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.s{{font-family:'Space Mono',monospace;font-size:.62rem;color:var(--muted);white-space:nowrap;flex-shrink:0}}
#lb{{display:none;position:fixed;inset:0;z-index:100;background:rgba(0,0,0,.92);backdrop-filter:blur(10px);flex-direction:column;align-items:center;justify-content:center;gap:14px;padding:20px}}
#lb.on{{display:flex}}
#lb img,#lb video{{max-width:100%;max-height:80vh;border-radius:10px;border:1px solid var(--border);object-fit:contain}}
#lb video{{background:#000}}
#lb span{{font-family:'Space Mono',monospace;font-size:.75rem;color:var(--muted);word-break:break-all;text-align:center}}
#lbx{{position:fixed;top:14px;right:14px;background:var(--card);border:1px solid var(--border);color:var(--text);width:36px;height:36px;border-radius:50%;font-size:1rem;cursor:pointer;display:flex;align-items:center;justify-content:center;z-index:101;transition:border-color .15s,color .15s}}
#lbx:hover{{border-color:var(--accent);color:var(--accent)}}
.empty{{text-align:center;padding:80px 20px;color:var(--muted)}}
.empty p{{font-size:3rem;margin-bottom:12px}}.empty h2{{font-size:1.2rem;color:var(--text);margin-bottom:6px}}
</style>
</head>
<body>
<header><h1>GIF<span>.</span>gallery</h1><span class="count">{total} arquivo{'s' if total!=1 else ''}</span></header>
<main>{body}</main>
<div id="lb">
  <button id="lbx" onclick="close_lb()">&#x2715;</button>
  <img id="lbi" src="" alt="" style="display:none">
  <video id="lbv" src="" autoplay loop muted playsinline controls style="display:none"></video>
  <span id="lbn"></span>
</div>
<script>
var VIDEO_EXTS = ['.mp4','.webm','.mov'];
function open_lb(u,n){{
  var isVideo = VIDEO_EXTS.some(function(e){{return u.toLowerCase().endsWith(e)}});
  var img = document.getElementById('lbi');
  var vid = document.getElementById('lbv');
  if(isVideo){{
    img.style.display='none';
    vid.src=u; vid.style.display='block'; vid.play();
  }} else {{
    vid.style.display='none'; vid.src='';
    img.src=u; img.style.display='block';
  }}
  document.getElementById('lbn').textContent=n;
  document.getElementById('lb').classList.add('on');
}}
function close_lb(){{
  document.getElementById('lb').classList.remove('on');
  document.getElementById('lbi').src='';
  var v=document.getElementById('lbv'); v.pause(); v.src='';
}}
document.getElementById('lb').addEventListener('click',function(e){{if(e.target===this)close_lb()}});
document.addEventListener('keydown',function(e){{if(e.key==='Escape')close_lb()}});
</script>
</body>
</html>"""


class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        p = unquote(self.path).split("?")[0]
        if p in ("/", ""):
            data = make_html().encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        else:
            filepath = ROOT / p.lstrip("/")
            if filepath.is_file():
                ct = MIME.get(filepath.suffix.lower(), "application/octet-stream")
                data = filepath.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", ct)
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
            else:
                self.send_response(404)
                self.end_headers()

    def log_message(self, *args):
        pass


socketserver.ThreadingTCPServer.allow_reuse_address = True
try:
    with socketserver.ThreadingTCPServer(("0.0.0.0", PORT), Handler) as httpd:
        print(f"GIF Gallery -> http://0.0.0.0:{PORT}")
        print(f"Pasta: {ROOT}")
        print("Ctrl+C para encerrar.")
        httpd.serve_forever()
except KeyboardInterrupt:
    print("\nServidor encerrado.")
    sys.exit(0)
