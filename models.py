"""40 related tables for the Cricket League & Tournament Management system.
Table names come from Flask-SQLAlchemy (CamelCase -> snake_case). Every *_id foreign key
gets a relationship automatically via link_relationships() at the bottom of this file."""
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()


def S(n=80, req=True): return db.Column(db.String(n), nullable=not req)
def U(n=80): return db.Column(db.String(n), unique=True, nullable=False)
def I(req=False, default=None): return db.Column(db.Integer, nullable=not req, default=default)
def F(): return db.Column(db.Float)
def D(): return db.Column(db.Date)
def B(): return db.Column(db.Boolean, default=False)
def fk(table, req=False): return db.Column(db.Integer, db.ForeignKey(table + '.id'), nullable=not req)


class Base(db.Model):
    __abstract__ = True
    id = db.Column(db.Integer, primary_key=True)

    def __str__(self):
        return str(getattr(self, 'name', None) or getattr(self, 'title', None) or f'{type(self).__name__} #{self.id}')


# --- Setup ---
class Country(Base): name = U(); code = U(3)
class City(Base): name = S(); country_id = fk('country', True)
class Venue(Base): name = S(); city_id = fk('city', True); capacity = I()
class Stand(Base): name = S(); venue_id = fk('venue', True); seats = I()
class Season(Base): name = U(20); year = I(True)

# --- Teams & people ---
class Team(Base): name = U(); short_name = S(5); city_id = fk('city'); founded = I()
class Coach(Base): name = S(); team_id = fk('team'); country_id = fk('country'); experience_years = I()
class PlayerRole(Base): name = U(30)
class Player(Base):
    name = S(); team_id = fk('team'); role_id = fk('player_role'); country_id = fk('country')
    dob = D(); batting_style = S(30, False); bowling_style = S(30, False)
class Umpire(Base): name = S(); country_id = fk('country'); matches_officiated = I(default=0)
class MatchReferee(Base): name = S(); country_id = fk('country')
class Commentator(Base): name = S(); country_id = fk('country'); language = S(30, False)
class Captaincy(Base): team_id = fk('team', True); player_id = fk('player', True); tournament_id = fk('tournament', True)
class Contract(Base):
    player_id = fk('player', True); team_id = fk('team', True)
    start_date = D(); end_date = D(); salary_million = F()
class Transfer(Base):
    player_id = fk('player', True); from_team_id = fk('team'); to_team_id = fk('team', True)
    fee_million = F(); transfer_date = D()
class Injury(Base): player_id = fk('player', True); description = S(120); injury_date = D(); recovery_days = I()

# --- Tournament ---
class Tournament(Base):
    name = U(); season_id = fk('season', True); format = S(10)
    start_date = D(); end_date = D()
class TournamentTeam(Base): tournament_id = fk('tournament', True); team_id = fk('team', True)
class Squad(Base): tournament_id = fk('tournament', True); team_id = fk('team', True); player_id = fk('player', True); jersey_no = I()
class CricketMatch(Base):
    title = S(); tournament_id = fk('tournament', True)
    team1_id = fk('team', True); team2_id = fk('team', True); venue_id = fk('venue')
    umpire_id = fk('umpire'); referee_id = fk('match_referee'); match_date = D()
    winner_id = fk('team'); status = S(15)
class PointsTable(Base):
    tournament_id = fk('tournament', True); team_id = fk('team', True)
    played = I(default=0); won = I(default=0); lost = I(default=0); points = I(default=0); net_run_rate = F()
class Award(Base): name = S(); tournament_id = fk('tournament', True); player_id = fk('player')
class Penalty(Base): match_id = fk('cricket_match', True); player_id = fk('player'); reason = S(120); fine_amount = F()
class Review(Base):
    match_id = fk('cricket_match', True); team_id = fk('team', True)
    umpire_decision = S(30, False); outcome = S(20, False)

# --- Scoring ---
class Innings(Base):
    match_id = fk('cricket_match', True); batting_team_id = fk('team', True); number = I(True)
    runs = I(default=0); wickets = I(default=0); overs = F()
class Ball(Base):
    innings_id = fk('innings', True); over_no = I(True); ball_no = I(True)
    batter_id = fk('player'); bowler_id = fk('player'); runs = I(default=0)
    is_wicket = B(); extra_type = S(10, False)
class Scorecard(Base):
    innings_id = fk('innings', True); player_id = fk('player', True)
    runs = I(default=0); balls_faced = I(default=0); fours = I(default=0); sixes = I(default=0); out_type = S(20, False)
class BowlingFigure(Base):
    innings_id = fk('innings', True); player_id = fk('player', True)
    overs = F(); maidens = I(default=0); runs_conceded = I(default=0); wickets = I(default=0)
class PlayerStat(Base):
    player_id = fk('player', True); tournament_id = fk('tournament', True)
    matches = I(default=0); runs = I(default=0); wickets = I(default=0); strike_rate = F()

# --- Business ---
class Sponsor(Base): name = U(); industry = S(40, False)
class TeamSponsor(Base): team_id = fk('team', True); sponsor_id = fk('sponsor', True); amount_million = F()
class TicketCategory(Base): name = U(30); price = F()
class Spectator(Base): name = S(); email = U(120); phone = S(20, False)
class Ticket(Base):
    match_id = fk('cricket_match', True); category_id = fk('ticket_category', True)
    stand_id = fk('stand'); price = F(); seat_no = S(10, False)
class Booking(Base): spectator_id = fk('spectator', True); ticket_id = fk('ticket', True); booked_on = D(); paid = B()
class Broadcaster(Base): name = U(); country_id = fk('country')
class BroadcastDeal(Base): broadcaster_id = fk('broadcaster', True); tournament_id = fk('tournament', True); value_million = F()

# --- Misc ---
class PracticeSession(Base): team_id = fk('team', True); venue_id = fk('venue'); session_date = D(); focus = S(60, False)
class Equipment(Base): name = S(); team_id = fk('team'); quantity = I()
class News(Base): title = S(120); tournament_id = fk('tournament'); body = S(500, False); published_on = D()


# --- Login accounts (not exposed through generic CRUD) ---
class AppUser(Base):
    username = db.Column(db.String(40), unique=True, nullable=False)
    password_hash = S(200)
    role = S(10)

    def set_password(self, pw): self.password_hash = generate_password_hash(pw)
    def check(self, pw): return check_password_hash(self.password_hash, pw)


def link_relationships():
    """Create a relationship() for every foreign key: team_id -> .team, team1_id -> .team1 ..."""
    by_table = {m.__tablename__: m for m in Base.__subclasses__()}
    for cls in by_table.values():
        for col in cls.__table__.columns:
            for f in col.foreign_keys:
                setattr(cls, col.name[:-3], db.relationship(by_table[f.column.table.name], foreign_keys=[col]))


link_relationships()
