#!/usr/bin/env python3
"""
Intelligent section extraction for criterion-based analysis.
Extracts relevant parts of report for each rubric criterion.
"""

import re
from typing import List, Dict, Any


def extract_sections_for_criterion(report: Dict[str, Any], criterion: Dict[str, Any]) -> str:
    """
    Extract relevant sections from report for a specific criterion.

    Args:
        report: Parsed report with content, structure, metadata
        criterion: Rubric criterion with keywords, artifacts, etc.

    Returns:
        Focused text containing only relevant sections for this criterion
    """
    criterion_id = criterion.get('id', '')
    keywords = criterion.get('keywords', [])
    artifacts = criterion.get('artifacts', [])

    # Get full content and structure
    full_content = report['content']
    structure = report['structure']

    # Different extraction strategies based on criterion type
    if 'simulation' in criterion_id or any('simulat' in k.lower() for k in keywords):
        return extract_simulation_sections(full_content, structure, keywords)

    elif 'problem' in criterion_id or 'formul' in criterion_id:
        return extract_problem_formulation_sections(full_content, structure, keywords)

    elif 'design' in criterion_id and 'judgement' not in criterion_id:
        return extract_design_sections(full_content, structure, keywords, artifacts)

    elif 'background' in criterion_id or 'knowledge' in criterion_id:
        return extract_background_sections(full_content, structure, keywords)

    elif 'experiment' in criterion_id:
        return extract_experiment_sections(full_content, structure, keywords)

    elif 'interpret' in criterion_id or 'result' in criterion_id:
        return extract_results_sections(full_content, structure, keywords)

    elif 'judgement' in criterion_id:
        return extract_design_judgement_sections(full_content, structure, keywords)

    elif 'introduction' in criterion_id:
        return extract_introduction_sections(full_content, structure)

    elif 'conclusion' in criterion_id or 'summary' in criterion_id:
        return extract_conclusion_sections(full_content, structure)

    else:
        # Generic keyword-based extraction
        return extract_by_keywords(full_content, structure, keywords)


def extract_simulation_sections(content: str, structure: List[Dict], keywords: List[str]) -> str:
    """Extract sections related to simulations."""
    sections = []

    # Look for PreLab sections (simulations typically in PreLab)
    prelab_pattern = r'##\s*PreLab.*?(?=##\s*(?:PreLab|Report|Lab|$))'
    prelab_sections = re.findall(prelab_pattern, content, re.DOTALL | re.IGNORECASE)

    for section in prelab_sections:
        # Check if section mentions simulations
        if any(kw in section.lower() for kw in ['simulat', 'ltspice', 'spice', 'predict']):
            sections.append(section)

    # Also extract figures that look like simulations
    figure_pattern = r'!\[.*?\]\(.*?(?:sim|circuit|schematic).*?\)'
    sim_figures = re.findall(figure_pattern, content, re.IGNORECASE)
    if sim_figures:
        sections.append("\n\n**Simulation Figures Found:**\n" + "\n".join(sim_figures))

    # Extract question sections that mention simulations
    question_sections = extract_questions_mentioning(content, keywords)
    sections.extend(question_sections)

    if not sections:
        return "No clear simulation sections found in report."

    return "\n\n---\n\n".join(sections)


