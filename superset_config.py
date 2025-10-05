# superset_config.py
import os
import secrets
import pathlib

# --- Paths / Home ---
HOME = os.getenv("SUPERSET_HOME", "/home/app/superset")
pathlib.Path(HOME).mkdir(parents=True, exist_ok=True)

# --- SECRET KEY (robust resolution) ---
# Order:
#   1) SECRET_KEY env
#   2) SUPERSET_SECRET_KEY env
#   3) Persisted file at SUPERSET_HOME/SECRET_KEY (created on first run)
_secret = os.getenv("SECRET_KEY") or os.getenv("SUPERSET_SECRET_KEY")
secret_file = os.path.join(HOME, "SECRET_KEY")
if not _secret:
    if os.path.exists(secret_file):
        with open(secret_file, "r") as f:
            _secret = f.read().strip()
    else:
        _secret = secrets.token_urlsafe(64)
        with open(secret_file, "w") as f:
            f.write(_secret)

SECRET_KEY = _secret

# --- Metadata DB (Superset’s own state: users, dashboards, etc.) ---
# Pulled from env; defaults to SQLite in the local app filesystem (ephemeral).
SQLALCHEMY_DATABASE_URI = os.getenv(
    "SQLALCHEMY_DATABASE_URI",
    f"sqlite:////{os.path.join(HOME, 'metadata.db')}",
)

# --- Reverse proxy / security bits for Apps ---
ENABLE_PROXY_FIX = True           # respect X-Forwarded-* from Databricks proxy
WTF_CSRF_ENABLED = True
SESSION_COOKIE_SAMESITE = "Lax"   # keeps logins working behind proxies

# --- Nice defaults ---
ROW_LIMIT = 50000
MAX_UPLOAD_SIZE = 1024 * 1024 * 200  # 200 MB CSV

# Optional: feature flags (leave commented unless you need them)
# FEATURE_FLAGS = {
#     "EMBEDDED_SUPERSET": True,
# }

# Optional: If you use Mapbox visuals, set MAPBOX_API_KEY via env
MAPBOX_API_KEY = os.getenv("MAPBOX_API_KEY", "")