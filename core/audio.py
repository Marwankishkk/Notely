import subprocess
import tempfile
import wave
from io import BytesIO
from pathlib import Path

from fastapi import HTTPException, status
from mutagen import MutagenError
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4
from mutagen.oggvorbis import OggVorbis
from mutagen.wave import WAVE


def get_audio_duration_seconds(file_bytes: bytes, filename: str) -> float:
    """Measure audio duration server-side. Never trust the client."""
    extension = Path(filename).suffix.lower()

    duration = _duration_with_mutagen(file_bytes, extension)
    if duration is not None:
        return duration

    if extension == ".wav":
        duration = _duration_with_wave(file_bytes)
        if duration is not None:
            return duration

    duration = _duration_with_ffprobe(file_bytes, extension)
    if duration is not None:
        return duration

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Could not determine audio duration. Please use a supported format.",
    )


def _duration_with_mutagen(file_bytes: bytes, extension: str) -> float | None:
    try:
        bio = BytesIO(file_bytes)
        audio = None

        if extension in {".mp3", ".mpga", ".mpeg"}:
            audio = MP3(bio)
        elif extension in {".m4a", ".mp4"}:
            audio = MP4(bio)
        elif extension in {".ogg"}:
            audio = OggVorbis(bio)
        elif extension == ".wav":
            audio = WAVE(bio)
        else:
            return None

        if audio is None or audio.info is None or not getattr(audio.info, "length", None):
            return None

        length = float(audio.info.length)
        return length if length > 0 else None
    except (MutagenError, Exception):
        return None


def _duration_with_wave(file_bytes: bytes) -> float | None:
    try:
        with wave.open(BytesIO(file_bytes), "rb") as wav_file:
            frames = wav_file.getnframes()
            rate = wav_file.getframerate()
            if rate <= 0:
                return None
            length = frames / float(rate)
            return length if length > 0 else None
    except Exception:
        return None


def _duration_with_ffprobe(file_bytes: bytes, extension: str) -> float | None:
    suffix = extension if extension else ".webm"
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix) as tmp:
            tmp.write(file_bytes)
            tmp.flush()
            result = subprocess.run(
                [
                    "ffprobe",
                    "-v",
                    "error",
                    "-show_entries",
                    "format=duration",
                    "-of",
                    "default=noprint_wrappers=1:nokey=1",
                    tmp.name,
                ],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
        if result.returncode != 0:
            return None
        length = float(result.stdout.strip())
        return length if length > 0 else None
    except Exception:
        return None
