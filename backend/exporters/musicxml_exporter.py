"""
exporters/musicxml_exporter.py
Genera archivo MusicXML 3.1 — compatible con MuseScore, Finale, Sibelius, Dorico.
"""
from __future__ import annotations
import math
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom
from core.transcriber import TranscriptionResult, Note


PITCH_TABLE = {
    0:  ("C",  0), 1:  ("C", 1),  2:  ("D",  0), 3:  ("D", 1),
    4:  ("E",  0), 5:  ("F", 0),  6:  ("F",  1), 7:  ("G", 0),
    8:  ("G",  1), 9:  ("A", 0), 10:  ("A",  1), 11: ("B", 0),
}

DURATION_MAP = [
    (4.0,  "whole",    0),
    (3.0,  "half",     1),
    (2.0,  "half",     0),
    (1.5,  "quarter",  1),
    (1.0,  "quarter",  0),
    (0.75, "eighth",   1),
    (0.5,  "eighth",   0),
    (0.25, "16th",     0),
    (0.125,"32nd",     0),
]

INSTRUMENT_CLEFS = {
    "Piano":     ("treble", 0),
    "Melody":    ("treble", 0),
    "Guitar":    ("treble", -1),
    "Bass":      ("bass",   0),
    "Violin":    ("treble", 0),
    "Cello":     ("bass",   0),
    "Flute":     ("treble", 0),
    "Trumpet":   ("treble", 0),
    "Saxophone": ("treble", 0),
}

MIDI_PROGRAMS = {
    "Piano": 1, "Melody": 1, "Guitar": 26,
    "Bass": 34, "Violin": 41, "Cello": 43,
    "Flute": 74, "Trumpet": 57, "Saxophone": 66,
}


