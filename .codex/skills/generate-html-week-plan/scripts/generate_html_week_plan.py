#!/usr/bin/env python3
"""Generate a weekly workout HTML plan from a directory of workout Markdown files."""

from __future__ import annotations

import argparse
import datetime as dt
import html
import re
import sys
from pathlib import Path

WEEKDAYS = [
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
]


def format_inline(text: str) -> str:
    """Escape HTML and render basic bold markup."""
    escaped = html.escape(text, quote=False)
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
    return escaped


def parse_notes(lines: list[str], start_index: int) -> tuple[str | None, int]:
    line = lines[start_index]
    notes = line[len("Notes:") :].strip()
    if notes:
        return notes, start_index + 1

    collected: list[str] = []
    index = start_index + 1
    while index < len(lines):
        candidate = lines[index].strip()
        if candidate.startswith("#"):
            break
        if candidate == "":
            if collected:
                break
            index += 1
            continue
        collected.append(candidate)
        index += 1

    notes = " ".join(collected).strip() if collected else None
    return notes, index


def parse_markdown(path: Path) -> dict:
    content = path.read_text(encoding="utf-8").splitlines()
    workout: dict = {"title": None, "notes": None, "phases": []}
    current_phase: dict | None = None
    current_block: dict | None = None
    intro_lines: list[str] = []

    def flush_block() -> None:
        nonlocal current_block
        if current_block and current_phase is not None:
            current_phase["blocks"].append(current_block)
        current_block = None

    def flush_phase() -> None:
        nonlocal current_phase
        if current_phase is not None:
            workout["phases"].append(current_phase)
        current_phase = None

    index = 0
    while index < len(content):
        line = content[index].rstrip()
        stripped = line.strip()

        if stripped.startswith("# "):
            workout["title"] = stripped[2:].strip()
            index += 1
            continue

        if stripped.startswith("Notes:") and workout["notes"] is None:
            notes, index = parse_notes(content, index)
            workout["notes"] = notes
            continue

        if stripped.startswith("## "):
            if intro_lines and workout["notes"] is None:
                workout["notes"] = " ".join(intro_lines).strip() or None
                intro_lines = []
            flush_block()
            flush_phase()
            phase_title = stripped[3:].strip()
            current_phase = {"title": phase_title, "blocks": []}
            index += 1
            continue

        if stripped.startswith("### "):
            if intro_lines and workout["notes"] is None:
                workout["notes"] = " ".join(intro_lines).strip() or None
                intro_lines = []
            flush_block()
            if current_phase is None:
                current_phase = {"title": "Session", "blocks": []}
            block_title = stripped[4:].strip()
            current_block = {"title": block_title, "items": []}
            index += 1
            continue

        if stripped and current_phase is None and current_block is None and workout["notes"] is None:
            intro_lines.append(stripped)
            index += 1
            continue

        if current_phase is not None and stripped and current_block is None:
            current_block = {"title": "", "items": []}

        if current_block is not None and stripped:
            current_block["items"].append(stripped)

        index += 1

    if intro_lines and workout["notes"] is None:
        workout["notes"] = " ".join(intro_lines).strip() or None

    flush_block()
    flush_phase()
    return workout


def split_phase_title(title: str) -> tuple[str | None, str]:
    match = re.match(r"^([A-Za-z]\d+)\s+—\s+(.+)$", title)
    if match:
        return match.group(1), match.group(2)
    return None, title


def split_day_title(title: str | None, day_label: str) -> str | None:
    if not title:
        return None
    cleaned = title.strip()
    if cleaned.lower().startswith("workout:"):
        cleaned = cleaned[len("workout:") :].strip()
    if "—" in cleaned:
        left, right = cleaned.split("—", 1)
        if left.strip().lower().startswith(day_label.lower()):
            return right.strip()
    return cleaned if cleaned else None


def segment_items(items: list[str]) -> list[dict]:
    segments: list[dict] = []
    for item in items:
        stripped = item.strip()
        if not stripped:
            continue
        ordered = re.match(r"^(\d+)\)\s*(.+)$", stripped)
        if ordered:
            content = ordered.group(2)
            if not segments or segments[-1]["type"] != "ol":
                segments.append({"type": "ol", "items": []})
            segments[-1]["items"].append(content)
            continue
        if stripped.startswith("-") or stripped.startswith("•"):
            content = stripped[1:].strip()
            if not segments or segments[-1]["type"] != "ul":
                segments.append({"type": "ul", "items": []})
            segments[-1]["items"].append(content)
            continue
        segments.append({"type": "p", "text": stripped})
    return segments


def render_block(block: dict) -> str:
    parts: list[str] = []
    parts.append('<div class="block">')
    title = str(block.get("title") or "").strip()
    if title:
        parts.append(f'<h4 class="block-title">{format_inline(title)}</h4>')
    segments = segment_items(block.get("items", []))
    if not segments:
        parts.append('<p class="empty">No exercises listed.</p>')
    else:
        for segment in segments:
            if segment["type"] == "p":
                parts.append(f'<p>{format_inline(segment["text"])}</p>')
            else:
                tag = segment["type"]
                parts.append(f"<{tag}>")
                for item in segment["items"]:
                    parts.append(f"<li>{format_inline(item)}</li>")
                parts.append(f"</{tag}>")
    parts.append("</div>")
    return "\n".join(parts)


