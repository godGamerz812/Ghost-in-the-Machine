"""Small, dependency-free helpers for the local story archive."""
from __future__ import annotations

import json
import uuid
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterable


def normalize_tags(raw: str | Iterable[str] | None) -> list[str]:
    """Return a de-duplicated list of non-empty tags."""
    if raw is None:
        return []
    parts = raw.split(",") if isinstance(raw, str) else raw
    seen: set[str] = set()
    tags: list[str] = []
    for part in parts:
        tag = str(part).strip().lstrip("#")
        key = tag.casefold()
        if tag and key not in seen:
            tags.append(tag)
            seen.add(key)
    return tags


def create_story(
    title: str,
    transcript: str,
    story_date: str | date | None = None,
    tags: str | Iterable[str] | None = None,
    story_id: str | None = None,
) -> dict[str, Any]:
    """Validate and construct one archive record."""
    clean_title = title.strip()
    clean_transcript = transcript.strip()
    if not clean_title:
        raise ValueError("Story title cannot be empty.")
    if not clean_transcript:
        raise ValueError("Story transcript cannot be empty.")
    if isinstance(story_date, date):
        date_value = story_date.isoformat()
    elif story_date:
        date_value = str(story_date).strip()
        try:
            date.fromisoformat(date_value)
        except ValueError as exc:
            raise ValueError("Story date must use YYYY-MM-DD format.") from exc
    else:
        date_value = date.today().isoformat()

    return {
        "id": story_id or str(uuid.uuid4()),
        "title": clean_title,
        "story_date": date_value,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "tags": normalize_tags(tags),
        "transcript": clean_transcript,
    }


def load_stories(path: str | Path) -> list[dict[str, Any]]:
    """Load a JSON archive; a missing archive is an empty archive."""
    archive_path = Path(path)
    if not archive_path.exists():
        return []
    try:
        payload = json.loads(archive_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Could not read archive file: {exc}") from exc
    if not isinstance(payload, list) or any(not isinstance(row, dict) for row in payload):
        raise ValueError("Archive must contain a JSON list of story objects.")
    return payload


def save_archive(path: str | Path, stories: Iterable[dict[str, Any]]) -> None:
    """Write the archive as UTF-8 JSON, creating its parent directory."""
    archive_path = Path(path)
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    data = list(stories)
    temp_path = archive_path.with_suffix(archive_path.suffix + ".tmp")
    temp_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temp_path.replace(archive_path)


def add_story(path: str | Path, story: dict[str, Any]) -> list[dict[str, Any]]:
    stories = load_stories(path)
    if any(existing.get("id") == story.get("id") for existing in stories):
        raise ValueError("A story with this ID already exists.")
    stories.insert(0, story)
    save_archive(path, stories)
    return stories


def delete_story(path: str | Path, story_id: str) -> list[dict[str, Any]]:
    stories = load_stories(path)
    updated = [story for story in stories if story.get("id") != story_id]
    if len(updated) == len(stories):
        raise ValueError("Story not found.")
    save_archive(path, updated)
    return updated


def search_stories(stories: Iterable[dict[str, Any]], query: str) -> list[dict[str, Any]]:
    """Case-insensitive search across title, transcript, date, and tags."""
    needle = query.strip().casefold()
    rows = list(stories)
    if not needle:
        return rows
    matches = []
    for story in rows:
        searchable = " ".join(
            [
                str(story.get("title", "")),
                str(story.get("transcript", "")),
                str(story.get("story_date", "")),
                " ".join(str(tag) for tag in story.get("tags", [])),
            ]
        ).casefold()
        if needle in searchable:
            matches.append(story)
    return matches