class MusicXMLExporter:

    def export(self, transcription: TranscriptionResult, analysis: dict, output_path: str) -> str:
        xml_str = self._build_xml(transcription, analysis)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(xml_str)
        return output_path

    def export_string(self, transcription: TranscriptionResult, analysis: dict) -> str:
        return self._build_xml(transcription, analysis)

    def _build_xml(self, t: TranscriptionResult, analysis: dict) -> str:
        tempo   = float(analysis.get("tempo", t.tempo) or 120)
        ts_num  = t.time_signature[0]
        ts_den  = t.time_signature[1]
        key_str = analysis.get("tonalidad", t.key)
        title   = analysis.get("titulo", "Transcript IA")

        beats_per_measure = ts_num
        divisions = 4

        by_instrument: dict[str, list[Note]] = {}
        for note in t.notes:
            by_instrument.setdefault(note.instrument, []).append(note)

        if not by_instrument:
            by_instrument["Piano"] = []

        root = Element("score-partwise")
        root.set("version", "3.1")

        work = SubElement(root, "work")
        SubElement(work, "work-title").text = title

        identification = SubElement(root, "identification")
        encoding = SubElement(identification, "encoding")
        SubElement(encoding, "software").text = "Transcript IA — Powered by Claude AI"
        SubElement(encoding, "encoding-date").text = "2024-01-01"

        part_list = SubElement(root, "part-list")
        part_ids = {}

        for i, inst_name in enumerate(by_instrument.keys()):
            part_id = f"P{i+1}"
            part_ids[inst_name] = part_id

            score_part = SubElement(part_list, "score-part")
            score_part.set("id", part_id)
            SubElement(score_part, "part-name").text = inst_name

            score_inst = SubElement(score_part, "score-instrument")
            score_inst.set("id", f"{part_id}-I1")
            SubElement(score_inst, "instrument-name").text = inst_name

            midi_inst = SubElement(score_part, "midi-instrument")
            midi_inst.set("id", f"{part_id}-I1")
            SubElement(midi_inst, "midi-channel").text = str(i + 1)
            SubElement(midi_inst, "midi-program").text = str(MIDI_PROGRAMS.get(inst_name, 1))
            SubElement(midi_inst, "volume").text = "80"

        for inst_name, notes in by_instrument.items():
            part_id = part_ids[inst_name]
            part = SubElement(root, "part")
            part.set("id", part_id)

            measures = self._notes_to_measures(notes, tempo, ts_num, ts_den, divisions)
            clef_sign, clef_line = INSTRUMENT_CLEFS.get(inst_name, ("treble", 0))
            key_fifths = self._key_to_fifths(key_str)

            for m_idx, measure_notes in enumerate(measures):
                measure = SubElement(part, "measure")
                measure.set("number", str(m_idx + 1))

                if m_idx == 0:
                    attrs = SubElement(measure, "attributes")
                    SubElement(attrs, "divisions").text = str(divisions)

                    key_el = SubElement(attrs, "key")
                    SubElement(key_el, "fifths").text = str(key_fifths)
                    SubElement(key_el, "mode").text = "minor" if "minor" in key_str else "major"

                    time_el = SubElement(attrs, "time")
                    SubElement(time_el, "beats").text = str(ts_num)
                    SubElement(time_el, "beat-type").text = str(ts_den)

                    clef_el = SubElement(attrs, "clef")
                    SubElement(clef_el, "sign").text = clef_sign
                    if clef_line:
                        SubElement(clef_el, "line").text = "4"

                    direction = SubElement(measure, "direction")
                    direction.set("placement", "above")
                    dir_type = SubElement(direction, "direction-type")
                    metronome = SubElement(dir_type, "metronome")
                    metronome.set("parentheses", "no")
                    SubElement(metronome, "beat-unit").text = "quarter"
                    SubElement(metronome, "per-minute").text = str(int(tempo))
                    SubElement(direction, "sound").set("tempo", str(int(tempo)))

                total_divisions = beats_per_measure * divisions
                used_divisions = 0

                for note_data in measure_notes:
                    note_el = SubElement(measure, "note")
                    pitch_midi, dur_beats, velocity = note_data
                    dur_div = max(1, round(dur_beats * divisions))

                    if pitch_midi == -1:
                        SubElement(note_el, "rest")
                    else:
                        pitch_el = SubElement(note_el, "pitch")
                        step, alter = PITCH_TABLE.get(pitch_midi % 12, ("C", 0))
                        SubElement(pitch_el, "step").text = step
                        if alter:
                            SubElement(pitch_el, "alter").text = str(alter)
                        SubElement(pitch_el, "octave").text = str(pitch_midi // 12 - 1)

                    SubElement(note_el, "duration").text = str(dur_div)
                    SubElement(note_el, "voice").text = "1"
                    type_str, dots = self._duration_to_type(dur_beats)
                    SubElement(note_el, "type").text = type_str
                    for _ in range(dots):
                        SubElement(note_el, "dot")

                    used_divisions += dur_div

                remaining = total_divisions - used_divisions
                if remaining > 0:
                    rest_el = SubElement(measure, "note")
                    SubElement(rest_el, "rest")
                    SubElement(rest_el, "duration").text = str(remaining)
                    SubElement(rest_el, "voice").text = "1"
                    type_str, _ = self._duration_to_type(remaining / divisions)
                    SubElement(rest_el, "type").text = type_str

        raw = tostring(root, encoding="unicode")
        xml_declaration = '<?xml version="1.0" encoding="UTF-8"?>\n'
        doctype = ('<!DOCTYPE score-partwise PUBLIC '
                   '"-//Recordare//DTD MusicXML 3.1 Partwise//EN" '
                   '"http://www.musicxml.org/dtds/partwise.dtd">\n')
        dom = minidom.parseString(raw)
        pretty = dom.toprettyxml(indent="  ", encoding=None)
        lines = pretty.split("\n")
        if lines[0].startswith("<?xml"):
            lines = lines[1:]
        return xml_declaration + doctype + "\n".join(lines)

    def _notes_to_measures(self, notes, tempo, ts_num, ts_den, divisions):
        if not notes:
            return [[(-1, ts_num, 80)]]

        seconds_per_beat = 60.0 / tempo
        measure_duration = ts_num * seconds_per_beat
        total_duration = max(n.end for n in notes)
        num_measures = max(1, math.ceil(total_duration / measure_duration))
        measures: list[list[tuple]] = [[] for _ in range(num_measures)]

        for note in notes:
            m_idx = int(note.start / measure_duration)
            if m_idx >= num_measures:
                m_idx = num_measures - 1
            dur_beats = (note.end - note.start) / seconds_per_beat
            dur_beats = max(0.25, min(dur_beats, ts_num))
            measures[m_idx].append((note.pitch, dur_beats, note.velocity))

        for i, m in enumerate(measures):
            if not m:
                measures[i] = [(-1, ts_num, 0)]

        return measures

    def _duration_to_type(self, beats: float) -> tuple[str, int]:
        for threshold, type_str, dots in DURATION_MAP:
            if beats >= threshold * 0.9:
                return type_str, dots
        return "32nd", 0

    def _key_to_fifths(self, key_str: str) -> int:
        major_keys = {
            "C major": 0,  "G major": 1,  "D major": 2,  "A major": 3,
            "E major": 4,  "B major": 5,  "F# major": 6, "C# major": 7,
            "F major": -1, "Bb major": -2,"Eb major": -3,"Ab major": -4,
            "Db major": -5,"Gb major": -6,"Cb major": -7,
        }
        minor_keys = {
            "A minor": 0,  "E minor": 1,  "B minor": 2,  "F# minor": 3,
            "C# minor": 4, "G# minor": 5, "D# minor": 6, "A# minor": 7,
            "D minor": -1, "G minor": -2, "C minor": -3, "F minor": -4,
            "Bb minor": -5,"Eb minor": -6,"Ab minor": -7,
        }
        return major_keys.get(key_str, minor_keys.get(key_str, 0))
