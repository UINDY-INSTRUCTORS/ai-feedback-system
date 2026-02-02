# PH 280 Project 2: The Heun Method - AI Assessment Rubric

**Course**: PH 280 - Computational Physics
**Assignment**: Project 2: The Heun Method
**Criterion Weights**: Abstract & Description 10%, Algorithm & Discussion 20%, Implementation/Code 40%, Results 20%, Conclusion 10%

---

## Critical Standards (Applied Throughout Assessment)

### 1. Precision-Uncertainty Alignment (Conceptual Error)

**Definition**: When a student reports a value with uncertainty, the reported precision must match the precision implied by the uncertainty.

**Example of correct alignment**:
- ✅ `Distance = 420 ± 5 feet` (both to nearest 10)
- ✅ `Time = 5.23 ± 0.05 s` (both to hundredths)

**Example of misalignment** (CONCEPTUAL ERROR):
- ❌ `Distance = 420.386471 ± 5 feet` (reports to 0.000001 but uncertainty is ±5)
- ❌ `Time = 5.23984726 ± 0.05 s` (7 extra digits)

**Assessment Rule**:
- If precision-uncertainty mismatch exists, rate as **"Developing"** (not Good, not Excellent)
- This is a **conceptual error**, not a formatting issue
- Severity: If >3 extra digits of false precision, consider lowering overall criterion rating
- Apply this check to: Abstract, Results, and Conclusion sections

---

### 2. Uncertainty Source (Critical for Excellent)

**Definition**: When a student states uncertainty (±X), they must explain HOW they estimated it.

**Valid sources** (student must reference one):
- Comparison to analytical solution
- Comparison to known physics (e.g., energy conservation)
- Variation with different parameters
- Error propagation from input uncertainties
- Physical constraints on the answer

**Assessment Rule**:
- **For Excellent**: Uncertainty must be stated with explicit source explanation
  - Not just "±5" but "±5, determined by comparing to [method]"
  - Should appear in Results section with detail; can be summarized in Abstract/Conclusion
- **For Good**: Can omit uncertainty entirely
- **For Developing**: Uncertainty stated without source explanation

---

### 3. Attributions Required

**Definition**: Student must acknowledge all external help, resources, and collaborations.

**What to check**:
- Other students discussed with?
- Resources consulted (books, websites, AI, etc.)?
- Tutoring or help from faculty/TAs?
- Should be in a brief "Attributions" or "Acknowledgments" section

**Assessment Rule**:
- Deduct 1-2 points if attributions completely missing
- Note in feedback if present and thorough
- This is part of academic integrity and professionalism

---

## Detailed Criterion Assessment

### Criterion 1: Abstract & Description (10%)

**Purpose**: Student clearly introduces the project, main result, and significance.

#### Performance Levels

| Level | Range | Description |
|-------|-------|-------------|
| **Excellent** | 65-100% | Option choice absolutely clear (A, B, or C stated explicitly); Main result stated clearly with units AND uncertainty estimate; Significance well explained: Why is this interesting? What did you learn? |
| **Good** | 35-65% | Option stated; idea is clear; Result stated; Brief significance mentioned |
| **Developing** | 0-35% | Option choice not stated or unclear; Result missing, vague, or nonsensical; No significance explanation |
| Abstract may be multiple paragraphs | Abstract present but may be longer than ideal | **Abstract is 1-2 sentences max**: What computed, how, and main result only |
| Precision-uncertainty mismatch present | Precision reasonable | **Precision matches uncertainty** (if uncertainty stated) |
| | | **Uncertainty source explained** (if uncertainty stated) |

#### Red Flags (Significant Deductions)

- Callout boxes from template still present: Major deduction
- Option unclear: Significant deduction
- Result completely missing: Major deduction
- Abstract longer than 2 sentences: Minor deduction
- Precision-uncertainty mismatch: Rate as Developing, not Good

#### Assessment Guidance

**Excellent indicators**:
- Option A: Clear statement that it's space travel, final time values mentioned with ±
- Option B: Clear statement that it's baseball trajectory, final distance with ±
- Option C: Clear statement of chosen system, relevant numerical result with ±
- Description explains why this problem is interesting/significant
- Precision matches stated uncertainty

