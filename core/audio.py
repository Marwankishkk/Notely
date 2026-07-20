import os
import re
import shutil
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

_FFPROBE = shutil.which("ffprobe") or "/usr/bin/ffprobe"
_FFMPEG = shutil.which("ffmpeg") or "/usr/bin/ffmpeg"
_CLOCK_RE = re.compile(r"(\d+):(\d+):(\d+(?:\.\d+)?)")
_DURATION_RE = re.compile(
    r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)",
    re.IGNORECASE,
)
_TIME_RE = re.compile(r"time=(\d+):(\d+):(\d+(?:\.\d+)?)")


def get_audio_duration_seconds(file_bytes: bytes, filename: str) -> float:
    """Measure audio duration server-side. Never trust the client."""
    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty audio file.",
        )

    extension = Path(filename).suffix.lower()

    duration = _duration_with_mutagen(file_bytes, extension)
    if duration is not None:
        return duration

    if extension == ".wav":
        duration = _duration_with_wave(file_bytes)
        if duration is not None:
            return duration

    # Browser MediaRecorder webm/opus often has no container duration.
    duration = _duration_with_ffprobe(file_bytes, extension)
    if duration is not None:
        return duration

    duration = _duration_with_ffmpeg(file_bytes, extension)
    if duration is not None:
        return duration

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Could not determine audio duration. Please use a supported format.",
    )


def _clock_to_seconds(hours: str, minutes: str, seconds: str) -> float | None:
    length = int(hours) * 3600 + int(minutes) * 60 + float(seconds)
    return length if length > 0 else None


def _write_temp_audio(file_bytes: bytes, extension: str) -> str:
    suffix = extension if extension else ".webm"
    fd, path = tempfile.mkstemp(suffix=suffix)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(file_bytes)
            handle.flush()
            os.fsync(handle.fileno())
    except Exception:
        os.unlink(path)
        raise
    return path


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
    path = _write_temp_audio(file_bytes, extension)
    try:
        for entries in ("format=duration", "stream=duration"):
            result = subprocess.run(
                [
                    _FFPROBE,
                    "-v",
                    "error",
                    "-show_entries",
                    entries,
                    "-of",
                    "default=noprint_wrappers=1:nokey=1",
                    path,
                ],
                capture_output=True,
                text=True,
                timeout=15,
                check=False,
            )
            if result.returncode != 0:
                continue
            for line in result.stdout.splitlines():
                value = line.strip()
                if not value or value.upper() == "N/A":
                    continue
                try:
                    length = float(value)
                except ValueError:
                    continue
                if length > 0:
                    return length
        return None
    except Exception:
        return None
    finally:
        os.unlink(path)


def _duration_with_ffmpeg(file_bytes: bytes, extension: str) -> float | None:
    """Decode with ffmpeg. Prefer progress time= (webm often has Duration: N/A)."""
    path = _write_temp_audio(file_bytes, extension)
    try:
        result = subprocess.run(
            [_FFMPEG, "-i", path, "-f", "null", "-"],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        stderr = result.stderr or ""

        # Last time=HH:MM:SS.xx from decode progress is the real length for webm.
        time_matches = list(_TIME_RE.finditer(stderr))
        if time_matches:
            length = _clock_to_seconds(*time_matches[-1].groups())
            if length is not None:
                return length

        duration_match = _DURATION_RE.search(stderr)
        if duration_match:
            length = _clock_to_seconds(*duration_match.groups())
            if length is not None:
                return length

        return None
    except Exception:
        return None
    finally:
        os.unlink(path)
