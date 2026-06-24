# Capture Pakistan Tourism

Flask tour-management platform with public tours, destination search,
trekking, gallery, customer accounts, wishlist, bookings, PDF invoices,
reviews, email notifications, admin reporting, technical SEO and security.

## Local validation

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
python tools/check_project.py
python tools/security_audit.py
python run.py
```

## Production entry point

`wsgi.py` exports `app`. A common Gunicorn command is:

```bash
gunicorn --workers 3 --bind 127.0.0.1:8000 wsgi:app
```

Do not upload a local virtual environment, `.env`, logs, database exports or
backup ZIP files inside the public web root.
