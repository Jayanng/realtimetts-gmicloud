"""Live verification against the GMI Cloud API (requires GMI_CLOUD_API_KEY)."""

import os
import queue
import sys

from realtimetts_gmicloud import GmicloudEngine


def main() -> int:
    key = os.environ.get("GMI_CLOUD_API_KEY") or os.environ.get("GMI_API_KEY")
    if not key:
        print("SKIP: no GMI_CLOUD_API_KEY in environment")
        return 1

    failures = 0

    def check(name, cond, note=""):
        nonlocal failures
        print(f"{'PASS' if cond else 'FAIL'} {name}" + (f" ({note})" if note else ""))
        if not cond:
            failures += 1

    # 1) direct synthesis: inworld
    e = GmicloudEngine(api_key=key, model="inworld-tts-2", debug=True)
    e.queue = queue.Queue()
    ok = e.synthesize("Live verification of the GMI Cloud engine for RealtimeTTS.")
    samples = e.queue.qsize() and len(e.queue.get_nowait()) // 2
    check("inworld synthesize", ok and samples and samples > 40000,
          f"{samples} samples at 48000 Hz mono")

    # 2) direct synthesis: minimax (queued path, one retry)
    ok = False
    for attempt in (1, 2):
        e = GmicloudEngine(api_key=key, model="minimax-tts-speech-2.8-turbo",
                           poll_interval_secs=2.0, poll_attempts=90, debug=True)
        e.queue = queue.Queue()
        try:
            ok = e.synthesize("And this is the MiniMax family through the same engine.")
            if ok:
                samples = len(e.queue.get_nowait()) // 2
                check("minimax synthesize", samples > 40000,
                      f"{samples} samples normalized to 48000 Hz mono")
                break
        except Exception as exc:  # noqa: BLE001 - report any failure, keep trying
            print(f"minimax attempt {attempt}: {type(exc).__name__}: {str(exc)[:80]}")
    if not ok:
        check("minimax synthesize", False, "both attempts failed")

    # 3) end-to-end through a real TextToAudioStream (muted, WAV captured)
    try:
        from RealtimeTTS import TextToAudioStream

        engine = GmicloudEngine(api_key=key, model="inworld-tts-2")
        stream = TextToAudioStream(engine, muted=True)
        out_wav = os.path.join(os.path.dirname(__file__), "out", "stream_capture.wav")
        os.makedirs(os.path.dirname(out_wav), exist_ok=True)
        stream.feed("This audio came through a real RealtimeTTS stream.")
        stream.play(output_wavfile=out_wav)
        size = os.path.getsize(out_wav) if os.path.exists(out_wav) else 0
        check("TextToAudioStream end-to-end", size > 100000, f"{size} bytes captured")
    except Exception as exc:  # noqa: BLE001 - report any failure of the stream run
        check("TextToAudioStream end-to-end", False, f"{type(exc).__name__}: {str(exc)[:80]}")

    # 4) chatterbox rejects without a Resemble voice UUID (clear config error)
    try:
        GmicloudEngine(api_key=key, model="Chatterbox-tts")
        check("chatterbox voice_uuid validation", False)
    except ValueError as exc:
        check("chatterbox voice_uuid validation", "voice_uuid" in str(exc))

    # 5) bad key maps to a failed synthesis (HTTP 401 surfaces as error)
    e = GmicloudEngine(api_key="sk-invalid", model="inworld-tts-2")
    e.queue = queue.Queue()
    ok = e.synthesize("bad key check")
    check("bad API key rejected", ok is False)

    print("LIVE_ALL_PASS" if failures == 0 else f"LIVE_FAILURES={failures}")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
