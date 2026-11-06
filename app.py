import os
import secrets
import sqlite3

from flask import Flask, abort, flash, redirect, render_template, request, session, url_for
from sqlalchemy import event
from sqlalchemy.engine import Engine

from crud import GROUPS, bp
from models import AppUser, db


@event.listens_for(Engine, 'connect')
def enforce_foreign_keys(conn, _):
    if isinstance(conn, sqlite3.Connection):
        conn.execute('PRAGMA foreign_keys=ON')


def create_app():
    app = Flask(__name__)
    app.config.update(SECRET_KEY=os.environ.get('SECRET_KEY', 'dev-only-change-me'),
                      SQLALCHEMY_DATABASE_URI=os.environ.get('DATABASE_URL', 'sqlite:///cricket.db'),
                      SESSION_COOKIE_SAMESITE='Lax')
    db.init_app(app)
    app.register_blueprint(bp)
    with app.app_context():
        db.create_all()

    @app.before_request
    def check_csrf():
        if request.method == 'POST' and request.form.get('_csrf') != session.get('_csrf'):
            abort(400)

    @app.context_processor
    def inject():
        session.setdefault('_csrf', secrets.token_hex(16))
        return dict(GROUPS=GROUPS, csrf=session['_csrf'])

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            user = AppUser.query.filter_by(username=request.form.get('username', '').strip()).first()
            if user and user.check(request.form.get('password', '')):
                session['user'] = user.username
                flash(f'Welcome back, {user.username}.', 'success')
                nxt = request.args.get('next', '')
                return redirect(nxt if nxt.startswith('/') and not nxt.startswith('//') else url_for('crud.home'))
            flash('Wrong username or password.', 'error')
        return render_template('login.html')

    @app.post('/logout')
    def logout():
        session.pop('user', None)
        flash('You are logged out.', 'success')
        return redirect(url_for('crud.home'))

    return app


if __name__ == '__main__':
    create_app().run(debug=True)
