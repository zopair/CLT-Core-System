# Task manager demo (standalone, local only)
Python 3.10+ standard library. Node and Chrome are only needed for the interactive UI check.

## Run
- Unit tests: `python3 -m unittest discover -s tests -t .`
- CLI: `python3 -m taskmgr.cli --db data/tasks.json add "Title" --priority high --due 2026-12-01` then `list`, `done ID`, `delete ID`
- Full staged pipeline: `python3 orchestrator.py` (add `--stop-after STAGE` to stop on purpose, run again to resume, `--reset` to start over). Exit code 0 = all stages ok, 1 = a stage failed, 3 = intentional stop.
- Interactive UI check: `node ui_test.js` (headless Chrome, exits 1 if any check fails)
- Sequential benchmark: `python3 bench_sequential.py`

## Persistence
- Python side: tasks are saved to a JSON file (CLI `--db`, `TaskStore.save()`).
- HTML UI (ui/index.html): tasks live in browser memory only. They start from the embedded seed data and are lost on reload. It does not read or write the JSON file.

## Notes
- The malformed-import job in the parallel stage is an intended failure; it must fail while the unit tests job passes.
- Each parallel job has an artificial 1 s pause so overlap can be measured.
- Static UI check only searches the HTML for expected content; the interactive check is a separate stage.
