# CSCI-350 Math Parser — acceptance suite and template contract

**Status:** DESIGN — approved 2026-08-15. Not built.
**Parent spec:** `2026-08-15-csci350-s3-acceptance-testing-design.md` (the tier contract, the E/S/D/U ladder, the open-tests decision). This document instantiates it once.
**Plan 1 delivered:** the `level` runner, in the course image — `csci350-devcontainer` PR #1.
**Deadline:** HW 5 goes out **Tue Sep 29** (course plan §4a wk 5).
**Course plan:** `1. Projects/Classes/CSCI-350-Fall-2026-Plan.md` §3a (standards), §3c (reassessment), §4c (toolchain), §5 (assignment sequence), §7a (ramp).

---

## 1. Scope: one worked reference, not six templates

Plan 2 was originally framed as "tier targets in the assignment templates." Context exploration
showed the templates do not exist: `202610/projs/` holds `act01-lexer`, `act02-dfa`,
`hw01-lexer` and `hw02-bnf`, and nothing parser-shaped exists anywhere. Authoring HW 5, HW 6,
HW 7, HW 8 and the Tokenizer is course content — Steve's, spread across September to November
as the §7a ramp allows — not tooling work, and four of them are gated on languages not yet
learned.

**This spec therefore covers the Math Parser only**, built end to end as the worked reference
the remaining five copy: template, four-tier suite, generators, timeouts, seed handling. It is
also the first artifact that needs the machinery, so meeting Sep 29 means shipping one
assignment rather than six.

**Why it matters beyond the deadline.** Course plan §3c now promises students a one-week
reassessment window with unlimited resubmissions. That promise is only affordable because
levels are *computed*. If this suite does not exist, the syllabus has committed to a policy the
tooling cannot honour, and the window becomes a judgement call made 34 times.

## 2. Decisions inherited, and where they were made

| Decision | Value | Source |
|---|---|---|
| Implementation language | **Java**, JUnit console-standalone at `$JUNIT_JAR` | Course plan §4c, from Paul's `Lisp-Project/` |
| Numeric domain | **Integer only** | Decided 8/15 — makes the oracle exact |
| Parse stage | **AST exposed**: `parse → Node`, `eval(Node) → int` | Decided 8/15 |
| Tests | **Open** — nothing hidden | Parent spec §3 |
| Levels | E/S/D/U by ordered gating tiers | Parent spec §2 |

Integer-only was chosen so that "wrong" is never confused with "associated differently."
Floating point would force an epsilon and make last-bit association differences — invisible in
the source — a grading dispute.

## 3. Template contract

### 3.1 Given (instructor-authored, present in the distributed repo)

- **`src/Node.java`** — the AST family:
  - `Num(int value)`
  - `BinOp(char op, Node left, Node right)` for `+ - * /`
  - `Neg(Node operand)` for unary minus
  - `equals`/`hashCode`, so a test can construct an expected tree and compare directly
  - `toString()` rendering **fully-parenthesized canonical form**, so a failure message shows
    the tree rather than an object identity
- **`src/ParseException.java`** — the error type **syntactically invalid input** must produce,
  thrown from `parse`. Errors that are only discoverable while evaluating a well-formed tree —
  division by zero being the only one in this grammar — are **not** `ParseException`: `eval`
  lets Java's own `ArithmeticException` propagate. The two are separate because they are
  separate student mistakes, and a suite that conflated them would report a broken evaluator as
  a broken parser
- **`test/`** — the four tagged suites and `ExpressionGenerator.java`
- **`Makefile`**, **`assessment.yml`**, **`.devcontainer/devcontainer.json`** (copied verbatim
  from `csci350-devcontainer/template/`)

### 3.2 Student-written

- The **tokenizer**, built in Math Parser studio I (§4a wk 5 Thu) on top of HW 1's lexer
- `Parser.parse(String) → Node throws ParseException`
- `Evaluator.eval(Node) → int`

Giving them the AST is what makes the D/S split testable at all. It also pays forward: week 6's
scope-and-environment material and the Lisp Interpreter both assume students are already fluent
in "build a tree, then walk it."

