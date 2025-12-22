# Changelog

All notable changes to the AI Feedback System will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Automatic Markdown-to-YAML conversion** - GitHub Actions workflow now auto-converts RUBRIC.md to rubric.yml
- **Default .gitignore for rubric.yml** - Markdown-first workflow is now the default, no manual gitignore needed
- **Structured guidance parser** - Automatically extracts general guidance (Part I) and criterion-specific guidance (Part II) from guidance.md, dramatically reducing token usage (~9,000 tokens saved per report)

### Changed
- **Markdown rubrics are now the default workflow** - Faculty only need to edit RUBRIC.md
- Updated documentation to emphasize Markdown-first approach
- Simplified setup instructions (one less step for faculty)
- **Rubric links in issues** - Now link to RUBRIC.md if it exists, otherwise fall back to rubric.yml (more readable for students)
- **Guidance file structure improved** - Redesigned `guidance-template.md` with clear separation between general guidance (Part I) and criterion-specific guidance (Part II) for more targeted, efficient feedback

### Fixed
- **GitHub Issue formatting** - Sub-topic headers now render correctly with proper bold markdown syntax (`**Title:**`)

## [1.0.0] - 2025-12-20

### Added
- **Comprehensive notebook output extraction** - Extracts HTML tables, text, markdown, and LaTeX from Jupyter notebook cells
- **HTML to Markdown converter** - Converts pandas DataFrames to clean markdown tables
- **Rubric converter** - Bidirectional conversion between YAML and Markdown rubrics
- **Criterion-based analysis** - Analyzes each rubric criterion separately to work within token limits
- **Vision support** - Image analysis capabilities with token management
- **Multi-course templates** - Examples for EENG-320, PHYS-230, PHYS-280, EENG-340
- **Update script** - Easy way to pull latest features into deployed assignments
- **Comprehensive documentation** - Setup guides, testing docs, and session logs

### Changed
- Parse report now extracts all notebook outputs, not just images
- Section extractor augments text with relevant notebook outputs
- README updated with new features and markdown rubric workflow

### Fixed
- CSS styling properly stripped from HTML tables
- Notebook output discovery improved (prefers output/*.out.ipynb)
- Graceful handling of missing cell labels

## How to Update

### From a Deployed Assignment

Run the update script from your assignment repository:

```bash
# Update to latest version
bash .github/scripts/update_feedback_system.sh

# Update to specific version
bash .github/scripts/update_feedback_system.sh v1.0.0
```

Your custom rubric, guidance, and config files will be preserved.

### Manual Update

If you prefer manual control:

```bash
# 1. Backup current scripts
cp -r .github/scripts .github/scripts.backup

# 2. Download new scripts from ai-feedback-system repo
# 3. Copy only the script files (preserve your rubric/guidance/config)
# 4. Test before committing
```

## Version History

- **v1.0.0** (2025-12-20) - Initial release with notebook outputs and rubric converter
