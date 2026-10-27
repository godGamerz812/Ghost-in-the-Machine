"""Ghost in the Machine: a local-first oral-history archive."""
from __future__ import annotations

import json
import os
import tempfile
from datetime import date
from pathlib import Path

import streamlit as st

from story_archive import add_story, create_story, delete_story, load_stories, search_stories

st.set_page_config(page_title="Ghost in the Machine", page_icon="👻", layout="centered")

ARCHIVE_PATH = Path(os.environ.get("GHOST_ARCHIVE_PATH", "stories.json"))

st.title("👻 Ghost in the Machine")
st.subheader("A private archive for the stories we don't want to lose")
st.write(
    "Capture a family memory, transcribe it with an open-weight speech model running "
    "on this machine, and keep the text searchable in a simple local archive."
)

st.info(
    "**Privacy note:** Run this app on your own computer for private stories. "
    "When hosted on Streamlit Community Cloud or another server, processing and the "
    "JSON archive live on that server, not on your phone. Do not upload sensitive family "
    "recordings to a public demo. The app does not call a hosted AI API."
)


def get_stories() -> list[dict]:
    try:
        return load_stories(ARCHIVE_PATH)
    except ValueError as exc:
        st.error(f"Archive problem: {exc}")
        return []


def transcribe_locally(audio_bytes: bytes, filename: str, model_size: str) -> str:
    """Transcribe using faster-whisper on the same machine as this app."""
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise RuntimeError(
            "Local transcription dependencies are not installed. Run "
            "pip install -r requirements-ai.txt and restart the app."
        ) from exc

    suffix = Path(filename or "recording.wav").suffix or ".wav"
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(prefix="ghost_story_", suffix=suffix, delete=False) as handle:
            handle.write(audio_bytes)
            temp_path = Path(handle.name)
        # CPU/int8 gives a broadly compatible default. Download happens only when
        # the chosen model is not already cached on this machine.
        model = WhisperModel(model_size, device="cpu", compute_type="int8")
        segments, _info = model.transcribe(str(temp_path), beam_size=5, vad_filter=True)
        return " ".join(segment.text.strip() for segment in segments).strip()
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)


create_tab, archive_tab, about_tab = st.tabs(["Capture a story", "Story archive", "How it works"])

with create_tab:
    st.markdown("### Start with a memory")
    title = st.text_input("Story title", placeholder="e.g. Grandmother's first journey")
    story_day = st.date_input("When did it happen?", value=date.today())
    tag_text = st.text_input("Tags (comma-separated)", placeholder="family, childhood, recipes")

    recorder = getattr(st, "audio_input", None)
    audio_file = None
    if recorder is not None:
        audio_file = recorder("Record a story (optional)")
    uploaded_audio = st.file_uploader(
        "Or upload an audio recording",
        type=["wav", "mp3", "m4a", "ogg", "flac", "webm"],
        help="Audio is processed by a local model when you run this app locally.",
    )
    if uploaded_audio is not None:
        audio_file = uploaded_audio

    model_size = st.selectbox(
        "Local speech model",
        options=["tiny", "base", "small"],
        index=0,
        help="Tiny is the lightest. Larger models may be more accurate but need more time and memory.",
    )
    if audio_file is not None:
        st.audio(audio_file)

    if st.button("Transcribe with local model", type="secondary", disabled=audio_file is None):
        try:
            with st.spinner("Loading the local model and transcribing…"):
                transcript = transcribe_locally(audio_file.getvalue(), audio_file.name or "recording.wav", model_size)
            if transcript:
                st.session_state["story_transcript"] = transcript
                st.success("Transcription completed. Review it before saving.")
            else:
                st.warning("No speech was detected. You can type the transcript below.")
        except Exception as exc:
            st.error(f"Local transcription did not complete: {exc}")

    transcript_text = st.text_area(
        "Transcript / story text",
        key="story_transcript",
        height=220,
        placeholder="Write a story here, or transcribe an audio recording with the local model.",
        help="Review names, dates, and details before saving. Automatic transcription can make mistakes.",
    )
    if st.button("Save story to this machine", type="primary"):
        if not title.strip():
            st.error("Please add a story title.")
        elif not transcript_text.strip():
            st.error("Please add a transcript or story text.")
        else:
            try:
                story = create_story(title, transcript_text, story_day, tag_text)
                add_story(ARCHIVE_PATH, story)
                st.success("Story saved to the local JSON archive.")
                st.session_state["story_transcript"] = ""
                st.rerun()
            except (OSError, ValueError) as exc:
                st.error(f"Story could not be saved: {exc}")

with archive_tab:
    st.markdown("### Your saved memories")
    all_stories = get_stories()
    st.caption(f"{len(all_stories)} story/stories in {ARCHIVE_PATH}")
    query = st.text_input("Search titles, transcripts, dates, or tags", key="archive_search")
    matching_stories = search_stories(all_stories, query)
    if not matching_stories:
        st.write("No matching stories yet. Save a story in the Capture a story tab to begin.")
    for story in matching_stories:
        heading = f"{story.get('title', 'Untitled')} · {story.get('story_date', 'Undated')}"
        with st.expander(heading):
            tags = story.get("tags", [])
            if tags:
                st.caption("Tags: " + ", ".join(str(tag) for tag in tags))
            st.write(story.get("transcript", ""))
            st.download_button(
                "Download this story (JSON)",
                data=json.dumps(story, ensure_ascii=False, indent=2),
                file_name=f"story-{story.get('id', 'export')}.json",
                mime="application/json",
                key=f"download-{story.get('id', 'unknown')}",
            )
            if st.button("Delete this story", key=f"delete-{story.get('id', 'unknown')}"):
                try:
                    delete_story(ARCHIVE_PATH, str(story.get("id", "")))
                    st.success("Story deleted.")
                    st.rerun()
                except (OSError, ValueError) as exc:
                    st.error(f"Could not delete story: {exc}")

    if all_stories:
        st.download_button(
            "Export full archive (JSON)",
            data=json.dumps(all_stories, ensure_ascii=False, indent=2),
            file_name="ghost-in-the-machine-archive.json",
            mime="application/json",
            key="download-full-archive",
        )

with about_tab:
    st.markdown(
        """
        ### Designed to keep memories close

        1. Record audio or upload a recording.
        2. Run an open-weight Whisper speech model locally through faster-whisper.
        3. Review the transcript and correct mistakes.
        4. Save and search stories in a local JSON file.

        **Local model setup:** install requirements-ai.txt. The first run may need an
        internet connection to download model weights; after they are cached, transcription
        can run locally. Model size affects speed and memory use.

        **Limitations:** this is a single-user prototype, not an encrypted vault or a
        multi-user service. Anyone with access to the machine and archive file may be able
        to read the stories. Back up the JSON archive yourself. Avoid using a shared/public
        deployment for private content.
        """
    )
    st.code("pip install -r requirements-ai.txt\nstreamlit run app.py", language="bash")
