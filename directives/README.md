# Directives

This directory contains **SOP-style instructions** that define what needs to be done.

## Structure

Each directive should include:

1. **Goal** - What this directive accomplishes
2. **Inputs** - What data/parameters are required
3. **Tools/Scripts** - Which execution scripts to use
4. **Outputs** - What deliverables are produced
5. **Edge Cases** - Known constraints, limitations, or special handling

## Example Template

```markdown
# [Directive Name]

## Goal
[Clear statement of what this accomplishes]

## Inputs
- Input 1: [description]
- Input 2: [description]

## Tools/Scripts
- `execution/script_name.py`

## Outputs
- Output 1: [description and location]
- Output 2: [description and location]

## Edge Cases
- [Known limitation or special case]
- [API rate limits, timing constraints, etc.]

## Notes
[Any additional context or learnings]
```

## Guidelines

- Write directives as if briefing a competent teammate
- Use plain language, be specific
- Update directives when you learn new constraints or better approaches
- Directives are living documents that improve over time
