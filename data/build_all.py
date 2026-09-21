# Builds src/data.js — REAL player pools for every code (no fictional players).
import json, glob, re, math, pathlib, statistics, unicodedata
D = pathlib.Path(__file__).parent; R = D / 'raw'; OUT = D.parent / 'src' / 'data.js'
def clamp(x, a, b): return max(a, min(b, x))
def r1k(x): return int(round(x / 1000.0) * 1000)
data = {}

# ---------------- NBA (ESPN live rosters + ESPN 2025-26/2024-25 per-game stats + real 2026-27 schedule) ----------------
nba = json.load(open(D / 'nba.json'))
P = []
for x in nba['players']:
    if x['m'] < 4 and x['gp'] >= 10 and not x['src'].startswith('rookie'): continue      # deep end-of-bench guys who barely play
    fp = x['fp']; av = max(0.5, x['av']) if not x['src'].startswith('rookie') else 0.85
    price = r1k(clamp(280000 + (fp - 6) * 23000, 280000, 1750000))
    hm = re.match(r"(\d+)' ?(\d+)", x['ht'] or ''); inch = int(hm.group(1)) * 12 + int(hm.group(2)) if hm else 78
    p2 = None
    if x['p'] == 'F' and (inch >= 82 or (x['blk'] >= 1.2 and x['reb'] >= 7)): p2 = 'C'
    elif x['p'] == 'F' and inch <= 79 and x['ast'] >= 4: p2 = 'G'
    elif x['p'] == 'G' and inch >= 78: p2 = 'F'
    elif x['p'] == 'C' and inch <= 83: p2 = 'F'
    P.append([x['n'], x['t'], x['p'], price, 1 if x['new'] else 0, round(fp, 1), av, x['m'], x['pts'], x['reb'], x['ast'], x['stl'], x['blk'], x['tov'], x['gp'], x['src'], x['age'], x['ht'], x['j'], x['td'], x['dd'], x['tl'], p2])
G = [[g['d'], g['h'], g['a']] for g in nba['games']]
data['nba'] = {'fields': 'n t p price new fp av m pts reb ast stl blk tov gp src age ht j td dd tl p2', 'players': P, 'games': G,
               'report': nba['report'], 'source': 'ESPN live rosters (21 Sep 2026), ESPN per-game stats 2025-26 (2024-25 if injured), ESPN 2026-27 schedule'}

# ---------------- EPL (official Fantasy Premier League 2026-27 data) ----------------
f = json.load(open(R / 'fpl.json')); tm = {t['id']: t['short_name'] for t in f['teams']}
POS = {1: 'GK', 2: 'DEF', 3: 'MID', 4: 'FWD'}; P = []
for e in f['elements']:
    if e['status'] == 'u': continue                      # left the club / unavailable for the season
    ppg = float(e['points_per_game'] or 0); price = e['now_cost'] * 100000
    exp = {1: 0.55, 2: 0.55, 3: 0.62, 4: 0.62}[e['element_type']] * (e['now_cost'] / 10.0) - 0.4   # prior from price (FPL pts per game ~ price)
    mins = e['minutes']; w = min(1.0, mins / 900.0)
    fp = round(max(1.0, w * ppg + (1 - w) * exp), 2)
    cop = e.get('chance_of_playing_next_round'); av = 0.9 if cop is None else max(0.1, cop / 100.0)
    fn, sn, wb = e['first_name'], e['second_name'], e['web_name']
    if ' ' in wb: name = wb
    elif '.' in wb: name = fn.split()[0] + ' ' + wb.split('.')[-1]
    elif wb == fn: name = fn + ' ' + sn.split()[-1]
    elif wb in sn: name = fn.split()[0] + ' ' + wb
    else: name = wb
    P.append([name, tm[e['team']], POS[e['element_type']], price, 0, fp, round(av, 2), e['total_points'], e['goals_scored'], e['assists'], e['clean_sheets'], mins, e['web_name'], e['status'], e['id']])
data['epl'] = {'fields': 'n t p price new fp av tot g a cs min web status fid', 'players': P, 'source': 'Official Fantasy Premier League 2026-27 player list & prices (21 Sep 2026, after GW4)'}

