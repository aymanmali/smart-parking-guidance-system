# Contributing to Smart Parking Guidance & Management System

Thank you for your interest in contributing! Whether you are improving the computer-vision pipeline (`cv_engine/`), FastAPI guidance backend (`backend/`), React operator/signage UI (`frontend/`), ESP32 firmware (`firmware/`), or KiCad PCB hardware (`hardware/`), contributions are welcome.

## Development Setup

```bash
# Python backend & CV engine
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest

# Frontend signage & operator UI
cd frontend
npm install
npm run dev
```

## Submitting a Pull Request

1. Fork the repository and create a topic branch from `main`.
2. Keep changes scoped and include tests for bug fixes or new behavior.
3. Verify locally:
   - `pytest` (backend & CV tests)
   - `ruff check .` (Python lint)
   - `cd frontend && npm run build` (frontend build, if UI changed)
4. Open a pull request describing what changed and why.