**Good indicators**:
- Option is clear
- Main result stated with units (uncertainty optional)
- Description is present and sensible

**Developing indicators**:
- Option unclear or missing
- Result is vague or missing
- Precision-uncertainty mismatch
- Description doesn't explain significance

---

### Criterion 2: Algorithm & Discussion (20%)

**Purpose**: Student demonstrates computational thinking—explains their approach and how it applies to their specific problem.

#### Performance Levels

| Level | Range | Description |
|-------|-------|-------------|
| **Excellent** | 65-100% | Heun method explained with clear mathematical formulation; Why Heun was chosen over alternatives (vs. Euler, etc.) explained; Decomposition shown explicitly and explained; System-specific equations written mathematically with parameter definitions; Clear connection between Heun method and problem setup; Motivation for approach clearly stated: Why this way? Why these choices?; Sufficient detail that competent reader can follow code without additional explanation |
| **Good** | 35-65% | Heun method described clearly and correctly; Brief mention of method choice; Decomposition shown; Equations present but may lack context; Some connection shown; Approach makes sense |
| **Developing** | 0-35% | Heun method not explained or incorrectly described; No discussion of why Heun was chosen; ODE decomposition missing or incorrect; System-specific equations missing; No connection between algorithm and problem; Motivation for approach unclear or absent |

#### Red Flags (Significant Deductions)

- Callout boxes from template still present: Major deduction
- Heun method described incorrectly: Major deduction
- No explanation of why decomposition needed: Significant deduction
- System equations missing: Significant deduction
- Significant confusion between Heun and Euler: Major deduction

#### Assessment Guidance

**Excellent indicators**:
- Heun predictor-corrector clearly explained: $s_{predict} = s_{old} + f(s_{old}) \Delta t$, then $s_{new} = s_{old} + \frac{1}{2}(f(s_{old}) + f(s_{predict})) \Delta t$
- Comparison to Euler method shown
- Coupled first-order ODE decomposition explicitly shown
- For Option A: Relativistic equations shown ($\gamma = 1/\sqrt{1-v^2/c^2}$, acceleration equations)
- For Option B: Drag model equations shown ($F = -bv^2/m$ or similar)
- For Option C: System decomposition clearly explained
- Time step choice justified
- Reader can follow code without asking "how is the problem set up?"

**Good indicators**:
- Heun method explained correctly, mostly complete
- Decomposition shown
- System equations presented
- Some motivation for approach

**Developing indicators**:
- Heun method described incorrectly or incompletely
- Decomposition missing or confused
- Equations unclear or missing
- No explanation of why decomposition matters

---

### Criterion 3: Implementation/Code (40%)

**Purpose**: Code is correct, verifiable, and demonstrates computational competence.

#### Performance Levels

