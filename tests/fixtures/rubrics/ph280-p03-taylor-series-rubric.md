# PH 280 Project 3: Taylor Series Approximations - Grading Rubric

**Course**: PH 280 - Computational Physics
**Assignment**: Project 3: Taylor Series Approximations
**Focus**: First experience with Taylor series and their applications
**Total**: 100%

---

## Criterion 1: Abstract & Description (10%)

Clear explanation of what you're approximating, why it matters, and what you found.

### Performance Levels

| Level | Percentage | Description |
|-------|-----------|-------------|
| **Excellent** | 9-10% | Abstract is clear and concise. What you're approximating is stated. Why the approximation is useful is explained. Your main result is stated clearly. Description explains the significance of the project. |
| **Good** | 6-8% | Abstract is present and has some merit. The problem is stated and result mentioned. Description gives some idea of significance. |
| **Poor** | 0-5% | Abstract missing or lacks substantial merit. Problem not clearly stated. Result not stated. Description missing or doesn't convey significance. |

### What We're Looking For
- Clear statement of what function/system you're approximating
- Explanation of why using a Taylor series approximation is useful
- Your main result clearly stated
- Some sense of whether the approximation worked

---

## Criterion 2: Algorithm & Discussion (20%)

Clear explanation of how Taylor series work mathematically and how you applied them to your problem.

### Performance Levels

| Level | Percentage | Description |
|-------|-----------|-------------|
| **Excellent** | 18-20% | All important details of the algorithm are described. Presentation is perfectly clear and completely correct. Explains why more terms improve accuracy and how you applied this to your problem. |
| **Good** | 12-17% | Most important details are described and mostly clear and correct. Your approach is described but some details could be clearer. |
| **Poor** | 0-11% | Important details missing or incorrect. Algorithm explanation is vague or superficial. Your approach is unclear. |

### What We're Looking For
- **Conceptual understanding**: What is a Taylor series and why does it approximate a function?
- **Why it works**: Why does accuracy improve with more terms? What limits it?
- **Your approach**: How did you implement this for your specific problem?
- **Mathematical clarity**: Equations shown where appropriate

---

## Criterion 3: Implementation/Code (40%)

Code that works correctly, is well-documented, and demonstrates that you verified it's working.

### Performance Levels

| Level | Percentage | Description |
|-------|-----------|-------------|
| **Excellent** | 36-40% | Code is complete and functions flawlessly. Easy to read and understand with sufficient documentation. Correctness is validated using a special case, known analytical result, or comparison to a library function. |
| **Good** | 24-35% | Code is all there and functions almost perfectly. Fairly easy to read and understand. Some documentation embedded in the code. At least some attempt to validate correct operation. |
| **Poor** | 0-23% | Code is missing, not functional, or hard to follow. Nothing done to demonstrate code operates correctly. Minimal or no documentation. |

### What We're Looking For
- **Correctness**: Code computes the Taylor series accurately
- **Clarity**: Variable names make sense; logic is easy to follow
- **Documentation**: Comments explain what each section does
- **Validation**: You checked your code against something you know (compare to numpy.sin(), test with x=0, compare to analytical solution)

---

## Criterion 4: Results (20%)

Complete results showing your approximation works, with clear visualization and interpretation.

### Performance Levels

| Level | Percentage | Description |
|-------|-----------|-------------|
| **Excellent** | 18-20% | Results are complete and clearly presented. Plots show approximation vs exact solution with at least 2-3 different numbers of terms. Units clearly given and correct. Interpretation shows understanding of the system and technique. Axes labeled with formulas where appropriate. |
| **Good** | 12-17% | Results present and mostly complete. Units clearly given. Reasonable interpretation shown. Plots fairly clear, mostly understandable. |
| **Poor** | 0-11% | Results missing or seriously incomplete. No interpretation or invalid interpretation. Plots missing, unclear, or indecipherable. Units incorrect or missing. |

### What We're Looking For
- **Completeness**: Results for your chosen problem are shown
- **Comparison**: Plot showing approximation compared to exact solution
- **Quality indicators**: Results show how approximation improves (more terms, closer to expansion point)
- **Clarity**: Plots have labeled axes, titles, legends; units are correct
- **Interpretation**: You discuss what the results mean and how accurate the approximation is

---

## Criterion 5: Conclusion (10%)

Brief summary of your project with final result and some estimate of accuracy or uncertainty.

### Performance Levels

| Level | Percentage | Description |
|-------|-----------|-------------|
| **Excellent** | 9-10% | Conclusion is clear and complete. Final result stated clearly with some estimate of uncertainty or accuracy (e.g., "accurate to within 0.01" or "±5% error"). |
| **Good** | 6-8% | Conclusion is present and reasonably complete. Final result is stated clearly. Some indication of accuracy or success provided. |
| **Poor** | 0-5% | Conclusion is missing or seriously incomplete. Final result not clearly stated. No indication of uncertainty or accuracy. |

### What We're Looking For
- **Final result**: What did you approximate and how well did it work?
- **Uncertainty/accuracy**: Estimate of how good the approximation is (e.g., "maximum error was 0.005", "accurate to within ±2% for |x-x₀| < 1")
- **Validity**: Some discussion of when the approximation works and where it fails
- **Brevity**: 2-3 sentences; no need to repeat the report

---

## How to Succeed

1. **Choose an interesting function** to approximate (sin, cos, exp, or something else)
2. **Explain why** the approximation matters
3. **Write clear code** that implements the Taylor series with comments and validation
4. **Validate against something you know** (library function, analytical solution, special cases)
5. **Create plots** showing how approximation improves with more terms
6. **Estimate accuracy** - describe how good your approximation is and where it fails
7. **Explain what you learned** about why Taylor series work and when they're useful

---

## Grading Scale

| Total | Grade | Interpretation |
|-------|-------|-----------------|
| 90-100% | A | Excellent understanding and execution |
| 80-89% | B | Good work with minor gaps |
| 70-79% | C | Satisfactory work; shows basic understanding |
| 60-69% | D | Weak work but shows some effort |
| <60% | F | Insufficient work or major conceptual gaps |

---

## Key Principles

- **Validate your results**: Show that your code actually works (comparison to known answer)
- **Estimate accuracy**: Describe how good your approximation is and when it breaks down
- **Show your work**: Comments in code and explanations in report help us understand your thinking
- **Make it visual**: A good plot demonstrates that your approximation works
- **Focus on understanding**: We want to see that you *get* why Taylor series are useful
- **Celebrate the practical**: The goal is to understand Taylor series as a problem-solving tool

---

**Last Updated**: January 2026
**Version**: First Experience with Taylor Series
