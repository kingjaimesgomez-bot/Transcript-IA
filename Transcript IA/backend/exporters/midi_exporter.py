"""
exporters/midi_exporter.py
Generates a MIDI file from transcription + Claude analysis.
"""
from __future__ import annotations
import io
from midiutil import MIDIFile
from core.transcriber import TranscriptionResult, Note


MIDI_PROGRAMS = {
    "Piano":      0,
    "Melody":     0,
    "Guitar":     25,
    "Bass":       33,
    "Violin":     40,
    "Viola":      41,
    "Cello":      42,
    "Flute":      73,
    "Trumpet":    56,
    "Saxophone":  65,
    "Drums":      0,
}


class MIDIExporter:
    def export(
        self,
        transcription: TranscriptionResult,
        analysis: dict,
        output_path: str
    ) -> str:
        tempo = analysis.get("tempo", transcription.tempo) or 120.0

        by_instrument: dict[str, list[Note]] = {}
        for note in transcription.notes:
            by_instrument.setdefault(note.instrument, []).append(note)

        num_tracks = max(1, len(by_instrument))
        midi = MIDIFile(num_tracks, removeDuplicates=True, deinterleave=True)

        track_idx = 0
        for instrument, notes in by_instrument.items():
            channel = 9 if instrument == "Drums" else (track_idx % 9)
            program = MIDI_PROGRAMS.get(instrument, 0)

            midi.addTrackName(track_idx, 0, instrument)
            midi.addTempo(track_idx, 0, tempo)
            midi.addProgramChange(track_idx, channel, 0, program)

            for note in notes:
                start_beat = (note.start / 60.0) * tempo
                dur_beat   = max(0.1, (note.end - note.start) / 60.0 * tempo)
                midi.addNote(
                    track=track_idx,
                    channel=channel,
                    pitch=note.pitch,
                    time=start_beat,
                    duration=dur_beat,
                    volume=note.velocity
                )

            track_idx += 1

        with open(output_path, "wb") as f:
            midi.writeFile(f)

        return output_path

    def export_bytes(
        self,
        transcription: TranscriptionResult,
        analysis: dict
    ) -> bytes:
        buf = io.BytesIO()
        tempo = analysis.get("tempo", transcription.tempo) or 120.0

        by_instrument: dict[str, list[Note]] = {}
        for note in transcription.notes:
            by_instrument.setdefault(note.instrument, []).append(note)

        num_tracks = max(1, len(by_instrument))
        midi = MIDIFile(num_tracks)

        track_idx = 0
        for instrument, notes in by_instrument.items():
            channel = 9 if instrument == "Drums" else (track_idx % 9)
            program = MIDI_PROGRAMS.get(instrument, 0)

            midi.addTrackName(track_idx, 0, instrument)
            midi.addTempo(track_idx, 0, tempo)
            midi.addProgramChange(track_idx, channel, 0, program)

            for note in notes:
                start_beat = (note.start / 60.0) * tempo
                dur_beat   = max(0.1, (note.end - note.start) / 60.0 * tempo)
                midi.addNote(track_idx, channel, note.pitch, start_beat, dur_beat, note.velocity)

            track_idx += 1

        midi.writeFile(buf)
        return buf.getvalue()