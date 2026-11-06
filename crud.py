"""Generic CRUD blueprint: list / add / edit / delete for every table, with server-side validation."""
from datetime import date
from functools import wraps

from flask import Blueprint, abort, flash, redirect, render_template, request, session, url_for
from sqlalchemy import Boolean, Date, Float, Integer
from sqlalchemy.exc import IntegrityError

from models import AppUser, Base, db

bp = Blueprint('crud', __name__)

GROUPS = {
    'Setup': ['country', 'city', 'venue', 'stand', 'season'],
    'Teams & People': ['team', 'coach', 'player_role', 'player', 'umpire', 'match_referee', 'commentator',
                       'captaincy', 'contract', 'transfer', 'injury'],
    'Tournament': ['tournament', 'tournament_team', 'squad', 'cricket_match', 'points_table', 'award',
                   'penalty', 'review'],
    'Scoring': ['innings', 'ball', 'scorecard', 'bowling_figure', 'player_stat'],
    'Business': ['sponsor', 'team_sponsor', 'ticket_category', 'ticket', 'spectator', 'booking',
                 'broadcaster', 'broadcast_deal'],
    'Misc': ['practice_session', 'equipment', 'news'],
}


def registry():
    return {m.__tablename__: m for m in Base.__subclasses__() if m is not AppUser}


def get_model(table):
    return registry().get(table) or abort(404)


def login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if 'user' not in session:
            flash('Log in to add, edit or delete records.', 'error')
            return redirect(url_for('login', next=request.path))
        return view(*args, **kwargs)
    return wrapper


def fields(model):
    out = []
    for c in model.__table__.columns:
        if c.primary_key:
            continue
        is_fk = bool(c.foreign_keys)
        kind = ('select' if is_fk else 'checkbox' if isinstance(c.type, Boolean)
                else 'date' if isinstance(c.type, Date)
                else 'number' if isinstance(c.type, (Integer, Float)) else 'text')
        out.append(dict(
            name=c.name, col=c, kind=kind,
            label=(c.name[:-3] if is_fk else c.name).replace('_', ' ').title(),
            attr=c.name[:-3] if is_fk else c.name,
            target=registry()[next(iter(c.foreign_keys)).column.table.name] if is_fk else None))
    return out


def parse(fs, form):
    """Validate a submitted form on the server. Returns (values, errors)."""
    vals, errs = {}, {}
    for f in fs:
        name, c = f['name'], f['col']
        if f['kind'] == 'checkbox':
            vals[name] = name in form
            continue
        raw = (form.get(name) or '').strip()
        if not raw:
            if not c.nullable:
                errs[name] = 'This field is required.'
            elif c.default is None:
                vals[name] = None
            continue
        try:
            if f['kind'] == 'select':
                v = int(raw)
                if not db.session.get(f['target'], v):
                    raise ValueError
            elif f['kind'] == 'number':
                v = int(raw) if isinstance(c.type, Integer) else float(raw)
                if v < 0:
                    errs[name] = 'Must be zero or more.'
            elif f['kind'] == 'date':
                v = date.fromisoformat(raw)
            else:
                v = raw
                if len(raw) > c.type.length:
                    errs[name] = f'Use at most {c.type.length} characters.'
        except ValueError:
            errs[name] = 'Enter a valid value.'
            continue
        vals[name] = v
    if vals.get('start_date') and vals.get('end_date') and vals['end_date'] < vals['start_date']:
        errs['end_date'] = 'End date must be on or after the start date.'
    return vals, errs


@bp.route('/')
def home():
    counts = {t: db.session.scalar(db.select(db.func.count()).select_from(m)) for t, m in registry().items()}
    return render_template('index.html', counts=counts, total=len(counts))


@bp.route('/<table>/')
def index(table):
    m = get_model(table)
    page = db.paginate(db.select(m).order_by(m.id.desc()), page=request.args.get('page', 1, type=int), per_page=15)
    return render_template('list.html', table=table, title=table.replace('_', ' ').title(), fs=fields(m), page=page)


@bp.route('/<table>/new', methods=['GET', 'POST'])
@bp.route('/<table>/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(table, id=None):
    m = get_model(table)
    fs = fields(m)
    obj = db.get_or_404(m, id) if id else None
    errs = {}
    if request.method == 'POST':
        vals, errs = parse(fs, request.form)
        if not errs:
            target = obj or m()
            for k, v in vals.items():
                setattr(target, k, v)
            try:
                db.session.add(target)
                db.session.commit()
                flash('Changes saved.' if obj else 'Record added.', 'success')
                return redirect(url_for('crud.index', table=table))  # Post-Redirect-Get
            except IntegrityError:
                db.session.rollback()
                errs = {fs[0]['name']: 'A record with this value already exists.'}
        cur = request.form
    else:
        cur = {f['name']: getattr(obj, f['name']) if getattr(obj, f['name']) is not None else '' for f in fs} if obj else {}
    options = {f['name']: db.session.scalars(db.select(f['target']).limit(500)).all() for f in fs if f['kind'] == 'select'}
    return render_template('form.html', table=table, title=table.replace('_', ' ').title(),
                           fs=fs, obj=obj, cur=cur, errs=errs, options=options)


@bp.post('/<table>/<int:id>/delete')
@login_required
def delete(table, id):
    obj = db.get_or_404(get_model(table), id)
    try:
        db.session.delete(obj)
        db.session.commit()
        flash('Record deleted.', 'success')
    except IntegrityError:
        db.session.rollback()
        flash('This record is used by other records. Remove those first.', 'error')
    return redirect(url_for('crud.index', table=table))
