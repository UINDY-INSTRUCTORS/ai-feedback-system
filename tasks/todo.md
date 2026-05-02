# Task List: levels-only + PDF repo discovery

## Phase 1: Core prompt simplification

- [ ] Task 1: Add LEVELS_ONLY env-var branch to `build_criterion_prompt()` in `ai_feedback_criterion.py`
- [ ] Task 2: Thread `levels_only` kwarg + `--levels-only` CLI flag through `run-local-feedback.py`

### Checkpoint: Phase 1
- [ ] Inspect both files; confirm no regressions to existing scoring paths

## Phase 2: CLI surface

- [ ] Task 3: Add `--levels-only` flag to `batch-feedback.py`, pass to pipeline
- [ ] Task 4: Add `--pdf-dir` / `--submissions-dir` flags to `batch-feedback.py`

### Checkpoint: Phase 2
- [ ] `--help` shows all new flags; existing modes unaffected
