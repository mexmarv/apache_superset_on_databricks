# Superset on Databricks App

Apache Superset running directly as a Databricks App, fully integrated with your Databricks SQL Warehouse via the official `databricks-sqlalchemy` connector.
apache-superset==6.0.0rc1

## Setup

### 1. Upload
Upload this project folder as a Databricks App.

### 2. Configure Secrets
In your App settings, define the following secrets:
```
SUPERSET_SECRET_KEY=<your_random_secret>
SUPERSET_ADMIN_PASSWORD=<your_admin_password>
DATABRICKS_HOST=<your_databricks_workspace_host>
DATABRICKS_HTTP_PATH=<your_sql_warehouse_http_path>
DATABRICKS_TOKEN=<your_personal_access_token>
```

### 3. Deploy
Deploy the App from the Databricks UI.
The App will automatically:
- Initialize Superset metadata tables.
- Create an admin user.
- Start the Superset web server.

### 4. Access
Once deployed, open the App URL and log in:
```
Username: admin
Password: ${SUPERSET_ADMIN_PASSWORD}
```

## Databricks SQL Connection

Inside Superset, create a new Database connection with:
```
Dialect: Databricks
SQLAlchemy URI:
databricks+connector://token:${DATABRICKS_TOKEN}@${DATABRICKS_HOST}:443?http_path=${DATABRICKS_HTTP_PATH}
```

This connection enables direct access to Unity Catalog objects such as:
- `cat_alpura_master.sch_silver_layer.iot_arduino_sensors`
- `cat_rgm_reporting.sch_gold_layer.*`

## Environment Versions

| Component | Version |
|------------|----------|
| Apache Superset | 6.0.0rc1 |
| SQLAlchemy | 2.0.30 |
| Databricks SQL Connector | 4.0.5 |
| Databricks SQLAlchemy | 2.0.8 |
| Python | 3.11 |

## Boot Logic

The `boot.py` script:
- Ensures the environment and database migrations are consistent.
- Initializes the admin account.
- Starts Superset under Gunicorn.

If the App crashes, redeploying will re-initialize safely.

## Known Working Flow

- Detects and connects to Databricks catalogs (e.g. `cat_alpura_master`)
- Lists schemas and tables correctly (e.g. `sch_silver_layer.iot_arduino_sensors`)
- Allows SQL Lab and Chart queries through the Warehouse
- Fully operational inside Databricks Apps sandbox

## TODO / Next Improvements

- [ ] Persist Superset metadata in PostgreSQL instead of SQLite for multi-user setups.
- [ ] Enable HTTPS reverse proxy for secure access via Databricks workspace.
- [ ] Add OAuth integration using Azure AD or Databricks identity federation.
- [ ] Enable Superset caching layer (Redis or Memcached) for faster dashboard loads.
- [ ] Add dataset auto-discovery from Unity Catalog.
- [ ] Support full multi-catalog browsing (beyond `cat_master_blah`).
- [ ] Automate secrets rotation using Databricks Secret Scopes.
- [ ] Optionally persist state in Delta tables within Unity Catalog for audit/history.
- [ ] CI/CD integration with Databricks Repos or GitHub Actions for auto-deploys.

## License
MIT License © 2025
Built with ❤️ on Databricks by mexmarv.
