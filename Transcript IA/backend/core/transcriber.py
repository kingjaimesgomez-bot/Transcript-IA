"""
core/transcriber.py
Transcribe audio to note events using Spotify's Basic Pitch.
"""
from __future__ import annotations
import os
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import numpy as np
import librosa
import soundfile as sf

try:
    from basic_pitch.inference import predict
    from basic_pitch import ICASSP_2022_MODEL_PATH
    BASIC_PITCH_AVAILABLE = True
except ImportError:
    BASIC_PITCH_AVAILABLE = False


@dataclass
class Note:
    pitch: int
    start: float
    end: float
    velocity: int = 80
    instrument: str = "Piano"
    channel: int = 0


@dataclass
class TranscriptionResult:
    notes: list[Note]
    tempo: float
    time_signature: tuple[int,int]
    key: str
    duration: float
    sample_rate: int
    instruments_detected: list[str]
    raw_analysis: dict = field(default_factory=dict)


class AudioTranscriber:

    def __init__(self):
        if not BASIC_PITCH_AVAILABLE:
            raise RuntimeError("basic-pitch not installed. Run: pip install basic-pitch")

    def transcribe(self, audio_path: str | Path) -> TranscriptionResult:
        audio_path = Path(audio_path)

        y, sr = librosa.load(str(audio_path), sr=22050, mono=True)
        duration = librosa.get_duration(y=y, sr=sr)

        tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
        tempo = float(tempo)

        chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
        key_str = self._detect_key(chroma)

        time_sig = self._estimate_time_signature(y, sr, beat_frames)

        wav_path = self._ensure_wav(audio_path, y, sr)
        model_output, midi_data, note_events = predict(wav_path)
        notes = self._parse_note_events(note_events, tempo)

        if wav_path != str(audio_path):
            os.unlink(wav_path)

        instruments = self._detect_instruments(notes)
        notes = self._assign_instruments(notes, instruments)

        return TranscriptionResult(
            notes=notes,
            tempo=round(tempo, 1),
            time_signature=time_sig,
            key=key_str,
            duration=duration,
            sample_rate=sr,
            instruments_detected=list(instruments.keys()),
            raw_analysis={
                "beat_count": len(beat_frames),
                "chroma_mean": chroma.mean(axis=1).tolist(),
            }
        )

    def _ensure_wav(self, path: Path, y: np.ndarray, sr: int) -> str:
        if path.suffix.lower() in ('.wav',):
            return str(path)
        tmp = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        sf.write(tmp.name, y, sr)
        return tmp.name

    def _detect_key(self, chroma: np.ndarray) -> str:
        major_profile = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09,
                                   2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
        minor_profile = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53,
                                   2.54, 4.75, 3.98, 2.69, 3.34, 3.17])

        chroma_mean = chroma.mean(axis=1)
        note_names = ['C','C#','D','Eb','E','F','F#','G','Ab','A','Bb','B']

        best_corr = -np.inf
        best_key = 'C major'

        for i in range(12):
            rotated = np.roll(major_profile, i)
            corr = np.corrcoef(chroma_mean, rotated)[0, 1]
            if corr > best_corr:
                best_corr = corr
                best_key = f"{note_names[i]} major"
            rotated = np.roll(minor_profile, i)
            corr = np.corrcoef(chroma_mean, rotated)[0, 1]
            if corr > best_corr:
                best_corr = corr
                best_key = f"{note_names[i]} minor"

        return best_key

    def _estimate_time_signature(self, y, sr, beat_frames) -> tuple[int, int]:
        try:
            oenv = librosa.onset.onset_strength(y=y, sr=sr)
            tempogram = librosa.feature.tempogram(onset_envelope=oenv, sr=sr)
            beats_per_measure_4 = np.mean(tempogram[3::4]) if len(tempogram) > 4 else 0
            beats_per_measure_3 = np.mean(tempogram[2::3]) if len(tempogram) > 3 else 0
            if beats_per_measure_3 > beats_per_measure_4 * 1.1:
                return (3, 4)
            return (4, 4)
        except Exception:
            return (4, 4)

    def _parse_note_events(self, note_events, tempo) -> list[Note]:
        notes = []
        if note_events is None or len(note_events) == 0:
            return notes

        for event in note_events:
            if len(event) >= 4:
                start, end, pitch, velocity = (
                    float(event[0]), float(event[1]),
                    int(event[2]), int(min(127, max(1, event[3] * 127)))
                )
                if end > start and 21 <= pitch <= 108:
                    notes.append(Note(pitch=pitch, start=start, end=end, velocity=velocity))

        notes.sort(key=lambda n: n.start)
        return notes

    def _detect_instruments(self, notes: list[Note]) -> dict[str, tuple[int,int]]:
        if not notes:
            return {"Piano": (21, 108)}

        pitches = [n.pitch for n in notes]
        p_mean = sum(pitches) / len(pitches)
        instruments = {}

        bass_notes = [p for p in pitches if 28 <= p <= 55]
        if len(bass_notes) > len(pitches) * 0.15:
            instruments["Bass"] = (28, 55)

        mid_notes = [p for p in pitches if 48 <= p <= 84]
        if len(mid_notes) > len(pitches) * 0.2:
            if p_mean < 65:
                instruments["Guitar"] = (40, 84)
            else:
                instruments["Piano"] = (48, 84)

        high_notes = [p for p in pitches if 60 <= p <= 88]
        if len(high_notes) > len(pitches) * 0.25:
            instruments["Melody"] = (60, 88)

        if not instruments:
            instruments["Piano"] = (min(pitches), max(pitches))

        return instruments

    def _assign_instruments(self, notes, instruments) -> list[Note]:
        inst_list = list(instruments.items())
        for note in notes:
            best = "Piano"
            best_score = 999
            for name, (lo, hi) in inst_list:
                if lo <= note.pitch <= hi:
                    center = (lo + hi) / 2
                    score = abs(note.pitch - center)
                    if score < best_score:
                        best_score = score
                        best = name
            note.instrument = best
            note.channel = list(instruments.keys()).index(best)
        return notes