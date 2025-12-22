# PHYS/MENG 230 - Laboratory Instrumentation
# AI Feedback Guidance - Example

> **IMPORTANT**: This file has TWO parts:
> - **Part I**: General guidance applied to ALL criteria
> - **Part II**: Specific guidance for EACH individual criterion

---

# PART I: GENERAL GUIDANCE

*This section is included in the prompt for EVERY criterion.*

## Course Context

**Course**: PHYS/MENG 230 - Laboratory Instrumentation
**Assignment**: Lab Report
**Type**: Lab

### Learning Objectives

Students are learning to:
- Construct and test electronic circuits using standard lab components
- Apply measurement techniques with oscilloscopes, function generators, and multimeters
- Perform statistical analysis on experimental data (mean, standard deviation, uncertainty)
- Validate circuit operation through quantitative measurements
- Document technical work with schematics, code, and written analysis

### Assignment Overview

In PHYS 230 labs, students build electronic circuits to explore instrumentation concepts ranging from basic amplifiers and filters to microcontroller-based measurement systems. Each lab requires students to design or construct a circuit, document it with a schematic, validate its operation with measurements, perform statistical analysis on data, and draw conclusions about performance. Open-ended projects allow students to demonstrate creativity and originality in their designs.

---

## Feedback Philosophy

### Tone and Style
- **Encouraging**: Emphasize learning and improvement. Frame mistakes as learning opportunities.
- **Specific**: Reference exact figures, sections, equations, or code line numbers.
- **Actionable**: Provide concrete steps students can take to improve.
- **Balanced**: Always identify strengths first before suggesting improvements.
- **Professional**: Use appropriate electrical engineering terminology.

### What Excellent Work Looks Like

In this course, exemplary lab reports demonstrate:
- Clear, professional schematics with all component values and pin numbers labeled
- Quantitative validation of circuit function through measurements with uncertainty
- Statistical analysis of data (mean, standard deviation, error propagation)
- Clean, well-documented code with comments explaining key sections
- Professional graphs with axis labels, units, and descriptive captions
- Thoughtful discussion connecting results to theory and course concepts

### Common Student Challenges

Be particularly attentive to these frequent issues:
- Schematics missing component values, pin numbers, or part numbers
- Results stated without units or uncertainty estimates
- Graphs without axis labels or with incorrect scaling
- Code without comments or documentation
- Statistical exercises incomplete or with calculation errors
- No validation measurements showing circuit actually works
- Conclusions that just repeat results without interpretation

---

## Technical Expectations

### Required Tools/Software
Students are using:
- Quarto/Jupyter notebooks for report generation
- Python with NumPy, Matplotlib, Pandas for data analysis
- Arduino IDE or PlatformIO for microcontroller programming
- Lab equipment: Oscilloscope, function generator, DMM, power supply, breadboard

### Expected Report Structure
The report typically includes:
1. **Abstract** - Brief summary of project, methods, and key results
2. **Introduction/Background** - Context and circuit description
3. **Schematic** - Circuit diagram with all details labeled
4. **Methodology** - How circuit was built and tested
5. **Results** - Data, measurements, graphs, statistical analysis
6. **Discussion** - Interpretation and comparison to theory
7. **Conclusion** - Summary of findings with uncertainty

Note: Structure may vary by lab - focus on completeness, not rigid order.

### Figure and Table Requirements
- **Schematics**: All components labeled with values, pin numbers, IC part numbers
- **Oscilloscope screenshots**: Scale settings visible, cursors showing measurements
- **Graphs**: Axis labels with units, descriptive titles, legend if multiple traces
- **Tables**: Column headers with units, proper significant figures
- **Code**: Syntax highlighting, line numbers for easy reference

### References and Citations
Students should reference:
- Component datasheets (especially for ICs and specialized parts)
- Lab manual for experimental procedures
- Textbook or online resources for theory (when applicable)
- Previous labs if building on earlier work

---

## Feedback Quality Guidelines

### ❌ Avoid Vague Feedback
Bad: "Your circuit schematic needs work."