## 4. The four tiers

| Tier | Awards | Contents |
|---|---|---|
| `smoke` | U on failure | `make build` compiles; `Main` runs on input `1` without crashing |
| `parse` | **D** | ~15 hand-written cases asserting **exact trees**: precedence, left-associativity, parentheses, unary minus, whitespace tolerance. Exercises `parse` only |
| `eval` | **S** | Values — on hand-built trees (isolating `eval`) and on parsed strings (end to end) |
| `prop` | **E** | The three generators of §5, seeded |

Tiers gate in order per the parent spec: the level is the highest tier such that every tier up
to and including it passed.

## 5. The generators — the oracle is construction, not a second implementation

A reference parser would be a second implementation that can disagree with the first, is more
code to get wrong, and — with open tests — is readable by students. Instead the answer and the
question are generated together.

### 5.1 Value preservation

1. Build a random AST from the grammar, seeded from `LEVEL_SEED`.
2. Compute its value **during construction** — no evaluator is involved, so there is nothing to
   disagree with.
3. Render fully parenthesized, so the text is unambiguous.
4. Assert `eval(parse(rendered)) == knownValue`.

### 5.2 Precedence

Render the **same tree** with redundant parentheses stripped; assert the same value. This is
what catches a broken precedence table — under full parenthesization alone, a parser that gets
`1+2*3` wrong still passes.

### 5.3 Malformed rejection

Mutate valid strings into invalid ones — drop a parenthesis, double an operator, leave a
trailing `+`, empty string — and assert **`ParseException`**, not a crash, a `null`, or a wrong
number.

Generated divisors are **non-zero by construction**; division by zero belongs here, asserting a
deliberate `ArithmeticException`.

## 6. Mechanics

- **`ExpressionGenerator.java` lives in `test/`**, open like everything else (parent spec §3).
  Reads `LEVEL_SEED` once.
- **Per-test timeouts: JUnit 5 `@Timeout(5)` on every method.** This closes the gap plan 1
  deferred — a single non-terminating case now fails one test rather than the whole tier, with
  no new machinery.
- **Seed enforcement.** The Makefile does `export LEVEL_SEED`, and the harness passes it as a
  command-line override (`make test-prop LEVEL_SEED=<n>`), which outranks any `LEVEL_SEED :=`
  a student writes into the Makefile. This closes the determinism hole recorded in the parent
  spec §6b.
- **Tier targets** wrap JUnit tag selection: `--include-tag parse`, etc.
- **`assessment.yml`** carries `standard: S3`, the seed, `timeout_s`, tier order and awards.

## 7. Validation before distribution

The suite **must run green against Steve's own end-to-end solution** before any repo is
created. §7a already requires that solution be built in August; this makes it a gate rather
than a study aid.

Shipping an untested suite is the one mistake `gh rba assignment patch` does not fully undo —
patching corrects the files, but students have already built against what they were given.

## 8. Out of scope

- **The other five assignments.** Each follows this pattern when the §7a ramp reaches it.
- **The Makefile-is-the-gate hole** (parent spec §6b) — a student can still rewrite
  `test-eval:` to `@true`. Restoration of the Makefile alongside `test/` is plan 3.
- **Streaming output capture.** The 64 KB cap bounds the report, not memory (parent spec §6a).
- **The `failures` array.** Structured per-case failures could now be produced from JUnit
  output, but rendering them into the feedback issue is plan 3.

## 9. Open questions

1. **How many generated cases per property?** Enough to catch a precedence bug, few enough to
   stay inside the tier budget. A starting figure of 200 is a guess and should be set by
   measuring runtime against the reference solution.
2. **Does the tokenizer need its own tier?** It is student-written and studio-built, but the
   ladder currently attributes tokenizer failures to `parse`. Splitting would give a more
   precise diagnosis at the cost of a fifth tier.
3. **Whitespace and unary-minus edge cases** — `- -3`, `3 - -2`, `(-3)` — need pinning in the
   grammar before the `parse` tier can assert on them.
