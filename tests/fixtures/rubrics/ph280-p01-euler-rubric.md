# PH 280 - Computational Physics Rubric
## Project 1: The Euler Method

**Course**: PH 280 - Computational Physics
**Assignment**: Project 1: The Euler Method
**Project Type**: Numerical Methods (Parameter Fitting or Open-Ended System)
**Total Points**: 100

---

## Important: Version A vs. Version B

This project has two versions. **Both versions use the same three assessment criteria**, but they're interpreted differently:

### **Version A: Parameter Fitting (Free Fall with Air Resistance)**
- **Methodology**: Finding and justifying the drag coefficient b through systematic exploration
- **Results & Validation**: Showing the simulation matches experimental measurements
- **Communication**: Clear documentation of the fitting process

### **Version B: Open-Ended System (Student-Chosen)**
- **Methodology**: Thoughtfully selecting a system, deriving/understanding its equation, implementing it correctly
- **Results & Validation**: Demonstrating the simulation produces physically reasonable results
- **Communication**: Clear explanation of the system and findings

**Note for graders**: Check the beginning of the student's report for "Version Choice" statement. If it says "Version B," interpret the methodology criterion as evaluating system design and implementation rather than parameter fitting. The validation criteria remain similar (does the simulation work correctly?).

---

## Criterion 1: Methodology & Approach (50%)

Students document their methodology and reasoning clearly.

**For Version A**: Explain how you found the drag coefficient b and justify your choice through systematic exploration.

**For Version B**: Explain your system selection, the governing equation, your implementation choices (parameters, dt), and your validation approach.

Focus is on methodology, reasoning, and systematic thinking rather than finding a "perfect" answer.

### Performance Levels

| Level | Points | Description |
|-------|--------|-------------|
| **Excellent** | 40-50 | Clear methodology, systematic approach to finding b, well-justified choice with evidence |
| **Good** | 28-39 | Reasonable methodology with minor gaps in justification or exploration |
| **Poor** | 0-27 | Unclear approach, insufficient justification, or little evidence of systematic exploration |

### Excellent Indicators
- **Clear methodology**: Student explains step-by-step how they adjusted b and why
- **Systematic exploration**: Evidence of testing multiple b values, not just one guess
- **Well-justified choice**: Final b value is supported by data comparison
- **Understanding demonstrated**: Student shows they understand how b affects the simulation
- **Reproducible process**: Another student could follow their methodology

### Good Indicators
- Methodology is present but could be more detailed
- Some exploration of b values shown
- b value has reasonable justification but could be stronger
- Shows general understanding of the relationship between b and simulation
- Process is mostly clear but has minor gaps

### Poor Indicators
- Methodology is unclear or missing
- Little evidence of exploring different b values
- b value chosen with minimal justification
- Limited understanding of how parameters affect results
- Process cannot be easily followed

### What to Include

**For Version A:**
1. **Initial approach**: How did you start? What was your first guess for b?
2. **Exploration process**: How did you test different values? What b values did you try?
3. **Comparison method**: How did you decide if the simulation matched the data?
4. **Final justification**: Why is your final b value the best choice?
5. **Physical interpretation**: Is this value reasonable? What does it mean physically?

**For Version B:**
1. **System selection**: Why did you choose this system? What makes it interesting?
2. **Equation explanation**: What is the governing differential equation? Where does it come from?
3. **Implementation details**: How did you adapt the Euler code? What parameters did you use? Why those values?
4. **Validation approach**: How did you verify your solution is correct? (analytical solution, physical intuition, known behavior, etc.)
5. **Challenges**: What was tricky about implementing this system?

### Example of Excellent Methodology

**Version A Example:**
> "I started with b = 0.001 kg/m (a rough estimate) and plotted the simulation against the experimental data. The simulation diverged quickly—the drag was too small. I then tried b = 0.005 kg/m, which overestimated drag. By adjusting incrementally (b = 0.002, 0.003, 0.004 kg/m), I found that b = 0.0033 kg/m produced the best agreement. The simulated trajectory closely followed the experimental data points throughout the fall. This value is physically reasonable for a small ball with typical air resistance at these speeds."

**Version B Example:**
> "I chose to study the exponential decay of radioactive elements, modeled by dN/dt = -λN. This is a classic system that demonstrates both the Euler method and real-world applications in nuclear physics. I used N₀ = 1000 atoms and λ = 0.1 per time unit. To validate, I compared the numerical solution to the analytical solution N(t) = N₀·e^(-λt), which showed excellent agreement (error < 1%) across the time range. I tested different dt values (0.01, 0.1, 0.5) and found dt = 0.01 provided good accuracy without excessive computation."

### Keywords
methodology, approach, reasoning, validation, systematic thinking, implementation

### Common Issues

