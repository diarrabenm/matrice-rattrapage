"""Micro-application minimale pour le module C4.

- GET /health : vivacité du processus. Ne teste PAS la base (choix assumé :
  un incident PostgreSQL ne doit pas faire redémarrer l'application).
- GET /ready  : disponibilité réelle, exécute `SELECT 1` sur PostgreSQL.
"""
import os

import psycopg
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(title="matrice-c4")


def database_url() -> str:
    # Les valeurs viennent de l'environnement (compose.yaml + .env), jamais de l'image.
    password = os.environ.get("POSTGRES_PASSWORD", "")
    password_file = os.environ.get("POSTGRES_PASSWORD_FILE")
    if password_file:
        with open(password_file, encoding="utf-8") as f:
            password = f.read().strip()
    return (
        f"postgresql://{os.environ.get('POSTGRES_USER', 'matrice')}:{password}"
        f"@{os.environ.get('DB_HOST', 'db')}:{os.environ.get('DB_PORT', '5432')}"
        f"/{os.environ.get('POSTGRES_DB', 'matrice')}"
    )


def check_database() -> None:
    with psycopg.connect(database_url(), connect_timeout=2) as conn:
        conn.execute("SELECT 1")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/ready")
def ready():
    try:
        check_database()
    except Exception:
        # Pas de détail d'erreur renvoyé : il pourrait contenir l'URL de connexion.
        return JSONResponse(status_code=503, content={"status": "unavailable", "database": "down"})
    return {"status": "ok", "database": "up"}
