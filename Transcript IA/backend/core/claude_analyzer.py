"""
core/claude_analyzer.py
Sends transcription data to Claude API for deep musical analysis.
"""
from __future__ import annotations
import json
import anthropic
from .transcriber import TranscriptionResult


SYSTEM_PROMPT = """Eres un arreglista musical experto con décadas de experiencia en:
- Teoría musical, armonía y contrapunto
- Producción musical y orquestación
- Notación musical (partitura, MusicXML, MIDI)
- Géneros: clásico, jazz, pop, rock, electrónica, latina, etc.

Cuando recibas datos de transcripción de audio, debes:
1. Analizar la información musical proporcionada
2. Generar un arreglo musical completo y detallado
3. Responder ÚNICAMENTE con un objeto JSON válido (sin texto adicional, sin backticks)

El JSON debe seguir EXACTAMENTE esta estructura:
{
  "titulo": "Análisis Musical",
  "tonalidad": "C major",
  "tempo": 120,
  "compas": "4/4",
  "genero": "Pop",
  "duracion_total": "3:45",
  "estructura": [
    {"seccion": "Intro", "compases": "1-8", "descripcion": "..."},
    {"seccion": "Verso 1", "compases": "9-24", "descripcion": "..."},
    {"seccion": "Coro", "compases": "25-40", "descripcion": "..."},
    {"seccion": "Puente", "compases": "73-88", "descripcion": "..."},
    {"seccion": "Outro", "compases": "89-96", "descripcion": "..."}
  ],
  "instrumentos": [
    {
      "nombre": "Piano",
      "midi_program": 0,
      "rango": "C3-C6",
      "secciones": [
        {
          "nombre": "Intro",
          "descripcion": "Acordes arpeggiados en corcheas",
          "patron": "Am - F - C - G",
          "tecnicas": ["arpegio", "pedal sustain"],
          "notas_destacadas": ["A3", "C4", "E4"]
        }
      ]
    }
  ],
  "armonia": {
    "progresion_principal": "Am - F - C - G",
    "progresion_coro": "F - G - Am - Em",
    "modulaciones": [],
    "modo": "Eolio"
  },
  "produccion": {
    "efectos": ["reverb en voz", "delay en guitarra"],
    "tempo_variaciones": [],
    "dinamica": "mp a mf con crescendo en coro"
  },
  "notas_arreglista": "Observaciones importantes para reproducir el arreglo"
}"""


class ClaudeAnalyzer:
    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)

    def analyze(self, transcription: TranscriptionResult, filename: str = "audio") -> dict:
        note_summary = self._summarize_notes(transcription)

        user_message = f"""Analiza este audio transcripto y genera el arreglo musical completo.

DATOS DE TRANSCRIPCIÓN:
- Archivo: {filename}
- Tonalidad detectada: {transcription.key}
- Tempo: {transcription.tempo} BPM
- Compás estimado: {transcription.time_signature[0]}/{transcription.time_signature[1]}
- Duración: {transcription.duration:.1f} segundos
- Instrumentos detectados: {', '.join(transcription.instruments_detected)}
- Total de notas transcritas: {len(transcription.notes)}

RESUMEN DE NOTAS POR INSTRUMENTO:
{note_summary}

DISTRIBUCIÓN DE ALTURAS (primeras 30 notas):
{self._pitch_sequence(transcription.notes[:30])}

Genera el arreglo musical completo en JSON siguiendo exactamente la estructura indicada.
Sé específico con los patrones de cada instrumento en cada sección.
Infiere la estructura de la canción basándote en los patrones de notas."""

        response = self.client.messages.create(
            model="claude-opus-4-5",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}]
        )

        raw = response.content[0].text.strip()

        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return self._fallback_analysis(transcription, filename)

    def _summarize_notes(self, t: TranscriptionResult) -> str:
        lines = []
        from collections import defaultdict
        by_inst: dict[str, list] = defaultdict(list)
        for n in t.notes:
            by_inst[n.instrument].append(n)
        for inst, notes in by_inst.items():
            pitches = [n.pitch for n in notes]
            avg_vel = sum(n.velocity for n in notes) / len(notes)
            lines.append(
                f"  {inst}: {len(notes)} notas, "
                f"rango MIDI {min(pitches)}-{max(pitches)}, "
                f"velocidad promedio {avg_vel:.0f}"
            )
        return "\n".join(lines) if lines else "  (sin notas detectadas)"

    def _pitch_sequence(self, notes: list) -> str:
        note_names = ['C','C#','D','Eb','E','F','F#','G','Ab','A','Bb','B']
        return " ".join(
            f"{note_names[n.pitch % 12]}{n.pitch // 12 - 1}"
            for n in notes
        )

    def _fallback_analysis(self, t: TranscriptionResult, filename: str) -> dict:
        return {
            "titulo": filename,
            "tonalidad": t.key,
            "tempo": t.tempo,
            "compas": f"{t.time_signature[0]}/{t.time_signature[1]}",
            "genero": "No determinado",
            "duracion_total": f"{int(t.duration//60)}:{int(t.duration%60):02d}",
            "estructura": [
                {"seccion": "Completa", "compases": "1-fin", "descripcion": "Análisis completo"}
            ],
            "instrumentos": [
                {
                    "nombre": inst,
                    "midi_program": self._midi_program(inst),
                    "rango": "Variable",
                    "secciones": [
                        {
                            "nombre": "Completa",
                            "descripcion": f"Parte de {inst}",
                            "patron": "Variable",
                            "tecnicas": [],
                            "notas_destacadas": []
                        }
                    ]
                }
                for inst in t.instruments_detected
            ],
            "armonia": {"progresion_principal": "No determinada", "modulaciones": []},
            "produccion": {"efectos": [], "dinamica": "Variable"},
            "notas_arreglista": "Análisis automático — revisar manualmente."
        }

    def _midi_program(self, instrument: str) -> int:
        mapping = {
            "Piano": 0, "Guitar": 25, "Bass": 33,
            "Violin": 40, "Cello": 42, "Flute": 73,
            "Trumpet": 56, "Saxophone": 65, "Melody": 0,
        }
        return mapping.get(instrument, 0)