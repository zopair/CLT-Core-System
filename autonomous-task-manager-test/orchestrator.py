"""Staged pipeline with checkpointing, parallel jobs, failure isolation, stop/resume."""
import json, os, sys, time, subprocess, argparse
from concurrent.futures import ThreadPoolExecutor
ROOT = os.path.dirname(os.path.abspath(__file__))
CP = os.path.join(ROOT, "state", "checkpoint.json")
LOG = os.path.join(ROOT, "evidence", "step_log.txt")
STAGES = ["requirements_check", "parallel_jobs", "build_ui", "static_ui_check", "interactive_ui_check", "final_summary"]

def now(): return time.strftime("%H:%M:%S")
def log(msg):
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a") as f: f.write("%s %s\n" % (now(), msg))
    print(msg, flush=True)
def load():
    if os.path.exists(CP):
        with open(CP) as f: return json.load(f)
    return {"completed": [], "results": {}, "runs": 0}
def save(st):
    os.makedirs(os.path.dirname(CP), exist_ok=True)
    with open(CP, "w") as f: json.dump(st, f, indent=2)

def job(name, cmd):
    start = time.time(); t0 = now()
    time.sleep(1.0)  # makes overlap measurable
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    return {"job": name, "exit": p.returncode, "start": start, "end": time.time(),
            "tail": (p.stdout + p.stderr).strip().splitlines()[-3:]}

def s_requirements_check(st):
    ok = all(os.path.exists(os.path.join(ROOT, f)) for f in ["docs_requirements.md", "taskmgr/core.py", "data/seed_tasks.json"])
    return {"ok": ok}

def s_parallel_jobs(st):
    A = ("unit_tests", [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-t", "."])
    B = ("import_bad_file", [sys.executable, "-c",
         "from taskmgr.core import TaskStore;s=TaskStore();s.import_json(open('data/bad_import.json').read())"])
    with ThreadPoolExecutor(2) as ex:
        fa, fb = ex.submit(job, *A), ex.submit(job, *B)
        ra, rb = fa.result(), fb.result()
    overlap = min(ra["end"], rb["end"]) - max(ra["start"], rb["start"])
    wall = max(ra["end"], rb["end"]) - min(ra["start"], rb["start"])
    for r in (ra, rb):
        log("  job %s exit=%d tail=%s" % (r["job"], r["exit"], " | ".join(r["tail"])[-160:]))
    log("  overlap=%.2fs wall=%.2fs (sum of job times=%.2fs)" % (overlap, wall, (ra["end"]-ra["start"])+(rb["end"]-rb["start"])))
    return {"unit_tests_exit": ra["exit"], "import_bad_file_exit": rb["exit"],
            "overlap_s": round(overlap, 2), "wall_s": round(wall, 2),
            "ok": ra["exit"] == 0, "isolated_failure": rb["exit"] != 0 and ra["exit"] == 0}

def s_build_ui(st):
    seed = json.load(open(os.path.join(ROOT, "data/seed_tasks.json")))
    t = open(os.path.join(ROOT, "ui/template.html")).read()
    a, b = t.index("/*SEED*/"), t.index("/*END*/")
    out = t[:a] + json.dumps(seed) + t[b + 7:]
    open(os.path.join(ROOT, "ui/index.html"), "w").write(out)
    return {"ok": True, "tasks_embedded": len(seed)}

def s_static_ui_check(st):
    h = open(os.path.join(ROOT, "ui/index.html")).read()
    return {"ok": "http://" not in h and "https://" not in h and "Write requirements" in h}

def s_interactive_ui_check(st):
    p = subprocess.run(["node", "ui_test.js"], cwd=ROOT, capture_output=True, text=True)
    lines = p.stdout.strip().splitlines()
    for l in lines: log("  " + l)
    return {"ok": p.returncode == 0, "exit": p.returncode, "checks": sum(1 for l in lines if l[:4] in ("PASS", "FAIL"))}

def s_final_summary(st):
    return {"ok": all(v.get("ok") for v in st["results"].values())}

FN = {n: globals()["s_" + n] for n in STAGES}
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--stop-after"); ap.add_argument("--reset", action="store_true")
    a = ap.parse_args()
    if a.reset and os.path.exists(CP): os.remove(CP)
    st = load(); st["runs"] += 1; save(st)
    log("RUN #%d start, checkpoint says completed=%s" % (st["runs"], st["completed"]))
    for s in STAGES:
        if s in st["completed"]:
            log("SKIP %s (already in checkpoint)" % s); continue
        log("START %s" % s)
        try:
            r = FN[s](st)
        except Exception as e:
            log("ERROR %s: %r (not marked complete, exit 1)" % (s, e)); sys.exit(1)
        st["results"][s] = r
        if not r.get("ok"):
            save(st); log("FAILED %s -> %s (not marked complete, exit 1)" % (s, json.dumps(r))); sys.exit(1)
        st["completed"].append(s); save(st)
        log("DONE  %s -> %s" % (s, json.dumps(r)))
        if a.stop_after == s:
            log("INTENTIONAL STOP after %s (exit code 3)" % s); sys.exit(3)
    log("PIPELINE COMPLETE")
if __name__ == "__main__": main()
