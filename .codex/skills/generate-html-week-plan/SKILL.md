---
name: generate-html-week-plan
description: Generate a nicely formatted HTML weekly workout plan from a directory of workout Markdown files (e.g., 202601_us with monday.md, tuesday.md, etc.). Use when you need a shareable weekly HTML view of the workout template structure (phases, blocks, exercises) or when exporting a week plan to HTML.
---

# Generate HTML Week Plan

## Quick Start

1) Identify the directory that contains the workout Markdown files (e.g., `202601_us/`).
2) Run the script:

```bash
python3 scripts/generate_html_week_plan.py 202601_us
```

This writes `week_plan.html` inside the directory.

## Options

- `--out <path>`: write to a specific HTML file.
- `--title "..."`: override the document title.
- `--include-missing`: include placeholders for missing weekdays.
- `--weekdays-only`: only include weekday files (`monday.md` ... `sunday.md`).
- `--template <path>`: use a custom HTML template (default is `assets/week_template.html`).

## Notes on Parsing

- The script expects the workout template structure: `#` title, `##` phases, `###` blocks, and lines under blocks for exercises.
- It preserves block/exercise text exactly, only converting `**bold**` to HTML.
- If a workout file has `Notes:` it becomes a highlighted notes panel in the HTML.

## Resources

- `scripts/generate_html_week_plan.py`: CLI script that renders the weekly HTML.
- `assets/week_template.html`: base HTML + CSS template. Edit or copy this to customize styling.
