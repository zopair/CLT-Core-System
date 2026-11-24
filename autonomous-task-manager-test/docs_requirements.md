# Requirements (stage 1)
R1 Add a task with title, priority (low/medium/high) and optional due date.
R2 Reject empty titles and unknown priorities.
R3 Mark a task done / reopen it.
R4 Delete a task; list tasks filtered by status and priority, sorted by priority then due date.
R5 Persist to a local JSON file; load local mock data from data/seed_tasks.json.
R6 Import a JSON file; a malformed import must fail with a clear error and leave existing data unchanged.
R7 Interactive HTML page (add, toggle, delete, filter) using only local mock data, no network.
R8 Automated tests; final report with evidence.
Out of scope: accounts, network, deployment, paid services.

# Architecture (stage 2)
taskmgr/core.py   TaskStore: pure Python, JSON persistence
taskmgr/cli.py    small command line
ui/index.html     single-file UI, vanilla JS, embedded mock data
tests/            unittest suite
orchestrator.py   staged pipeline with checkpoint file (state/checkpoint.json), parallel jobs, stop/resume
