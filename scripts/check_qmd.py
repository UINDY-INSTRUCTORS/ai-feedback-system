#!/usr/bin/env python3
"""
Check .qmd files for embed problems and common syntax gotchas.

Checks performed:
  1. Embed references: verifies tags/labels exist in the target notebook
  2. Code fence + hr collision: '---' immediately after closing '```'
     (no blank line) can be misparsed as a YAML delimiter
  3. Unclosed code fences: odd number of fence markers means one is missing
  4. Unclosed callout divs: ':::' divs that are opened but never closed
  5. Ambiguous '---': a '---' not inside front matter that lacks a blank
     line before it may be misparsed as a YAML delimiter
  6. Missing blank lines around shortcodes: shortcodes like embed may be
     silently ignored if not separated from surrounding content
  7. Duplicate notebook tags: two cells sharing the same tag in a notebook
     referenced by an embed — Quarto may not resolve the right cell

Usage:
    python check_qmd.py <qmd_file>
    python check_qmd.py index.qmd
    python check_qmd.py path/to/dir   # checks all .qmd files in dir
"""

import json
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Embed checks
# ---------------------------------------------------------------------------

def parse_embeds(qmd_path: Path) -> list[dict]:
    """Extract all embed references from a .qmd file.

    Returns a list of dicts with keys: notebook, tag, line_num, raw.
    """
    embed_pattern = re.compile(
        r"\{\{<\s*embed\s+(\S+?)#(\S+?)(?:\s+[^>]*)?\s*>\}\}"
    )
    embeds = []
    for line_num, line in enumerate(qmd_path.read_text().splitlines(), start=1):
        for m in embed_pattern.finditer(line):
            embeds.append({
                "notebook": m.group(1),
                "tag": m.group(2),
                "line_num": line_num,
                "raw": m.group(0),
            })
    return embeds


def get_notebook_identifiers(nb_path: Path) -> dict[str, list[str]]:
    """Return all cell tags and code-comment labels from a notebook.

    Returns a dict: identifier -> list of sources (e.g. ["tag", "label"]).
    """
    with open(nb_path) as f:
        nb = json.load(f)

    identifiers: dict[str, list[str]] = {}

    for i, cell in enumerate(nb["cells"]):
        # Tags from cell metadata
        tags = cell.get("metadata", {}).get("tags", [])
        for tag in tags:
            identifiers.setdefault(tag, []).append(f"cell {i} tag")

        # Code-comment labels (#| label: xxx)
        source = "".join(cell.get("source", []))
        for src_line in source.split("\n"):
            stripped = src_line.strip()
            label_match = re.match(r"^#\|\s*label:\s*(\S+)", stripped)
            if label_match:
                label = label_match.group(1)
                identifiers.setdefault(label, []).append(f"cell {i} label")

        # Cell id
        cell_id = cell.get("id", "")
        if cell_id:
            identifiers.setdefault(cell_id, []).append(f"cell {i} id")

    return identifiers


def check_embeds(qmd_path: Path) -> list[dict]:
    """Check embed references resolve to notebook tags/labels."""
    embeds = parse_embeds(qmd_path)
    if not embeds:
        return []

    # Group by notebook
    notebooks: dict[str, list[dict]] = {}
    for embed in embeds:
        notebooks.setdefault(embed["notebook"], []).append(embed)

    issues = []
    for nb_name, nb_embeds in notebooks.items():
        nb_path = qmd_path.parent / nb_name
        if not nb_path.exists():
            for embed in nb_embeds:
                issues.append({
                    "check": "embed",
                    "line_num": embed["line_num"],
                    "issue": f"Notebook file not found: {nb_name}",
                })
            continue

        identifiers = get_notebook_identifiers(nb_path)

        for embed in nb_embeds:
            tag = embed["tag"]
            if tag not in identifiers:
                lower_map = {k.lower(): k for k in identifiers}
                hint = ""
                if tag.lower() in lower_map:
                    hint = f" (case mismatch — found '{lower_map[tag.lower()]}')"
                issues.append({
                    "check": "embed",
                    "line_num": embed["line_num"],
                    "issue": f"Tag/label '{tag}' not found in {nb_name}{hint}",
                })

    return issues


