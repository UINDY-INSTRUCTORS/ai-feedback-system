#!/bin/bash
# Compare deterministic vs AI-based section extraction

echo "=================================================="
echo "Section Extraction Method Comparison"
echo "=================================================="
echo ""

# Check for required files
if [ ! -f "parsed_report.json" ]; then
    echo "❌ Error: parsed_report.json not found"
    echo "Run: python scripts/parse_report.py"
    exit 1
fi

if [ ! -f ".github/feedback/rubric.yml" ]; then
    echo "❌ Error: rubric.yml not found"
    exit 1
fi

# Test deterministic extraction
echo "1️⃣  Testing DETERMINISTIC extraction (keyword-based)..."
echo "   Using section_extractor.py"
echo ""

USE_AI_EXTRACTION=false python scripts/ai_feedback_criterion_ai_extract.py > deterministic_output.log 2>&1
mv feedback.md feedback_deterministic.md

echo "   ✅ Output saved to: feedback_deterministic.md"
echo ""

# Test AI extraction
echo "2️⃣  Testing AI EXTRACTION (LLM-based)..."
echo "   Using ai_section_extractor.py"
echo ""

USE_AI_EXTRACTION=true python scripts/ai_feedback_criterion_ai_extract.py > ai_output.log 2>&1
mv feedback.md feedback_ai.md

echo "   ✅ Output saved to: feedback_ai.md"
echo ""

# Compare results
echo "=================================================="
echo "Comparison Summary"
echo "=================================================="
echo ""

det_size=$(wc -c < feedback_deterministic.md)
ai_size=$(wc -c < feedback_ai.md)

det_words=$(wc -w < feedback_deterministic.md)
ai_words=$(wc -w < feedback_ai.md)

echo "File Sizes:"
echo "  Deterministic: $det_size bytes ($det_words words)"
echo "  AI-based:      $ai_size bytes ($ai_words words)"
echo ""

# Check which criteria were analyzed
det_criteria=$(grep -c "^### " feedback_deterministic.md)
ai_criteria=$(grep -c "^### " feedback_ai.md)

echo "Criteria Analyzed:"
echo "  Deterministic: $det_criteria"
echo "  AI-based:      $ai_criteria"
echo ""

# Extract token usage from logs
det_tokens=$(grep -oP "Total estimated tokens: \K\d+" deterministic_output.log || echo "N/A")
ai_tokens=$(grep -oP "Total estimated tokens: \K\d+" ai_output.log || echo "N/A")

echo "Token Usage:"
echo "  Deterministic: $det_tokens tokens"
echo "  AI-based:      $ai_tokens tokens"
echo ""

echo "=================================================="
echo "Files Generated:"
echo "=================================================="
echo "  📄 feedback_deterministic.md - Keyword-based extraction"
echo "  📄 feedback_ai.md - AI-based extraction"
echo "  📋 deterministic_output.log - Execution log"
echo "  📋 ai_output.log - Execution log"
echo ""
echo "💡 Tip: Use 'diff feedback_deterministic.md feedback_ai.md' to see differences"
echo ""
