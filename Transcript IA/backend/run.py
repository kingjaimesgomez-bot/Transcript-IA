"""
run.py — Transcript IA Backend
Usage:
    python run.py
    python run.py --port 8000 --reload
"""
import sys
import argparse
import uvicorn

def main():
    parser = argparse.ArgumentParser(description="Transcript IA API Server")
    parser.add_argument("--host",   default="0.0.0.0",  help="Host (default: 0.0.0.0)")
    parser.add_argument("--port",   default=8000, type=int, help="Port (default: 8000)")
    parser.add_argument("--reload", action="store_true",   help="Auto-reload on file change")
    args = parser.parse_args()

    print(f"""
╔══════════════════════════════════════╗
║     Transcript IA — Backend API      ║
║     Powered by Claude AI             ║
╠══════════════════════════════════════╣
║  http://{args.host}:{args.port}
║  Docs: http://localhost:{args.port}/docs
╚══════════════════════════════════════╝
    """)

    uvicorn.run(
        "api.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info",
    )

if __name__ == "__main__":
    main()