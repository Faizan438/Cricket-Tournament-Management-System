# Cricket League & Tournament Management (Flask)

A Flask + SQLAlchemy web app for running a cricket league: teams, players, tournaments, matches,
ball-by-ball scoring, tickets, sponsors and more.

- **40 related tables** in `models.py` (every `*_id` foreign key gets a SQLAlchemy relationship)
- **Full CRUD** on all 40 tables (`crud.py`), with server-side validation, flash messages and Post-Redirect-Get
- **Sessions**: login/logout; only logged-in users can add, edit or delete. CSRF token on every POST
- **Jinja2 inheritance**: every page extends `templates/base.html`

## Setup
```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python seed.py                  # creates cricket.db with sample data
python app.py                   # open http://127.0.0.1:5000
```
Admin login after seeding: `admin` / `admin123`.

Environment variables (optional): `SECRET_KEY` (set a real one outside development), `DATABASE_URL`.

## Structure
`app.py` app factory + login/logout · `models.py` tables · `crud.py` routes (blueprint) ·
`seed.py` sample data · `templates/` · `static/style.css`
