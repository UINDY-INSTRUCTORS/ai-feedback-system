#!/bin/bash
# validate_repos.sh
# Validation script to detect tampering with AI feedback system files
# Run this before final grading to ensure .github folder integrity across all student repos

set -e  # Exit on error

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ORG="${GITHUB_CLASSROOM_ORG:-}"
EXPECTED_CHECKSUM="${EXPECTED_CHECKSUM:-}"
CHECKSUM_FILE="${CHECKSUM_FILE:-.github_checksum}"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}AI Feedback System - Integrity Validation${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo -e "${RED}Error: GitHub CLI (gh) is not installed${NC}"
    echo "Install from: https://cli.github.com/"
    exit 1
fi

# Check if authenticated
if ! gh auth status &> /dev/null; then
    echo -e "${RED}Error: Not authenticated with GitHub CLI${NC}"
    echo "Run: gh auth login"
    exit 1
fi

# Function to compute checksum of .github folder
compute_checksum() {
    local repo_dir="$1"
    if [ ! -d "$repo_dir/.github" ]; then
        echo "NO_GITHUB_FOLDER"
        return
    fi

    # Compute checksum of all files in .github folder
    # Sorted by path for consistency
    find "$repo_dir/.github" -type f \
        \( -name "*.py" -o -name "*.yml" -o -name "*.yaml" -o -name "*.md" -o -name "*.sh" \) \
        -exec sha256sum {} \; 2>/dev/null | \
        sort -k 2 | \
        sha256sum | \
        cut -d' ' -f1
}

# Generate expected checksum from template
generate_expected_checksum() {
    echo -e "${BLUE}Generating expected checksum from template...${NC}"

    # Check if we're in the ai-feedback-system repo
    if [ -d "dot_github_folder" ]; then
        CHECKSUM=$(compute_checksum "dot_github_folder")
        echo -e "${GREEN}Expected checksum: $CHECKSUM${NC}"
        echo "$CHECKSUM" > "$CHECKSUM_FILE"
        echo -e "${GREEN}Saved to $CHECKSUM_FILE${NC}"
        echo ""
        echo "Set this as environment variable:"
        echo "  export EXPECTED_CHECKSUM='$CHECKSUM'"
        return 0
    else
        echo -e "${RED}Error: dot_github_folder not found${NC}"
        echo "Run this from the ai-feedback-system directory, or provide EXPECTED_CHECKSUM"
        return 1
    fi
}

# If --generate flag, generate checksum and exit
if [ "$1" = "--generate" ] || [ "$1" = "-g" ]; then
    generate_expected_checksum
    exit 0
fi

# Load expected checksum from file if not set
if [ -z "$EXPECTED_CHECKSUM" ] && [ -f "$CHECKSUM_FILE" ]; then
    EXPECTED_CHECKSUM=$(cat "$CHECKSUM_FILE")
    echo -e "${BLUE}Loaded expected checksum from $CHECKSUM_FILE${NC}"
fi

# Prompt for expected checksum if not set
if [ -z "$EXPECTED_CHECKSUM" ]; then
    echo -e "${YELLOW}Expected checksum not set.${NC}"
    echo ""
    echo "Options:"
    echo "  1. Generate from template: $0 --generate"
    echo "  2. Set manually: export EXPECTED_CHECKSUM='your-checksum-here'"
    echo ""
    exit 1
fi

# Prompt for organization if not set
if [ -z "$ORG" ]; then
    echo -e "${YELLOW}Enter your GitHub Classroom organization name:${NC}"
    read -r ORG
fi

if [ -z "$ORG" ]; then
    echo -e "${RED}Error: Organization name is required${NC}"
    exit 1
fi

# Verify organization access
echo -e "${BLUE}Verifying access to organization: $ORG${NC}"
if ! gh api "/orgs/$ORG" &> /dev/null; then
    echo -e "${RED}Error: Cannot access organization '$ORG'${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Organization access verified${NC}"
echo ""

# Create temporary directory for cloning
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

# Get all repos in organization
echo -e "${BLUE}Fetching repositories from $ORG...${NC}"
REPOS=$(gh api "/orgs/$ORG/repos" --paginate --jq '.[].name')

if [ -z "$REPOS" ]; then
    echo -e "${RED}Error: No repositories found in organization '$ORG'${NC}"
    exit 1
fi

REPO_COUNT=$(echo "$REPOS" | wc -l)
echo -e "${GREEN}✓ Found $REPO_COUNT repositories${NC}"
echo ""
echo -e "${BLUE}Validating repositories...${NC}"
echo -e "${BLUE}Expected checksum: $EXPECTED_CHECKSUM${NC}"
echo ""

# Arrays to track results
VALID_REPOS=()
INVALID_REPOS=()
MISSING_REPOS=()
ERROR_REPOS=()

for repo in $REPOS; do
    echo -n "Checking $repo... "

    # Clone repository
    if ! gh repo clone "$ORG/$repo" "$TEMP_DIR/$repo" -- --quiet --depth 1 &>/dev/null; then
        echo -e "${RED}ERROR${NC} (failed to clone)"
        ERROR_REPOS+=("$repo")
        continue
    fi

    # Compute checksum
    ACTUAL_CHECKSUM=$(compute_checksum "$TEMP_DIR/$repo")

    if [ "$ACTUAL_CHECKSUM" = "NO_GITHUB_FOLDER" ]; then
        echo -e "${YELLOW}MISSING${NC} (.github folder not found)"
        MISSING_REPOS+=("$repo")
    elif [ "$ACTUAL_CHECKSUM" = "$EXPECTED_CHECKSUM" ]; then
        echo -e "${GREEN}VALID${NC}"
        VALID_REPOS+=("$repo")
    else
        echo -e "${RED}TAMPERED${NC} (checksum mismatch)"
        INVALID_REPOS+=("$repo")
    fi

    # Clean up
    rm -rf "$TEMP_DIR/$repo"
done

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Validation Results${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Summary
echo -e "${GREEN}Valid:${NC} ${#VALID_REPOS[@]} repositories"
echo -e "${YELLOW}Missing .github:${NC} ${#MISSING_REPOS[@]} repositories"
echo -e "${RED}Tampered:${NC} ${#INVALID_REPOS[@]} repositories"
echo -e "${RED}Errors:${NC} ${#ERROR_REPOS[@]} repositories"
echo ""

# Details for invalid repos
if [ ${#INVALID_REPOS[@]} -gt 0 ]; then
    echo -e "${RED}⚠️  TAMPERING DETECTED in the following repositories:${NC}"
    for repo in "${INVALID_REPOS[@]}"; do
        echo -e "  ${RED}•${NC} $ORG/$repo"
    done
    echo ""
    echo "These repositories have modified .github folders."
    echo "Investigate before grading:"
    echo "  gh repo clone $ORG/REPO_NAME"
    echo "  cd REPO_NAME"
    echo "  git log --all -- .github/"
    echo ""
fi

# Details for missing repos
if [ ${#MISSING_REPOS[@]} -gt 0 ]; then
    echo -e "${YELLOW}⚠️  .github folder MISSING in the following repositories:${NC}"
    for repo in "${MISSING_REPOS[@]}"; do
        echo -e "  ${YELLOW}•${NC} $ORG/$repo"
    done
    echo ""
    echo "These repositories may not have the feedback system deployed."
    echo ""
fi

# Details for error repos
if [ ${#ERROR_REPOS[@]} -gt 0 ]; then
    echo -e "${RED}⚠️  ERRORS accessing the following repositories:${NC}"
    for repo in "${ERROR_REPOS[@]}"; do
        echo -e "  ${RED}•${NC} $ORG/$repo"
    done
    echo ""
fi

# Save report
REPORT_FILE="validation_report_$(date +%Y%m%d_%H%M%S).txt"
{
    echo "AI Feedback System - Integrity Validation Report"
    echo "Generated: $(date)"
    echo "Organization: $ORG"
    echo "Expected Checksum: $EXPECTED_CHECKSUM"
    echo ""
    echo "Summary:"
    echo "  Valid: ${#VALID_REPOS[@]}"
    echo "  Missing .github: ${#MISSING_REPOS[@]}"
    echo "  Tampered: ${#INVALID_REPOS[@]}"
    echo "  Errors: ${#ERROR_REPOS[@]}"
    echo ""

    if [ ${#INVALID_REPOS[@]} -gt 0 ]; then
        echo "Tampered Repositories:"
        printf '  %s\n' "${INVALID_REPOS[@]}"
        echo ""
    fi

    if [ ${#MISSING_REPOS[@]} -gt 0 ]; then
        echo "Missing .github Repositories:"
        printf '  %s\n' "${MISSING_REPOS[@]}"
        echo ""
    fi

    if [ ${#ERROR_REPOS[@]} -gt 0 ]; then
        echo "Error Repositories:"
        printf '  %s\n' "${ERROR_REPOS[@]}"
        echo ""
    fi
} > "$REPORT_FILE"

echo -e "${GREEN}Report saved to: $REPORT_FILE${NC}"
echo ""

# Exit code
if [ ${#INVALID_REPOS[@]} -gt 0 ]; then
    echo -e "${RED}❌ Validation FAILED - tampering detected${NC}"
    exit 1
elif [ ${#MISSING_REPOS[@]} -gt 0 ]; then
    echo -e "${YELLOW}⚠️  Validation WARNING - some repos missing .github${NC}"
    exit 2
else
    echo -e "${GREEN}✓ All repositories validated successfully${NC}"
    exit 0
fi
