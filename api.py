import os

from src.api import app


if __name__ == "__main__":
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    debug = os.getenv("DEBUG", "0") == "1"
    print(f"Servidor local: http://127.0.0.1:{port}/")
    app.run(debug=debug, host=host, port=port, use_reloader=False)
