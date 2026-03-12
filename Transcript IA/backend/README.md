# Transcript IA — Backend

API Python para transcripción y análisis de arreglos musicales.

## Instalación
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## Configuración
```bash
copy .env.example .env
```

Abre `.env` y agrega tu clave:
```
ANTHROPIC_API_KEY=sk-ant-tu-clave-aqui
```

## Correr el servidor
```bash
python run.py
```

- API: http://localhost:8000
- Docs: http://localhost:8000/docs

## Endpoints

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | /health | Estado del servidor |
| POST | /analyze | Subir audio → retorna job_id |
| GET | /status/{job_id} | Progreso del análisis |
| GET | /export/midi/{job_id} | Descargar MIDI |
| GET | /export/musicxml/{job_id} | Descargar MusicXML |
| GET | /export/pdf/{job_id} | Descargar PDF |

## Formatos soportados

MP3 · WAV · FLAC · AAC · OGG · M4A — máximo 25 MB
```

---

✅ **¡Backend completo!** Tu carpeta debe verse así:
```
backend/
├── api/
│   └── main.py
├── core/
│   ├── __init__.py
│   └── transcriber.py
│   └── claude_analyzer.py
├── exporters/
│   ├── __init__.py
│   ├── midi_exporter.py
│   ├── musicxml_exporter.py
│   └── pdf_exporter.py
├── .env.example
├── requirements.txt
├── run.py
└── README.md