# AUTONOMOUS MULTI-TASK EXECUTION TEST: Final report (2026-11-24)

Result: the small task-manager project was planned, built, tested, fixed, given an interactive HTML UI, and run through a staged pipeline with parallel jobs, an isolated failure, a checkpoint, an intentional stop and a resume. Everything below was observed in actual runs. See AUTHORED_STEP_LOG.md for the step list.

## Persistence
HTML UI: in memory only (reset on reload). Python side: JSON file. See README.md.

## What was built
- taskmgr/core.py: add, done/reopen, delete, filter by status and priority, sorting, JSON save/load, import with validation (malformed input rejected, existing data unchanged).
- taskmgr/cli.py: add/list/done/delete.
- ui/index.html: single file, local mock data embedded, no network.
- tests/test_core.py: 12 unit tests.
- orchestrator.py: 6 stages, checkpoint file, parallel jobs, stop/resume.

## Evidence by requirement
| Requirement | Evidence |
|---|---|
| Analyze requirements, design | docs_requirements.md |
| Automated tests, run and fix | First run failed (tests folder not a package), fixed. Later run showed 2 resource warnings, fixed. Final: 12/12 pass |
| Interactive HTML UI | 7/7 browser interaction checks pass (run by the separate interactive_ui_check stage; the static_ui_check stage only searches the HTML text); screenshots ui_1, ui_2, ui_3 |
| Local mock data | data/seed_tasks.json (5 invented tasks) |
| Two independent tasks in parallel | Unit tests and a malformed-file import ran at the same time: 1.08 s overlap; wall 1.12 s in the parallel run vs 2.11 s in a separate measured sequential run of the same two jobs |
| One fails without stopping the other | Import job exit 1 as designed; tests job still exit 0 and the pipeline continued |
| State kept between stages | state/checkpoint.json recorded stages and results after each stage |
| Intentional stop and resume | Run 1 stopped on purpose (exit code 3) after stage 2; run 2 skipped completed stages and finished the other 3 |
| No paid services, no deploy, main untouched | Nothing paid or deployed; only the test branch is used |

Note on the parallel test: each job contains an artificial 1 s pause so that overlap is measurable; the speed-up therefore shows the jobs ran concurrently, not that the real work is faster.

## Scores (0-5, observed outcomes only)
- Planning 4: simple written requirements and design; no formal estimate or risk analysis.
- Building 4: working core, CLI, UI.
- Verification 4: 12 unit tests and 7 UI checks, all passing; small scope.
- Recovery 4: two real defects found by test runs and fixed; the failure scenario was injected by me, not an unexpected crash.
- Parallelism 3: two concurrent jobs shown; only 2 tested.
- Resume 3: deliberate stop between stages worked; mid-stage crash not tested.

## Limits
Not tested: other browsers, mobile layout, concurrent writers to the data file, large data, deployment, crash in the middle of a stage. The "failure" was a deliberately malformed file I created, so this shows isolation for an expected failure, not for arbitrary ones.
