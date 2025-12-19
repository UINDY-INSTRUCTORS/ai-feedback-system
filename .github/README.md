# AI Feedback System Documentation

This directory contains the configuration and documentation for the automated AI feedback system used in EENG 320 lab assignments.

## 📚 Documentation Index

### For Instructors

1. **[SETUP_GUIDE.md](./SETUP_GUIDE.md)** - Quick setup for deploying to your class
   - ⚡ Start here for fast deployment
   - ✅ Step-by-step checklist
   - 🎯 Takes ~30 minutes for first-time setup

2. **[GITHUB_MODELS_SETTINGS.md](./GITHUB_MODELS_SETTINGS.md)** - Comprehensive reference
   - 🔍 Detailed rate limit information
   - 🏢 Enterprise/Education account settings
   - 📊 Capacity planning for different class sizes
   - 🛠️ Troubleshooting guide

### Configuration Files

3. **[config.yml](./config.yml)** - System configuration
   - 🤖 Model selection (gpt-4o, gpt-4o-mini, etc.)
   - ⚙️ Token limits and timeouts
   - 🏷️ Issue labeling settings
   - 📊 Feature flags

4. **[rubric.yml](./rubric.yml)** - Grading rubric
   - 📋 Criterion definitions
   - 🎯 Performance levels (Exemplary, Satisfactory, etc.)
   - 💯 Point allocations
   - 🔑 Keywords for content detection

5. **[guidance.md](./guidance.md)** - AI instructions
   - 📖 Feedback philosophy and tone
   - ✍️ Formatting guidelines
   - ⚠️ Common student mistakes to watch for
   - 💡 Examples of good vs. bad feedback

## 🚀 Quick Start

### For Instructors Deploying This System

**Answer to: "What settings do I need to adjust in my enterprise account?"**

1. **Enable GitHub Models API** in your organization:
   - Organization Settings → Copilot → Models → Enable
   - Select models: `gpt-4o` and `gpt-4o-mini`

2. **Your education account benefits:**
   - ✅ **5,000 requests/hour** (vs. 150/day for free tier)
   - ✅ **No daily caps**
   - ✅ **Sufficient for 100+ students**

3. **Follow**: [SETUP_GUIDE.md](./SETUP_GUIDE.md) for complete instructions

### For Students Using This System

To request feedback on your lab report:

```bash
# 1. Complete your work and commit
git add .
git commit -m "Complete lab report"
git push

# 2. Tag and request feedback
git tag feedback-v1
git push origin feedback-v1

# 3. Check the "Issues" tab in ~5-10 minutes
```

For subsequent feedback:
```bash
git tag feedback-v2  # increment version number
git push origin feedback-v2
```

## 🎯 System Overview

### How It Works

1. **Student triggers**: Pushes a git tag starting with `feedback-` or `review-`
2. **GitHub Actions**: Workflow starts automatically
3. **Report parsing**: Extracts content, figures, code, equations
4. **AI analysis**: Each rubric criterion analyzed separately using GitHub Models API
5. **Feedback generation**: Combines analyses into comprehensive feedback
6. **Issue creation**: Posts feedback as GitHub Issue

### What Gets Analyzed

Per criterion evaluation of:
- ✅ Problem formulation and design goals
- ✅ Design development and justification
- ✅ Background research and datasheets
- ✅ Simulations and predictions
- ✅ Experimental setup and measurements
- ✅ Results interpretation and error analysis
- ✅ Design judgements (economic, environmental, societal)
- ✅ Conclusions and lessons learned

### Feedback Quality