def extract_problem_formulation_sections(content: str, structure: List[Dict], keywords: List[str]) -> str:
    """Extract sections related to problem formulation."""
    sections = []

    # Look for sections with headings about problem/goals/objectives
    for heading in structure:
        heading_text = heading['text'].lower()
        if any(kw in heading_text for kw in ['problem', 'goal', 'objective', 'formulate', 'design goal']):
            # Extract this section
            section = extract_section_by_heading(content, heading['text'])
            if section:
                sections.append(f"### {heading['text']}\n{section}")

    # Also check introduction and first sections
    intro_pattern = r'^.*?(?=##\s*PreLab|##\s*Lab|$)'
    intro = re.match(intro_pattern, content, re.DOTALL)
    if intro and len(intro.group(0)) > 100:
        sections.insert(0, f"**Introduction/Overview:**\n{intro.group(0)[:1000]}")

    # Extract design specifications or requirements if mentioned
    spec_pattern = r'(?:specifications?|requirements?|constraints?).*?(?:\n\n|\n###|\n##|$)'
    specs = re.findall(spec_pattern, content, re.IGNORECASE | re.DOTALL)
    for spec in specs[:3]:  # Limit to first 3
        if len(spec) > 50:
            sections.append(spec)

    if not sections:
        return "No clear problem formulation sections found. Report may not explicitly state design goals."

    return "\n\n".join(sections[:5])  # Limit to prevent overwhelming


def extract_design_sections(content: str, structure: List[Dict], keywords: List[str], artifacts: List[str]) -> str:
    """Extract sections related to design development."""
    sections = []

    # Look for design-related headings
    for heading in structure:
        heading_text = heading['text'].lower()
        if any(kw in heading_text for kw in ['design', 'develop', 'solution', 'circuit']):
            section = extract_section_by_heading(content, heading['text'])
            if section:
                sections.append(f"### {heading['text']}\n{section}")

    # Extract schematics and circuit diagrams
    figure_pattern = r'!\[.*?\]\(.*?(?:schematic|circuit|design).*?\)'
    design_figures = re.findall(figure_pattern, content, re.IGNORECASE)
    if design_figures:
        sections.append("\n**Design Schematics/Circuits:**\n" + "\n".join(design_figures[:5]))

    # Look for component value discussions
    component_pattern = r'(?:resistor|capacitor|transistor|R_?[ce]|C\d+).*?[0-9]+\s*(?:k?Ω|μF|nF|mA|V)'
    components = re.findall(component_pattern, content, re.IGNORECASE)
    if components:
        sections.append(f"\n**Component Values Discussed:** {len(components)} instances found")

    # Extract calculation sections
    calc_sections = extract_sections_with_equations(content)
    if calc_sections:
        sections.append(f"\n**Design Calculations:**\n{calc_sections[:1500]}")

    if not sections:
        return "No clear design development sections found."

    return "\n\n".join(sections)


def extract_background_sections(content: str, structure: List[Dict], keywords: List[str]) -> str:
    """Extract sections related to background knowledge and datasheets."""
    sections = []

    # Look for background/knowledge headings
    for heading in structure:
        heading_text = heading['text'].lower()
        if any(kw in heading_text for kw in ['background', 'knowledge', 'datasheet', 'theory']):
            section = extract_section_by_heading(content, heading['text'])
            if section:
                sections.append(f"### {heading['text']}\n{section}")

    # Look for datasheet mentions
    datasheet_pattern = r'(?:datasheet|data\s*sheet|spec\s*sheet).*?(?:\n\n|$)'
    datasheets = re.findall(datasheet_pattern, content, re.IGNORECASE | re.DOTALL)
    for ds in datasheets[:3]:
        sections.append(f"**Datasheet Reference:** {ds[:300]}")

    # Look for part numbers (common transistor/IC naming)
    part_pattern = r'\b(?:2N\d{4}|LM\d{3,4}|TL\d{3}|NE\d{3}|74\w{2,4})\b'
    parts = re.findall(part_pattern, content)
    if parts:
        sections.append(f"\n**Component Part Numbers Mentioned:** {', '.join(set(parts))}")

    # Look for equations and theory
    equations = extract_sections_with_equations(content)
    if equations:
        sections.append(f"\n**Theoretical Equations:**\n{equations[:1000]}")

    if not sections:
        return "No clear background knowledge sections found. Datasheet references may be minimal."

    return "\n\n".join(sections)