# ---------------- NFL (Sleeper player list + 2025 season PPR stats; ESPN 2026 schedule for real byes) ----------------
sp = json.load(open(R / 'sleeper_players.json')); ss = json.load(open(R / 'sleeper_stats25.json')); P = []
try: s26 = json.load(open(R / 'sleeper_stats26.json'))   # 2026 season to date
except Exception: s26 = {}
BANDS = {'QB': (300000, 1000000), 'RB': (250000, 950000), 'WR': (250000, 950000), 'TE': (200000, 700000), 'K': (150000, 350000), 'DEF': (150000, 400000)}
for pid, v in sp.items():
    pos = v.get('position'); team = v.get('team')
    if pos not in BANDS or not team or not v.get('active'): continue
    st = ss.get(pid) or {}; gp = st.get('gp') or 0; ppr = st.get('pts_ppr') or 0
    ppg = ppr / gp if gp else 0
    dco = v.get('depth_chart_order') or 9; rookie = (v.get('years_exp') == 0)
    if gp < 3:
        est = {'QB': [16, 8, 4], 'RB': [11, 6, 3], 'WR': [10, 6, 4], 'TE': [7, 4, 2], 'K': [7, 6, 6], 'DEF': [6, 6, 6]}[pos]
        ppg = est[min(2, dco - 1)] if dco <= 3 else 2; src = 'rookie/depth estimate' if rookie else 'depth estimate'
    else: src = '2025 season'
    c = s26.get(pid) or {}; g26 = c.get('gp') or 0
    if g26 and c.get('pts_ppr') is not None:     # blend this season's real PPR per game (4-game prior weight)
        w = g26 / (g26 + 4); ppg = w * (c['pts_ppr'] / g26) + (1 - w) * ppg; src = f'2026 ({int(g26)} gp) + ' + src
    if pos not in ('K', 'DEF') and dco > 3 and ppg < 4: continue
    if pos == 'K' and dco > 1: continue
    lo, hi = BANDS[pos]; top = {'QB': 24, 'RB': 22, 'WR': 21, 'TE': 15, 'K': 10, 'DEF': 10}[pos]
    ppg = max(0.0, ppg); price = r1k(clamp(lo + (hi - lo) * (ppg / top) ** 1.2, lo, hi))
    name = v.get('full_name') or (team + ' D/ST' if pos == 'DEF' else pid)
    if pos == 'DEF': name = f"{team} D/ST"
    av = clamp((gp / 17.0) if gp else 0.85, 0.55, 0.97)
    P.append([name, team, pos, price, 1 if rookie else 0, round(ppg, 1), round(av, 2), gp, round((st.get('pass_yd') or 0) / max(gp, 1)), round((st.get('rush_yd') or 0) / max(gp, 1)), round((st.get('rec_yd') or 0) / max(gp, 1)), round(((st.get('pass_td') or 0) + (st.get('rush_td') or 0) + (st.get('rec_td') or 0)) / max(gp, 1), 2), src, v.get('number'), v.get('age')])
NFLMAP = {'WSH': 'WAS', 'LAR': 'LAR'}
byes = {}; games = []
for fn in glob.glob(str(R / 'nflsched_*.json')):
    d = json.load(open(fn)); t = d['team']['abbreviation']; t = NFLMAP.get(t, t); weeks = set()
    for ev in d.get('events', []):
        wk = ev['week']['number']; weeks.add(wk); c = ev['competitions'][0]; h = a = None
        for x in c['competitors']:
            ab = NFLMAP.get(x['team']['abbreviation'], x['team']['abbreviation'])
            if x['homeAway'] == 'home': h = ab
            else: a = ab
        games.append((wk, ev['date'], h, a))
    byes[t] = sorted(set(range(1, 19)) - weeks)
games = sorted(set(games))
data['nfl'] = {'fields': 'n t p price new fp av gp passyd rushyd recyd td src j age', 'players': P, 'byes': byes, 'games': [list(g) for g in games], 'source': 'Sleeper NFL player database + 2025 season PPR stats (21 Sep 2026); ESPN 2026 schedule (real bye weeks)'}

# ---------------- NRL (official NRL Fantasy 2026 data) ----------------
p = json.load(open(R / 'nrl_players.json')); sq = {x['id']: x['short_name'] for x in json.load(open(R / 'nrl_squads.json'))}
NPOS = {1: 'HOK', 2: 'MID', 3: 'EDG', 4: 'HLF', 5: 'CTR', 6: 'WFB'}; SQMAP = {'BUL': 'CBY', 'STG': 'SGI', 'CAN': 'CBR', 'GOL': 'GLD', 'WAR': 'NZW', 'CBR': 'CBR', 'DRA': 'SGI', 'GCT': 'GLD', 'WAR': 'NZW', 'WST': 'WST', 'SEA': 'MAN', 'STO': 'MEL', 'RAB': 'SOU', 'ROO': 'SYD', 'SHA': 'CRO', 'TIT': 'GLD', 'KNI': 'NEW', 'COW': 'NQL', 'PAN': 'PEN', 'EEL': 'PAR', 'BRO': 'BRI', 'DOL': 'DOL', 'RAI': 'CBR'}
P = []
for x in p:
    s = x['stats']; gp = s.get('games_played') or 0; avg = s.get('avg_points') or 0
    if gp < 1 and x['cost'] <= 230000 and x['status'] == 'not-playing': continue
    sc = list((s.get('scores') or {}).values()); sd = round(statistics.pstdev(sc), 1) if len(sc) >= 3 else round(max(8, avg * 0.3), 1)
    prior = max(15.0, (x['cost'] - 150000) / 9500.0); fp = round((avg * gp + prior * 5) / (gp + 5), 1)
    team = sq[x['squad_id']]; team = SQMAP.get(team, team)
    P.append([x['first_name'] + ' ' + x['last_name'], team, NPOS[x['positions'][0]], x['cost'], 0, fp, round(clamp(gp / 24.0, 0.45, 0.96) if gp else 0.6, 2), gp, sd, s.get('high_score') or 0, '/'.join(NPOS[i] for i in x['positions']), x['status'], NPOS[x['positions'][1]] if len(x['positions']) > 1 else None])
data['nrl'] = {'fields': 'n t p price new fp av gp sd high dual status p2', 'players': P, 'source': 'Official NRL Fantasy 2026 player list, prices and averages (end of 2026 season)'}

json.dump(data, open(D / 'all.json', 'w'), ensure_ascii=False)
for k, v in data.items():
    import collections
    print(k, len(v['players']), dict(collections.Counter(x[2] for x in v['players'])), 'price', min(x[3] for x in v['players']), max(x[3] for x in v['players']))
