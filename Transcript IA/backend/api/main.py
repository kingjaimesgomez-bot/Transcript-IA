"""
api/main.py
FastAPI backend for Transcript IA.

Endpoints:
  POST /analyze      → full pipeline: transcribe + analyze + export
  GET  /export/midi/{job_id}
  GET  /export/musicxml/{job_id}
  GET  /export/pdf/{job_id}
  GET  /health
"""
from __future__ import annotations
import os
import uuid
import asyncio
import json
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
import aiofiles
from dotenv import load_dotenv

load_dotenv()

# ── Import pipeline ────────────────────────────────────────────────────────────
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.transcriber import AudioTranscriber
from core.claude_analyzer import ClaudeAnalyzer
from exporters.midi_exporter import MIDIExporter
from exporters.musicxml_exporter import MusicXMLExporter
from exporters.pdf_exporter import PDFExporter

# ── Config ────────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "uploads"))
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "outputs"))
MAX_FILE_MB = int(os.getenv("MAX_FILE_MB", "25"))
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")

UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {".mp3", ".wav", ".flac", ".ogg", ".aac", ".m4a", ".mp4"}

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Transcript IA API",
    description="Audio → Musical Arrangement → MIDI + MusicXML + PDF",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory job store
jobs: dict[str, dict] = {}


# ── Health ────────────────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {
        "status": "ok",
        "anthropic_key_set": bool(ANTHROPIC_API_KEY),
        "version": "1.0.0",
    }


# ── Main Analyze Endpoint ─────────────────────────────────────────────────────
@app.post("/analyze")
async def analyze(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    api_key: Optional[str] = None,
):
    suffix = Path(file.filename or "audio.mp3").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"Formato no soportado: {suffix}")

    content = await file.read()
    if len(content) > MAX_FILE_MB * 1024 * 1024:
        raise HTTPException(413, f"Archivo demasiado grande. Máximo {MAX_FILE_MB} MB.")

    job_id = str(uuid.uuid4())
    audio_path = UPLOAD_DIR / f"{job_id}{suffix}"
    async with aiofiles.open(audio_path, "wb") as f_out:
        await f_out.write(content)

    jobs[job_id] = {
        "id": job_id,
        "filename": file.filename,
        "status": "processing",
        "progress": 0,
        "error": None,
        "result": None,
    }

    effective_key = api_key or ANTHROPIC_API_KEY
    background_tasks.add_task(
        run_pipeline, job_id, audio_path, file.filename or "audio", effective_key
    )

    return {"job_id": job_id, "status": "processing"}


# ── Job Status ────────────────────────────────────────────────────────────────
@app.get("/status/{job_id}")
async def job_status(job_id: str):
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(404, "Job no encontrado")
    return job


# ── Download Endpoints ────────────────────────────────────────────────────────
@app.get("/export/midi/{job_id}")
async def download_midi(job_id: str):
    path = OUTPUT_DIR / f"{job_id}.mid"
    if not path.exists():
        raise HTTPException(404, "MIDI no disponible aún")
    job = jobs.get(job_id, {})
    fname = Path(job.get("filename","arrangement")).stem + ".mid"
    return FileResponse(str(path), media_type="audio/midi", filename=fname)


@app.get("/export/musicxml/{job_id}")
async def download_musicxml(job_id: str):
    path = OUTPUT_DIR / f"{job_id}.musicxml"
    if not path.exists():
        raise HTTPException(404, "MusicXML no disponible aún")
    job = jobs.get(job_id, {})
    fname = Path(job.get("filename","arrangement")).stem + ".musicxml"
    return FileResponse(
        str(path),
        media_type="application/vnd.recordare.musicxml+xml",
        filename=fname
    )


@app.get("/export/pdf/{job_id}")
async def download_pdf(job_id: str):
    path = OUTPUT_DIR / f"{job_id}.pdf"
    if not path.exists():
        raise HTTPException(404, "PDF no disponible aún")
    job = jobs.get(job_id, {})
    fname = Path(job.get("filename","arrangement")).stem + "_arreglo.pdf"
    return FileResponse(str(path), media_type="application/pdf", filename=fname)


@app.get("/export/analysis/{job_id}")
async def download_analysis_json(job_id: str):
    job = jobs.get(job_id)
    if not job or not job.get("result"):
        raise HTTPException(404, "Análisis no disponible aún")
    return JSONResponse(job["result"]["analysis"])


# ── Pipeline ──────────────────────────────────────────────────────────────────
async def run_pipeline(
    job_id: str,
    audio_path: Path,
    filename: str,
    api_key: str,
):
    def update(progress: int, status: str = "processing"):
        jobs[job_id]["progress"] = progress
        jobs[job_id]["status"] = status

    try:
        update(10)
        loop = asyncio.get_event_loop()
        transcriber = AudioTranscriber()
        transcription = await loop.run_in_executor(
            None, transcriber.transcribe, str(audio_path)
        )
        update(40)

        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY no configurada")
        analyzer = ClaudeAnalyzer(api_key)
        analysis = await loop.run_in_executor(
            None, analyzer.analyze, transcription, filename
        )
        update(70)

        midi_path = str(OUTPUT_DIR / f"{job_id}.mid")
        midi_exp = MIDIExporter()
        await loop.run_in_executor(None, midi_exp.export, transcription, analysis, midi_path)
        update(80)

        xml_path = str(OUTPUT_DIR / f"{job_id}.musicxml")
        xml_exp = MusicXMLExporter()
        await loop.run_in_executor(None, xml_exp.export, transcription, analysis, xml_path)
        update(90)

        pdf_path = str(OUTPUT_DIR / f"{job_id}.pdf")
        pdf_exp = PDFExporter()
        await loop.run_in_executor(None, pdf_exp.export, analysis, pdf_path)
        update(100, "done")

        jobs[job_id]["result"] = {
            "analysis": analysis,
            "exports": {
                "midi":     f"/export/midi/{job_id}",
                "musicxml": f"/export/musicxml/{job_id}",
                "pdf":      f"/export/pdf/{job_id}",
            },
            "transcription_info": {
                "key":         transcription.key,
                "tempo":       transcription.tempo,
                "time_sig":    f"{transcription.time_signature[0]}/{transcription.time_signature[1]}",
                "duration":    transcription.duration,
                "note_count":  len(transcription.notes),
                "instruments": transcription.instruments_detected,
            }
        }

    except Exception as e:
        jobs[job_id]["status"] = "error"
        jobs[job_id]["error"] = str(e)
        raise

    finally:
        try:
            audio_path.unlink(missing_ok=True)
        except Exception:
            pass