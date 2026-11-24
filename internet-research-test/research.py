"""Research test: latest stable Flask release from three public sources.
Fetches live data, saves raw responses, writes verification.json, research_report.md, execution_log.txt.
Python 3 standard library only. Run: python3 research.py"""
import json, os, re, urllib.request, urllib.error
from datetime import datetime, timezone

UA = {"User-Agent": "research-test/1.1"}
LOG, RAW = [], "raw"
os.makedirs(RAW, exist_ok=True)

def now(): return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
def log(m): LOG.append(f"{now()} {m}"); print(LOG[-1])

def get(name, url, timeout=20):
    """Return dict: url, status, read_success, checked_at, body(str), error."""
    r = {"url": url, "status": None, "read_success": False, "checked_at": now(), "body": "", "error": None}
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as resp:
            raw = resp.read(); r["status"] = resp.status
            r["body"] = raw.decode("utf-8", "replace"); r["read_success"] = True
            with open(os.path.join(RAW, name), "wb") as f: f.write(raw)
            log(f"GET {url} -> {resp.status}, {len(raw)} bytes, saved raw/{name}")
    except urllib.error.HTTPError as e:
        r["status"] = e.code; r["error"] = f"HTTP {e.code}"; log(f"GET {url} -> HTTP {e.code}")
    except Exception as e:
        r["error"] = f"{type(e).__name__}: {e}"; log(f"GET {url} -> FAILED {r['error']}")
    return r

def parse_json(r):
    try: return json.loads(r["body"])
    except ValueError as e:
        r["error"] = f"JSON parse failed: {e}"; r["read_success"] = False; log(r["error"]); return None

V = {"project": "Flask (pallets/flask)", "definition_of_stable":
     "Stable = the version the publisher's own flags point to as current: PyPI info.version (not yanked, not a pre/dev release) and GitHub 'latest' release (not prerelease, not draft). Not independent corroboration: all three sources are published by the project or its package host.",
     "sources": {}, "errors": []}

# ---- Source 1: PyPI JSON
r = get("pypi.json", "https://pypi.org/pypi/flask/json"); d = parse_json(r) if r["read_success"] else None
s1 = {"url": r["url"], "status": r["status"], "read_success": r["read_success"], "checked_at": r["checked_at"], "error": r["error"]}
if d:
    try:
        v = d["info"]["version"]; files = d["releases"].get(v, [])
        s1.update(version=v, date=min(f["upload_time_iso_8601"] for f in files) if files else None,
                  yanked=any(f.get("yanked") for f in files), prerelease=bool(re.search(r"(a|b|rc|dev)\d*$", v)),
                  license=d["info"].get("license_expression") or d["info"].get("license"),
                  summary=d["info"].get("summary"), requires_python=d["info"].get("requires_python"),
                  description_first_text=re.sub(r"<[^>]+>|[#*\[\]]", "", d["info"].get("description", "")).strip()[:200])
    except (KeyError, TypeError) as e: s1["error"] = f"unexpected JSON shape: {e!r}"; V["errors"].append(s1["error"])
V["sources"]["pypi"] = s1

# ---- Source 2: GitHub latest release (API)
r = get("github_release.json", "https://api.github.com/repos/pallets/flask/releases/latest"); d = parse_json(r) if r["read_success"] else None
s2 = {"url": r["url"], "status": r["status"], "read_success": r["read_success"], "checked_at": r["checked_at"], "error": r["error"]}
if d:
    try:
        s2.update(version=d["tag_name"].lstrip("v"), date=d["published_at"], prerelease=d["prerelease"], draft=d["draft"],
                  release_page_url=d["html_url"], body=(d.get("body") or "")[:2000])
    except (KeyError, TypeError, AttributeError) as e: s2["error"] = f"unexpected JSON shape: {e!r}"; V["errors"].append(s2["error"])
V["sources"]["github_release"] = s2

