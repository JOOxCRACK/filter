from flask import Flask, request, render_template_string, send_file
from io import BytesIO

app = Flask(__name__)

PAGE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>File Line Subtraction Tool</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600&display=swap" rel="stylesheet">
  <style>
    body { font-family: 'Cairo', system-ui, -apple-system, Segoe UI, Roboto, Arial; background:#0f1115; color:#e8e8ea; }
    .wrap { max-width: 820px; margin: 40px auto; padding: 24px; background: #161a22; border-radius: 16px; box-shadow: 0 6px 24px rgba(0,0,0,.25); }
    h1 { margin-top: 0; font-weight: 700; font-size: 24px; }
    .card { background:#0f1320; padding:16px; border-radius:12px; margin:12px 0; }
    label { display:block; margin-bottom: 8px; font-weight:600; }
    input[type=file] { width:100%; padding:10px; background:#0e1220; border:1px solid #2a3142; border-radius:10px; color:#cfd3dc; }
    .row { display:grid; grid-template-columns: 1fr 1fr; gap:16px; }
    .btn { cursor:pointer; padding:12px 18px; border-radius:12px; border:1px solid #2a3142; background:#3751ff; color:white; font-weight:700; }
    .btn:disabled { opacity:.6; cursor:not-allowed; }
    .opts { display:flex; gap:16px; flex-wrap:wrap; }
    .muted { color:#a8b0c2; font-size:14px; }
    .stat { background:#121725; padding:10px 12px; border:1px dashed #2a3142; border-radius:10px; display:inline-block; margin-right:8px; }
    a.download { display:inline-block; margin-top:12px; }
    .footer { color:#8a91a6; font-size:12px; margin-top:24px; text-align:center; }
  </style>
</head>
<body>
  <div class="wrap">
    <h1>🗂️ Remove lines from Bottom File that exist in Top File</h1>
    <form method="POST" enctype="multipart/form-data">
      <div class="row">
        <div class="card">
          <label for="file_top">Top File (lines to remove)</label>
          <input id="file_top" name="file_top" type="file" required>
          <div class="muted">Preferred: .txt or .csv — one value per line.</div>
        </div>
        <div class="card">
          <label for="file_bottom">Bottom File (to be cleaned)</label>
          <input id="file_bottom" name="file_bottom" type="file" required>
        </div>
      </div>
      <div class="card">
        <label>Options</label>
        <div class="opts">
          <label><input type="checkbox" name="case_sensitive"> Case sensitive (A≠a)</label>
          <label><input type="checkbox" name="trim_spaces" checked> Trim spaces</label>
          <label><input type="checkbox" name="ignore_empty" checked> Ignore empty lines</label>
        </div>
      </div>
      <button class="btn" type="submit">Process & Download</button>
    </form>

    {% if stats %}
    <div class="card" style="margin-top:16px;">
      <div class="stat">Top file lines: <b>{{stats.top}}</b></div>
      <div class="stat">Bottom file lines: <b>{{stats.bottom}}</b></div>
      <div class="stat">Remaining after removal: <b>{{stats.out}}</b></div>
      <a class="download btn" href="/download" download>⬇️ Download Result</a>
    </div>
    {% endif %}

    <div class="footer">Made BY JOOxCRACK · Supports UTF‑8 by default.</div>
  </div>
</body>
</html>
"""

def _read_text(file_storage, try_encodings=("utf-8", "utf-8-sig", "cp1256", "latin-1")):
    data = file_storage.read()
    try:
        file_storage.seek(0)
    except Exception:
        pass
    for enc in try_encodings:
        try:
            return data.decode(enc)
        except Exception:
            continue
    return data.decode("utf-8", errors="replace")

def _normalize(line: str, trim_spaces: bool, case_sensitive: bool) -> str:
    if trim_spaces:
        line = line.strip()
    return line if case_sensitive else line.lower()

_LAST_RESULT = None

@app.route("/", methods=["GET", "POST"])
def index():
    global _LAST_RESULT
    if request.method == "GET":
        return render_template_string(PAGE)

    case_sensitive = bool(request.form.get("case_sensitive"))
    trim_spaces = bool(request.form.get("trim_spaces"))
    ignore_empty = bool(request.form.get("ignore_empty"))

    top_fs = request.files.get("file_top")
    bottom_fs = request.files.get("file_bottom")
    if not top_fs or not bottom_fs:
        return render_template_string(PAGE, stats=None)

    top_text = _read_text(top_fs)
    bottom_text = _read_text(bottom_fs)

    top_lines_raw = top_text.splitlines()
    bottom_lines_raw = bottom_text.splitlines()

    top_norm_set = set()
    for L in top_lines_raw:
        n = _normalize(L, trim_spaces, case_sensitive)
        if ignore_empty and (n == ""):
            continue
        top_norm_set.add(n)

    out_lines = []
    for L in bottom_lines_raw:
        n = _normalize(L, trim_spaces, case_sensitive)
        if ignore_empty and (n == ""):
            continue
        if n in top_norm_set:
            continue
        out_lines.append(L)

    output_text = "\n".join(out_lines)
    _LAST_RESULT = output_text.encode("utf-8")

    stats = {
        "top": len(top_lines_raw),
        "bottom": len(bottom_lines_raw),
        "out": len(out_lines),
    }
    return render_template_string(PAGE, stats=stats)

@app.route("/download")
def download():
    global _LAST_RESULT
    if not _LAST_RESULT:
        return "No result to download — run the process first.", 400
    buf = BytesIO(_LAST_RESULT)
    return send_file(buf, as_attachment=True, download_name="result.txt", mimetype="text/plain; charset=utf-8")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
