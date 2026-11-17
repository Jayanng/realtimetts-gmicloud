# Changelog

## 0.1.0 (2026-11-17)

- Initial release: `GmicloudEngine` for RealtimeTTS covering GMI Cloud's
  Inworld Realtime TTS, MiniMax speech synthesis and Chatterbox families
  behind the request-queue API.
- Family-aware request mapping; resolves both synchronous inline and
  queued/polling response shapes.
- Output normalized to the declared format (mono 16-bit PCM at
  `sample_rate`, 48 kHz by default) so emitted audio always matches
  `get_stream_info()`.
- Fail-fast on permanent HTTP errors while polling; 408/429/5xx retry.
- Verified live: synthesis on Inworld and MiniMax, end-to-end through
  `TextToAudioStream`, Chatterbox `voice_uuid` validation, bad-key handling.