# ---- Source 3: project changelog, section for the version the release flags name
r = get("CHANGES.rst", "https://raw.githubusercontent.com/pallets/flask/main/CHANGES.rst")
s3 = {"url": r["url"], "status": r["status"], "read_success": r["read_success"], "checked_at": r["checked_at"], "error": r["error"]}
want = s2.get("version") or s1.get("version")
if r["read_success"]:
    # sections look like: "Version X\n----\n\nReleased DATE" or "Unreleased"
    secs = re.findall(r"^Version (\d+\.\d+\.\d+)\n-+\n\n(.*?)(?=^Version \d|\Z)", r["body"], re.M | re.S)
    first = secs[0] if secs else None
    s3["top_section"] = {"version": first[0], "status_line": first[1].strip().splitlines()[0]} if first else None
    rel = [(v, b) for v, b in secs if re.match(r"Released \d{4}-\d{2}-\d{2}", b.strip())]
    s3["latest_released_section"] = None
    for v, b in rel:
        if v == want:
            m = re.match(r"Released (\d{4}-\d{2}-\d{2})\s*(.*)", b.strip(), re.S)
            s3.update(version=v, date=m.group(1), section_text=re.sub(r"\s+", " ", m.group(2)).strip()[:600]); break
    if "version" not in s3: s3["error"] = f"no released changelog section for version {want}"; V["errors"].append(s3["error"])
V["sources"]["changelog"] = s3

# ---- Comparison
vers = {k: s.get("version") for k, s in V["sources"].items()}
dates = {k: (s.get("date") or "")[:10] or None for k, s in V["sources"].items()}
V["versions_by_source"], V["dates_by_source"] = vers, dates
V["version_agreement"] = len(set(vers.values())) == 1 and None not in vers.values()
V["date_agreement"] = len(set(dates.values())) == 1 and None not in dates.values()
V["stable_version"] = vers["pypi"] if V["version_agreement"] and not s1.get("yanked") and not s1.get("prerelease") \
    and s2.get("prerelease") is False and s2.get("draft") is False else None
V["final_release_page_url"] = s2.get("release_page_url")
V["date_note"] = (f"Dates differ: changelog {dates['changelog']}, PyPI {dates['pypi']}, GitHub {dates['github_release']} (UTC dates). Cause not established."
                  if V["version_agreement"] and not V["date_agreement"] else None)
bi = (s2.get("body") or ""); ch = (s3.get("section_text") or "")
V["content_comparison"] = {
  "github_release_body_mentions_security_fix": "security" in bi.lower(),
  "changelog_section_mentions_ghsa_advisory": "ghsa" in ch.lower(),
  "both_name_same_advisory_id": any(g.lower() in bi.lower() for g in re.findall(r":ghsa:`([\w-]+)`", ch)),
  "note": "PyPI summary/description carry no per-release notes, only the project overview."}

# ---- Link checks: status AND page content (a 200 can be a bot challenge)
checks = [("https://pypi.org/project/flask/", "pypi_page.html", "Flask"),
          ("https://github.com/pallets/flask", "gh_repo.html", "pallets/flask"),
          (V["final_release_page_url"] or "https://github.com/pallets/flask/releases", "gh_release_page.html", "3.1"),
          ("https://flask.palletsprojects.com/", "docs.html", "Flask"),
          ("https://example.invalid/nonexistent", "none.html", "")]
V["link_checks"] = []
for url, name, marker in checks:
    x = get(name, url); body = x["body"]
    challenge = "Client Challenge" in body[:3000]
    title = (re.search(r"<title>(.*?)</title>", body, re.S | re.I) or [None, ""])[1].strip()[:80]
    ok = x["read_success"] and x["status"] == 200 and not challenge and (marker in body if marker else True)
    V["link_checks"].append({"url": url, "status": x["status"], "checked_at": x["checked_at"], "title": title,
        "bot_challenge_page": challenge, "content_confirmed": bool(ok), "error": x["error"]})

