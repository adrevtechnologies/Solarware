"""WSGI entry point for Solarware backend."""
import sys
import os
from pathlib import Path

# Add backend directory to path
backend_path = str(Path(__file__).parent / "backend")
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# Import and expose the FastAPI app
from app.main import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
