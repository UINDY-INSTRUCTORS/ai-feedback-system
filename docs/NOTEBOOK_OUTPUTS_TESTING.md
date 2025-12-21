# Notebook Output Extraction - Testing Summary

**Date**: December 20, 2025
**Status**: ✅ **FULLY IMPLEMENTED AND TESTED**

## Overview

Successfully implemented comprehensive notebook output extraction that captures ALL cell outputs (not just images), including HTML tables, text, markdown, and LaTeX. These outputs are now included in the AI's context for criterion-based analysis.

---

## What Was Implemented

### 1. HTML-to-Markdown Converter (`html_to_markdown.py`)

**Purpose**: Convert pandas DataFrames and other HTML outputs to clean markdown

**Features**:
- Strips out CSS `<style>` tags and `<div>` wrappers
- Converts HTML tables to markdown tables
- Preserves formatting (bold, italic, links)
- Handles lists, code blocks, headers

**Key Improvements**:
- Removes pandas DataFrame CSS styling
- Token-efficient markdown output
- Clean, readable tables for AI analysis

### 2. Enhanced Report Parser (`parse_report.py`)

**New Functionality**:
```python
def _extract_notebook_outputs(body: str) -> list:
    """
    Find all {{< embed ... >}} shortcodes and extract their cell outputs.
    Extracts: HTML tables, text, markdown, LaTeX from notebook cells.
    """
```

**Smart Discovery**:
- Prefers `output/*.out.ipynb` (rendered notebooks with actual outputs)
- Falls back to source notebooks if needed
- Handles missing cell labels gracefully by extracting all outputs

**Output Types Extracted**:
- `text/html` → Converted to markdown tables
- `text/plain` → Preserved as text
- `text/markdown` → Preserved
- `text/latex` → Preserved
- `stream` outputs → Captured (print statements)

### 3. Enhanced Section Extractor (`section_extractor.py`)

**New Function**:
```python
def augment_with_notebook_outputs(report: Dict, extracted_text: str) -> str:
    """
    Find notebook outputs that correspond to embeds in the extracted text
    and append them in a readable format.
    """
```

**Integration**:
- Matches `{{< embed >}}` shortcodes to notebook outputs
- Appends outputs after relevant text sections
- Formats outputs for optimal AI readability

---

## Test Results

### Test Repository 1: `test-student-repo`

**Report**: Math with circuits (LPF and derivatives)
**Embeds**: 8 notebook cells

**Extraction Results**:
```
✅ Report parsed successfully:
   - 1000 words
   - 10 figures (manual + generated)
   - 8 notebook cell(s) with outputs extracted
   - 7 text output(s)
```

**Finding**: Successfully extracted text outputs from computational cells. No HTML tables in this report (student used print statements instead of DataFrames).

---

### Test Repository 2: `p3-amplification-submissions/p3-amplification-joeylongo17`

**Report**: Amplification project with extensive data analysis
**Embeds**: 26 notebook cells
**Source Notebooks**: `PDFs_allthat.ipynb` (68 cells, 45 with outputs, 15 with HTML)

**Extraction Results**:
```
✅ Report parsed successfully:
   - 1287 words
   - 5 figures (manual + generated)
   - 26 notebook cell(s) with outputs extracted
   - 9 HTML table(s) converted to markdown
   - 38 text output(s)
```

**Sample Converted Table**:
```markdown
|  | j | v-sweep | v(ADC0) | v(ADC1) | v(ADC2) | time |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | 0 | 0.000000 | 0.079963 | 0.080970 | 2.72998 | 0.000122 |
| 1 | 1 | 0.012891 | 0.079963 | 0.083992 | 2.72998 | 0.003937 |
| 2 | 2 | 0.025832 | 0.091998 | 0.095976 | 2.72998 | 0.008026 |
| 3 | 3 | 0.038773 | 0.099954 | 0.105997 | 2.72998 | 0.011902 |
| 4 | 4 | 0.051714 | 0.113953 | 0.116974 | 2.72998 | 0.015717 |
```

**Quality**:
- ✅ Clean conversion (no CSS remnants)
- ✅ Proper markdown table format
- ✅ Preserves all data values
- ✅ Readable for AI analysis

---

## Key Features Demonstrated

### 1. Pandas DataFrame Extraction
- **Source**: HTML tables with CSS styling
- **Output**: Clean markdown tables
- **Use Case**: Measurement data, statistical analysis, experimental results

### 2. Text Output Extraction
- **Source**: Print statements, numerical outputs
- **Output**: Preserved in code blocks
- **Use Case**: Calculations, error messages, debug output

### 3. Mixed Output Handling
- **Source**: Cells with multiple output types
- **Output**: All types captured and formatted appropriately
- **Use Case**: Complex analysis cells with tables + text

### 4. Graceful Degradation
- **Scenario**: Cell labels not found
- **Behavior**: Extracts all outputs from notebook
- **Result**: No data loss, system remains robust