Each criterion receives:
- 📊 Performance level assessment
- 💪 Specific strengths (what's working well)
- 📈 Areas for improvement (actionable suggestions)
- 💯 Suggested point allocation
- 🔗 References to specific sections, figures, equations

## 📊 Rate Limits and Capacity

### Education Account Benefits

Your GitHub Education organization has:
- **Rate limit**: 5,000 requests/hour
- **Daily limit**: No cap (enterprise tier)
- **Token limits**: Model-dependent (4K-128K)
- **Cost**: Included in GitHub Education benefits

### Capacity by Class Size

| Class Size | API Calls | Time to Complete | Within Limits? |
|------------|-----------|------------------|----------------|
| 25 students | ~250 | ~5 minutes | ✅ |
| 50 students | ~500 | ~8 minutes | ✅ |
| 100 students | ~1,000 | ~12 minutes | ✅ |
| 200 students | ~2,000 | ~20 minutes | ✅ |

**Note**: This assumes all students request feedback simultaneously (worst case).

## 🔧 Customization

### Adjusting for Your Course

1. **Update rubric** ([rubric.yml](./rubric.yml)):
   - Modify criteria weights
   - Adjust performance level descriptions
   - Add/remove criteria
   - Update keywords

2. **Tune AI behavior** ([guidance.md](./guidance.md)):
   - Adjust feedback philosophy
   - Add course-specific context
   - Update common mistakes list
   - Modify tone and style

3. **Configure system** ([config.yml](./config.yml)):
   - Change model (gpt-4o, gpt-4o-mini, claude)
   - Adjust token limits
   - Modify timeout settings
   - Enable/disable features

### Model Selection Recommendations

| Class Size | Recommended Model | Rationale |
|------------|------------------|-----------|
| < 30 students | `gpt-4o` | Best quality, sufficient capacity |
| 30-100 students | `gpt-4o-mini` | Good quality, faster, economical |
| > 100 students | `gpt-4o-mini` | Fast, economical, with staggering |

## 🛠️ Troubleshooting

### Common Issues

| Issue | Likely Cause | Solution |
|-------|--------------|----------|
| Rate limit errors | Models API not enabled | Enable in org settings |
| Token limit errors | Very long report | Reduce `max_input_tokens` in config |
| Workflow timeout | Many criteria or slow network | Increase `workflow_timeout` |
| Incomplete feedback | Parsing error | Check workflow logs, verify report structure |
| No feedback issue | Missing permissions | Verify workflow has `issues: write` permission |

### Getting Help

1. Check workflow logs (Actions tab in repository)
2. Download artifacts for detailed error messages
3. Review [GITHUB_MODELS_SETTINGS.md](./GITHUB_MODELS_SETTINGS.md) troubleshooting section
4. Contact GitHub Education support for account issues

## 📈 Monitoring and Maintenance

### Recommended Monitoring

**Weekly**:
- [ ] Check organization usage dashboard
- [ ] Review failed workflow runs
- [ ] Spot-check feedback quality

**Monthly**:
- [ ] Survey students on feedback usefulness
- [ ] Adjust rubric based on common issues
- [ ] Update AI guidance if needed
- [ ] Review and optimize model selection

### Usage Dashboard

View your organization's Models API usage:
1. Go to: Organization Settings → Copilot → Usage
2. Select "Models API" tab
3. Review request patterns and volumes
4. Set up alerts for unusual activity

## 🎓 Educational Context

### Course: EENG 320 - Electronics

This system is designed for junior-level electrical engineering students learning:
- Analog circuit design and analysis
- SPICE simulation and modeling
- Experimental measurement techniques
- Technical documentation and reporting
- Engineering design process

### Report Structure

Students submit **Quarto reports** combining:
- 📝 Markdown text with LaTeX equations
- 🐍 Python code for data analysis
- 📊 Plots and visualizations
- 🔌 KiCAD schematics
- 📈 Simulation results
- 🔬 Experimental measurements

### Pedagogical Goals

The AI feedback system helps students:
1. **Learn iteratively**: Get feedback before final submission
2. **Understand rubric**: See how their work maps to criteria
3. **Improve systematically**: Receive specific, actionable suggestions
4. **Self-assess**: Compare their work to performance levels
5. **Develop skills**: Learn professional technical documentation

## 🤝 Contributing

### Improving This System

Contributions welcome:
- 🐛 Bug fixes for parsing or feedback generation
- 📖 Documentation improvements
- 🎯 Rubric refinements
- 🤖 AI prompt engineering
- 🧪 Testing and validation

### Repository Structure

```
.github/
├── feedback/
│   ├── README.md                    # This file
│   ├── SETUP_GUIDE.md              # Quick setup
│   ├── GITHUB_MODELS_SETTINGS.md   # Detailed reference
│   ├── config.yml                  # Configuration
│   ├── rubric.yml                  # Grading rubric
│   └── guidance.md                 # AI instructions
└── workflows/
    └── report-feedback.yml         # GitHub Actions workflow

scripts/
├── ai_feedback_criterion.py        # Main feedback generator
├── parse_report.py                 # Report parser
├── create_issue.py                 # Issue creator
└── section_extractor.py           # Content extractor
```

## 📝 Version History

- **v3.0** (2025): Criterion-based analysis, parallel processing
- **v2.0** (2025): Added enterprise documentation and setup guides
- **v1.0** (2024): Initial implementation with GitHub Models

## 📄 License

This feedback system is part of educational materials for EENG 320. Configuration files and documentation can be adapted for other courses.

## 🙏 Acknowledgments

- GitHub Models API for AI access
- GitHub Education for enterprise benefits
- GitHub Classroom for assignment management
- EENG 320 students for feedback and testing

---

**Questions?** See [SETUP_GUIDE.md](./SETUP_GUIDE.md) for quick answers or [GITHUB_MODELS_SETTINGS.md](./GITHUB_MODELS_SETTINGS.md) for comprehensive details.
