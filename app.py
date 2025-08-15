from flask import Flask, request, render_template_string, send_file
from io import BytesIO
from urllib.parse import urlsplit
import re
import tldextract
import idna

app = Flask(__name__)

PAGE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Bulk Domain Filter</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600&display=swap" rel="stylesheet">
  <style>
    body { font-family: 'Cairo', system-ui, -apple-system, Segoe UI, Roboto, Arial; background:#0f1115; color:#e8e8ea; }
    .wrap { max-width: 960px; margin: 40px auto; padding: 24px; background: #161a22; border-radius: 16px; box-shadow: 0 6px 24px rgba(0,0,0,.25); }
    h1 { margin-top: 0; font-weight: 700; font-size: 24px; }
    .card { background:#0f1320; padding:16px; border-radius:12px; margin:12px 0; }
    label { display:block; margin-bottom: 8px; font-weight:600; }
    input[type=file], input[type=text] { width:100%; padding:10px; background:#0e1220; border:1px solid #2a3142; border-radius:10px; color:#cfd3dc; }
    .row { display:grid; grid-template-columns: 1fr; gap:16px; }
    .btn { cursor:pointer; padding:12px 18px; border-radius:12px; border:1px solid #2a3142; background:#3751ff; color:white; font-weight:700; }
    .btn:disabled { opacity:.6; cursor:not-allowed; }
    .opts { display:flex; gap:16px; flex-wrap:wrap; }
    .muted { color:#a8b0c2; font-size:14px; }
    .stat { background:#121725; padding:10px 12px; border:1px dashed #2a3142; border-radius:10px; display:inline-block; margin:6px 8px 0 0; }
    a.download { display:inline-block; margin-top:12px; }
    .footer { color:#8a91a6; font-size:12px; margin-top:24px; text-align:center; }
    .footer a { color:#4da3ff; text-decoration:none; font-weight:600; }
    .footer a:hover { text-decoration:underline; }
  </style>
</head>
<body>
  <div class="wrap">
    <h1>🧹 Bulk Domain Filter & Normalizer</h1>
    <form method="POST" enctype="multipart/form-data">
      <div class="card">
        <label for="files">Upload files (any count). Each line may be a domain, URL, or mixed text.</label>
        <input id="files" name="files" type="file" multiple required accept=".txt,.csv">
        <div class="muted">The tool scans every line in all files and extracts hostnames/domains.</div>
      </div>
      <div class="card">
        <label>Filter (optional)</label>
        <div class="opts" style="flex-direction:column;">
          <input type="text" name="filter_domain" placeholder="e.g. google.com">
          <label><input type="radio" name="filter_mode" value="endswith" checked> Match domain or subdomains (endswith)</label>
          <label><input type="radio" name="filter_mode" value="exact"> Exact match only</label>
        </div>
        <div class="muted">If set, output will include only entries that match the filter.</div>
      </div>
      <div class="card">
        <label>Options</label>
        <div class="opts">
          <label><input type="checkbox" name="to_lower" checked> Force lowercase</label>
          <label><input type="checkbox" name="trim_spaces" checked> Trim spaces</label>
          <label><input type="checkbox" name="ignore_comments" checked> Ignore comment lines starting with # or //</label>
          <label><input type="checkbox" name="keep_root" checked> Reduce to registered/root domain</label>
          <label><input type="checkbox" name="drop_private"> Drop private suffixes</label>
          <label><input type="checkbox" name="unique_only" checked> Unique only (de‑duplicate)</label>
          <label><input type="checkbox" name="sort_output"> Sort output (A→Z)</label>
          <label><input type="checkbox" name="keep_invalid"> Keep invalid tokens</label>
        </div>
      </div>
      <button class="btn" type="submit">Process & Download</button>
    </form>

    {% if stats %}
    <div class="card" style="margin-top:16px;">
      <div class="stat">Files: <b>{{stats.files}}</b></div>
      <div class="stat">Total lines scanned: <b>{{stats.total_lines}}</b></div>
      <div class="stat">Valid hosts: <b>{{stats.valid}}</b></div>
      <div class="stat">Unique after rules: <b>{{stats.unique}}</b></div>
      <div class="stat">Matched filter: <b>{{stats.matched}}</b></div>
      {% if stats.invalid %}<div class="stat">Invalid tokens: <b>{{stats.invalid}}</b></div>{% endif %}
      <a class="download btn" href="/download" download>⬇️ Download Result</a>
    </div>
    {% endif %}

    <div class="footer">BY <a href="https://t.me/JOOxCRACK" target="_blank">@JOOxCRACK</a></div>
  </div>
</body>
</html>
"""

# (rest of the Python backend remains as updated in previous step, with filter logic)
