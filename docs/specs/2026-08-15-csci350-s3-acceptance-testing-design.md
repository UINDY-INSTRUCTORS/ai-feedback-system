# CSCI-350 S3 — acceptance testing as the achievement-level source

**Status:** DESIGN — approved 2026-08-15. Not built.
**Drives:** CSCI-350 Fall 2026 syllabus (§3a standards), the `code` submission adapter.
**Related:** `1. Projects/AI-Feedback-For-Code.md` in the Obsidian vault (§2 establishes
tests-as-ground-truth; this spec makes it concrete), `1. Projects/Classes/CSCI-350-Fall-2026-Plan.md` §3a.
**Deadline:** Math Parser, week 5 (Sep 29) — the first artifact where per-student manual
feedback across 34 students stops being feasible.

---

## 1. Problem

CSCI-350 standard **S3** is *"Build a working interpreter for a defined language (parse +
evaluate)."* It was flagged in the course plan as the one standard whose achievement levels
don't fit a conceptual-mastery ladder: a build outcome is level-of-completeness, not
level-of-understanding. The plan's open item — "decide what achievement levels *mean* for a
build outcome" — blocks the syllabus.

The answer adopted here: **an acceptance test suite defines the levels.** The AI feedback
layer never judges correctness. This spec defines the level ladder, the contract a project
repo must satisfy for a level to be read off it, and the failure modes.

## 2. Level definitions

The course-wide **E / S / D / U** scale is used unchanged — the same vocabulary as EENG-340,
PH-230/280, and the existing FCAR automation. No build-specific scale is introduced.

| Level | Earned by | Meaning |
|---|---|---|
| **U** | Smoke tier fails | Does not build or run |
| **D** | Parse tier passes | Required grammar parses to a correct tree; evaluation incomplete or wrong |
| **S** | Parse + evaluate tiers pass | Full required grammar parses *and* evaluates correctly |
| **E** | S, plus the property tier | Generated well-formed inputs agree with the oracle; malformed inputs error deliberately rather than crashing |

Three rules govern how tiers become a level:

**Tiers gate in order.** The level is the highest tier such that every tier up to and
including it passed. A submission that passes the property tier while failing evaluation is
D, not E — `eval` gated. Without ordering the outcome space admits incoherent results like
"robust but doesn't work."

**Tiers are all-or-nothing.** Nine of ten core tests is D, not "almost S." A tier is a gate,
not a percentage. This is what keeps the scheme standards-based rather than points-based
wearing SBG vocabulary. Individual failures are still reported in full — the *feedback* is
granular, the *level* is not.

**The property tier is seeded.** Case count and RNG seed are fixed per assignment, so a given
commit always yields the same level. Unseeded randomization would let a student's level
change on re-push with no code change, which is indefensible to a student and unusable as
FCAR evidence.

### 2.1 Roll-up across the two S3 artifacts

S3 is evidenced by two artifacts — the Math Parser (wk 5) and the Lisp Interpreter (later) —
against a single Brightspace Outcome. **Most-recent evidence wins.** The parser sets S3
provisionally; the interpreter supersedes it. This follows standard SBG practice and reflects
that the interpreter subsumes the parser skill.

## 3. Tests are open

Students receive the complete acceptance suite. Nothing is withheld.

### 3.1 Why hiding was rejected

Students join the course org as **outside collaborators with write access to their own
repos** (course plan §4e). Write access includes `.github/workflows/`. Any secret exposed to
a workflow in a repo the student controls can be exfiltrated by editing that workflow — log
masking prevents accidents, not intent. A private tests repo pulled with a PAT therefore
leaks the tests to any student who wants them. The same reasoning already forced the GHCR
image to be public.

Gating the secret behind an Actions environment with required reviewers works but demands
manual approval on every run, which defeats the purpose.

### 3.2 What replaces secrecy

The E tier gets its rigour from **generation and differential comparison**, not concealment.
The test code is public; the specific cases are not enumerable in advance.

- **Math Parser** — generate random well-formed expressions from the assignment grammar and
  compare the student's evaluator against the host language's own arithmetic. No reference
  implementation is needed; the oracle is free.