def check_duplicate_notebook_tags(qmd_path: Path) -> list[dict]:
    """Check for duplicate tags across cells in notebooks referenced by embeds."""
    embeds = parse_embeds(qmd_path)
    if not embeds:
        return []

    # Collect unique notebooks
    nb_names = {e["notebook"] for e in embeds}
    issues = []

    for nb_name in nb_names:
        nb_path = qmd_path.parent / nb_name
        if not nb_path.exists():
            continue

        with open(nb_path) as f:
            nb = json.load(f)

        tag_cells: dict[str, list[int]] = {}
        for i, cell in enumerate(nb["cells"]):
            tags = cell.get("metadata", {}).get("tags", [])
            for tag in tags:
                tag_cells.setdefault(tag, []).append(i)

        # Check for tags used in multiple cells
        for tag, cells in tag_cells.items():
            if len(cells) > 1:
                cell_list = ", ".join(str(c) for c in cells)
                issues.append({
                    "check": "embed",
                    "line_num": 0,
                    "issue": (
                        f"Duplicate tag '{tag}' in {nb_name} "
                        f"(cells: {cell_list}) — Quarto may not resolve "
                        f"the intended cell."
                    ),
                })

        # Check for case-variant duplicates within a single cell
        for i, cell in enumerate(nb["cells"]):
            tags = cell.get("metadata", {}).get("tags", [])
            if len(tags) != len(set(tags)):
                dupes = [t for t in tags if tags.count(t) > 1]
                issues.append({
                    "check": "embed",
                    "line_num": 0,
                    "issue": (
                        f"Cell {i} in {nb_name} has duplicate tags: "
                        f"{', '.join(set(dupes))}"
                    ),
                })
            # Case-variant duplicates
            lower_tags: dict[str, list[str]] = {}
            for t in tags:
                lower_tags.setdefault(t.lower(), []).append(t)
            for _lower, variants in lower_tags.items():
                if len(variants) > 1:
                    issues.append({
                        "check": "embed",
                        "line_num": 0,
                        "issue": (
                            f"Cell {i} in {nb_name} has case-variant tags: "
                            f"{', '.join(repr(v) for v in variants)} — "
                            f"this may confuse tag resolution."
                        ),
                    })

    return issues


# ---------------------------------------------------------------------------
# Syntax gotcha checks
# ---------------------------------------------------------------------------

def _parse_structure(qmd_path: Path):
    """Parse a qmd file into lines with structural annotations.

    Returns (lines, front_matter_end) where front_matter_end is the
    line index of the closing '---' of YAML front matter (0-based),
    or -1 if there is no front matter.
    """
    lines = qmd_path.read_text().splitlines()

    # Find front matter boundaries
    front_matter_end = -1
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                front_matter_end = i
                break

    return lines, front_matter_end


def check_fence_hr_collision(qmd_path: Path) -> list[dict]:
    """Detect '---' immediately after a closing '```' with no blank line."""
    lines, _ = _parse_structure(qmd_path)
    issues = []
    for i in range(1, len(lines)):
        prev = lines[i - 1].strip()
        curr = lines[i].strip()
        if prev == "```" and curr == "---":
            issues.append({
                "check": "syntax",
                "line_num": i + 1,
                "issue": (
                    "'---' immediately after closing '```' (no blank line) — "
                    "Quarto may misparse this as a YAML delimiter, breaking "
                    "shortcodes. Add a blank line between them."
                ),
            })
    return issues


def check_unclosed_fences(qmd_path: Path) -> list[dict]:
    """Detect unclosed code fences (``` or ~~~)."""
    lines, _ = _parse_structure(qmd_path)
    issues = []

    # Track whether we're in a fenced block
    open_fence = None  # (marker_char, marker_len, line_num) or None
    for i, line in enumerate(lines):
        stripped = line.strip()
        m = re.match(r"^(`{3,}|~{3,})(.*)", stripped)
        if not m:
            continue

        marker = m.group(1)
        rest = m.group(2).strip()

        if open_fence is None:
            # Opening a new fence
            open_fence = (marker[0], len(marker), i + 1)
        else:
            # We're inside a fence — check if this closes it
            # Closing fence: same char, at least as many, no info string
            if (marker[0] == open_fence[0]
                    and len(marker) >= open_fence[1]
                    and rest == ""):
                open_fence = None

    if open_fence is not None:
        char, length, line_num = open_fence
        fence_str = char * length
        issues.append({
            "check": "syntax",
            "line_num": line_num,
            "issue": (
                f"Code fence opened with '{fence_str}' but never closed. "
                f"Add a matching '{fence_str}' to close it."
            ),
        })

    return issues


def check_unclosed_divs(qmd_path: Path) -> list[dict]:
    """Detect unclosed callout/div fences (:::)."""
    lines, _ = _parse_structure(qmd_path)
    issues = []

    div_stack = []  # list of (line_num, opening_text)
    for i, line in enumerate(lines):
        stripped = line.strip()
        # Opening div: ::: followed by something (e.g. ::: {.callout-note})
        if re.match(r"^:{3,}\s+\S", stripped):
            div_stack.append((i + 1, stripped))
        # Closing div: just :::
        elif re.match(r"^:{3,}\s*$", stripped):
            if div_stack:
                div_stack.pop()
            else:
                issues.append({
                    "check": "syntax",
                    "line_num": i + 1,
                    "issue": "Closing ':::' without a matching opening div.",
                })

    for line_num, text in div_stack:
        issues.append({
            "check": "syntax",
            "line_num": line_num,
            "issue": (
                f"Div opened with '{text}' but never closed. "
                f"Add ':::' on its own line to close it."
            ),
        })

    return issues


