import os
import sys
from pathlib import Path


def _ensure_project_python():
    script_name = Path(sys.argv[0]).name.lower() if sys.argv else ""
    if script_name != "api.py":
        return

    try:
        import matplotlib  # noqa: F401
        return
    except ModuleNotFoundError:
        pass

    venv_python = Path(__file__).resolve().parent / ".venv" / "Scripts" / "python.exe"
    if venv_python.exists() and Path(sys.executable).resolve() != venv_python.resolve():
        os.execv(str(venv_python), [str(venv_python), *sys.argv])


_ensure_project_python()

from src.api import app


if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    debug = os.getenv("DEBUG", "0") == "1"
    print(f"Servidor local: http://127.0.0.1:{port}/")
    app.run(debug=debug, host=host, port=port, use_reloader=False)
