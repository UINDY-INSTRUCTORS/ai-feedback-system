#!/bin/bash

# get-feedback.sh
#
# Simple script for students to request AI feedback on their reports.
#
# This script:
# 1. Checks that all changes are committed
# 2. Checks that all commits are pushed to GitHub
# 3. Creates a new version tag
# 4. Pushes the tag to GitHub (which triggers the feedback workflow)
#
# Usage: ./get-feedback.sh
#

set -e

echo "================================================"
echo "Preparing to request feedback..."
echo "================================================"

# Check if gh (GitHub CLI) is installed
if ! command -v gh &> /dev/null; then
    echo "⚠️  GitHub CLI (gh) is not installed"
    echo "Installing gh via apt..."
    sudo apt-get update -qq
    sudo apt-get install -y gh
    echo "✅ GitHub CLI installed"
else
    echo "✅ GitHub CLI (gh) is available"
fi

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "❌ Error: Not in a git repository"
    exit 1
fi

# Check for uncommitted changes
if ! git diff-index --quiet HEAD --; then
    echo "❌ Error: You have uncommitted changes"
    echo ""
    echo "Please commit your changes first:"
    echo "  git add ."
    echo "  git commit -m 'Your message here'"
    exit 1
fi

# Check for untracked files
if [ -n "$(git ls-files --others --exclude-standard)" ]; then
    echo "❌ Error: You have untracked files"
    echo ""
    echo "Please add and commit them, or add them to .gitignore:"
    echo "  git add <files>"
    echo "  git commit -m 'Your message here'"
    exit 1
fi

echo "✅ All changes committed"

# Check if there are unpushed commits
if git rev-list @{u}..HEAD 2>/dev/null | grep -q .; then
    echo "❌ Error: You have unpushed commits"
    echo ""
    echo "Please push your changes first:"
    echo "  git push"
    exit 1
fi

echo "✅ All commits pushed to GitHub"

# Get the latest tag or default to feedback-v0.0.0
LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "feedback-v0.0.0")
echo "📌 Latest tag: $LATEST_TAG"

# Parse version and increment patch version
if [[ $LATEST_TAG =~ ^feedback-v([0-9]+)\.([0-9]+)\.([0-9]+)$ ]]; then
    MAJOR=${BASH_REMATCH[1]}
    MINOR=${BASH_REMATCH[2]}
    PATCH=${BASH_REMATCH[3]}
else
    echo "❌ Error: Tag format is invalid. Expected feedback-vX.Y.Z format"
    exit 1
fi

# Increment patch version
PATCH=$((PATCH + 1))
NEW_TAG="feedback-v${MAJOR}.${MINOR}.${PATCH}"

echo "📝 Creating new tag: $NEW_TAG"

# Create the tag
git tag -a "$NEW_TAG" -m "Request feedback on report"

# Push the tag to GitHub
echo "🚀 Pushing tag to GitHub..."
git push origin "$NEW_TAG"

echo ""
echo "================================================"
echo "✅ Feedback requested successfully!"
echo "================================================"
echo ""
echo "Your feedback workflow has been triggered."
echo "Check the Actions tab on GitHub to see the progress:"
echo "  https://github.com/$(git remote get-url origin | sed 's/.*://;s/\.git$//')/actions"
echo ""
echo "The AI will analyze your report and post feedback as a comment on your commit."