### ✅ Provide Specific, Actionable Feedback
Good: "In Figure 2, the schematic is missing several critical details. Add: (1) values for R1 and R2, (2) pin numbers for the op-amp, (3) the op-amp part number (e.g., LM324), and (4) power supply connections (+12V, -12V, GND)."

### Reference Specific Evidence
Always point to:
- Figure numbers (e.g., "Figure 3 shows...")
- Section headings (e.g., "In your Results section...")
- Equation numbers (e.g., "Equation 2 correctly shows...")
- Code line numbers (e.g., "Line 45 in your Arduino code...")
- Table rows/columns (e.g., "Table 1, column 3 lacks units...")

---

# PART II: CRITERION-SPECIFIC GUIDANCE

*Each section below is extracted and used ONLY when evaluating that specific criterion.*

---

## CRITERION: Abstract & Description

### What to Evaluate

Focus on:
- Does the abstract clearly state what the project is about?
- Are the key results quantified with precision/uncertainty?
- Is the significance or purpose of the project explained?
- Is it concise (1 paragraph) yet complete?

### Excellence Indicators (High Scores)

Award 7-10 points when:
- Project idea stated in one clear, specific sentence
- Results include numerical values with units and uncertainty (e.g., "gain = 24.3 ± 0.5 dB")
- Significance connects to course concepts or real-world applications
- Abstract is self-contained (reader understands project without reading full report)

### Common Mistakes (Point Deductions)

Watch for:
- **Vague project description** (e.g., "built a circuit") - deduct 1-2 points
  - Should specify: "built a two-stage op-amp amplifier with 40 dB gain"
- **Results without precision** (e.g., "gain was about 24") - deduct 1-2 points
  - Should be: "gain = 24.3 ± 0.5 dB"
- **Missing significance** - deduct 1-2 points
  - Should explain why this matters or what it demonstrates
- **Too detailed** (more than 150 words) - deduct 0-1 points

### Red Flags (Unsatisfactory Work)

Award 0-3 points if:
- Abstract missing entirely
- Project idea completely unclear
- No results stated at all
- Abstract is just one vague sentence

### Feedback Suggestions

**If missing precision**: "In your abstract, you state 'the amplifier worked well.' Quantify this with your measured gain: 'The amplifier achieved a gain of 24.3 ± 0.5 dB at 1 kHz, meeting the design specification of 24 dB.'"

**If missing significance**: "Add one sentence explaining why this project matters. For example: 'This demonstrates key instrumentation amplifier principles used in biomedical sensors and data acquisition systems.'"

**If too vague**: "Instead of 'We built a circuit,' be specific: 'We designed and tested a Sallen-Key low-pass filter with a cutoff frequency of 1.0 kHz.'"

### Example Comparison

**❌ Unsatisfactory (3/10)**:
> "For this lab we built a circuit with an op amp. It worked and we got some data."

**✅ Excellent (9/10)**:
> "We designed and validated a two-stage instrumentation amplifier using LM324 op-amps to amplify low-level sensor signals. The circuit achieved a gain of 48.2 ± 1.1 dB with a bandwidth of 2.4 kHz, suitable for biomedical signal processing applications. Statistical analysis showed excellent noise performance with SNR > 40 dB."

---

## CRITERION: Circuit Schematic, Background and Discussion

### What to Evaluate

Focus on:
- Is a complete, readable schematic provided?
- Are all component values, pin numbers, and part numbers labeled?
- Is there background explaining how the circuit works?
- For open-ended projects, is there originality and creativity?

### Excellence Indicators (High Scores)

Award 13-20 points when:
- Schematic is professional-quality with ALL components labeled (values, pins, part numbers)
- Power supply connections shown (VCC, GND, VEE)
- Circuit operation explained clearly with reference to schematic
- Open-ended projects show genuine creativity and novelty
- Discussion references relevant theory or course concepts

### Common Mistakes (Point Deductions)

Watch for:
- **Missing component values** - deduct 2-3 points per critical component
  - "R1 = ?" should be "R1 = 10kΩ"
- **No pin numbers on ICs** - deduct 2-3 points
  - Op-amp should show pins 2, 3, 6, 7, 4, etc.