def render_phase(phase: dict) -> str:
    code, name = split_phase_title(phase["title"])
    parts: list[str] = []
    parts.append('<section class="phase">')
    if code:
        parts.append(
            f'<h3 class="phase-title"><span class="phase-code">{format_inline(code)}</span>{format_inline(name)}</h3>'
        )
    else:
        parts.append(f'<h3 class="phase-title">{format_inline(name)}</h3>')
    for block in phase.get("blocks", []):
        parts.append(render_block(block))
    parts.append("</section>")
    return "\n".join(parts)


def render_day(day_key: str, workout: dict | None) -> str:
    day_label = day_key.capitalize()
    parts: list[str] = []
    parts.append('<article class="day">')
    parts.append('<div class="day-header">')
    parts.append(f'<h2 class="day-name">{format_inline(day_label)}</h2>')

    subtitle = split_day_title(workout.get("title") if workout else None, day_label)
    if subtitle:
        parts.append(f'<div class="day-subtitle">{format_inline(subtitle)}</div>')
    parts.append("</div>")

    if workout and workout.get("notes"):
        parts.append(
            f'<div class="notes"><span>Notes:</span>{format_inline(workout["notes"])}</div>'
        )

    if not workout or not workout.get("phases"):
        parts.append('<p class="empty">No workout details available.</p>')
    else:
        for phase in workout["phases"]:
            parts.append(render_phase(phase))

    parts.append("</article>")
    return "\n".join(parts)


def sort_day_keys(keys: list[str]) -> list[str]:
    order = {day: index for index, day in enumerate(WEEKDAYS)}
    return sorted(keys, key=lambda key: (order.get(key, 99), key))


def load_template(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def render_week(workouts: dict, include_missing: bool) -> str:
    keys = set(workouts.keys())
    if include_missing:
        keys.update(WEEKDAYS)
    ordered_keys = sort_day_keys(list(keys))
    parts: list[str] = []
    for key in ordered_keys:
        workout = workouts.get(key)
        parts.append(render_day(key, workout))
    return "\n".join(parts)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate a weekly workout HTML plan from a directory of Markdown workouts."
    )
    parser.add_argument("directory", help="Directory containing workout .md files")
    parser.add_argument(
        "--out",
        help="Output HTML file path (default: <directory>/week_plan.html)",
    )
    parser.add_argument(
        "--title",
        help="Optional title for the HTML document (default: Week Plan — <directory name>)",
    )
    parser.add_argument(
        "--template",
        help="Optional HTML template path (default: assets/week_template.html)",
    )
    parser.add_argument(
        "--include-missing",
        action="store_true",
        help="Include placeholder days with no workout files",
    )
    parser.add_argument(
        "--weekdays-only",
        action="store_true",
        help="Only include weekday-named markdown files (monday.md ... sunday.md).",
    )
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        help="Exclude specific markdown files by name (repeatable; e.g. --exclude backup or --exclude backup.md).",
    )
    args = parser.parse_args()

    directory = Path(args.directory).expanduser().resolve()
    if not directory.is_dir():
        print(f"Error: {directory} is not a directory.", file=sys.stderr)
        return 1

    template_path = (
        Path(args.template).expanduser().resolve()
        if args.template
        else Path(__file__).resolve().parent.parent / "assets" / "week_template.html"
    )
    if not template_path.exists():
        print(f"Error: template not found at {template_path}.", file=sys.stderr)
        return 1

    markdown_files = list(directory.glob("*.md"))
    if args.weekdays_only:
        markdown_files = [
            path for path in markdown_files if path.stem.lower() in WEEKDAYS
        ]
    excludes: set[str] = set()
    for raw in args.exclude:
        name = Path(str(raw).strip()).name
        if name.lower().endswith(".md"):
            name = name[: -len(".md")]
        name = name.strip().lower()
        if name:
            excludes.add(name)
    if excludes:
        markdown_files = [
            path for path in markdown_files if path.stem.strip().lower() not in excludes
        ]
    if not markdown_files:
        print(f"Error: no .md files found in {directory}.", file=sys.stderr)
        return 1

    workouts: dict[str, dict] = {}
    for md_path in markdown_files:
        key = md_path.stem.lower()
        workouts[key] = parse_markdown(md_path)

    title = args.title or f"Week Plan — {directory.name}"
    content = render_week(workouts, args.include_missing)
    generated_on = dt.datetime.now().strftime("%B %d, %Y")

    template = load_template(template_path)
    output_html = (
        template.replace("{{title}}", format_inline(title))
        .replace("{{generated_on}}", generated_on)
        .replace("{{content}}", content)
    )

    out_path = Path(args.out).expanduser().resolve() if args.out else directory / "week_plan.html"
    out_path.write_text(output_html, encoding="utf-8")
    print(f"Wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
