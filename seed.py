"""Fills the database with sample league data. Run: python seed.py   (login: admin / admin123)"""
import random
from datetime import date

from app import create_app
from models import *  # noqa: F403

random.seed(7)
FIRST = ['Ali', 'Hamza', 'Usman', 'Bilal', 'Zain', 'Imran', 'Fahad', 'Saad', 'Hassan', 'Omar', 'Talha', 'Arslan']
LAST = ['Khan', 'Ahmed', 'Malik', 'Butt', 'Raza', 'Sheikh', 'Qureshi', 'Mirza']
name = lambda: f'{random.choice(FIRST)} {random.choice(LAST)}'


def add(model, **kw):
    obj = model(**kw)
    db.session.add(obj)
    db.session.flush()
    return obj


app = create_app()
with app.app_context():
    db.drop_all()
    db.create_all()
    admin = AppUser(username='admin', role='admin')
    admin.set_password('admin123')
    db.session.add(admin)

    pk, au = add(Country, name='Pakistan', code='PAK'), add(Country, name='Australia', code='AUS')
    cities = [add(City, name=n, country_id=pk.id) for n in ['Lahore', 'Karachi', 'Islamabad', 'Multan', 'Peshawar', 'Quetta']]
    venues = [add(Venue, name=n, city_id=c.id, capacity=cap) for n, c, cap in
              [('Gaddafi Stadium', cities[0], 34000), ('National Stadium', cities[1], 34228), ('Multan Cricket Stadium', cities[3], 35000)]]
    stands = [add(Stand, name=s, venue_id=v.id, seats=2000) for v in venues for s in ['North', 'South', 'Pavilion']]
    season = add(Season, name='2026', year=2026)
    roles = [add(PlayerRole, name=n) for n in ['Batter', 'Bowler', 'All-rounder', 'Wicketkeeper']]

    teams, players = [], {}
    for i, (n, s) in enumerate([('Lahore Qalandars', 'LQ'), ('Karachi Kings', 'KK'), ('Islamabad United', 'IU'),
                                ('Multan Sultans', 'MS'), ('Peshawar Zalmi', 'PZ'), ('Quetta Gladiators', 'QG')]):
        t = add(Team, name=n, short_name=s, city_id=cities[i].id, founded=2015)
        add(Coach, name=name(), team_id=t.id, country_id=pk.id, experience_years=random.randint(5, 20))
        players[t.id] = [add(Player, name=name(), team_id=t.id, role_id=random.choice(roles).id, country_id=pk.id,
                             dob=date(random.randint(1990, 2004), random.randint(1, 12), random.randint(1, 28)),
                             batting_style='Right-hand') for _ in range(8)]
        add(Equipment, name='Match balls', team_id=t.id, quantity=60)
        add(PracticeSession, team_id=t.id, venue_id=venues[i % 3].id, session_date=date(2026, 2, 5), focus='Death bowling')
        teams.append(t)

    tour = add(Tournament, name='Pakistan T20 League 2026', season_id=season.id, format='T20',
               start_date=date(2026, 2, 10), end_date=date(2026, 3, 20))
    pts = {}
    for t in teams:
        add(TournamentTeam, tournament_id=tour.id, team_id=t.id)
        pts[t.id] = add(PointsTable, tournament_id=tour.id, team_id=t.id, played=0, won=0, lost=0, points=0, net_run_rate=0.0)
        add(Captaincy, team_id=t.id, player_id=players[t.id][0].id, tournament_id=tour.id)
        for j, p in enumerate(players[t.id]):
            add(Squad, tournament_id=tour.id, team_id=t.id, player_id=p.id, jersey_no=j + 1)
            add(Contract, player_id=p.id, team_id=t.id, start_date=date(2026, 1, 1), end_date=date(2027, 12, 31), salary_million=round(random.uniform(1, 9), 1))
            add(PlayerStat, player_id=p.id, tournament_id=tour.id, matches=0, runs=0, wickets=0, strike_rate=0.0)

    umpires = [add(Umpire, name=name(), country_id=pk.id, matches_officiated=random.randint(20, 150)) for _ in range(3)]
    referee = add(MatchReferee, name='Roshan Mahanama', country_id=au.id)
    cats = [add(TicketCategory, name=n, price=p) for n, p in [('General', 800), ('Premium', 2500), ('VIP', 6000)]]
    fans = [add(Spectator, name=name(), email=f'fan{i}@example.com', phone='0300-0000000') for i in range(4)]

    for k, (a, b) in enumerate([(0, 1), (2, 3), (4, 5), (0, 2), (1, 3), (4, 0)]):
        ta, tb = teams[a], teams[b]
        winner = random.choice([ta, tb])
        loser = tb if winner is ta else ta
        m = add(CricketMatch, title=f'{ta.short_name} vs {tb.short_name}', tournament_id=tour.id, team1_id=ta.id, team2_id=tb.id,
                venue_id=venues[k % 3].id, umpire_id=umpires[k % 3].id, referee_id=referee.id,
                match_date=date(2026, 2, 10 + k), winner_id=winner.id, status='Completed')
        for n, bat, bowl in [(1, ta, tb), (2, tb, ta)]:
            inn = add(Innings, match_id=m.id, batting_team_id=bat.id, number=n, runs=random.randint(120, 200), wickets=random.randint(3, 10), overs=20.0)
            for p in players[bat.id][:3]:
                add(Scorecard, innings_id=inn.id, player_id=p.id, runs=random.randint(5, 80), balls_faced=random.randint(5, 50), fours=random.randint(0, 8), sixes=random.randint(0, 4), out_type='caught')
            bw = random.choice(players[bowl.id])
            add(BowlingFigure, innings_id=inn.id, player_id=bw.id, overs=4.0, maidens=0, runs_conceded=random.randint(20, 45), wickets=random.randint(0, 4))
            for ball in range(1, 7):
                add(Ball, innings_id=inn.id, over_no=1, ball_no=ball, batter_id=players[bat.id][0].id, bowler_id=bw.id, runs=random.choice([0, 1, 2, 4, 6]), is_wicket=False)
        add(Review, match_id=m.id, team_id=loser.id, umpire_decision='Not out', outcome='Umpire\'s call')
        if k == 0:
            add(Penalty, match_id=m.id, player_id=players[ta.id][1].id, reason='Slow over rate', fine_amount=50000)
        for c, st in zip(cats, stands):
            tk = add(Ticket, match_id=m.id, category_id=c.id, stand_id=st.id, price=c.price, seat_no=f'A{k + 1}')
            if k < 3:
                add(Booking, spectator_id=random.choice(fans).id, ticket_id=tk.id, booked_on=date(2026, 2, 1), paid=True)
        pts[winner.id].won += 1; pts[winner.id].points += 2
        pts[loser.id].lost += 1
        pts[winner.id].played += 1; pts[loser.id].played += 1

    sp = add(Sponsor, name='Pak Telecom', industry='Telecom')
    add(TeamSponsor, team_id=teams[0].id, sponsor_id=sp.id, amount_million=120.5)
    bc = add(Broadcaster, name='Sports Network', country_id=pk.id)
    add(BroadcastDeal, broadcaster_id=bc.id, tournament_id=tour.id, value_million=900.0)
    add(Commentator, name=name(), country_id=pk.id, language='Urdu')
    add(Award, name='Player of the Tournament', tournament_id=tour.id, player_id=players[teams[0].id][0].id)
    add(Injury, player_id=players[teams[1].id][2].id, description='Hamstring strain', injury_date=date(2026, 2, 20), recovery_days=14)
    add(Transfer, player_id=players[teams[2].id][3].id, from_team_id=teams[2].id, to_team_id=teams[3].id, fee_million=15.0, transfer_date=date(2026, 1, 15))
    add(News, title='Season opener set for Gaddafi Stadium', tournament_id=tour.id, body='The league begins on 10 February.', published_on=date(2026, 2, 1))
    db.session.commit()
    print('Seeded.')
