# Focus Feedback Tool — Design Spec

**Date:** 2026-04-18  
**Status:** Approved  
**Script:** `focus-feedback.py` (repo root, alongside `run-local-feedback.py`)

---

## Purpose

A rubric/guidance evaluation tool. Given a single named criterion and one or more LLM models, run AI feedback for that criterion only across many student repos and produce a single aggregated comparison report. Designed for iterating on rubric text and guidance quality — you tweak the rubric/guidance, re-run, and read the results side-by-side across real student work.

Reports are assumed to be pre-rendered. The tool skips Quarto rendering entirely.

---

## CLI Interface

```
# From a file listing repo paths (one per line)
python focus-feedback.py --repos repos.txt --criterion "Results & Analysis" [options]

# From stdin
cat repos.txt | python focus-feedback.py --criterion "Results & Analysis" [options]
find ~/ph230/repos -name index.qmd | xargs dirname | python focus-feedback.py --criterion "Results" ...

# Convenience: single directory (discovers all subdirs containing index.qmd)
python focus-feedback.py --repos-dir ~/ph230/repos --criterion "Results & Analysis" [options]
```

### Arguments

| Argument | Description |
|---|---|
| `--repos FILE` | File of repo paths, one per line. Use `-` for stdin. Mutually exclusive with `--repos-dir`. |
| `--repos-dir DIR` | Convenience: discover all subdirs of DIR that contain `index.qmd`. Mutually exclusive with `--repos`. |
| `--criterion NAME` | **Required.** Name matching a criterion in `rubric.yml` (exact match, case-insensitive fallback). |
| `--models m1 m2 …` | One or more model IDs to compare. Defaults to the configured primary model. |
| `--provider PROVIDER` | AI provider: `github_models`, `openrouter`, `anthropic`, `gemini`, `openai`. |
| `--rubric PATH` | Override `rubric.yml` for all repos. |
| `--guidance PATH` | Override `guidance.md` for all repos. |
| `--config PATH` | Override `config.yml` for all repos. |
| `--instructor-repo PATH` | Path to instructor repo; used to resolve rubric/guidance defaults. |
| `--output DIR` | Output directory. Defaults to `./focus-feedback-TIMESTAMP/`. |
| `--disable-json-mode` | Skip JSON response format (for models that don't support it). |
| `--verbose` | Print per-criterion AI call details as they run. |

### Override precedence (highest → lowest)

1. `--rubric` / `--guidance` / `--config` CLI flags
2. Repo's own `.github/feedback/rubric.yml`, `.github/feedback/guidance.md`, `.github/config.yml`
3. Instructor repo defaults (`--instructor-repo`)
4. Synthesized minimal config (fallback when no config.yml exists anywhere)

---

## Data Flow

For each repo:

1. **Validate** — check `index.qmd` exists; skip with error if not.
2. **Load parsed report** — read `parsed_report.json`. If missing, run `parse_report.py` as a subprocess to generate it, then continue.
3. **Load rubric** — from `--rubric` override, or repo's `.github/feedback/rubric.yml`, or instructor repo default. Find the named criterion by exact name match; fall back to case-insensitive. If not found, print available criterion names and exit.
4. **Load guidance** — from `--guidance` override, or repo's `.github/feedback/guidance.md`, or instructor repo default.
5. **Load config** — from `--config` override, or repo's `.github/config.yml`, or instructor repo default, or synthesized minimal config.
6. **For each model:**
   - Copy `provider_config` from `resolve_provider_config()` and patch `provider_config['model']` to the target model.
   - Call `analyze_criterion(report, criterion, guidance, config, provider_config=...)` directly (imported, no subprocess).
   - Collect result.
7. Append repo result to in-memory list.

All repos processed sequentially. Output file written once at the end.

---

## Output

A single markdown file: `<output-dir>/focus-feedback-TIMESTAMP.md`

```markdown
# Focus Feedback: Results & Analysis
Generated: 2026-04-18 14:30  |  Repos: 12  |  Models: gpt-4o, llama-4-scout
Rubric: /path/to/rubric.yml  |  Guidance: /path/to/guidance.md

## Summary
| Repo      | gpt-4o       | llama-4-scout |
|-----------|--------------|---------------|
| student-1 | Satisfactory | Developing    |
| student-2 | Exemplary    | Satisfactory  |
| student-3 | ERROR        | ERROR         |

---

## student-1

### gpt-4o — Satisfactory
**Summary:** ...

**Strengths:**
- ...

**Areas for Improvement:**
- **Issue:** ... **Suggestion:** ...

---

### llama-4-scout — Developing
...

---

## student-2
...
```

Failed repos show `ERROR` in the summary table and an error block in the body section.

---

## Architecture

### Imports from `dot_github_folder/scripts/`

| Symbol | Source | Used for |
|---|---|---|
| `analyze_criterion` | `ai_feedback_criterion` | Core AI call per criterion per model |
| `get_criterion_guidance` | `ai_feedback_criterion` | Extract criterion-specific guidance section |
| `resolve_provider_config` | `ai_provider` | Build provider config dict |

`run-local-feedback.py` is **not** imported. Repo discovery and validation (~20 lines) is self-contained in the new script.

### Model override

`resolve_provider_config()` returns a mutable dict. For each model in `--models`, the script deep-copies it and sets `provider_config['model']` to the target model before passing to `analyze_criterion()`. No env var manipulation needed.

### Minimal synthesized config

When no `config.yml` is found via any source, the script uses:

```python
{
    'feedback': {'scoring_enabled': False},
    'vision': {'enabled': False},
    'request_timeout': 120,
}
```

This is the fallback only. Real runs should have a config from one of the override sources.

### Rubric format

Accepts `rubric.yml` (machine-readable, used directly by `analyze_criterion`). If the user points `--rubric` at a `RUBRIC.md`, the script detects the `.md` extension and exits with a clear error pointing to `rubric_converter.py`.

---

## What This Tool Does NOT Do

- Render Quarto reports (always skipped)
- Write feedback back to student repos
- Create GitHub issues
- Process more than one criterion per run (use `run-local-feedback.py` for full rubric runs)
