# Ghost in the Machine 👻

A local-first, open-source AI companion for preserving family stories and memories. Record a story, transcribe it locally with an open-weight speech model, and create a searchable archive without sending recordings to a hosted API.

> Privacy by design: the app is built to keep audio and transcripts on the machine running it. No cloud AI API is required. Do not upload sensitive recordings to a public deployment.

## Project status

This is a prototype intended to demonstrate the Week 4 “Ghost in the Machine” challenge theme: useful open-source AI at the core, with an open-weight model that can run locally. The application uses faster-whisper with an open-weight Whisper model. The first transcription may download model weights to the machine running the app; after they are cached, audio is processed locally without a hosted AI API.

## Features

- Record or upload an audio file for a personal story.
- Transcribe speech with `faster-whisper` using a local model (first run may download model weights).
- Save a story title, date, transcript, and optional tags into a local JSON archive.
- Search archived stories by title, transcript, or tags.
- Export an individual story or the whole archive as JSON.
- Clear privacy messaging: the prototype does not call a hosted AI API.

## Run locally

Python 3.10 or newer is recommended.

```bash
git clone https://github.com/godGamerz812/Ghost-in-the-Machine.git
cd Ghost-in-the-Machine
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
streamlit run app.py
```

The first transcription may need an internet connection to download model weights. Choose a model size appropriate for your hardware. If model setup is unavailable, you can still create, search, and export text stories manually.

## Privacy and safety

- Audio and archive files are stored on the machine where the app runs.
- Do not put private family audio on a public demo or shared machine.
- Do not treat machine transcripts as authoritative; review names, dates, and sensitive details.
- This prototype does not provide identity recognition, voice cloning, or a claim that speech recognition works on every language or device.

## Tests

```bash
pip install -r requirements-dev.txt
pytest -q
```

## Why this fits the challenge

The Week 4 prompt asks for open-source AI at the core and highlights an offline/local experience. This project applies that idea to a “ghost archive”: family stories can remain available on a person's own device, while a locally running open-weight speech model can help turn audio into searchable text.

## License

MIT. See [LICENSE](LICENSE).
