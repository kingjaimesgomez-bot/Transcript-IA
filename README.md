# Transcript IA 🎵

> **Escucha. Analiza. Escribe.**

Analizador de arreglos musicales impulsado por IA. Sube cualquier canción y obtén:
- Transcripción nota por nota (Basic Pitch · Spotify)
- Análisis armónico y estructural completo (Claude AI)
- Exportación en MIDI · MusicXML · PDF

---

## Estructura del proyecto
```
transcript-ia/
├── frontend/
│   └── public/
│       ├── index.html
│       └── assets/images/
└── backend/
    ├── api/main.py
    ├── core/
    ├── exporters/
    ├── requirements.txt
    ├── run.py
    └── .env.example
```

## Instalación Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python run.py
```

## Uso

1. Corre el backend: `python run.py`
2. Abre `frontend/public/index.html` en el navegador
3. Sube una canción y obtén el arreglo completo

## Stack

- Frontend: HTML · CSS · JavaScript
- Backend: Python · FastAPI · Basic Pitch
- IA: Claude AI (Anthropic)
- Exports: MIDI · MusicXML · PDF

## Licencia

MIT © 2025 Transcript IA
```

---

✅ **¡Proyecto completo!** Así debe verse todo:
```
transcript-ia/
├── frontend/
│   └── public/
│       ├── index.html
│       └── assets/
│           └── images/
│               └── hero-bg.png
├── backend/
│   ├── api/
│   │   └── main.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── transcriber.py
│   │   └── claude_analyzer.py
│   ├── exporters/
│   │   ├── __init__.py
│   │   ├── midi_exporter.py
│   │   ├── musicxml_exporter.py
│   │   └── pdf_exporter.py
│   ├── .env.example
│   ├── requirements.txt
│   ├── run.py
│   └── README.md
├── .gitignore
└── README.md