# ---- Extra: free public API GET + failure handling
r = get("repo_api.json", "https://api.github.com/repos/pallets/flask"); d = parse_json(r) if r["read_success"] else None
api = {"url": r["url"], "status": r["status"], "checked_at": r["checked_at"], "parsed": None}
if d:
    try: api["parsed"] = {"full_name": d["full_name"], "language": d["language"], "license": (d["license"] or {}).get("spdx_id"), "stars": d["stargazers_count"]}
    except (KeyError, TypeError) as e: api["error"] = repr(e)
f = get("none.json", "https://nonexistent-host-zz.invalid/api")
api["failure_test"] = {"url": f["url"], "status": f["status"], "error": f["error"], "handled_without_invented_data": (not f["read_success"])}
V["api_test"] = api
V["generated_at_utc"] = now()
V["raw_evidence_dir"] = "raw/ (unmodified response bodies)"
V["unverified"] = ["Reason for the one-day changelog date difference.",
                   "Whether other Flask docs pages beyond the reachability/title check say the same thing (not read)."]
json.dump(V, open("verification.json", "w"), indent=2)

# ---- Report generated from the data above
def row(k, label):
    s = V["sources"][k]; return f"| {label} | {s['url']} | {s['status']} | {s['read_success']} | {s['checked_at']} | {s.get('version')} | {s.get('date')} |"
md = [f"# Research report: latest stable {V['project']}", "",
 f"Generated by research.py at {V['generated_at_utc']} (live fetch). Data: verification.json. Raw responses: raw/. Log: execution_log.txt.", "",
 "## Result", f"Latest stable version: **{V['stable_version']}**. Final release page: {V['final_release_page_url']}",
 f"Date: PyPI upload {s1.get('date')}, GitHub published {s2.get('date')}, changelog {s3.get('date')}.", "",
 f"Stable definition used: {V['definition_of_stable']}", "",
 "## Sources read", "| Source | URL | HTTP | Read OK | Checked at | Version | Date |", "|---|---|---|---|---|---|---|",
 row("pypi", "PyPI JSON"), row("github_release", "GitHub latest release API"), row("changelog", "Project changelog"), "",
 "## What each source says",
 f"- PyPI: summary \"{s1.get('summary')}\"; requires Python {s1.get('requires_python')}; license {s1.get('license')}; yanked={s1.get('yanked')}. The long description is a project overview, with no release notes.",
 f"- GitHub release body: {re.sub(chr(10)+'+', ' ', s2.get('body') or '')[:700]}",
 f"- Changelog section {s3.get('version')}: {s3.get('section_text')}", "",
 "## Comparison",
 f"- Version agreement: {V['version_agreement']} ({vers}).",
 f"- Date agreement: {V['date_agreement']} ({dates}). {V['date_note'] or ''}",
 ("- Content: both texts cite the same advisory ID. " if V["content_comparison"]["both_name_same_advisory_id"] else "- Content: the texts do not share an advisory ID (or none found). ") + f"Checks: {V['content_comparison']}",
 "- These are publisher sources (project and its package host), not independent corroboration.", "",
 "## Link checks (status and page content)", "| URL | HTTP | Content confirmed | Note |", "|---|---|---|---|"]
for c in V["link_checks"]:
    note = "bot challenge page, not the real page" if c["bot_challenge_page"] else (c["error"] or c["title"])
    md.append(f"| {c['url']} | {c['status']} | {c['content_confirmed']} | {note} |")
md += ["", "## Extra API test", f"GET {api['url']} -> {api['status']}; parsed {api['parsed']}.",
       f"Failure test: {api['failure_test']['url']} -> {api['failure_test']['error']}; no data invented.", "",
       "## Not verified"] + [f"- {u}" for u in V["unverified"]]
if V["errors"]: md += ["", "## Errors"] + [f"- {e}" for e in V["errors"]]
open("research_report.md", "w").write("\n".join(md) + "\n")
open("execution_log.txt", "w").write("\n".join(LOG) + "\n")