- **Lisp Interpreter** — the course image already carries **SBCL** (Common Lisp) and
  **Racket** (Scheme), so a real implementation serves as the oracle for generated forms.
  Which one depends on the dialect decision still open in the course plan §4b(e); the oracle
  is available either way, so this design does not block on it. (Note: `clisp` appears in
  Paul's inherited `Lisp-Playground` devcontainer, not in the course image.)
- **Malformed input** — generate garbage within and around the grammar and assert the student
  errors deliberately rather than crashing with an unhandled stack trace.

This makes "robust" a property that holds over inputs neither instructor nor student
enumerated, rather than a checklist of cases the instructor happened to think of. It also
removes the caution in the design note about withholding test content from the model: with
nothing hidden, the suite can go into the AI prompt, which strictly improves feedback.

## 4. The tier contract

### 4.1 Tiers are Make targets

The existing templates establish `build` / `test` / `run` / `clean` with a Makefile per
project. Tiers extend that vocabulary:

```
test          # unchanged — runs everything; remains the student's default
test-smoke    # builds and runs at all
test-parse    # required grammar → correct tree
test-eval     # correct evaluation over the published cases
test-prop     # generated inputs vs. oracle; malformed inputs error deliberately
level         # runs the tiers in order and writes assessment.json
```

The harness knows only these target names and their exit codes. It knows nothing about JUnit,
`raco`, or QuickCheck. For Java the targets are thin wrappers over JUnit 5 tag selection
(`@Tag("parse")` + `--include-tag parse`); for other toolchains the target bodies differ
entirely and the harness is unaffected. Make is the one interface all five toolchains share
and the one the templates already use.

**All tiers run on every invocation.** Execution does not stop at the first failing tier —
running all four is cheap and gives the feedback issue far more to work with. Only the *level*
calculation applies the gating rule.

### 4.2 Per-repo manifest

```yaml
standard: S3
seed: 20260929
floor: U                                  # level when the first tier fails
timeout_s: 120                            # default wall-clock budget per tier
timeouts: {prop: 600}                     # per-tier overrides
tiers:  [smoke, parse, eval, prop]        # evaluation order
awards: {smoke: U, parse: D, eval: S, prop: E}   # level awarded when this tier PASSES
```

`timeout_s` and `timeouts` were added during implementation: §5 requires per-tier timeouts and
the manifest originally had nowhere to put them.

`awards` maps a tier to the level earned by *passing* it; `floor` is the level when even the
first tier fails. For S3 the floor and `awards.smoke` are both U, since building without
parsing anything demonstrates nothing — but they are separate keys because a lab tier set may
want them to differ.

The manifest exists rather than hardcoded convention for two reasons unrelated to S3: the S4
lab repos need a different tier set (no parse stage), and the Brightspace import needs to know
which Outcome a given repo feeds.

### 4.3 Output

The harness writes `assessment.json`:

```json
{
  "status": "ok",
  "standard": "S3",
  "level": "S",
  "seed": 20260929,
  "tiers": [
    {"name": "smoke", "result": "pass"},
    {"name": "parse", "result": "pass"},
    {"name": "eval",  "result": "pass"},
    {"name": "prop",  "result": "fail",
     "failures": [
       {"case": "(- 3 (/ 4 0))", "expected": "error", "got": "crash: ArithmeticException"},
       {"case": "(let loop ...)", "expected": "42", "got": "timeout after 30s"}
     ]}
  ]
}
```

`result` is one of `pass`, `fail`, `timeout`, or `skip`. A tier is `timeout` only when the
tier as a whole exceeded its budget; an individual case that timed out inside an otherwise
completing tier appears as a failure with `got: "timeout after Ns"`, as above. `skip` covers
tiers not reached when `status` is `error`.

`create_issue.py` renders this into the feedback issue; it is also the input to the eventual
Brightspace Outcomes import. The `code` adapter emits it alongside the
`parsed_report.json`-compatible output, so the "two front ends, one downstream" design in the
design note holds unchanged.

### 4.4 Local parity is required, not incidental

`make level` must produce the same answer in a student's Codespace as in CI. A student sees
their own level before pushing and can iterate against it. Nothing about the level is a
surprise or a judgement call.

This is the property that makes generous reassessment safe and makes the level defensible
when disputed, and it is the reason tier logic lives in the Makefile rather than in the
Action.

## 5. Failure modes

**Build failure → U, with verbatim diagnostics, and no model call.** The feedback issue
carries the compiler output unparaphrased — compiler errors are already precise and an LLM
rewrite makes them worse. The AI pass is skipped entirely and the issue says "fix the build,
then re-tag." This is also the cheapest mitigation available for the volume concern: the
submissions that would waste quota most are exactly the ones that do not compile.

**Timeouts are a distinct outcome from wrong answers.** Non-termination is a normal student
bug in this course — left recursion in a recursive-descent parser, a missing base case in
eval. Every tier runs under a wall-clock timeout at two levels: per-test, so one hanging case
cannot consume the tier budget and mask the tests after it, and per-job as a backstop (the
workflow's existing `timeout-minutes: 15`). `assessment.json` records `timeout` distinctly
from `fail`, because the two have unrelated fixes.

Timeout budgets are generous — on the order of 10× the reference solution's runtime — for the
same reason the property tier is seeded. A correct but slow solution that passes locally and
times out on a loaded runner would be a level that changed without the code changing.

**Harness failure withholds the level.** An image pull failure, a network fault, or a GitHub
Models outage is not a student who cannot build an interpreter. `assessment.json` carries
`status: ok | error`; only `ok` yields a level. On `error` the level is withheld and the
instructor is notified, rather than 34 students receiving a spurious U.

**Student edits to tests cannot move the level.** The suite ships in a repo the student can
write to, and a student debugging late at night will comment out a failing assertion and
forget to restore it — no bad intent required. Before running anything, the harness discards
the student's `test/` directory and restores it from the assignment template pinned to a tag.
Students keep reading and running tests locally, which is the entire point of open tests;
their edits simply cannot affect the reported level. When `make level` locally disagrees with
the harness, that divergence is itself a signal worth having.

## 6. Out of scope

- **S4 lab tiers.** The S4 labs consume this contract but need their own tier set. Separate design.
- **The AI feedback layer.** It consumes `assessment.json` and is unchanged by this spec.
- **Brightspace Outcomes import.** `assessment.json` is designed to feed it; the import path itself is not specified here.

## 6a. What plan 1 actually shipped, and where it diverges from §4.3

Plan 1 (`csci350-devcontainer`, PR #1, 18 commits) built the runner. Three divergences from
this spec, recorded so the spec and the artifact do not drift apart silently:

- **No `failures` array.** §4.3 shows per-tier `failures: [{case, expected, got}]`. The shipped
  `assessment.json` carries a flat `output` string plus `duration_s` instead. Structured
  per-case failures have to come from the test framework, which is plan 2's territory —
  `create_issue.py` and the Brightspace import should expect `output` until then.
- **Per-tier timeouts only.** §5 asks for a per-*test* timeout so one hanging case cannot mask
  the tests after it. Plan 1 implements the per-tier budget; per-test lives in the test
  framework, so it lands with the tier targets in plan 2. Until then a single infinite loop
  fails the whole tier and understates what works.
- **The 64 KB output cap bounds the report, not memory.** `communicate()` reads a tier's output
  to EOF before truncation sees it — a 100 MB tier was measured at +348 MB RSS. A runaway
  `printf` inside the 600 s `prop` budget can still exhaust the harness, which produces *no*
  report at all. Bounding memory needs a streaming read replacing `communicate()`.

## 6b. Two integrity gaps this spec does not close

Found during plan 1's final review. Both are spec-level, not implementation defects.

- **The Makefile is the gate, and §5 does not protect it.** §5 promises student edits to tests
  cannot move the level, and restores `test/` from the pinned template. But the level is read
  from `make test-<tier>` exit codes, and the Makefile is not in `test/`. A student who
  rewrites `test-eval:` to `@true` moves their own level, untouched by the restoration.
  Plan 3 must restore the Makefile — or at least the tier targets — alongside `test/`.
- **`LEVEL_SEED` is student-overridable.** The runner exports it into the environment, and a
  `LEVEL_SEED := 1` assignment inside the Makefile takes precedence over an environment
  variable in GNU Make. Determinism is therefore a courtesy rather than an enforcement.
  Passing it as a command-line override (`make test-<tier> LEVEL_SEED=<n>`) outranks any
  Makefile assignment; adopt that when plan 2 lands the tier targets.

## 7. Open questions

1. **Feedback volume cap.** The design note proposes capping feedback tags at 3 per
   assignment; nothing implements it. 34 students × ~7 assignments × on-demand tags against
   `max_concurrent_requests: 2` will throttle at deadlines. The level recomputation is free,
   so students must understand the level loop and the feedback loop as two different things
   with different limits.
2. ~~**Reassessment windows**~~ — **CLOSED 8/15**, course plan §3c. One week after each
   deadline, extended past breaks, unlimited resubmissions inside it, feedback capped at 3
   requests per assignment, all closing Wed Dec 16. The rule is only defensible *because*
   levels are computed, which makes plan 2 a prerequisite for the policy rather than merely
   for the tooling: if the acceptance suites are not in place, a week-long window becomes a
   judgement call made 34 times.
3. ~~**S4 granularity**~~ — **CLOSED 8/15**, course plan §3a. Split one per paradigm:
   **S4a** imperative/OO, **S4b** functional, **S4c** logic. Three Brightspace Outcomes, so
   plan 2 needs three tier sets, not one — and S4c rests on a single artifact (HW 8 Prolog,
   authored fresh), which makes its suite the one with no second chance to get right.