- **Missing part numbers** - deduct 1-2 points
  - "Op-amp" should be "LM324" or "TL074"
- **No explanation of circuit operation** - deduct 3-5 points
- **Poor schematic quality** (hand-drawn, illegible) - deduct 2-4 points
- **Missing power connections** - deduct 1-2 points

### Red Flags (Unsatisfactory Work)

Award 0-6 points if:
- No schematic provided at all
- Schematic completely illegible or wrong
- Critical components missing from schematic
- No discussion of how circuit works
- Open-ended project copied from tutorial without modification

### Feedback Suggestions

**If missing labels**: "In Figure 1, add component values to your schematic. Label R1, R2, R3 with their ohm values (e.g., '10kΩ'), and add C1 capacitance (e.g., '100nF'). Also add the op-amp part number (LM324 or TL074)."

**If missing explanation**: "Add a paragraph explaining how your circuit works. Describe the signal path: input → inverting amplifier stage (U1A) with gain = -R2/R1 → output buffer (U1B) → load. Reference the component labels in your schematic."

**If schematic quality poor**: "Consider using a schematic capture tool like KiCad, CircuitLab, or even draw.io to create a cleaner schematic. Alternatively, use a ruler for straight lines and ensure component labels are readable."

### Example Comparison

**❌ Poor (4/20)**:
Hand-drawn schematic with unlabeled resistors, no op-amp pins shown, no explanation.

**✅ Excellent (18/20)**:
Professional schematic created in KiCad showing LM324 quad op-amp with all pin numbers (2,3,6 for first stage; 5,6,7 for second stage), power connections (V+ to pin 4, V- to pin 11), all resistor values labeled (R1=1kΩ, R2=10kΩ, etc.), and detailed paragraph explaining the two-stage design with gain calculations.

---

## CRITERION: Circuit Function

### What to Evaluate

Focus on:
- Was the circuit physically constructed (photos as evidence)?
- Does the circuit work correctly (validated by measurements)?
- Is the schematic/code clean and well-documented?
- Are there quantitative measurements proving functionality?
- Is statistical analysis used to validate operation?

### Excellence Indicators (High Scores)

Award 26-40 points when:
- Clear photos show professional circuit construction on breadboard/PCB
- Circuit functions perfectly as designed
- Quantitative measurements validate all key specifications (gain, frequency response, etc.)
- Statistical analysis (mean, std dev) applied to repeated measurements
- Code is beautifully formatted with meaningful comments
- Schematic matches constructed circuit exactly
- All functionality claims backed by data

### Common Mistakes (Point Deductions)

Watch for:
- **No photos of physical circuit** - deduct 3-5 points
- **Circuit built but not tested** - deduct 5-8 points
- **Code with no comments** - deduct 3-5 points
- **Functionality claims without supporting measurements** - deduct 5-7 points
- **No statistical analysis** - deduct 3-5 points
- **Circuit partially working** - deduct based on severity (2-10 points)
- **Messy construction (shorts, poor wiring)** - deduct 2-4 points

### Red Flags (Unsatisfactory Work)

Award 0-13 points if:
- Circuit not constructed at all
- Circuit built but completely non-functional
- No attempt to test or validate operation
- No schematic or code provided
- Schematic/code incomprehensible

### Feedback Suggestions

**If no photos**: "Include photos of your physical circuit showing component placement and wiring. Label key components (U1, R1, etc.) to match your schematic. Close-up views of connections are helpful."

**If no validation measurements**: "Add oscilloscope screenshots or multimeter readings proving your circuit works. For an amplifier, show: (1) input sine wave, (2) amplified output, (3) calculated gain = Vout/Vin. Repeat measurements 5-10 times and report mean ± std dev."

**If code lacks comments**: "Add comments to your Arduino code explaining each section. Example:
```cpp
// Initialize ADC for 10-bit resolution
analogReadResolution(10);

// Main sampling loop - acquire 100 samples
for (int i = 0; i < 100; i++) {
  // Read sensor on A0 and convert to voltage
  int rawValue = analogRead(A0);
  float voltage = rawValue * (5.0 / 1023.0);
}
```"

