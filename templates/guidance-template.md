# AI Feedback Guidance Template

> **IMPORTANT**: This file has TWO parts:
> - **Part I**: General guidance applied to ALL criteria
> - **Part II**: Specific guidance for EACH individual criterion
>
> The system will extract the appropriate guidance for each criterion automatically.

---

# PART I: GENERAL GUIDANCE

*This section is included in the prompt for EVERY criterion.*

## Course Context

**Course**: [Course Code and Name, e.g., "EENG 320 - Analog Circuit Design"]
**Assignment**: [Assignment Name/Number, e.g., "Lab 3: BJT Amplifier Design"]
**Type**: [Lab/Project/Assignment]

### Learning Objectives

Students are learning to:
- [Learning objective 1, e.g., "Design and analyze BJT amplifier circuits"]
- [Learning objective 2, e.g., "Use SPICE simulation tools"]
- [Learning objective 3, e.g., "Validate designs through experimental testing"]

### Assignment Overview

[1-2 paragraphs explaining what students are doing in this assignment]

Example:
> In this lab, students design a common-emitter BJT amplifier to meet specific gain and bandwidth requirements. They begin with SPICE simulations to predict performance, build the physical circuit, and measure actual performance. The goal is to understand the design process and the relationship between theory, simulation, and reality.

---

## Feedback Philosophy

### Tone and Style
- **Encouraging**: Frame feedback as growth opportunities. This is a learning process.
- **Specific**: Reference exact sections, figures, equations, or code lines.
- **Actionable**: Provide concrete, implementable suggestions.
- **Balanced**: Always acknowledge strengths before discussing improvements.
- **Professional**: Use appropriate technical terminology for the course level.

### What Excellent Work Looks Like

In this assignment, exemplary work demonstrates:
- [Characteristic 1, e.g., "Clear justification for component choices with calculations"]
- [Characteristic 2, e.g., "Properly labeled simulation results with correct units"]
- [Characteristic 3, e.g., "Thoughtful analysis of discrepancies between theory and experiment"]

### Common Student Challenges

Be particularly attentive to these common issues:
- [Challenge 1, e.g., "Forgetting to account for loading effects in multi-stage designs"]
- [Challenge 2, e.g., "Unlabeled or improperly scaled simulation plots"]
- [Challenge 3, e.g., "Measurements without uncertainty estimates"]

---

## Technical Expectations

### Required Tools/Software
Students are using:
- [Tool 1, e.g., "LTspice XVII for circuit simulation"]
- [Tool 2, e.g., "Quarto/Jupyter for report generation"]
- [Tool 3, e.g., "Lab equipment: Oscilloscope, function generator, DMM"]

### Expected Report Structure
The report should include:
1. [Section 1, e.g., "Introduction - Problem statement and specifications"]
2. [Section 2, e.g., "Design - Schematic and component selection"]
3. [Section 3, e.g., "Simulation - Predicted performance"]
4. [Section 4, e.g., "Experimental Results - Measured performance"]
5. [Section 5, e.g., "Analysis - Comparison and discussion"]

Note: Students may organize differently - focus on content completeness, not rigid structure.

### Figure and Table Requirements
- **All figures must have**: Descriptive captions, axis labels with units, readable text
- **All tables must have**: Column headers, units in headers or cells, clear organization
- **Code/calculations**: Should be reproducible with clear variable definitions

### References and Citations
Students should reference:
- [Source 1, e.g., "Component datasheets for all ICs"]
- [Source 2, e.g., "Textbook: Sedra & Smith Chapter 6"]
- [Source 3, e.g., "Lab manual for experimental procedures"]

---

## Feedback Quality Guidelines

### ❌ Avoid Vague Feedback
Bad example: "Your analysis needs improvement."

### ✅ Provide Specific, Actionable Feedback
Good example:
> "In Section 4.2, your gain measurement is reported as '15', but the units are unclear. Since this is voltage gain, specify 'Av = 15 V/V' or '23.5 dB'. Also, add ±0.5 dB measurement uncertainty based on your oscilloscope's accuracy."

### Reference Specific Evidence
Always point to:
- Section numbers or headings
- Figure/table numbers
- Equation numbers
- Line numbers (for code)
- Page numbers (for long reports)

---

# PART II: CRITERION-SPECIFIC GUIDANCE

*Each section below is extracted and used ONLY when evaluating that specific criterion.*
*The section heading MUST match the criterion name EXACTLY as it appears in the rubric.*

---

## CRITERION: [Exact Criterion Name from Rubric]

### What to Evaluate

