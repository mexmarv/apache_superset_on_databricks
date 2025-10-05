import os
import json
import subprocess
import sqlalchemy

# Ensure Superset CLI finds the app/config
os.environ["FLASK_APP"] = "superset.app:create_app()"
os.environ["SUPERSET_CONFIG_PATH"] = "/app/python/source_code/superset_config.py"
os.environ.setdefault("PYTHONPATH", "/app/python/source_code")

def sh(cmd: list[str], allow_fail: bool = False):
    env = os.environ.copy()
    print("+", " ".join(cmd))
    try:
        subprocess.run(cmd, env=env, check=True)
    except subprocess.CalledProcessError:
        if allow_fail:
            return
        raise

def bootstrap():
    home = os.environ.get("SUPERSET_HOME", "/home/app/superset")
    if os.environ.get("SUPERSET_WIPE") == "1":
        sh(["rm", "-rf", home], allow_fail=True)
        print(f"[WIPE] Deleted {home}")
    os.makedirs(home, exist_ok=True)

    # Migrate & init Superset
    sh([".venv/bin/superset", "db", "upgrade"])
    sh([".venv/bin/superset", "init"])

    # Create admin (idempotent)
    sh([
        ".venv/bin/superset", "fab", "create-admin",
        "--username", os.environ.get("SUPERSET_ADMIN_USERNAME", "admin"),
        "--firstname", "Superset", "--lastname", "Admin",
        "--email", os.environ.get("SUPERSET_ADMIN_EMAIL", "admin@example.com"),
        "--password", os.environ.get("SUPERSET_ADMIN_PASSWORD", "admin"),
    ], allow_fail=True)

    # Patch for Databricks dialect expecting sqlalchemy.types.Uuid
    if not hasattr(sqlalchemy.types, "Uuid"):
        from sqlalchemy.types import CHAR
        sqlalchemy.types.Uuid = CHAR(36)
        print("[PATCH] sqlalchemy.types.Uuid -> CHAR(36)")

    # Create/Update Databricks DB inside app context
    from superset.app import create_app
    app = create_app()
    with app.app_context():
        from superset import db
        from superset.models.core import Database

        host = (os.environ.get("DATABRICKS_HOST", "") or "").replace("https://", "").replace("http://", "")
        http_path = os.environ.get("DATABRICKS_HTTP_PATH", "") or ""
        token = os.environ.get("DATABRICKS_TOKEN", "") or ""
        catalog = os.environ.get("DBX_CATALOG", "cat_master_alpura") or ""
        schema = os.environ.get("DBX_SCHEMA", "sch_silver_layer") or ""

        if host and http_path and token:
            # Put catalog/schema in URI path to set defaults
            path_suffix = f"/{catalog}/{schema}" if catalog and schema else ""
            uri = (
                f"databricks+connector://token:{token}@{host}:443"
                f"{path_suffix}?http_path={http_path}"
            )

            # Extra: only valid keys; pass http_path/catalog/schema via connect_args
            extra = {
                "engine_params": {
                    "connect_args": {
                        "http_path": http_path,
                        **({"catalog": catalog} if catalog else {}),
                        **({"schema": schema} if schema else {})
                    }
                },
                # Optional: control Superset's metadata caching (0 = no cache)
                "metadata_cache_timeout": {"catalog": 0, "schema": 0, "table": 0},
                "schemas_allowed_for_csv_upload": []
            }

            existing = db.session.query(Database).filter_by(database_name="Databricks").first()
            if not existing:
                dbx = Database(database_name="Databricks", sqlalchemy_uri=uri, extra=json.dumps(extra))
                db.session.add(dbx)
                db.session.commit()
                print("[INFO] Databricks connection created.")
            else:
                changed = False
                if existing.sqlalchemy_uri != uri:
                    existing.sqlalchemy_uri = uri
                    changed = True
                new_extra = json.dumps(extra)
                if (existing.extra or "") != new_extra:
                    existing.extra = new_extra
                    changed = True
                if changed:
                    db.session.commit()
                    print("[INFO] Databricks connection updated.")
                else:
                    print("[INFO] Databricks connection already up-to-date.")
        else:
            print("[WARN] Missing DATABRICKS_* env; skipping auto-connection.")

if __name__ == "__main__":
    bootstrap()
    sh([
        ".venv/bin/gunicorn", "superset.app:create_app()",
        "-k", "gevent", "-w", "4",
        "-b", "0.0.0.0:8000", "--timeout", "120",
    ])