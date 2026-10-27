from datetime import date

import pytest

from story_archive import (
    add_story,
    create_story,
    delete_story,
    load_stories,
    normalize_tags,
    save_archive,
    search_stories,
)


def test_create_story_trims_fields_and_normalizes_tags():
    story = create_story(
        "  Grandma's recipe  ",
        "  We made bread every Sunday.  ",
        date(2020, 5, 2),
        "family, Food, family, #food",
        story_id="story-1",
    )
    assert story["title"] == "Grandma's recipe"
    assert story["transcript"] == "We made bread every Sunday."
    assert story["story_date"] == "2020-05-02"
    assert story["tags"] == ["family", "Food"]
    assert story["id"] == "story-1"
    assert story["created_at"]


@pytest.mark.parametrize(
    ("title", "transcript"),
    [("", "a story"), ("title", ""), ("   ", "  ")],
)
def test_create_story_requires_title_and_transcript(title, transcript):
    with pytest.raises(ValueError):
        create_story(title, transcript)


def test_invalid_date_is_rejected():
    with pytest.raises(ValueError, match="YYYY-MM-DD"):
        create_story("Title", "Text", "not-a-date")


def test_normalize_tags_handles_empty_and_duplicate_values():
    assert normalize_tags(None) == []
    assert normalize_tags(" , #Family, family, recipe ") == ["Family", "recipe"]


def test_missing_archive_is_empty(tmp_path):
    assert load_stories(tmp_path / "missing.json") == []


def test_save_and_load_archive_round_trip(tmp_path):
    path = tmp_path / "nested" / "stories.json"
    stories = [create_story("Memory", "A remembered event", story_id="one")]
    save_archive(path, stories)
    assert load_stories(path) == stories


def test_add_story_and_prevent_duplicate_id(tmp_path):
    path = tmp_path / "stories.json"
    story = create_story("Memory", "A remembered event", story_id="one")
    assert add_story(path, story) == [story]
    with pytest.raises(ValueError, match="already exists"):
        add_story(path, story)


def test_search_is_case_insensitive_and_searches_tags():
    stories = [
        create_story("Summer Trip", "We visited DELHI.", tags="Travel, Family", story_id="one"),
        create_story("Garden", "We planted roses.", tags="outdoors", story_id="two"),
    ]
    assert [s["id"] for s in search_stories(stories, "delhi")] == ["one"]
    assert [s["id"] for s in search_stories(stories, "FAMILY")] == ["one"]
    assert [s["id"] for s in search_stories(stories, "not found")] == []


def test_delete_story(tmp_path):
    path = tmp_path / "stories.json"
    first = create_story("One", "First", story_id="one")
    second = create_story("Two", "Second", story_id="two")
    save_archive(path, [first, second])
    assert [s["id"] for s in delete_story(path, "one")] == ["two"]
    with pytest.raises(ValueError, match="not found"):
        delete_story(path, "missing")


def test_corrupt_archive_reports_readable_error(tmp_path):
    path = tmp_path / "broken.json"
    path.write_text("{not json", encoding="utf-8")
    with pytest.raises(ValueError, match="Could not read archive"):
        load_stories(path)
