from flask import Flask, request, render_template_string, send_file
from urllib.parse import urlsplit
import tempfile
import re
import tldextract
import idna
import os

app = Flask(__name__)

# ملف مؤقت لتخزين آخر نتيجة
LAST_RESULT_FILE = None

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<title>Bulk Domain Filter — Ultra Pro Max</title>
<style>
body { background:#0f1115; color:#e8e8ea; font-family: Arial, sans-serif; }
.wrap { max-width: 900px; margin: 30px auto; padding: 20px; background:#161a22; border-radius: 12px; }
h1 { margin-top: 0; }
.card { background:#0f1320; padding:16px; border-radius:10px; margin:12px 0; }
label { display:block; margin-bottom: 6px; font-weight: bold; }
input[type=file], input[type=text] { width:100%; padding:8px; margin-bottom:10px; }
.btn { background:#3751ff; border:none; color:#fff; padding:10px 16px; border-radius:8px; cursor:pointer; }
.stat { display:inline-block; background:#121725; padding:6px 10px; margin:4px; border-radius:8px; }
.footer { text-align:center; margin-top:20px; font-size:13px; }
.footer a { color:#4da3ff; text-decoration:none; }
</style>
</head>
<body>
<div class="wrap">
<h1>🧹 Bulk Domain Filter & Normalizer — Ultra Pro Max</h1>
<form method="POST" enctype="multipart/form-data">
<div class="card">
<label>Upload files:</label>
<input type="file" name="files" multiple required>
</div>
<div class="card">
<label>Filter (optional)</label>
<input type="text" name="filter_domain" placeholder="e.g. google.com">
<label><input type="radio" name="filter_mode" value="endswith" checked> Match domain or subdomains</label>
<label><input type="radio" name="filter_mode" value="exact"> Exact match only</label>
</div>
<div class="card">
<label>Options</label>
<label><input type="checkbox" name="to_lower" checked> Force lowercase</label>
<label><input type="checkbox" name="trim_spaces" checked> Trim spaces</label>
<label><input type="checkbox" name="ignore_comments" checked> Ignore comment lines</label>
<label><input type="checkbox" name="keep_root" checked> Reduce to registered/root domain</label>
<label><input type="checkbox" name="unique_only" checked> Unique only</label>
<label><input type="checkbox" name="sort_output"> Sort output</label>
<label><input type="checkbox" name="keep_invalid"> Keep invalid tokens</label>
</div>
<button class="btn" type="submit">Process & Download</button>
</form>

{% if stats %}
<div class="card">
<div class="stat">Files: {{stats.files}}</div>
<div class="stat">Total lines: {{stats.total_lines}}</div>
<div class="stat">Valid: {{stats.valid}}</div>
<div class="stat">Matched: {{stats.matched}}</div>
<div class="stat">Unique: {{stats.unique}}</div>
<a class="btn" href="/download">⬇️ Download Result</a>
</div>
{% endif %}

<div class="footer">BY <a href="https://t.me/JOOxCRACK" target="_blank">@JOOxCRACK</a></div>
</div>
</body>
</html>"""

HOST_RE = re.compile(r"^[A-Za-z0-9.-]+$")

def extract_host(token: str):
    s = token.strip()
    if not s:
        return None
    if "://" in s:
        try:
            parts = urlsplit(s)
            host = parts.hostname
        except:
            host = None
    else:
        host = s.split()[0]
        for ch in ["/", "?", "#", ":", "\\"]:
            host = host.split(ch)[0]
    if not host:
        return None
    if "@" in host:
        host = host.split("@")[-1]
    host = host.strip("[]")
    if host.lower().startswith("www."):
        host = host[4:]
    return host

def is_valid_domain(host: str) -> bool:
    if not HOST_RE.match(host): return False
    if host.startswith('.') or host.endswith('.'): return False
    if '..' in host: return False
    if '.' not in host: return False
    try:
        idna.encode(host)
        return True
    except:
        return False

@app.route("/", methods=["GET", "POST"])
def index():
    global LAST_RESULT_FILE
    if request.method == "GET":
        return render_template_string(PAGE)

    to_lower = bool(request.form.get("to_lower"))
    trim_spaces = bool(request.form.get("trim_spaces"))
    ignore_comments = bool(request.form.get("ignore_comments"))
    keep_root = bool(request.form.get("keep_root"))
    unique_only = bool(request.form.get("unique_only"))
    sort_output = bool(request.form.get("sort_output"))
    keep_invalid = bool(request.form.get("keep_invalid"))

    filter_domain_raw = (request.form.get("filter_domain") or "").strip()
    filter_mode = request.form.get("filter_mode") or "endswith"

    seen = set()
    total_lines = valid = invalid = matched_count = 0

    tmp = tempfile.NamedTemporaryFile(delete=False, mode="w", encoding="utf-8")
    try:
        for fs in request.files.getlist("files"):
            for raw_line in fs.stream:
                total_lines += 1
                try:
                    line = raw_line.decode("utf-8", errors="replace")
                except:
                    continue
                if trim_spaces:
                    line = line.strip()
                if not line:
                    continue
                if ignore_comments and (line.lstrip().startswith("#") or line.lstrip().startswith("//")):
                    continue
                host = extract_host(line)
                if to_lower and host:
                    host = host.lower()
                if not host or not is_valid_domain(host):
                    if keep_invalid:
                        tmp.write(line + "\n")
                        invalid += 1
                    continue
                if keep_root:
                    ext = tldextract.extract(host)
                    if ext.registered_domain:
                        host = ext.registered_domain
                # filter
                if filter_domain_raw:
                    filt = filter_domain_raw.lower() if to_lower else filter_domain_raw
                    if filter_mode == "exact":
                        if host != filt: continue
                    else:
                        if not (host == filt or host.endswith("." + filt)): continue
                valid += 1
                if unique_only:
                    if host in seen:
                        continue
                    seen.add(host)
                tmp.write(host + "\n")
        tmp.flush()
    finally:
        tmp.close()

    if sort_output:
        with open(tmp.name, "r", encoding="utf-8") as f:
            lines = sorted(set(line.strip() for line in f if line.strip()))
        with open(tmp.name, "w", encoding="utf-8") as f:
            for l in lines:
                f.write(l + "\n")

    LAST_RESULT_FILE = tmp.name
    stats = {
        "files": len(request.files.getlist("files")),
        "total_lines": total_lines,
        "valid": valid,
        "invalid": invalid,
        "matched": matched_count if matched_count else valid,
        "unique": len(seen) if unique_only else "—"
    }
    return render_template_string(PAGE, stats=stats)

@app.route("/download")
def download():
    global LAST_RESULT_FILE
    if not LAST_RESULT_FILE or not os.path.exists(LAST_RESULT_FILE):
        return "No result to download", 400
    return send_file(LAST_RESULT_FILE, as_attachment=True, download_name="domains.txt")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