**If missing statistics**: "Perform statistical analysis on your gain measurements. Take 10 measurements of Vin and Vout, calculate gain for each (Gain_i = Vout_i / Vin_i), then report: mean gain ± standard deviation. This validates repeatability."

### Example Comparison

**❌ Poor (8/40)**:
"We built the circuit and it worked." No photos, no measurements, no code shown.

**✅ Excellent (38/40)**:
Photos show neat breadboard construction with labeled components. Oscilloscope screenshots show input (100 mV, 1 kHz) and output (2.43 V, 1 kHz) signals. Calculated gain = 2.43/0.10 = 24.3. Repeated measurement 10 times: mean gain = 24.3 ± 0.5 (std dev). Arduino code beautifully commented with clear variable names. Circuit meets all design specifications with statistical validation.

---

## CRITERION: Results (including stats exercises)

### What to Evaluate

Focus on:
- Are results complete and clearly presented?
- Do all quantities have correct units?
- Are graphs clear with proper axis labels and units?
- Are formulas shown where calculations were performed?
- Are all statistical exercises completed correctly?
- Is there valid interpretation showing understanding?

### Excellence Indicators (High Scores)

Award 13-20 points when:
- All results presented in well-formatted tables or graphs
- Every quantity has correct units (V, mA, kHz, dB, etc.)
- Graphs have labeled axes with units, titles, and legends
- Formulas shown for key calculations (gain, uncertainty, etc.)
- All statistical exercises (mean, std dev, propagation) correct
- Interpretation demonstrates deep understanding of physics/electronics
- Results compared to theoretical predictions with % error analysis

### Common Mistakes (Point Deductions)

Watch for:
- **Missing units** - deduct 1 point per instance (max 3 points)
- **Unlabeled graph axes** - deduct 2-3 points per graph
- **No formulas shown** - deduct 1-2 points
- **Statistical exercises incomplete** - deduct 2-5 points per missing/wrong calculation
- **No interpretation** - deduct 3-5 points
- **Results stated but not discussed** - deduct 2-4 points
- **Graphs present but not referenced in text** - deduct 1-2 points

### Red Flags (Unsatisfactory Work)

Award 0-6 points if:
- Results completely missing or seriously incomplete
- No graphs or indecipherable graphs
- Units wrong or missing throughout
- No statistical exercises attempted
- No interpretation or completely wrong interpretation

### Feedback Suggestions

**If missing units**: "In Table 1, add units to all columns. For example: 'Voltage (V)', 'Current (mA)', 'Power (mW)'. Also, in your text, write 'the gain was 24.3 dB' not just '24.3'."

**If unlabeled axes**: "Add axis labels to Figure 4. The x-axis should be 'Frequency (Hz)' and the y-axis should be 'Gain (dB)'. Also add a title: 'Frequency Response of Two-Stage Amplifier'."

**If no formulas**: "Show your calculation for gain. For example:
$$A_v = \\frac{V_{out}}{V_{in}} = \\frac{2.43\\text{ V}}{0.10\\text{ V}} = 24.3$$
Or in dB:
$$A_v(dB) = 20\\log_{10}(24.3) = 27.7\\text{ dB}$$"

**If stats incomplete**: "Complete all statistical exercises:
1. Calculate mean and standard deviation of your 10 gain measurements
2. Propagate uncertainty using: δA_v = A_v × √[(δVout/Vout)² + (δVin/Vin)²]
3. Report final result as: Gain = 24.3 ± 0.8 (mean ± std dev)"

**If no interpretation**: "After presenting your results, interpret them. Example: 'The measured gain of 24.3 dB is 3.6% higher than the theoretical value of 23.5 dB calculated from the resistor ratio. This discrepancy is likely due to resistor tolerances (±5%) and is within expected uncertainty.'"

### Example Comparison

**❌ Poor (3/20)**:
Results stated as numbers without units. Graph has no axis labels. No statistical analysis. No interpretation.

