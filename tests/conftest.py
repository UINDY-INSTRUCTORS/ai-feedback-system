"""
Shared pytest fixtures for ai-feedback-system tests.
Provides sample data, configurations, and utilities for deterministic testing.
"""

import pytest
import json
import yaml
from pathlib import Path
from typing import Dict, Any


# ============================================================================
# FIXTURE: Sample YAML Configurations
# ============================================================================

@pytest.fixture
def sample_config() -> Dict[str, Any]:
    """Sample course configuration."""
    return {
        'course_id': 'PH280',
        'course_name': 'Computational Physics',
        'project_id': 'p01',
        'project_name': 'Euler Method',
        'model': {
            'extractor': 'gpt-4o-mini',
            'feedback': 'gpt-4o',
        },
        'vision': {
            'enabled': True,
            'criteria': ['Results'],
            'auto_detect': True,
            'max_images_per_criterion': 3,
        },
        'budget': {
            'extraction_tokens': 8000,
            'feedback_tokens': 4000,
        }
    }


@pytest.fixture
def sample_rubric() -> Dict[str, Any]:
    """Sample rubric in YAML format."""
    return {
        'course': 'PH280',
        'project': 'p01-euler-method',
        'criteria': [
            {
                'id': 'theory',
                'name': 'Theory & Explanation',
                'weight': 20,
                'levels': [
                    {
                        'level': 'Exemplary',
                        'percentage': '18-20%',
                        'description': 'Clear and thorough explanation'
                    },
                    {
                        'level': 'Satisfactory',
                        'percentage': '12-17%',
                        'description': 'Adequate explanation with minor gaps'
                    },
                    {
                        'level': 'Developing',
                        'percentage': '6-11%',
                        'description': 'Basic explanation, significant gaps'
                    },
                    {
                        'level': 'Unsatisfactory',
                        'percentage': '0-5%',
                        'description': 'Missing or unclear'
                    }
                ]
            },
            {
                'id': 'implementation',
                'name': 'Implementation/Code',
                'weight': 40,
                'levels': [
                    {
                        'level': 'Exemplary',
                        'percentage': '36-40%',
                        'description': 'Correct, well-documented code'
                    },
                    {
                        'level': 'Satisfactory',
                        'percentage': '24-35%',
                        'description': 'Mostly correct, some documentation'
                    },
                    {
                        'level': 'Developing',
                        'percentage': '12-23%',
                        'description': 'Partially correct, minimal documentation'
                    },
                    {
                        'level': 'Unsatisfactory',
                        'percentage': '0-11%',
                        'description': 'Incorrect or missing'
                    }
                ]
            }
        ]
    }


@pytest.fixture
def sample_qmd_frontmatter() -> str:
    """Sample YAML frontmatter from a Quarto document."""
    return """---
title: "Project 1: Euler Method"
author: "Student Name"
format:
  html:
    code-fold: true
  typst: default
jupyter: python3
---"""


# ============================================================================
# FIXTURE: Sample Report Content (Quarto Markdown)
# ============================================================================

@pytest.fixture
def sample_qmd_with_callouts() -> str:
    """Quarto markdown with template callout boxes."""
    return """---
title: "Project 1: Euler Method"
author: "Test Student"
---

# Report

## Theory & Explanation

::: {.callout-note}
This section should explain the theory.

- What is the Euler method?
- Why is it useful?

Delete this callout before you submit.
:::

The Euler method is a numerical integration technique...

## Implementation/Code

::: {.callout-warning}
Show your working code here.

Delete this callout before you submit.
:::

```python
def euler_step(y, t, dt, dydt_func):
    return y + dt * dydt_func(t, y)
```

## Results

Some results here.
"""


@pytest.fixture
def sample_qmd_with_embeds() -> str:
    """Quarto markdown with notebook embeds."""
    return """---
title: "Project 1"
author: "Student"
---

# Results

The plot shows convergence:

{{< embed notebook.ipynb#plot-convergence >}}

And the numerical results:

{{< embed notebook.ipynb#results-table >}}
"""


@pytest.fixture
def sample_qmd_with_figures() -> str:
    """Quarto markdown with figures."""
    return """---
title: "Project"
author: "Student"
---

# Introduction

Figure 1 shows the setup:

![Circuit diagram](./images/circuit.png)

# Results

![Convergence plot](./output/convergence.png "Convergence with different step sizes")

![Error analysis](./output/error.png)
"""


@pytest.fixture
def sample_qmd_complete() -> str:
    """Complete realistic Quarto document with all elements."""
    return """---
title: "Project 1: Euler Method"
author: "Jane Doe"
date: 2024-01-20
format:
  html:
    code-fold: true
  typst: default
jupyter: python3
---

## Theory & Explanation

::: {.callout-note}
Explain the algorithm you're implementing.
Delete this callout before you submit.
:::

The Euler method is a first-order numerical integration technique.

## Implementation

::: {.callout-note}
Show your code here. Use the embed syntax: {{< embed notebook.ipynb#cell-label >}}
Delete this callout before you submit.
:::

```python
def euler_method(y0, t, dydt):
    y = np.zeros_like(t)
    y[0] = y0
    for i in range(len(t)-1):
        dt = t[i+1] - t[i]
        y[i+1] = y[i] + dt * dydt(t[i], y[i])
    return y
```

## Results

![Convergence](./plots/convergence.png)

The method converges as expected.

## Conclusion

We successfully implemented the Euler method.
"""