def check_ambiguous_hr(qmd_path: Path) -> list[dict]:
    """Detect '---' outside front matter that lacks a blank line before it.

    A '---' without a preceding blank line can be misparsed as a YAML
    delimiter or setext heading underline instead of a horizontal rule.
    """
    lines, front_matter_end = _parse_structure(qmd_path)
    issues = []

    # Track whether we're inside a code fence
    in_fence = False
    for i, line in enumerate(lines):
        stripped = line.strip()

        # Skip front matter
        if i <= front_matter_end:
            continue

        # Track code fences
        if re.match(r"^(`{3,}|~{3,})", stripped):
            in_fence = not in_fence
            continue

        if in_fence:
            continue

        if stripped == "---" and i > 0:
            prev = lines[i - 1].strip()
            # Already caught by fence_hr_collision
            if prev == "```" or prev.startswith("~~~"):
                continue
            if prev != "":
                issues.append({
                    "check": "syntax",
                    "line_num": i + 1,
                    "issue": (
                        f"'---' without a blank line before it (previous line: "
                        f"'{prev[:50]}') — may be misparsed as a YAML delimiter "
                        f"or setext heading. Add a blank line above."
                    ),
                })

    return issues


def check_shortcode_spacing(qmd_path: Path) -> list[dict]:
    """Detect shortcodes ({{< ... >}}) lacking blank lines before/after.

    Block-level shortcodes like embed should be on their own line with
    blank lines separating them from other content.
    """
    lines, front_matter_end = _parse_structure(qmd_path)
    issues = []

    shortcode_re = re.compile(r"\{\{<\s*\w+\s+.*>\}\}")

    # Track code fences
    in_fence = False
    for i, line in enumerate(lines):
        stripped = line.strip()

        if re.match(r"^(`{3,}|~{3,})", stripped):
            in_fence = not in_fence
            continue

        if in_fence:
            continue

        if not shortcode_re.search(stripped):
            continue

        # Only flag block-level shortcodes (line is just the shortcode)
        if not shortcode_re.fullmatch(stripped):
            continue

        # Check line before
        if i > 0 and lines[i - 1].strip() != "":
            issues.append({
                "check": "syntax",
                "line_num": i + 1,
                "issue": (
                    "Shortcode has no blank line before it — it may not be "
                    "processed correctly. Add a blank line above."
                ),
            })

        # Check line after
        if i < len(lines) - 1 and lines[i + 1].strip() != "":
            issues.append({
                "check": "syntax",
                "line_num": i + 1,
                "issue": (
                    "Shortcode has no blank line after it — it may not be "
                    "processed correctly. Add a blank line below."
                ),
            })

    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

ALL_CHECKS = [
    ("Embed references", check_embeds),
    ("Duplicate notebook tags", check_duplicate_notebook_tags),
    ("Code fence + hr collision", check_fence_hr_collision),
    ("Unclosed code fences", check_unclosed_fences),
    ("Unclosed callout divs", check_unclosed_divs),
    ("Ambiguous hr", check_ambiguous_hr),
    ("Shortcode spacing", check_shortcode_spacing),
]


def check_qmd(qmd_path: Path) -> list[dict]:
    """Run all checks on a single .qmd file."""
    issues = []
    for _name, check_fn in ALL_CHECKS:
        issues.extend(check_fn(qmd_path))
    return issues


def main():
    if len(sys.argv) < 2:
        print(__doc__.strip())
        sys.exit(1)

    target = Path(sys.argv[1])
    if target.is_dir():
        qmd_files = sorted(target.glob("**/*.qmd"))
    else:
        qmd_files = [target]

    if not qmd_files:
        print("No .qmd files found.")
        sys.exit(1)

    all_ok = True
    for qmd_path in qmd_files:
        embeds = parse_embeds(qmd_path)
        issues = check_qmd(qmd_path)

        print(f"\n{'='*60}")
        print(f"File: {qmd_path}")

        # Embed summary
        if embeds:
            print(f"  Embeds found: {len(embeds)}")
            embed_issues = {i["line_num"] for i in issues if i["check"] == "embed"}
            for embed in embeds:
                status = "MISSING" if embed["line_num"] in embed_issues else "OK"
                print(f"    Line {embed['line_num']:>4}: {embed['notebook']}#{embed['tag']}  [{status}]")

        # All issues
        if issues:
            all_ok = False
            print(f"\n  Problems ({len(issues)}):")
            for issue in issues:
                ln = f"Line {issue['line_num']:>4}" if issue["line_num"] else "          "
                print(f"    [{issue['check']:>6}] {ln}: {issue['issue']}")
        else:
            print("\n  All checks passed.")

    print(f"\n{'='*60}")
    if all_ok:
        print("Result: All checks passed.")
    else:
        print("Result: Problems found.")
        sys.exit(1)


if __name__ == "__main__":
    main()
