# Local Setup

## Windows PowerShell

1. Open PowerShell in the project root.
2. Run:

```powershell
.\start_local.ps1
```

This script will:

- create `.venv` if it does not exist
- install Python dependencies from `requirements.txt`
- create the `instance` folder if needed
- start the Flask app at `http://127.0.0.1:5000`

## Manual Setup

If you want to run it manually:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run.py
```

## Demo Login

- Admin: `admin` / `admin123`
- User: `maya` / `user123`

## Database

Default local database:

```text
sqlite:///instance/app.db
```

You can change it by setting environment variables before starting:

```powershell
$env:SECRET_KEY = "replace-this"
$env:DATABASE_URL = "sqlite:///instance/app.db"
$env:APP_NAME = "Import Export Admin"
python run.py
```

## Notes

- The first run auto-creates tables and seed data.
- To reset local demo data, delete `instance/app.db` and start again.
- For MySQL or PostgreSQL later, replace `DATABASE_URL` with the correct SQLAlchemy connection string.
