# PHYS 230 P3: BJT and Op-Amp Amplifier — Grading Guidance

## Assignment Overview

Students performed two experiments:

1. **BJT current gain measurement** — Drove a BJT base through a ~10kΩ resistor using a
   DAC. Monitored voltages at both ends of the base resistor to compute Ib (via Ohm's law)
   and the collector voltage (collector resistor ~100Ω, other end tied to 3.3V, so
   Ic = (3.3V − Vc) / 100Ω). Swept the DAC across multiple values and fit a line to
   Ic vs Ib to extract β = Ic/Ib.

2. **Op-amp non-inverting amplifier** — Built a simple non-inverting amplifier with
   gain = 2. Validated with an oscilloscope showing input and output signals.

These are **introductory students**. Apply the rubric generously — if a student made a
genuine effort, give them the benefit of the doubt. Focus on whether the key evidence is
present, not on polish or perfect terminology.

---

## What to Look For, Row by Row

### Abstract & Description
- Do they name both experiments?
- Is β stated as a numerical result (even approximately, even without uncertainty)?
- Is there a sentence on why the experiments matter?

### Circuit Schematic, Background and Discussion
- Is there a schematic or clear diagram/photo for the BJT circuit?
- Is there a schematic or clear diagram/photo for the op-amp circuit?
- Are component values (10kΩ base resistor, 100Ω collector resistor, op-amp resistors)
  mentioned anywhere in the report — even in prose, not necessarily on the schematic?

### Circuit Function
- **BJT**: Is there a plot or data table from a DAC sweep showing Ib and Ic values
  at multiple operating points? Does it look like the circuit actually produced sensible data?
- **Op-amp**: Is there a scope screenshot or trace showing the input signal and a larger
  output signal?

### Results (including stats exercises)
- **BJT fit**: Did they exclude data clearly outside the linear regime (e.g., where Vc
  is at the ADC upper limit, or where the transistor is in saturation)? Is a fit line
  plotted over the data? Does the data align reasonably well with the fit?
- **Op-amp**: Does the report confirm that the measured gain matches the expected value
  of 2? Even a brief sentence noting agreement is sufficient.
- **Exercise 1 (Bayesian dice)**: Posterior probabilities reported after observing 1, 4, 2, 5?
- **Exercise 2 (Exponential distribution)**: Probability of a defect between t=4.5 and
  t=5.5 min computed and justified?
- **Exercise 3 (curve_fit)**: β ± δβ extracted using `curve_fit` and compared to the
  slope from the linear fit?

For **Excellent** on Results: need excellent BJT analysis + op-amp gain confirmed +
all three exercises seriously attempted.
For **Good**: BJT fit present but imperfect, op-amp gain confirmed, or one exercise missing.
For **Poor**: No fit, no op-amp validation, exercises absent.

### Conclusion
- Is β stated (any numerical value)?
- Is the op-amp result mentioned?
- Is there any reflection on what was learned or how things could be improved?

---

## Level Definitions

**Excellent** — The key evidence is clearly present and correct. Student demonstrates
understanding of what they measured and why.

**Good** — A genuine effort was made. Something is missing or imperfect, but the core
work is there.

**Poor** — A required element is absent entirely, or the work is so incomplete that it
does not demonstrate the student engaged with this part of the assignment.

Return `overall_assessment` as exactly one of: `Excellent`, `Good`, `Poor`.