# ============================================================================
# FIXTURE: Sample HTML Content
# ============================================================================

@pytest.fixture
def sample_html_table_simple() -> str:
    """Simple HTML table."""
    return """<table>
<tr><th>Step</th><th>Value</th></tr>
<tr><td>1</td><td>0.0</td></tr>
<tr><td>2</td><td>0.1</td></tr>
</table>"""


@pytest.fixture
def sample_html_table_complex() -> str:
    """HTML table with headers and multiple rows."""
    return """<table>
<thead>
<tr><th>Method</th><th>Error at t=1.0</th><th>Accuracy</th></tr>
</thead>
<tbody>
<tr><td>Euler</td><td>0.0234</td><td>Good</td></tr>
<tr><td>RK4</td><td>0.0001</td><td>Excellent</td></tr>
<tr><td>Adaptive</td><td>0.00001</td><td>Outstanding</td></tr>
</tbody>
</table>"""


@pytest.fixture
def sample_html_list_unordered() -> str:
    """HTML unordered list."""
    return """<ul>
<li>First item</li>
<li>Second item</li>
<li>Third item</li>
</ul>"""


@pytest.fixture
def sample_html_list_ordered() -> str:
    """HTML ordered list."""
    return """<ol>
<li>Initialize y and t arrays</li>
<li>For each time step, compute dy/dt</li>
<li>Update y using y_{n+1} = y_n + dt * dy/dt</li>
</ol>"""


@pytest.fixture
def sample_html_nested_lists() -> str:
    """HTML with nested lists."""
    return """<ul>
<li>Theory
<ul>
<li>Differential equations</li>
<li>Numerical methods</li>
</ul>
</li>
<li>Implementation
<ul>
<li>Python code</li>
<li>Testing</li>
</ul>
</li>
</ul>"""


@pytest.fixture
def sample_html_mixed_content() -> str:
    """HTML with mixed tables, text, and lists."""
    return """<p>Here are the results:</p>
<table>
<tr><th>Parameter</th><th>Value</th></tr>
<tr><td>dt</td><td>0.01</td></tr>
</table>
<p>Steps to reproduce:</p>
<ol>
<li>Load the data</li>
<li>Run the simulation</li>
</ol>"""


# ============================================================================
# FIXTURE: Sample Report Structure (Parsed)
# ============================================================================

@pytest.fixture
def sample_parsed_report() -> Dict[str, Any]:
    """Sample parsed report structure (what parse_report.py produces)."""
    return {
        'content': """# Theory & Explanation

The Euler method approximates solutions to differential equations.

## Implementation

```python
def euler_step(y, t, dt, dydt_func):
    return y + dt * dydt_func(t, y)
```

## Results

![Convergence Plot](output/convergence.png)

The error decreases with smaller step sizes.

## Conclusion

We successfully implemented the Euler method.
""",
        'metadata': {
            'title': 'Project 1: Euler Method',
            'author': 'Test Student',
            'date': '2024-01-20',
        },
        'structure': [
            {'level': 1, 'heading': 'Theory & Explanation'},
            {'level': 2, 'heading': 'Implementation'},
            {'level': 2, 'heading': 'Results'},
            {'level': 2, 'heading': 'Conclusion'},
        ],
        'figures': {
            'count': 1,
            'details': [
                {
                    'caption': 'Convergence Plot',
                    'path': 'output/convergence.png',
                    'type': 'markdown',
                }
            ]
        },
        'stats': {
            'word_count': 95,
            'code_block_count': 1,
            'equation_count': 0,
            'figure_count': 1,
        }
    }


# ============================================================================
# FIXTURE: Sample Criterion Configuration
# ============================================================================

@pytest.fixture
def sample_criterion() -> Dict[str, Any]:
    """Sample criterion for feedback analysis."""
    return {
        'id': 'implementation',
        'name': 'Implementation/Code',
        'weight': 40,
        'vision_enabled': False,
        'auto_detect_images': False,
    }


@pytest.fixture
def sample_criterion_with_vision() -> Dict[str, Any]:
    """Sample criterion with vision enabled."""
    return {
        'id': 'results',
        'name': 'Results',
        'weight': 20,
        'vision_enabled': True,
        'auto_detect_images': True,
    }


# ============================================================================
# UTILITY FIXTURES
# ============================================================================

@pytest.fixture
def temp_test_dir(tmp_path):
    """Provides a temporary directory for test files."""
    return tmp_path


@pytest.fixture
def fixture_dir():
    """Path to the fixtures directory."""
    return Path(__file__).parent / 'fixtures'


# ============================================================================
# SAMPLE DATA for Image Token Calculation
# ============================================================================

@pytest.fixture
def image_dimensions_samples() -> Dict[str, tuple]:
    """Sample image dimensions for token calculation testing."""
    return {
        'small': (256, 256),         # 1x1 tiles -> 85 + 170 = 255 tokens
        'medium': (512, 512),        # 1x1 tiles -> 85 + 170 = 255 tokens
        'large': (1024, 1024),       # 2x2 tiles -> 85 + 4*170 = 765 tokens
        'portrait': (512, 1024),     # 1x2 tiles -> 85 + 2*170 = 425 tokens
        'landscape': (1024, 512),    # 2x1 tiles -> 85 + 2*170 = 425 tokens
        'very_large': (2048, 2048),  # 4x4 tiles -> 85 + 16*170 = 2805 tokens
    }
