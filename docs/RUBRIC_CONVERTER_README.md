# Rubric Converter - Quick Reference

Convert between YAML rubrics (for the AI system) and Markdown rubrics (for humans).

## Commands

### Convert YAML to Markdown
```bash
python rubric_converter.py yaml-to-md input.yml output.md
```

### Convert Markdown to YAML
```bash
python rubric_converter.py md-to-yaml input.md output.yml
```

### Validate Round-Trip
```bash
python rubric_converter.py validate rubric.yml
```

## Docker Usage (Recommended)

```bash
# YAML → Markdown
docker run --rm -v $PWD:/work -w /work ghcr.io/202420-phys-230/quarto:1 \
  python3 .github/scripts/rubric_converter.py yaml-to-md rubric.yml RUBRIC.md

# Markdown → YAML
docker run --rm -v $PWD:/work -w /work ghcr.io/202420-phys-230/quarto:1 \
  python3 .github/scripts/rubric_converter.py md-to-yaml RUBRIC.md rubric.yml

# Validate
docker run --rm -v $PWD:/work -w /work ghcr.io/202420-phys-230/quarto:1 \
  python3 .github/scripts/rubric_converter.py validate rubric.yml
```

## Typical Workflow

**For Faculty Writing a New Rubric:**

1. Copy example markdown:
```bash
cp examples/phys-230-lab-example-RUBRIC.md .github/feedback/RUBRIC.md
```

2. Edit `RUBRIC.md` in any text editor

3. Convert to YAML:
```bash
docker run --rm -v $PWD:/work -w /work ghcr.io/202420-phys-230/quarto:1 \
  python3 .github/scripts/rubric_converter.py md-to-yaml \
  .github/feedback/RUBRIC.md .github/feedback/rubric.yml
```

4. Deploy:
```bash
git add .github/feedback/
git commit -m "Add rubric"
git push
```

## See Also

- **Full documentation**: [docs/RUBRIC_CONVERTER.md](../../docs/RUBRIC_CONVERTER.md)
- **Examples**: [examples/](../../examples/)

## Quick Tips

✅ **DO**: Write in Markdown (easier for humans)
✅ **DO**: Validate after converting (`validate` command)
✅ **DO**: Commit both `.md` and `.yml` files

❌ **DON'T**: Edit both files (pick one as source of truth)
❌ **DON'T**: Forget to regenerate after editing source
❌ **DON'T**: Mix tabs and spaces in YAML