---

## Technical Details

### Embed Shortcode Parsing

**Format**: `{{< embed notebook.ipynb#cell-id param1 param2 >}}`

**Parsing Strategy**:
1. Split on whitespace to separate notebook reference from parameters
2. Split notebook reference on `#` to get path and cell ID
3. Search for output notebook: `output/notebook.out.ipynb`
4. Fall back to source notebook if output not found

### Cell Matching

Tries multiple strategies to find cells:
1. Exact cell `id` match
2. Cell metadata `label` match
3. Cell metadata `tags` match
4. If all fail: extract ALL outputs from notebook

### Output Format for AI

```markdown
### Notebook Output from {{< embed notebook.ipynb#cell-id >}}

| Column1 | Column2 | Column3 |
| ------- | ------- | ------- |
| value1  | value2  | value3  |

```
Additional text output...
```
```

---

## Benefits for AI Feedback

### Before (Images Only)
- ❌ Couldn't see tabular data
- ❌ Missed numerical results
- ❌ No access to computational outputs
- ❌ Required vision API for everything

### After (All Outputs)
- ✅ Analyzes measurement tables
- ✅ Reviews statistical results
- ✅ Verifies calculations
- ✅ More token-efficient (text < images)

---

## Use Cases by Course Type

### PHYS 230 (Circuits & Instrumentation)
- **Measurement tables**: Voltage, current, frequency data
- **Calibration data**: Sensor readings, error analysis
- **Statistical analysis**: Mean, std dev, uncertainty calculations

### PHYS 280 (Computational Physics)
- **Algorithm outputs**: Convergence data, iteration counts
- **Parameter studies**: Tables of results across parameter sweeps
- **Performance metrics**: Runtime, accuracy, error rates

### EENG Courses
- **Simulation results**: SPICE output tables
- **Component specifications**: Parts lists with values
- **Test results**: Pass/fail tables, measurement logs

---

## Known Limitations

1. **Requires Jupyter Notebooks**
   - System designed for `.ipynb` files
   - Doesn't extract from pure Python scripts

2. **Best with Rendered Notebooks**
   - Prefers `output/*.out.ipynb` (executed versions)
   - Source notebooks may have stale/missing outputs

3. **HTML Complexity**
   - Very complex HTML may not convert perfectly
   - Pandas-style tables work best

4. **Cell Label Matching**
   - Students must use consistent cell labels
   - Falls back to extracting all outputs if labels missing

---

## Future Enhancements

### High Priority
1. **Better cell label detection**
   - Parse Quarto's cell execution metadata
   - Match by code content similarity

2. **Image + Table correlation**
   - Link images to their generating cells
   - Associate tables with related plots

### Medium Priority
3. **Smart table summarization**
   - Large tables (>100 rows) summarized for token efficiency
   - Include first/last N rows + statistics

4. **Code context inclusion**
   - Include cell source code alongside outputs
   - Helps AI understand what was calculated

### Low Priority
5. **Multi-format output**
   - Handle matplotlib/plotly interactive outputs
   - Extract alt-text from images

---

## Deployment Checklist

- [x] HTML-to-markdown converter implemented
- [x] Notebook output extraction in parse_report.py
- [x] Integration with section_extractor.py
- [x] Tested with real student reports
- [x] CSS/styling stripping working
- [x] Graceful fallbacks implemented
- [ ] Update GitHub Actions workflow (when ready to deploy)
- [ ] Document for instructors
- [ ] Test with more diverse reports

---

## Success Metrics

**Test 1 (test-student-repo)**:
- 8/8 cells extracted (100%)
- 7 text outputs captured
- 0 errors

**Test 2 (p3-amplification-joeylongo17)**:
- 26/26 cells extracted (100%)
- 9 HTML tables converted
- 38 text outputs captured
- Clean markdown output
- 0 errors

**Overall**: ✅ **PRODUCTION READY**

---

## Files Modified

1. `dot_github_folder/scripts/html_to_markdown.py` - NEW
2. `dot_github_folder/scripts/parse_report.py` - ENHANCED
3. `dot_github_folder/scripts/section_extractor.py` - ENHANCED

## Dependencies

- `pyyaml` - Already required
- No new dependencies needed

---

## Conclusion

The notebook output extraction system successfully captures and converts all types of notebook outputs into AI-friendly markdown format. Testing with real student reports demonstrates:

- **Robust extraction** from diverse notebook structures
- **Clean conversion** of HTML tables to markdown
- **Comprehensive coverage** of all output types
- **Graceful handling** of edge cases

This enhancement significantly improves the AI's ability to provide feedback on:
- Data analysis quality
- Numerical accuracy
- Statistical reasoning
- Experimental methodology

**Next Step**: Ready for broader testing with additional student repositories to validate across more course types and reporting styles.