Focus on:
- [Specific aspect 1 to check for this criterion]
- [Specific aspect 2 to check for this criterion]
- [Specific aspect 3 to check for this criterion]

### Excellence Indicators (High Scores)

Award high scores when you see:
- [Indicator 1, e.g., "Component values clearly justified with calculations"]
- [Indicator 2, e.g., "Trade-offs explicitly discussed"]
- [Indicator 3, e.g., "Design meets all specifications with margin"]

### Common Mistakes (Point Deductions)

Watch for:
- [Mistake 1, e.g., "Missing biasing calculations - deduct 2-3 points"]
- [Mistake 2, e.g., "Component values given without justification - deduct 1-2 points"]
- [Mistake 3, e.g., "Design doesn't meet specifications - deduct 3-5 points"]

### Red Flags (Unsatisfactory Work)

These indicate serious issues:
- [Red flag 1, e.g., "No schematic provided"]
- [Red flag 2, e.g., "Circuit cannot possibly work (fundamental errors)"]
- [Red flag 3, e.g., "Plagiarized design from online source"]

### Feedback Suggestions

When you observe [specific situation], suggest:
- **If missing calculations**: "Add the biasing calculations showing how you selected R1, R2, and RE. Start with the desired IC (e.g., 2mA), then calculate VB, VE, and resistor values using Ohm's law."
- **If poorly labeled figures**: "Add axis labels with units to Figure 3. For example: 'Frequency (Hz)' on x-axis and 'Gain (dB)' on y-axis."
- **If [condition]**: "[Specific actionable suggestion]"

### Example Comparison

**❌ Unsatisfactory**:
> [Brief example or description of poor work for this criterion]

**✅ Excellent**:
> [Brief example or description of exemplary work for this criterion]

---

## CRITERION: [Second Criterion Name]

### What to Evaluate

Focus on:
- [Specific aspect 1]
- [Specific aspect 2]
- [Specific aspect 3]

### Excellence Indicators

Award high scores when:
- [Indicator 1]
- [Indicator 2]

### Common Mistakes

Watch for:
- [Mistake 1 - severity/points]
- [Mistake 2 - severity/points]

### Red Flags

Critical issues:
- [Red flag 1]
- [Red flag 2]

### Feedback Suggestions

Condition-based suggestions:
- **If [condition]**: "[Specific feedback]"
- **If [condition]**: "[Specific feedback]"

### Example Comparison

**❌ Unsatisfactory**: [Example]
**✅ Excellent**: [Example]

---

## CRITERION: [Third Criterion Name]

[Repeat structure for each criterion in your rubric...]

---

## CRITERION: [Continue for ALL criteria...]

---

# CUSTOMIZATION CHECKLIST

Before using this guidance file:

- [ ] Fill in course context (course code, assignment name, learning objectives)
- [ ] Update "What Excellent Work Looks Like" with assignment-specific characteristics
- [ ] List common student challenges you've observed
- [ ] Specify exact tools/software students are using
- [ ] Define expected report sections
- [ ] Add criterion-specific sections for EVERY criterion in your rubric
- [ ] Ensure criterion names EXACTLY match your rubric.yml file
- [ ] Include specific examples of good vs. poor work for key criteria
- [ ] Add any domain-specific technical considerations
- [ ] Review and adjust tone for student level (freshman/senior/graduate)

---

# USAGE NOTES

## How the System Uses This File

1. **Part I (General Guidance)** is included in EVERY criterion evaluation
2. **Part II sections** are matched by criterion name:
   - If criterion is "Circuit Design", system extracts "## CRITERION: Circuit Design"
   - General guidance + specific guidance = complete prompt for that criterion

## Naming Convention

- Criterion sections MUST start with `## CRITERION:` (case-sensitive)
- The name after the colon must EXACTLY match the criterion name in rubric.yml
- Example: If rubric has `name: "Abstract & Description"`, use `## CRITERION: Abstract & Description`

## Tips for Writing Good Guidance

1. **Be specific**: "Check for axis labels" > "Good figures"
2. **Provide examples**: Show what good/bad looks like
3. **Set scoring thresholds**: "Missing X = -2 points"
4. **Give conditional feedback**: "If Y, then suggest Z"
5. **Reference resources**: Point to textbook sections, datasheets, etc.

---

# EXAMPLES

See `examples/` directory for complete guidance files from:
- EENG-320 (Electronics Lab)
- PHYS-280 (Scientific Computing)
- PHYS-230 (Instrumentation Lab)
- EENG-340 (Interfacing Project)
