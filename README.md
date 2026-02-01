# Workouts

A lightweight repository of workout sessions stored as Markdown.

## Structure

Workouts are grouped into directories by month and region. Expect multiple folders over time, e.g.:

- `2026_01_us/` — January 2026 workouts (US), one file per day
- `2026_01_eu/` — January 2026 workouts (EU)
- `2026_02_us/` — future month example

Each directory contains day-of-week files such as:

- `monday.md`
- `tuesday.md`
- `thursday.md`
- `friday.md`
- `saturday.md`

## Workout Template

The canonical workout template lives here:

- `.codex/skills/format_workout/assets/template.md`

Use it as the starting point for new workouts to keep formatting consistent.

## Adding a Workout

1. Copy the template file into the appropriate month/region folder.
2. Rename it to the day of the week.
3. Fill in phases, blocks, and exercises.

## Notes

If you’re using Codex, the `format_workout` skill can format raw workout notes into the template style.

## Generate HTML Week Plans

To export a week directory (e.g., `202601_us/`) into a nicely formatted HTML plan, use the `generate-html-week-plan` skill script:

```bash
python3 .codex/skills/generate-html-week-plan/scripts/generate_html_week_plan.py 202601_us
```

This writes `week_plan.html` into the target directory. Use `--out` to choose a different output path, or `--title` to override the page title.