**Version A:**
- **No methodology described** - Student just reports a final b value with no explanation
- **Only one value tested** - Shows b value but doesn't demonstrate exploration
- **Weak justification** - "I chose this b value" without evidence it's better than others
- **Unclear process** - Reader cannot understand how student arrived at answer
- **No physical interpretation** - No discussion of whether answer makes sense

**Version B:**
- **System not explained** - Student doesn't explain why they chose their system
- **Equation missing or unclear** - Differential equation not stated or explained
- **Implementation details sparse** - How the code was adapted is not documented
- **No validation** - Student doesn't verify their solution is correct
- **Unjustified choices** - Parameters or dt chosen without explanation

---

## Criterion 2: Results & Validation (35%)

Students present numerical results clearly and demonstrate that their simulation is correct and produces reasonable results.

**For Version A**: Does the fitted model actually reproduce the experimental data?

**For Version B**: Does the simulation produce physically reasonable results? Can you verify it's correct?

Validation is the core of this criterion—does the simulation work?

### Performance Levels

| Level | Points | Description |
|-------|--------|-------------|
| **Excellent** | 28-35 | Clear results with strong validation showing model matches data well |
| **Good** | 20-27 | Results and validation present but with minor gaps in comparison |
| **Poor** | 0-19 | Results unclear, incomplete, or validation shows poor fit |

### Excellent Indicators
- **Clear presentation**: Final b value stated explicitly with units (e.g., b = 0.0033 kg/m)
- **Direct comparison**: Graph shows both simulated and experimental trajectories clearly
- **Quantitative validation**: Includes measure of fit quality (e.g., "maximum deviation 5 cm", "RMS error 0.08 m/s")
- **Good visual agreement**: When b is correct, simulation and data should track together
- **Discussion of results**: Explains what the fit tells us about air resistance

### Good Indicators
- Results stated but perhaps without units or precision
- Comparison plot present but could be clearer (overlapping lines, poor labels)
- Some quantitative validation (e.g., visual agreement) but incomplete
- Generally good agreement between simulation and data
- Some interpretation of what results mean

### Poor Indicators
- Results unclear or incomplete
- No comparison plot or plots don't show data vs. simulation together
- No quantitative assessment of fit quality
- Simulated and experimental data clearly diverge significantly
- No interpretation of results

### What to Show
Your results section should include:
1. **Final parameter value**: State b explicitly with units
2. **Comparison plot**: Show experimental data points and your simulation trajectory together
3. **Goodness of fit**: Quantify agreement (e.g., max deviation, RMS error, or visual description)
4. **Results table** (optional): Tabulate key values (initial velocity, maximum velocity, final position, etc.)

### Example of Excellent Results

**Version A Example:**
> **Final Parameter: b = 0.0033 kg/m**
>
> The simulation with b = 0.0033 kg/m reproduces the experimental free-fall data with good agreement (Figure 1). The maximum deviation between simulated and experimental position is less than 5 cm throughout the 0.3-second fall. The simulation captures both the initial acceleration and the approach to terminal velocity, validating that our drag model is appropriate.

**Version B Example:**
> **Radioactive Decay Simulation: λ = 0.1, N₀ = 1000**
>
> Figure 2 shows the number of atoms over time computed with the Euler method (blue dots) compared to the analytical solution (red curve). The simulation matches the analytical solution with excellent agreement (maximum error < 1.2%). Our choice of dt = 0.01 provides sufficient accuracy; testing dt = 0.001 showed the results converge, confirming dt = 0.01 is appropriate. The exponential decay pattern is clearly visible and matches the known behavior of radioactive decay.

### Keywords
results, validation, comparison, fit quality, agreement, simulation vs. experiment

### Common Issues
- **No final b value stated** - Results section exists but doesn't state what they found
- **Poor comparison plot** - Shows data OR simulation, not both clearly together
- **No fit validation** - Reports b value but doesn't show it actually fits the data
- **Significant divergence** - Simulation doesn't match experiment (indicates wrong b)
- **Missing quantification** - Says "pretty close" instead of measuring how close

---

## Criterion 3: Scientific Communication (15%)

Writing is clear, concise, and well-organized. Figures are properly labeled and integrated into the narrative. Overall report is easy to read and understand.

### Performance Levels

| Level | Points | Description |
|-------|--------|-------------|
| **Excellent** | 12-15 | Clear writing, well-labeled figures, polished presentation |
| **Good** | 9-11 | Generally clear with minor issues in grammar, labels, or organization |
| **Poor** | 0-8 | Writing unclear, figures poorly labeled or missing, disorganized |

### Excellent Indicators
- **Clear writing**: Sentences are direct and easy to understand
- **Well-organized**: Report flows logically (methods → results → interpretation)
- **Proper figure labels**: Axes labeled with units, clear caption explaining what figure shows
- **Good grammar**: Few spelling or grammatical errors
- **Concise**: Explains concepts without unnecessary verbosity

