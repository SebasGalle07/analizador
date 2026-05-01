from src.api import app


if __name__ == "__main__":
    host = "127.0.0.1"
    port = 8000
    print(f"Servidor local: http://{host}:{port}/")
    app.run(debug=True, host=host, port=port, use_reloader=False)
