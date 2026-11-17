# realtimetts-gmicloud

GMI Cloud text-to-speech engine for [RealtimeTTS](https://github.com/KoljaB/RealtimeTTS).

One engine covers the speech model families behind GMI Cloud's multimodal
inference request queue:

- **Inworld Realtime TTS** (`inworld-tts-*`) — the low-latency option, well
  suited to real-time conversation.
- **MiniMax speech synthesis** (`minimax-tts-speech-*`).
- **Resemble AI's Chatterbox** (`Chatterbox-tts`) — requires a Resemble
  `voice_uuid`, passed as `voice`.

The engine picks the request shape from the model id and resolves both
documented response shapes: synchronous inline `outcome` responses, and
queued/dispatched generations resolved by polling.

## Installation

```bash
pip install realtimetts-gmicloud
```

RealtimeTTS playback needs PyAudio, which is an optional extra of RealtimeTTS:

```bash
pip install "realtimetts[playback]"
```

## Prerequisites

A GMI Cloud API key, passed as `api_key` or set as `GMI_CLOUD_API_KEY`.

## Usage

```python
from RealtimeTTS import TextToAudioStream
from realtimetts_gmicloud import GmicloudEngine

engine = GmicloudEngine(
    api_key="your-gmi-cloud-api-key",   # or GMI_CLOUD_API_KEY env var
    model="inworld-tts-2",              # GMI Cloud model id
    voice="Dennis",                     # family voice id (Resemble UUID for Chatterbox)
)
stream = TextToAudioStream(engine)
stream.feed("Hello from GMI Cloud.").play()
```

Chatterbox models need a Resemble voice UUID:

```python
engine = GmicloudEngine(model="Chatterbox-tts", voice="your-resemble-voice-uuid")
```

## Configuration

| Parameter | Default | Notes |
| --- | --- | --- |
| `api_key` | `GMI_CLOUD_API_KEY` or `GMI_API_KEY` env | Required |
| `model` | `inworld-tts-2` | Family selected from the id; unknown ids use the Inworld request shape |
| `voice` | per family (`Dennis`, `English_expressive_narrator`) | Chatterbox requires a Resemble `voice_uuid` |
| `speed` | `1.0` | Speaking rate |
| `temperature` | `None` | Inworld family only |
| `extra_payload` | `{}` | Merged into the request payload last (overrides built-in fields) |
| `poll_interval_secs` | `2.0` | Delay between polls of a queued generation |
| `poll_attempts` | `90` | Polls before giving up (MiniMax generations can be slow through GMI's queue) |
| `sample_rate` | `48000` | Emitted PCM rate; responses are resampled to it |
| `timeout` | `60.0` | Per-request HTTP timeout in seconds |
| `debug` | `False` | Print synthesis timing and errors |

## Output contract

Every response is normalized before playback: GMI Cloud returns each model's
native WAV format (48 kHz mono for Inworld, 32 kHz stereo for MiniMax), and
the engine down-mixes to mono and resamples to the declared `sample_rate`, so
the emitted PCM always matches `get_stream_info()` exactly (mono 16-bit at
48 kHz by default).

## Measured results (2026-11-17, live GMI Cloud API)

| Model | Family | Emitted samples | Synthesis time | Notes |
| --- | --- | --- | --- | --- |
| `inworld-tts-2` | Inworld | 204,000 (4.25 s) | 2.9 s | low latency, reliable |
| `minimax-tts-speech-2.8-turbo` | MiniMax | 163,840 (3.4 s) | 18.6 s | queued path; normalized from native 32 kHz stereo |

Also verified live: end-to-end synthesis through a real `TextToAudioStream`
(347 KB WAV captured), Chatterbox rejection without a `voice_uuid`, and a bad
API key mapping to a failed synthesis.

Sample counts vary slightly between runs; the table records one measured run.

Behavior notes, verified live:

- MiniMax generations go through GMI Cloud's queue. Most complete in seconds;
  an occasional request stays `processing` past the default poll budget
  (`poll_attempts` / `poll_interval_secs` are configurable). The Inworld
  family is the low-latency option.
- Chatterbox models reject requests without a Resemble `voice_uuid` with a
  clear `ValueError` before any network call.
- Permanent HTTP errors (e.g. 401/404) fail immediately; only 408/429/5xx are
  retried while polling.

## License

Apache-2.0