### Good Indicators
- Generally clear writing with occasional awkward phrasing
- Organization is logical but could be smoother
- Figure labels mostly complete but could be clearer
- Minor grammar/spelling issues that don't impede understanding
- Appropriate level of detail

### Poor Indicators
- Difficult to follow or confusing explanations
- Poorly organized (hard to find key information)
- Figures missing labels or captions
- Numerous grammar/spelling errors
- Too wordy or overly technical

### What to Do
- **Use plain language**: Explain concepts clearly without jargon
- **Label everything**: Every figure needs axis labels with units and a descriptive caption
- **Organize logically**: Abstract → Methods → Results → Conclusion
- **Keep it concise**: Each section should be 1-2 paragraphs for this short project
- **Proofread**: Check grammar and spelling before submitting

### Keywords
writing, organization, clarity, figures, labels, communication

### Common Issues
- **Unlabeled axes**: Figures show data but don't indicate what quantities are plotted
- **Missing captions**: "See Figure 1" but reader doesn't know what Figure 1 shows
- **Vague explanation**: "I adjusted b until it looked right" (be specific)
- **Poor organization**: Key information scattered throughout instead of grouped logically
- **Spelling/grammar issues**: Multiple errors that distract from content

---

---

## Additional Criteria (Not Graded for P01)

The following criteria are important for later projects but are **not assessed for P01** to keep this introductory project focused.

### Code Quality & Documentation

**Note**: For P01, the code is provided to you in the notebook. You do not need to write or modify code. The Euler method implementation is complete and ready to use. You will not be assessed on code quality or documentation.

If you're curious about how the code works, we encourage you to read through it and ask questions in lab, but this is not required for assessment.

### Convergence Analysis

**Note**: For P01, we focus on parameter fitting with a fixed time step (dt). Convergence analysis—studying how results change as dt varies—is an important topic but not required for this introductory project. You can explore it if interested, but it will not affect your grade.

Later projects will focus on convergence behavior in more detail.

---

---

## Grading Scale

Use this table to determine overall performance:

| Total Points | Grade | Interpretation |
|--------------|-------|-----------------|
| 90-100 | A | Excellent work: systematic exploration, validated results, clear communication |
| 80-89 | B | Good work: solid methodology, results match data, minor presentation gaps |
| 70-79 | C | Satisfactory work: basic methodology present, some validation, communication adequate |
| 60-69 | D | Weak work: minimal methodology documented, weak validation, unclear presentation |
| <60 | F | Insufficient work: missing methodology, poor validation, or unclear results |

## Key Evaluation Principles for P01

1. **Process over Perfection**: Value the methodology and reasoning more than finding the "perfect" b value
2. **Validation Matters**: Strong results must include evidence that the model fits the experimental data
3. **Documentation is Critical**: Even an excellent result gets low marks if methodology is not explained
4. **Communication is Essential**: Poor presentation obscures good work; invest in clarity
5. **Proportional Assessment**: Parameter fitting (50%) is weighted more heavily than communication (15%)

## Feedback Guidelines

- **Acknowledge good work first**: "Your systematic approach is excellent... one area for improvement..."
- **Be specific**: Reference figures, values, and specific sections in your feedback
- **Frame as learning**: "Consider including... to demonstrate..." not "You forgot..."
- **Encourage iteration**: Parameter fitting is trial-and-error; reward thoughtful exploration
- **Connect to concepts**: Explain how their work illustrates Euler method principles

---

**Last Updated**: January 11, 2025
**Version**: PH 280 Project 1 Scoped Edition
**Scoped By**: Steve (with Claude)

---

## Summary of Changes from Generic Rubric

This rubric has been **scoped** for P01 to focus on the primary learning objectives:

**What Changed:**
- **Reduced from 4 to 3 assessed criteria** (removed code quality, convergence analysis)
- **Redistributed point weights**: Parameter Fitting & Methodology is now 50% (primary focus)
- **Made project-specific**: Examples, common issues, and standards are tailored to fitting air resistance data
- **Added clarity about non-assessed criteria**: Code and convergence study are explicitly marked "not graded"
- **Emphasized process over answer**: Methodology documentation is weighted higher than getting the "right" b value

**Why This Scoping:**
P01 is an introductory project with limited time (3-5 hours). The focus is on:
1. Learning to apply a numerical method to real data
2. Understanding how parameters affect simulation outcomes
3. Validating results against observations
4. Communicating scientific findings clearly

Code implementation and convergence analysis are important topics that will be emphasized in later projects. For P01, we skip these to reduce cognitive load and maintain focus on parameter fitting fundamentals.