def extract_experiment_sections(content: str, structure: List[Dict], keywords: List[str]) -> str:
    """Extract sections related to experiments and data collection."""
    sections = []

    # Look for Lab Report section (experiments typically here)
    lab_pattern = r'#\s*(?:Report|Lab\s*Report).*?$'
    lab_match = re.search(lab_pattern, content, re.IGNORECASE | re.DOTALL)
    if lab_match:
        lab_content = content[lab_match.start():]
        sections.append(f"**Lab Report Section:**\n{lab_content[:2000]}")

    # Look for experimental setup descriptions
    setup_pattern = r'(?:setup|procedure|method|measure|test).*?(?:\n\n|###|##|$)'
    setups = re.findall(setup_pattern, content, re.IGNORECASE | re.DOTALL)
    for setup in setups[:3]:
        if len(setup) > 50:
            sections.append(setup[:500])

    # Extract photos/figures from lab
    photo_pattern = r'!\[.*?\]\(.*?(?:photo|lab|setup|measurement).*?\)'
    photos = re.findall(photo_pattern, content, re.IGNORECASE)
    if photos:
        sections.append(f"\n**Experimental Photos/Figures:** {len(photos)} found\n" + "\n".join(photos[:5]))

    # Look for data tables or measurements
    if 'data/' in content:
        sections.append("\n**Data files referenced:** Yes, data directory mentioned")

    if not sections:
        return "No clear experimental sections found. Lab work may not be thoroughly documented."

    return "\n\n".join(sections)


def extract_results_sections(content: str, structure: List[Dict], keywords: List[str]) -> str:
    """Extract sections related to result interpretation and analysis."""
    sections = []

    # Look for interpretation/analysis headings
    for heading in structure:
        heading_text = heading['text'].lower()
        if any(kw in heading_text for kw in ['interpret', 'result', 'analysis', 'finding', 'discuss']):
            section = extract_section_by_heading(content, heading['text'])
            if section:
                sections.append(f"### {heading['text']}\n{section}")

    # Look for comparison language
    comparison_pattern = r'(?:compar|versus|vs\.|differ|match|agree|disagree|expect|predict).*?(?:\n\n|$)'
    comparisons = re.findall(comparison_pattern, content, re.IGNORECASE | re.DOTALL)
    for comp in comparisons[:5]:
        if len(comp) > 50:
            sections.append(comp[:300])

    # Look for error/uncertainty discussions
    error_pattern = r'(?:error|uncertainty|tolerance|deviation|accuracy).*?(?:\n\n|$)'
    errors = re.findall(error_pattern, content, re.IGNORECASE | re.DOTALL)
    if errors:
        sections.append(f"\n**Error Analysis Found:** {len(errors)} mentions")
        sections.append(errors[0][:300])

    # Extract plots and graphs (key for interpretation)
    plot_pattern = r'!\[.*?\]\(.*?(?:plot|graph|data|result).*?\)'
    plots = re.findall(plot_pattern, content, re.IGNORECASE)
    if plots:
        sections.append(f"\n**Result Figures:** {len(plots)} plots/graphs found")

    if not sections:
        return "No clear result interpretation sections found. Analysis may be minimal."

    return "\n\n".join(sections)


def extract_design_judgement_sections(content: str, structure: List[Dict], keywords: List[str]) -> str:
    """Extract sections about design judgements (economic, environmental, etc.)."""
    sections = []

    # Look for design judgement heading
    for heading in structure:
        heading_text = heading['text'].lower()
        if any(kw in heading_text for kw in ['judgement', 'judgment', 'context', 'economic', 'environmental', 'societal']):
            section = extract_section_by_heading(content, heading['text'])
            if section:
                sections.append(f"### {heading['text']}\n{section}")

    # Look for economic mentions
    economic_pattern = r'(?:cost|economic|price|cheap|expensive|\$|dollar).*?(?:\n\n|$)'
    economic = re.findall(economic_pattern, content, re.IGNORECASE | re.DOTALL)
    if economic:
        sections.append(f"\n**Economic Discussion:**\n" + "\n".join(economic[:3]))

    # Look for environmental mentions
    env_pattern = r'(?:environmental|sustainab|power\s+consumption|energy|recyclable).*?(?:\n\n|$)'
    env = re.findall(env_pattern, content, re.IGNORECASE | re.DOTALL)
    if env:
        sections.append(f"\n**Environmental Discussion:**\n" + "\n".join(env[:3]))

    if not sections:
        return "No clear design judgement sections found. Broader context analysis may be missing."

    return "\n\n".join(sections)