| Level | Range | Description |
|-------|-------|-------------|
| **Excellent** | 65-100% | Code runs flawlessly; Heun implementation verified correct; Predictor and corrector steps implemented correctly; Sound validation story with independent verification; Code easy to read with semantic variable/function names; Clear explanation of HOW student knows code is correct; Option-specific validation performed (A: Energy conservation check at midpoint shown; B: No-drag analytical comparison shown; C: Student's validation approach clearly explained); Independent verification (separate from main code logic) |
| **Good** | 35-65% | Code runs; Heun mostly correct; Predictor/corrector mostly correct; Some validation attempted; Code fairly readable; some documentation; Brief validation mention |
| **Developing** | 0-35% | Code missing or does not run; Heun method incorrectly implemented; No attempt at validation; Code difficult to follow; unclear names; No explanation of how correctness known |

#### Red Flags (Significant Deductions)

- Callout boxes from template still present: Major deduction
- Predictor step incorrect: Major deduction
- Corrector step incorrect (e.g., using only $k_2$ instead of averaging): Major deduction
- Time stepping loop has errors: Significant deduction
- No validation: Major deduction
- Poor variable names AND minimal comments (bad code): Significant deduction
- Not using NumPy vectorization (slow nested loops): Minor deduction

#### Assessment Guidance

**Excellent indicators**:
- Heun implementation is mathematically sound
- Predictor step: $k_1 = f(state_{old}), state_{predict} = state_{old} + k_1 \Delta t$
- Corrector step: $k_2 = f(state_{predict}), state_{new} = state_{old} + \frac{1}{2}(k_1 + k_2) \Delta t$
- Code structure is clear (separate functions for predictor, corrector, validation)
- Semantic names: `predictor_step()`, `corrector_step()`, `energy_check()` rather than `func()`, `temp`, `x`
- Comments only where logic is non-obvious
- Validation present and independent from main loop:
  - Option A: Gamma calculation from simulation compared to energy conservation prediction
  - Option B: No-drag case compared to analytical projectile motion formula
  - Option C: Student demonstrates chosen validation approach
- Results of validation shown (e.g., "Error from analytical: 1.2%")

**Good indicators**:
- Code works and Heun mostly correct
- Structure is fairly clear
- Some documentation present
- Validation attempted
- Variable names are reasonable

**Developing indicators**:
- Code has significant errors
- Heun implementation incorrect
- No validation or validation nonsensical
- Code is hard to follow
- Unclear names AND insufficient documentation

#### Code Quality Philosophy

- **Prefer good names over comments**: Code with semantic naming (`compute_predictor_step()`) and clear structure needs fewer comments
- **Comments only when necessary**: Obscure logic needs explanation; clear code doesn't
- **This incentivizes good coding practices**: Students should write well, not just comment more
- **Example of acceptable minimal comments**:
  ```python
  def time_step(state, forces, dt):
      """Apply one Heun step"""
      k1 = forces(state)
      predict = state + k1 * dt
      k2 = forces(predict)
      return state + 0.5 * (k1 + k2) * dt
  ```
  This needs no inline comments because names and structure are clear.

---

### Criterion 4: Results (20%)

**Purpose**: Student presents results, validates them, and interprets physical meaning.

#### Performance Levels

| Level | Range | Description |
|-------|-------|-------------|
| **Excellent** | 65-100% | Plots present, titled, labeled with units, with legends; Main result clearly stated with units; Precision matches uncertainty (critical standard); Physical interpretation provided: What do numbers mean? Why?; Uncertainty estimated with EXPLAINED source; Validation results clearly shown and discussed; Results connected to original physical question; Error bars on plots where appropriate |
| **Good** | 35-65% | Plots present; mostly clear; Results stated clearly; Reasonable precision; Some interpretation given; Brief uncertainty mention; Validation mentioned; Some connection made |
| **Developing** | 0-35% | Plots missing or indecipherable; Results missing or nonsensical; Precision-uncertainty mismatch present; No interpretation; No uncertainty stated or source missing; No validation shown; No comparison to physical expectations |

#### Red Flags (Significant Deductions)

- Callout boxes from template still present: Major deduction
- **Precision-uncertainty mismatch**: Rate as Developing (not Good)
  - Examples: `420.3847 ± 5 feet` (7 extra digits) or `5.23984726 ± 0.05 s`
  - If >3 extra digits, major deduction or lower criterion rating
- Plot axes missing labels: Deduction per axis
- Units missing throughout: Significant deduction
- No plots when plots are expected: Significant deduction
- Results stated without units: Significant deduction
- Uncertainty stated but source not explained: Significant deduction
- Option-specific results missing (no drag/no-drag for B, no gamma for A): Significant deduction
- Validation not shown: Significant deduction

#### Assessment Guidance

**Excellent indicators**:
- Plots have titles, axis labels with units, legends (multi-line)
- Main result: "`Distance = 420 ± 5 feet`" or equivalent with units and uncertainty
- Uncertainty source explained: "Estimated by comparing to no-drag analytical solution (differs by ~5 feet)"
- Precision matches uncertainty (see critical standards)
- Physical interpretation: "The 10-foot difference from no-drag case represents approximately 2.4% reduction due to air resistance, which aligns with typical baseball drag effects"
- Validation clearly shown:
  - **Option A**: "Energy conservation at midpoint predicts gamma = 1.051; simulation yields 1.052 (0.1% error)"
  - **Option B**: "No-drag case matches analytical solution x = v₀cos(θ)t within 0.5%"
  - **Option C**: Validation approach clearly explained and results shown
- Error bars on plots where uncertainty exists
- Plots referenced in text: "Figure 2 shows..."

**Good indicators**:
- Plots present and mostly clear with labels
- Results stated with units
- Some interpretation provided
- Validation attempted
- Uncertainty optional but if stated, source given

**Developing indicators**:
- Plots missing or unclear
- Precision-uncertainty mismatch
- No interpretation or wrong interpretation
- Uncertainty not explained
- Validation missing
- Units missing or inconsistent

---

### Criterion 5: Conclusion (10%)

**Purpose**: Student brings work together, reflects on learning, and completes academic integrity.

#### Performance Levels

| Level | Range | Description |
|-------|-------|-------------|
| **Excellent** | 65-100% | Present and complete; Final result stated with units and uncertainty; Genuine reflection on what was learned; Clear attributions included (students, resources, AI, faculty); Precision matches uncertainty (consistent with abstract/results); Connection to original question and learning goals clear; Statement about project success: Did it work? How do you know?; What learned about: Heun method, coupled ODEs, validation |
| **Good** | 35-65% | Present and reasonably complete; Final result stated; Brief learning mentioned; Attribution vague or missing; Reasonable precision; Some connection made |
| **Developing** | 0-35% | Missing or severely incomplete; Result not stated; No reflection on learning; No attribution; Precision-uncertainty mismatch; No connection to project goals |

#### Red Flags (Significant Deductions)

- Callout boxes from template still present: Major deduction
- Result not stated or vague: Significant deduction
- Precision-uncertainty mismatch: Rate as Developing
- No attribution: Significant deduction
- Too brief (one phrase instead of paragraph): Minor deduction
- Doesn't reflect on learning: Significant deduction

#### Assessment Guidance

**Excellent indicators**:
- Final result restated: "`Distance = 420 ± 5 feet, estimated accurate to ±5 feet based on comparison to analytical solution`"
- Precision-uncertainty alignment consistent with Abstract/Results
- Learning clearly reflected:
  - "The Heun predictor-corrector method effectively improves accuracy over Euler by averaging slopes..."
  - "Understanding coupled ODE decomposition showed me why we separate position and velocity equations..."
  - "Validating against the no-drag analytical case was critical to verifying correctness..."
- Project success addressed: "The validation showed our code matches the analytical solution within 1%, confirming the Heun implementation was correct"
- Attribution section: "I discussed approach with [name]; used AI for [specific task]; consulted [resource]"
- Tone shows genuine reflection, not just completion

**Good indicators**:
- Final result stated with units
- Some reflection on learning
- Attributions mentioned
- Connection to goals present

**Developing indicators**:
- Result vague or missing
- No learning reflection
- Attributions missing
- Precision-uncertainty mismatch

---

## Criterion Weights

| Criterion | Weight | Developing | Good | Excellent |
|-----------|--------|-----------|------|-----------|
| Abstract & Description | 10% | 0-35% | 35-65% | 65-100% |
| Algorithm & Discussion | 20% | 0-35% | 35-65% | 65-100% |
| Implementation/Code | 40% | 0-35% | 35-65% | 65-100% |
| Results | 20% | 0-35% | 35-65% | 65-100% |
| Conclusion | 10% | 0-35% | 35-65% | 65-100% |
| **TOTAL** | **100%** | | | |

---

## Key Assessment Principles

1. **Correctness first**: Code must implement Heun correctly. Both Good and Excellent require correct implementation.

2. **Verification is demonstration of understanding**: Excellent work shows HOW the student knows code is correct, not just that it ran.

3. **Precision-Uncertainty is conceptual**: Mismatches are not formatting errors—they indicate misunderstanding of uncertainty's meaning.

4. **Uncertainty source is required for Excellent**: Numbers with ±X are only Excellent if they explain where the estimate came from.

5. **Code quality over comments**: Semantic naming + clear structure > poor names + many comments. Incentivize good design.

6. **Context matters for Excellent**: Reader should understand the full problem setup and approach without hunting through code.

7. **Validation is independent verification**: Not just "code runs" but actual comparison to analytical solution, energy conservation, or other physical principle.

8. **Attributions are integrity**: Missing acknowledgments should be noted as academic integrity concern.

---

**Last Updated**: January 2025
**Version**: PH 280 Project 2 (Heun Method) - AI Assessment Edition
