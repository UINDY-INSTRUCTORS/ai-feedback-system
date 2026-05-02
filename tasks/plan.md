# Implementation Plan: levels-only mode + PDF-based repo discovery

## Overview

Two independent features:

1. **`--levels-only` flag** — strips the AI prompt JSON schema down to `{"overall_assessment": "..."}`, skipping summary/strengths/areas_for_improvement. Makes batch classification faster and cheaper when prose feedback is not needed. Flows bottom-up: `ai_feedback_criterion.py` → `run-local-feedback.py` → `batch-feedback.py`.

2. **`--pdf-dir` / `--submissions-dir` flags in `batch-feedback.py`** — exposes the existing `find_repos_from_pdf_dir()` function (already in `run-local-feedback.py`) as a third repo-discovery mode. Lets users point at a folder of PDFs + a submissions folder and automatically discover matching repos.

## Architecture Decisions

- Follow the existing env-var pattern: `SCORING_ENABLED` → add `LEVELS_ONLY=1`. The subprocess pipeline reads env vars, so no new IPC is needed.
- `--levels-only` implies `--no-scoring` (no point showing a numerical score when there is no score). Enforce this silently in `run_feedback_pipeline`.
- `--pdf-dir` + `--submissions-dir` form a new mutually exclusive group alongside the existing `--repos` / `--repos-dir` group. They delegate to the already-tested `find_repos_from_pdf_dir()`.
- No changes to `rubric.yml` or guidance files — those are content, handled separately.

## Dependency Graph

```
Task 1: ai_feedback_criterion.py reads LEVELS_ONLY, emits minimal JSON schema
    │
Task 2: run-local-feedback.py accepts levels_only kwarg, sets env var
    │
Task 3: batch-feedback.py adds --levels-only CLI flag, passes to pipeline
    │
Task 4: batch-feedback.py adds --pdf-dir/--submissions-dir CLI flags (independent of Tasks 1-3)
```

Tasks 1→2→3 are sequential. Task 4 is independent (can be done in any order relative to 1-3).

---

## Phase 1: Core prompt simplification

### Task 1: Add LEVELS_ONLY mode to `ai_feedback_criterion.py`

**Description:** In `build_criterion_prompt()`, check for the `LEVELS_ONLY` env var. When set, use a minimal JSON schema: `{"overall_assessment": "<Poor|Good|Excellent>"}` with a terse instruction. When disabled, existing behavior is unchanged.

**Files touched:**
- `dot_github_folder/scripts/ai_feedback_criterion.py` (~10 lines changed in `build_criterion_prompt`)

**Acceptance criteria:**
- [ ] `LEVELS_ONLY=1` env var produces a prompt with schema `{"overall_assessment": "..."}` only — no summary, strengths, areas_for_improvement, score fields
- [ ] Existing behavior unchanged when env var is absent or falsy
- [ ] The instruction text tells the AI to pick the level name verbatim from the rubric

**Verification:**
- [ ] Read the modified `build_criterion_prompt` and confirm the three branches are correct
- [ ] Run a single repo with `LEVELS_ONLY=1` manually and inspect the prompt via `--debug`

**Dependencies:** None

**Estimated scope:** XS

---

### Task 2: Thread `levels_only` through `run-local-feedback.py`

**Description:** Add `levels_only: bool = False` parameter to `run_feedback_pipeline()`. When true, set `env['LEVELS_ONLY'] = '1'` and also force `env['SCORING_ENABLED'] = 'false'` (levels-only implies no numerical scores). Add `--levels-only` flag to the standalone CLI parser in `run-local-feedback.py`.

**Files touched:**
- `run-local-feedback.py` (signature of `run_feedback_pipeline`, env-var block, argparse)

**Acceptance criteria:**
- [ ] `run_feedback_pipeline(..., levels_only=True)` sets `LEVELS_ONLY=1` in the subprocess env
- [ ] `levels_only=True` forces `SCORING_ENABLED=false` regardless of the `scoring` arg
- [ ] `run-local-feedback.py --levels-only` CLI flag works when running standalone

**Verification:**
- [ ] Read the modified function signature and env-var block
- [ ] Confirm `--levels-only` appears in `run-local-feedback.py --help`

**Dependencies:** Task 1

**Estimated scope:** S

---

### Checkpoint: Phase 1

- [ ] Both files look correct on inspection
- [ ] `python run-local-feedback.py --help` shows `--levels-only`
- [ ] No regressions: existing `--scoring` / `--no-scoring` paths are unchanged

---

## Phase 2: CLI surface in batch-feedback.py

### Task 3: Add `--levels-only` flag to `batch-feedback.py`

**Description:** Add `--levels-only` to the argparse in `batch-feedback.py` and pass it to `run_feedback_pipeline()`. Document that it implies `--no-scoring`.

**Files touched:**
- `batch-feedback.py` (argparse, `run_feedback_pipeline` call)

**Acceptance criteria:**
- [ ] `--levels-only` flag visible in `batch-feedback.py --help`
- [ ] Flag passed as `levels_only=args.levels_only` to `run_feedback_pipeline`
- [ ] Summary table still renders correctly (levels in the assessment column)

**Verification:**
- [ ] `python batch-feedback.py --help` shows `--levels-only`
- [ ] Inspect the modified `run_feedback_pipeline` call to confirm kwarg is present

**Dependencies:** Task 2

**Estimated scope:** XS

---

### Task 4: Add `--pdf-dir` / `--submissions-dir` flags to `batch-feedback.py`

**Description:** Add a new pair of flags to the repo-discovery group in `batch-feedback.py`. When both are supplied, call `_rlf.find_repos_from_pdf_dir(pdf_dir, submissions_dir)` (already imported from `run-local-feedback.py`). Update `load_repo_paths()` to accept these arguments.

**Files touched:**
- `batch-feedback.py` (argparse group, `load_repo_paths`, main call)

**Acceptance criteria:**
- [ ] `--pdf-dir DIR --submissions-dir DIR` is a valid third mode alongside `--repos` / `--repos-dir`
- [ ] Calling with just one of the two raises a clear argparse error
- [ ] `load_repo_paths` returns the same type (`list[Path]`) as the other discovery modes
- [ ] Warning messages from `find_repos_from_pdf_dir` (missing usernames) are preserved

**Verification:**
- [ ] `python batch-feedback.py --help` shows both new flags
- [ ] Dry-run: `python batch-feedback.py --pdf-dir /path/to/pdfs --submissions-dir /path/to/repos --no-render` lists expected repos before processing

**Dependencies:** None (independent of Tasks 1-3)

**Estimated scope:** S

---

### Checkpoint: Phase 2 Complete

- [ ] `python batch-feedback.py --help` shows all new flags
- [ ] `--levels-only` + `--pdf-dir`/`--submissions-dir` work together
- [ ] Existing `--repos` / `--repos-dir` paths unaffected

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| `extract_scores_from_feedback` fails to parse minimal JSON | Med | It already handles missing fields gracefully; `overall_assessment` is always extracted |
| `find_repos_from_pdf_dir` already imported? | Low | It's not — need to expose it from `_rlf` (the dynamically-loaded module) |
| `--pdf-dir` without `--submissions-dir` silently does nothing | Med | Use argparse `required_together` validation or manual check |

## Open Questions

- None — scope is fully defined.