def extract_introduction_sections(content: str, structure: List[Dict]) -> str:
    """Extract introduction sections."""
    sections = []

    # Get first major section (usually introduction)
    intro_pattern = r'^.*?(?=##\s*PreLab|##\s*Lab|#\s*Report|$)'
    intro = re.match(intro_pattern, content, re.DOTALL)
    if intro:
        intro_text = intro.group(0)
        if len(intro_text) > 50:
            sections.append(f"**Document Introduction:**\n{intro_text}")

    # Look for Introduction heading
    for heading in structure:
        if 'introduction' in heading['text'].lower():
            section = extract_section_by_heading(content, heading['text'])
            if section:
                sections.append(f"### {heading['text']}\n{section}")

    if not sections:
        return "No clear introduction found. Report may start directly with technical content."

    return "\n\n".join(sections)


def extract_conclusion_sections(content: str, structure: List[Dict]) -> str:
    """Extract conclusion/summary sections."""
    sections = []

    # Look for conclusion headings
    for heading in structure:
        heading_text = heading['text'].lower()
        if any(kw in heading_text for kw in ['conclusion', 'summary', 'closing']):
            section = extract_section_by_heading(content, heading['text'])
            if section:
                sections.append(f"### {heading['text']}\n{section}")

    # Get last major section if no explicit conclusion
    if not sections:
        last_section = content.split('###')[-1]
        if len(last_section) > 100:
            sections.append(f"**Final Section:**\n{last_section}")

    if not sections:
        return "No clear conclusion found. Report may end abruptly."

    return "\n\n".join(sections)


def extract_section_by_heading(content: str, heading: str) -> str:
    """Extract content under a specific heading until next heading."""
    # Escape special regex characters in heading
    escaped_heading = re.escape(heading)
    # Match this heading and capture until next heading of same or higher level
    pattern = rf'###?\s*{escaped_heading}\s*\n(.*?)(?=\n###?\s|\n#\s|$)'
    match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return ""


def extract_questions_mentioning(content: str, keywords: List[str]) -> List[str]:
    """Extract question sections that mention any of the keywords."""
    sections = []

    # Find all question sections
    question_pattern = r'Question\s+\d+.*?(?=Question\s+\d+|###|##|$)'
    questions = re.findall(question_pattern, content, re.DOTALL | re.IGNORECASE)

    for question in questions:
        # Check if any keyword appears
        if any(kw.lower() in question.lower() for kw in keywords):
            sections.append(question[:1000])  # Limit length

    return sections


def extract_sections_with_equations(content: str) -> str:
    """Extract sections that contain equations (LaTeX math)."""
    # Find paragraphs with inline or display math
    math_pattern = r'[^\n]*\$[^$]+\$[^\n]*(?:\n[^\n]*\$[^$]+\$[^\n]*)*'
    math_sections = re.findall(math_pattern, content)

    if not math_sections:
        return ""

    return "\n\n".join(math_sections[:5])  # Limit to first 5


def extract_by_keywords(content: str, structure: List[Dict], keywords: List[str]) -> str:
    """Generic keyword-based extraction."""
    sections = []

    # Find paragraphs mentioning keywords
    for keyword in keywords:
        pattern = rf'[^\n]*{keyword}[^\n]*(?:\n[^\n]*)*?(?:\n\n|$)'
        matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
        sections.extend(matches[:2])  # Limit per keyword

    if not sections:
        return f"No sections found matching keywords: {', '.join(keywords[:5])}"

    return "\n\n".join(sections[:10])  # Limit total
