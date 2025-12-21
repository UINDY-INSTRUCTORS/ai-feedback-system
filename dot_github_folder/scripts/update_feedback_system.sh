#!/bin/bash
#
# Update AI Feedback System Scripts
#
# This script safely updates the feedback system scripts in a deployed assignment
# while preserving your custom rubric, guidance, and config files.
#
# Usage:
#   bash .github/scripts/update_feedback_system.sh [version]
#
# Examples:
#   bash .github/scripts/update_feedback_system.sh          # Update to latest
#   bash .github/scripts/update_feedback_system.sh v1.2.0   # Update to specific version
#

set -e  # Exit on error

# Configure this with your ai-feedback-system repository URL
# For local testing, you can use a file:// URL:
#   REPO_URL="file:///path/to/ai-feedback-system"
REPO_URL="${AI_FEEDBACK_REPO_URL:-https://github.com/YOUR-ORG/ai-feedback-system.git}"

TEMP_DIR=$(mktemp -d)
VERSION="${1:-main}"  # Default to latest (main branch)

echo "================================================"
echo "AI Feedback System Updater"
echo "================================================"
echo ""

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo "❌ Error: Not in a git repository"
    echo "   Run this from the root of your assignment repository"
    exit 1
fi

# Check if .github/scripts exists
if [ ! -d ".github/scripts" ]; then
    echo "❌ Error: .github/scripts not found"
    echo "   This doesn't appear to be a repository with the feedback system"
    exit 1
fi

echo "📋 Pre-update checklist:"
echo "   1. Your custom files will be preserved:"
echo "      - .github/feedback/rubric.yml (or RUBRIC.md)"
echo "      - .github/feedback/guidance.md"
echo "      - .github/feedback/config.yml"
echo "   2. Script files will be updated to version: $VERSION"
echo "   3. A backup will be created before updating"
echo ""

read -p "Continue with update? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Update cancelled"
    exit 0
fi

# Create backup
BACKUP_DIR=".github/scripts.backup.$(date +%Y%m%d-%H%M%S)"
echo ""
echo "📦 Creating backup..."
cp -r .github/scripts "$BACKUP_DIR"
echo "   Backup saved to: $BACKUP_DIR"

# Clone the latest version
echo ""
echo "⬇️  Downloading latest version..."
git clone --depth 1 --branch "$VERSION" "$REPO_URL" "$TEMP_DIR" 2>/dev/null || {
    echo "❌ Failed to download version $VERSION"
    echo "   Available versions: https://github.com/YOUR-ORG/ai-feedback-system/tags"
    rm -rf "$TEMP_DIR"
    exit 1
}

# Update VERSION file
if [ -f "$TEMP_DIR/dot_github_folder/scripts/VERSION" ]; then
    cp "$TEMP_DIR/dot_github_folder/scripts/VERSION" ".github/scripts/VERSION"
    NEW_VERSION=$(cat ".github/scripts/VERSION")
    echo ""
    echo "📌 Updating to version: $NEW_VERSION"
fi

# Update scripts (but NOT config/rubric/guidance)
echo ""
echo "🔄 Updating scripts..."

# List of files to update (scripts only, not config)
SCRIPT_FILES=(
    "ai_feedback_criterion.py"
    "ai_feedback.py"
    "create_issue.py"
    "html_to_markdown.py"
    "image_utils.py"
    "parse_report.py"
    "rubric_converter.py"
    "section_extractor.py"
    "update_feedback_system.sh"
    "validate_config.py"
    "validation_schemas.py"
)

# Documentation to update
DOC_FILES=(
    "README.md"
    "README_DEBUG.md"
    "README_VALIDATION.md"
    "RUBRIC_CONVERTER_README.md"
)

updated_count=0

for file in "${SCRIPT_FILES[@]}"; do
    src="$TEMP_DIR/dot_github_folder/scripts/$file"
    dst=".github/scripts/$file"

    if [ -f "$src" ]; then
        cp "$src" "$dst"
        echo "   ✅ Updated: $file"
        ((updated_count++))
    else
        echo "   ⚠️  Skipped: $file (not found in new version)"
    fi
done

for file in "${DOC_FILES[@]}"; do
    src="$TEMP_DIR/dot_github_folder/scripts/$file"
    dst=".github/scripts/$file"

    if [ -f "$src" ]; then
        cp "$src" "$dst"
        echo "   ✅ Updated: $file"
        ((updated_count++))
    fi
done

# Update workflow file
if [ -f "$TEMP_DIR/dot_github_folder/workflows/report-feedback.yml" ]; then
    cp "$TEMP_DIR/dot_github_folder/workflows/report-feedback.yml" ".github/workflows/report-feedback.yml"
    echo "   ✅ Updated: GitHub Actions workflow"
    ((updated_count++))
fi

# Cleanup
rm -rf "$TEMP_DIR"

echo ""
echo "================================================"
echo "✅ Update Complete!"
echo "================================================"
echo "   Files updated: $updated_count"
echo "   Backup location: $BACKUP_DIR"
echo ""
echo "📋 Your custom files were preserved:"
echo "   ✅ .github/feedback/rubric.yml (or RUBRIC.md)"
echo "   ✅ .github/feedback/guidance.md"
echo "   ✅ .github/feedback/config.yml"
echo ""
echo "🧪 Next steps:"
echo "   1. Test the updated system locally:"
echo "      docker run --rm -v \$PWD:/docs ghcr.io/202420-phys-230/quarto:1 \\"
echo "        bash -c 'cd /docs && python .github/scripts/parse_report.py'"
echo ""
echo "   2. If everything works, commit the changes:"
echo "      git add .github/"
echo "      git commit -m \"Update AI feedback system to $VERSION\""
echo "      git push"
echo ""
echo "   3. If something breaks, restore from backup:"
echo "      rm -rf .github/scripts"
echo "      mv $BACKUP_DIR .github/scripts"
echo ""
