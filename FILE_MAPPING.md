# File Mapping for Repository Split

This document shows exactly which files from `feedback-system-test` go into which new repository.

## Files → `ai-feedback-system` (Keep/Modify)

### Keep As-Is
```
✅ .github/
   ✅ workflows/
      ✅ report-feedback.yml
      ✅ test-extraction-methods.yml
   ✅ feedback/
      ✅ examples/
         ✅ eeng-320-lab-example.yml
         ✅ eeng-340-project-example.yml
         ✅ phys-230-lab-example.yml
         ✅ phys-280-assignment-example.yml
      ✅ templates/
         ✅ lab-rubric-template.yml
         ✅ programming-assignment-rubric-template.yml
         ✅ guidance-template.md
      ✅ config-template.yml
      ✅ README.md
   ✅ SETUP_GUIDE.md
   ✅ GITHUB_MODELS_SETTINGS.md

✅ scripts/
   ✅ parse_report.py
   ✅ section_extractor.py
   ✅ ai_section_extractor.py
   ✅ ai_feedback_criterion.py
   ✅ ai_feedback_criterion_ai_extract.py
   ✅ ai_feedback.py
   ✅ create_issue.py
   ✅ AI_EXTRACTION_README.md

✅ Dockerfile
✅ pyproject.toml
✅ uv.lock
✅ INSTRUCTOR_GUIDE.md
✅ DEPLOYMENT.md
✅ TESTING_AI_EXTRACTION.md
✅ TEMPLATE_SYSTEM.md
```

### Modify These Files
```
📝 README.md
   - Make instructor-focused
   - Add clear "For Instructors" header
   - Remove or minimize student-facing content
   - Add link to quarto-report-template for student templates

📝 .gitignore
   - Add entries for testing artifacts
   - feedback.md, parsed_report.json, etc.
```

### Remove These Files
```
❌ REPO_SPLIT_PROPOSAL.md (this document)
❌ split-repos.sh (helper script)
❌ FILE_MAPPING.md (this document)
❌ main.py (empty placeholder)
❌ .devcontainer/ (moves to report template)
```

---

## Files → `quarto-report-template` (New Repo)

### Copy From Current Repo
```
✅ .devcontainer/
   ✅ devcontainer.json
```

### Create New Files

#### Directory Structure
```
templates/
├── lab-report/
│   ├── index.qmd                    # NEW: Lab report template
│   ├── _quarto.yml                  # NEW: Quarto config
│   └── references.bib               # NEW: Bibliography template
├── project-report/
│   ├── index.qmd                    # NEW: Project template
│   ├── _quarto.yml
│   └── sections/
│       ├── introduction.qmd
│       ├── methods.qmd
│       ├── results.qmd
│       └── conclusion.qmd
└── assignment/
    ├── index.qmd                    # NEW: Assignment template
    └── _quarto.yml

examples/
├── eeng-320-lab-example/            # NEW: Complete working example
│   ├── index.qmd
│   ├── figures/
│   ├── data/
│   └── schematics/
├── phys-280-assignment-example/
│   └── ...
└── phys-230-lab-example/
    └── ...

styles/
├── custom.css                       # NEW: Custom styling
└── ieee.csl                         # NEW: Citation styles

.github/workflows/
└── render-report.yml                # NEW: Auto-render workflow (optional)
```

#### Documentation Files (All NEW)
```
README.md                            # Student-focused
STUDENT_GUIDE.md                     # How to write reports
QUARTO_TIPS.md                       # Quarto markdown reference
CODESPACE_SETUP.md                   # Development environment setup
```

---

## Detailed File Decisions

### .devcontainer/devcontainer.json
**Decision**: Move to `quarto-report-template`
**Reason**: Students need it for writing reports. Feedback system runs in GitHub Actions containers.

### Dockerfile
**Decision**: Keep in `ai-feedback-system`
**Reason**: Only used by GitHub Actions for feedback generation.

### pyproject.toml / uv.lock
**Decision**: Keep in `ai-feedback-system`
**Reason**: Python dependencies for feedback scripts only.

### docs/CLAUDE.md, docs/SUMMARY.md, docs/TEST_DEPLOYMENT.md
**Decision**: Keep in `ai-feedback-system` (maybe move to docs/)
**Reason**: Development notes for feedback system.

### README.md
**Decision**:
- **ai-feedback-system**: Rewrite for instructors (how to deploy feedback)
- **quarto-report-template**: New file for students (how to write reports)

### Examples
**Decision**:
- Rubric examples (`.yml`) → `ai-feedback-system/.github/feedback/examples/`
- Report examples (`.qmd` with content) → `quarto-report-template/examples/`

---

## File Count Summary

### ai-feedback-system
```
Total: ~25 files
- Workflows: 2
- Python scripts: 7
- Rubric examples: 4
- Templates: 3
- Documentation: 9
```

### quarto-report-template
```
Total: ~20+ files (to be created)
- Report templates: 6+
- Example reports: 3 complete examples
- Styles: 2-3
- Documentation: 4
- Config: 2-3
```

---

## Git History

### Option A: Fresh Start (Recommended)
Both repos start with fresh git history:
- Clean slate
- No confusing history from combined repo
- Easier to understand commit logs

```bash
# In each repo
git init
git add .
git commit -m "Initial commit"
```

### Option B: Preserve History
Use git filter-branch to split history:
- Preserves who wrote what when
- More complex
- May not be necessary for a teaching tool

**Recommendation**: Fresh start (Option A)

---

## Migration Checklist

### Pre-Split
- [ ] Review REPO_SPLIT_PROPOSAL.md
- [ ] Decide on repository names
- [ ] Decide on GitHub organization/user

### Split Execution
- [ ] Run `split-repos.sh` to create local repos
- [ ] Review `ai-feedback-system` files
- [ ] Update `ai-feedback-system/README.md`
- [ ] Create templates in `quarto-report-template`
- [ ] Write student documentation

### Post-Split
- [ ] Create GitHub repos
- [ ] Push both repos to GitHub
- [ ] Add repo descriptions and topics
- [ ] Create releases/tags for versioning
- [ ] Update any external documentation/links
- [ ] Archive or mark `feedback-system-test` as superseded

### Testing
- [ ] Test feedback system deployment to sample repo
- [ ] Test report template as GitHub Classroom template
- [ ] Test combined usage (template + feedback system)
- [ ] Verify all workflows run correctly

---

## Example Combined Usage

After split, instructor creates assignment:

```bash
# 1. Start with report template
gh repo create my-org/lab-3-bjt-circuits --template quarto-report-template

cd lab-3-bjt-circuits

# 2. Add feedback system
git remote add feedback https://github.com/my-org/ai-feedback-system
git fetch feedback
git checkout feedback/main -- .github/workflows/report-feedback.yml
git checkout feedback/main -- .github/feedback
git checkout feedback/main -- scripts
git checkout feedback/main -- Dockerfile

# 3. Customize rubric
cd .github/feedback
cp examples/eeng-320-lab-example.yml rubric.yml
cp config-template.yml config.yml
# Edit rubric.yml and config.yml for this assignment

# 4. Commit and push
git add .
git commit -m "Add AI feedback system for Lab 3"
git push

# 5. Use as GitHub Classroom template
# Students get both report template and feedback system
```

---

## Questions?

- See REPO_SPLIT_PROPOSAL.md for strategic rationale
- See individual repo READMEs after split for usage instructions
- See INSTRUCTOR_GUIDE.md in ai-feedback-system for deployment details
