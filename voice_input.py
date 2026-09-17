"""
Voice-to-text transcription for field safety reports.

Uses faster-whisper running FULLY LOCALLY (no API calls) so this works
without internet during a live demo. Download the model once ahead of
time (happens automatically on first run, then cached) -- test this on
your actual machine before demo day, same as the MiniLM/spaCy models.
"""
import tempfile
import os
from faster_whisper import WhisperModel

# "base" is a good balance of speed vs accuracy for short field reports on
# CPU. Use "tiny" if transcription feels too slow during rehearsal, or
# "small" if accuracy matters more than latency and your machine can handle it.
_MODEL_SIZE = "base"
_model = None


def get_model() -> WhisperModel:
    """Lazily load and cache the Whisper model (loading takes a few seconds)."""
    global _model
    if _model is None:
        print(f"Loading Whisper model ({_MODEL_SIZE})...")
        _model = WhisperModel(_MODEL_SIZE, device="cpu", compute_type="int8")
    return _model


def transcribe_audio_bytes(audio_bytes: bytes, language: str = "en") -> str:
    """
    Transcribes raw audio bytes (as returned by st.audio_input) to text.
    Writes to a temp file because faster-whisper expects a file path.
    """
    model = get_model()

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        segments, info = model.transcribe(tmp_path, language=language, beam_size=5)
        transcript = " ".join(seg.text.strip() for seg in segments)
        return transcript.strip()
    finally:
        os.unlink(tmp_path)


if __name__ == "__main__":
    # Quick standalone test: point this at any short .wav file to verify
    # the model loads and transcribes correctly before wiring it into the
    # dashboard.
    import sys
    if len(sys.argv) > 1:
        with open(sys.argv[1], "rb") as f:
            audio_data = f.read()
        print("Transcript:", transcribe_audio_bytes(audio_data))
    else:
        print("Usage: python voice_input.py path/to/test_audio.wav")