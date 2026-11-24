# Step and result log (authored summary of what was run)
Date: 2026-11-24. All steps ran locally with Python 3.10 standard library, headless Chrome and Node. No network services, no paid services, no deployment.

| # | Step | Result observed |
|---|------|-----------------|
| 1 | Requirements written (docs_requirements.md, 8 requirements) | done |
| 2 | Architecture chosen: core module, CLI, single-file HTML UI, unittest suite, staged runner with checkpoint | done |
| 3 | Built taskmgr/core.py and cli.py | done |
| 4 | Wrote 12 automated tests | done |
| 5 | First test run | FAILED: discovery error, tests/ was not a package (missing tests/__init__.py). Fixed by adding it |
| 6 | Second test run | 12 of 12 passed. Also showed 2 ResourceWarnings (files opened without closing). Fixed with a `with` block |
| 7 | Third test run after the fix | 12 of 12 passed, no warnings |
| 8 | UI template written, UI built from local seed data (5 tasks) | done |
| 9 | Staged runner, run 1, planned stop after stage 2 | Stages requirements_check and parallel_jobs completed. Runner exited with code 3 on purpose. Checkpoint file held both stages |
| 10 | Parallel stage: two independent jobs at once (unit tests, and importing a deliberately malformed file) | Tests passed (exit 0). Import job failed as expected (exit 1, "title is required"). Jobs overlapped 1.08 s; wall time 1.12 s; a separate sequential run of the same jobs took 2.11 s. The failure did not stop the tests job |
| 11 | Resume: runner run 2 started from the checkpoint | Skipped the 2 completed stages, ran build_ui, ui_check, final_summary, finished OK |
| 12 | Interactive UI test in headless Chrome, 7 checks | 7 of 7 passed (render, sort, empty-title rejection, add, toggle, filter, delete). 3 screenshots saved |
| 13 | CLI smoke test | add works; empty title returns exit 1 with an error message |

Note: each parallel job includes an artificial 1 s pause so overlap is measurable.

Verification hardening (after review): the runner now marks a stage complete only if it succeeded and exits 1 on a failed or erroring stage; the UI test script exits 1 if any check fails. Both were checked with deliberate failures (evidence/exit_code_checks.txt). The pipeline was then rerun from scratch with the same stop/resume sequence: 12/12 unit tests, 7/7 interactive checks, 6 stages complete. Logs: evidence/first_failure/first_failure_reproduced.txt (reproduced, not the original capture), evidence/final_unit_test_log.txt, evidence/step_log.txt.
The HTML UI keeps tasks in memory only (lost on reload); the Python side persists to a JSON file. See README.md.

Not tested: other browsers, mobile layout, two writers editing the JSON file at once, large data sets, any deployment, recovery from a crash in the middle of a stage (only a deliberate stop between stages was tested).
