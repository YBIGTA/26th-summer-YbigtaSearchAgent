"""
Whisper STT wrapper
"""
from typing import List, Dict, Any, Optional
import os
import whisper
import numpy as np
import librosa


def transcribe_audio(file_path: str, model_name: str = "base", language: Optional[str] = None) -> Dict[str, Any]:
    """
    Transcribe an audio file using OpenAI Whisper.

    Args:
        file_path: Path to audio file
        model_name: Whisper model name (tiny, base, small, medium, large)
        language: Optional language hint (e.g., "en", "ko")

    Returns:
        Dict with keys: { text, language, segments: [ { start, end, text } ] }
    """
    model = whisper.load_model(model_name)

    def _run_transcribe(input_audio):
        return model.transcribe(
            input_audio,
            task="transcribe",
            language=language,
            fp16=False,
            verbose=False,
        )

    try:
        # If WAV, avoid external decoders by loading as numpy array
        if file_path.lower().endswith(".wav"):
            audio, sr = librosa.load(file_path, sr=16000, mono=True)
            result = _run_transcribe(audio)
        else:
            # Other formats (mp3/m4a) require ffmpeg in PATH
            result = _run_transcribe(file_path)
    except FileNotFoundError as e:
        raise RuntimeError("ffmpeg not found. Install ffmpeg and ensure it is in PATH, or use WAV files.") from e
    except OSError as e:
        # WinError 2 or similar when decoder not found
        if getattr(e, "winerror", None) == 2:
            raise RuntimeError("Decoder not found (likely ffmpeg). Install ffmpeg and restart the server.") from e
        raise

    segments: List[Dict[str, Any]] = []
    for seg in result.get("segments", []):
        segments.append({
            "start": float(seg.get("start", 0.0)),
            "end": float(seg.get("end", 0.0)),
            "text": seg.get("text", "").strip(),
        })

    return {
        "text": result.get("text", "").strip(),
        "language": result.get("language"),
        "segments": segments,
    }