**✅ Excellent (19/20)**:
Table 1 shows 10 measurements with units (Vin in mV, Vout in V, Gain in dB). Figure 3 is a properly labeled frequency response plot (Frequency (Hz) vs Gain (dB)) with grid lines and legend. Mean gain = 24.3 ± 0.5 dB (n=10). Formula shown for gain calculation and uncertainty propagation. Interpretation compares measured vs theoretical (24.3 vs 23.5 dB = 3.4% error) and explains discrepancy due to resistor tolerances.

---

## CRITERION: Conclusion

### What to Evaluate

Focus on:
- Is a conclusion present and reasonably complete?
- Is the final result stated clearly with units?
- Are uncertainty estimates included?
- Does it connect back to the project objectives?
- Is there reflection on what was learned?

### Excellence Indicators (High Scores)

Award 7-10 points when:
- Conclusion clearly summarizes the project and key findings
- Final result stated with numerical value, units, and uncertainty
- Results explicitly connected to initial objectives or design specs
- Reflection on learning or future improvements included
- Concise but complete (1-2 paragraphs)

### Common Mistakes (Point Deductions)

Watch for:
- **Just repeating results without synthesis** - deduct 1-2 points
- **No uncertainty mentioned** - deduct 1-2 points
- **Missing connection to objectives** - deduct 1-2 points
- **Extremely brief (1-2 sentences)** - deduct 2-3 points
- **No reflection on learning** - deduct 1 point

### Red Flags (Unsatisfactory Work)

Award 0-3 points if:
- Conclusion completely missing
- Conclusion is one vague sentence
- No final result stated
- No connection to project purpose

### Feedback Suggestions

**If just repeating results**: "Instead of just listing results again, synthesize them. Example: 'This project successfully demonstrated the design and validation of a two-stage op-amp amplifier. The measured gain of 24.3 ± 0.5 dB met the target specification of 24 dB, validating our design approach.'"

**If missing uncertainty**: "Include your uncertainty estimate in the conclusion. State: 'The final measured gain was 24.3 ± 0.5 dB (mean ± std dev, n=10)' rather than just '24.3 dB'."

**If not connected to objectives**: "Relate your conclusion back to the lab objectives. Example: 'This lab demonstrated key concepts in op-amp circuit design, statistical analysis of measurements, and validation of theoretical predictions through experimentation.'"

**If too brief**: "Expand your conclusion to 1-2 paragraphs. Include: (1) brief summary of what you did, (2) key results with uncertainty, (3) how results relate to objectives, (4) reflection on what you learned or would improve."

### Example Comparison

**❌ Poor (2/10)**:
"The amplifier worked and we got a gain of 24."

**✅ Excellent (9/10)**:
"This project successfully demonstrated the design, construction, and validation of a two-stage non-inverting op-amp amplifier using the LM324 quad op-amp. The measured voltage gain of 24.3 ± 0.5 dB (mean ± std dev, n=10 measurements) matched the design target of 24 dB within experimental uncertainty. Statistical analysis showed excellent repeatability with a relative uncertainty of 2.1%. This lab reinforced important concepts including op-amp circuit analysis, statistical treatment of experimental data, and the importance of uncertainty quantification in instrumentation. Future improvements could include implementing a variable gain stage and extending the frequency response analysis to higher frequencies."

---

# CUSTOMIZATION CHECKLIST

- [x] Course context filled in (PHYS/MENG 230)
- [x] Assignment overview describes typical lab structure
- [x] Learning objectives match course goals
- [x] Common challenges reflect actual student issues
- [x] Tools list matches what students use
- [x] All 5 criteria have specific guidance sections
- [x] Criterion names exactly match rubric.yml
- [x] Specific examples provided for each criterion
- [x] Scoring guidance reflects rubric point ranges

---

# USAGE NOTES

This guidance file is designed for PHYS 230 Laboratory Instrumentation. The system will:
1. Include all of "Part I: General Guidance" in every criterion evaluation
2. Extract the specific criterion section when evaluating that criterion
3. Combine general + specific guidance for focused, targeted feedback

Criterion sections are matched by exact name (e.g., "Abstract & Description" in rubric.yml → "## CRITERION: Abstract & Description" in this file).
