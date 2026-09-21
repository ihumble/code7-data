"""Extra real data: last-season team records for every code, EPL fixtures/deadlines/live GW points (FPL),
and the international Test rugby game (2026 Nations Championship: ESPN fixtures, results and matchday squads).
Writes data/extra.json. Network: ESPN public site/core APIs + fantasy.premierleague.com."""
import json, re, time, unicodedata, subprocess, concurrent.futures as cf
from pathlib import Path
R = Path(__file__).parent / 'raw'; R.mkdir(exist_ok=True)
def get(url, cache=None):
    if cache and (R / cache).exists(): return json.load(open(R / cache))
    for i in range(4):
        try:
            out = subprocess.run(['curl', '-s', '--compressed', url], capture_output=True, timeout=60).stdout
            d = json.loads(out)
            if cache: json.dump(d, open(R / cache, 'w'))
            return d
        except Exception as e: time.sleep(1 + i)
    raise RuntimeError('fetch failed ' + url)
nrm = lambda s: re.sub(r'[^a-z0-9 ]', '', unicodedata.normalize('NFD', s).encode('ascii', 'ignore').decode().lower())
L = json.load(open(Path(__file__).parent / 'teams.json'))          # team codes per league (regenerate from src/leagues.js when teams change)
TEAMS = {l['id']: l['teams'] for l in L}
def entries(d):
    out = []
    def walk(n):
        if 'standings' in n and 'entries' in n['standings']: out.extend(n['standings']['entries'])
        for c in n.get('children', []): walk(c)
    walk(d); return out
def st(e, *names):
    m = {s.get('name'): s for s in e['stats']}
    for n in names:
        if n in m and m[n].get('value') is not None: return m[n]['value']
    return 0
def match_team(lid, disp, abbr):
    T = TEAMS[lid]; dn = nrm(disp)
    if abbr in T and lid in ('nfl', 'nba') and abbr not in ('NEW',): return abbr
    fix = {'nba': {'GS': 'GSW', 'NO': 'NOP', 'NY': 'NYK', 'SA': 'SAS', 'UTAH': 'UTA', 'WSH': 'WAS'}, 'nfl': {'WSH': 'WAS'}}
    if abbr in fix.get(lid, {}): return fix[lid][abbr]
    special = {'queensland reds': 'RED', 'western force': 'FOR', 'new south wales waratahs': 'WAR', 'manchester united': 'MUN', 'manchester city': 'MCI', 'nottingham forest': 'NFO', 'tottenham hotspur': 'TOT', 'brighton  hove albion': 'BHA', 'afc bournemouth': 'BOU', 'ipswich town': 'IPS', 'coventry city': 'COV', 'hull city': 'HUL'}
    if dn in special and special[dn] in T: return special[dn]
    for k, v in T.items():
        if nrm(v) == dn or nrm(v) in dn.split(' ') or (len(nrm(v)) > 4 and nrm(v) in dn): return k
    return None
out = {'tables': {}}
def table(lid, url, season_label, cache):
    tab = {}
    for e in entries(get(url, cache)):
        t = match_team(lid, e['team'].get('displayName', ''), e['team'].get('abbreviation', ''))
        if not t: continue
        w = st(e, 'wins', 'gamesWon'); l = st(e, 'losses', 'gamesLost'); d = st(e, 'ties', 'gamesDrawn')
        pf = st(e, 'pointsFor'); pa = st(e, 'pointsAgainst'); gp = st(e, 'gamesPlayed') or (w + l + d)
        tab[t] = [int(w), int(l), int(d), int(pf), int(pa), int(gp), int(st(e, 'rank', 'playoffSeed') or 0)]
    return {'season': season_label, 'rows': tab}
S = 'https://site.api.espn.com/apis/v2/sports/'
out['tables']['nba'] = table('nba', S + 'basketball/nba/standings?season=2026', '2025-26 regular season', 'st_nba.json')
out['tables']['nfl'] = table('nfl', S + 'football/nfl/standings?season=2025', '2025 regular season', 'st_nfl.json')
out['tables']['epl'] = table('epl', S + 'soccer/eng.1/standings?season=2025', '2025-26 Premier League', 'st_epl.json')
ch = table('epl', S + 'soccer/eng.2/standings?season=2025', '2025-26 Championship', 'st_eng2.json')
out['tables']['epl']['promoted'] = {t: r for t, r in ch['rows'].items() if t not in out['tables']['epl']['rows']}
out['tables']['nrl'] = table('nrl', S + 'rugby-league/3/standings?season=2026', '2026 NRL regular season', 'st_nrl.json')
out['tables']['srp'] = table('srp', S + 'rugby/242041/standings?season=2026', '2026 Super Rugby Pacific', 'st_srp.json')
for k, v in out['tables'].items():
    miss = [t for t in TEAMS[k] if t not in v['rows'] and t not in v.get('promoted', {})]
    print(k, len(v['rows']), 'missing', miss)
# ---------------- EPL: real fixtures, GW deadlines, live GW points ----------------
fx = get('https://fantasy.premierleague.com/api/fixtures/', 'fpl_fix.json'); bs = json.load(open(R / 'fpl.json'))
tm = {t['id']: t['short_name'] for t in bs['teams']}
out['epl'] = {'games': [[f['kickoff_time'], tm[f['team_h']], tm[f['team_a']], f['event'], f['team_h_score'] if f['finished'] else None, f['team_a_score'] if f['finished'] else None, f['team_h_difficulty'], f['team_a_difficulty']] for f in fx if f['event']],
              'roundDates': [e['deadline_time'] for e in bs['events']], 'live': {}}
for e in bs['events']:
    if e['finished']:
        lv = get(f"https://fantasy.premierleague.com/api/event/{e['id']}/live/", f"fpl_live_{e['id']}.json")
        out['epl']['live'][e['id']] = {str(x['id']): [x['stats']['total_points'], x['stats']['minutes']] for x in lv['elements'] if x['stats']['minutes'] > 0 or x['stats']['total_points']}
print('epl games', len(out['epl']['games']), 'live GWs', list(out['epl']['live']))
# ---------------- Test rugby: 2026 Nations Championship ----------------
ESPN_T = {'SOU': 'RSA', 'JAP': 'JPN'}
code = lambda a: ESPN_T.get(a, a)
games = []; dates = ['20260704', '20260711', '20260718', '20261106', '20261107', '20261108', '20261113', '20261114', '20261115', '20261121']
evs = {}
for d in dates:
    for e in get(f'https://site.api.espn.com/apis/site/v2/sports/rugby/17567/scoreboard?dates={d}', f'nc_sb_{d}.json').get('events', []): evs[e['id']] = e
rnd = lambda iso: 1 if iso < '2026-07-08' else 2 if iso < '2026-07-15' else 3 if iso < '2026-08-01' else 4 if iso < '2026-11-10' else 5 if iso < '2026-11-17' else 6
for eid, e in sorted(evs.items(), key=lambda x: x[1]['date']):
    c = e['competitions'][0]; H = next(x for x in c['competitors'] if x['homeAway'] == 'home'); A = next(x for x in c['competitors'] if x['homeAway'] == 'away')
    fin = e['status']['type']['name'] == 'STATUS_FINAL'
    games.append([e['date'], code(H['team']['abbreviation']), code(A['team']['abbreviation']), rnd(e['date']), int(H['score']) if fin else None, int(A['score']) if fin else None, eid, (c.get('venue') or {}).get('fullName', '')])
print('nc games', len(games), 'final', sum(1 for g in games if g[4] is not None))
JPOS = {1: 'PR', 3: 'PR', 2: 'HK', 4: 'LK', 5: 'LK', 6: 'LF', 7: 'LF', 8: 'LF', 9: 'SH', 10: 'FH', 12: 'MID', 13: 'MID', 11: 'OB', 14: 'OB', 15: 'OB'}
APOS = {'prop': 'PR', 'loosehead prop': 'PR', 'tighthead prop': 'PR', 'hooker': 'HK', 'lock': 'LK', 'flanker': 'LF', 'number 8': 'LF', 'no. 8': 'LF', 'back row': 'LF', 'scrum half': 'SH', 'scrum-half': 'SH', 'fly half': 'FH', 'fly-half': 'FH', 'centre': 'MID', 'center': 'MID', 'wing': 'OB', 'fullback': 'OB', 'full back': 'OB', 'scrumhalf': 'SH', 'flyhalf': 'FH', 'backrow': 'LF', 'utility back': 'OB'}
pl = {}
for g in games:
    if g[4] is None: continue
    s = get(f'https://site.api.espn.com/apis/site/v2/sports/rugby/17567/summary?event={g[6]}', f'nc_sum_{g[6]}.json')
    for side in s.get('rosters', []):
        t = code(side['team']['abbreviation'])
        for r in side['roster']:
            a = r['athlete']; j = int(r.get('jersey') or 0); key = a['id']
            p = pl.setdefault(key, {'n': a['displayName'], 't': t, 'id': key, 'starts': 0, 'bench': 0, 'jp': {}, 'apos': APOS.get(nrm(a.get('position', {}).get('displayName', '')), None)})
            if 1 <= j <= 15: p['starts'] += 1; jp = JPOS.get(j); p['jp'][jp] = p['jp'].get(jp, 0) + 1
            elif j: p['bench'] += 1; bp = {16: 'HK', 17: 'PR', 18: 'PR', 19: 'LK', 20: 'LF', 21: 'SH', 22: 'FH', 23: 'OB'}.get(j); p.setdefault('bj', {})[bp] = p.get('bj', {}).get(bp, 0) + 1
            if r.get('captain'): p['capt'] = 1
def athlete(pid):
    try: return pid, get(f'https://sports.core.api.espn.com/v2/sports/rugby/athletes/{pid}', f'nc_ath_{pid}.json')
    except Exception: return pid, {}
with cf.ThreadPoolExecutor(8) as ex:
    for pid, a in ex.map(athlete, list(pl)):
        p = pl[pid]; dob = a.get('dateOfBirth'); p['age'] = (2026 - int(dob[:4]) - (1 if dob[5:10] > '09-21' else 0)) if dob else None
        p['ht'] = a.get('displayHeight'); p['wt'] = round(a['weight'] / 2.2046) if a.get('weight') else None
        if not p['apos']: p['apos'] = APOS.get(nrm((a.get('position') or {}).get('displayName', '')), None)
out['tst'] = {'games': games, 'players': list(pl.values()), 'table': None}
tt = table_rows = {}
for e in entries(get(S + 'rugby/17567/standings?season=2026', 'st_nc.json')):
    t = code(e['team']['abbreviation']); tt[t] = [int(st(e, 'gamesWon')), int(st(e, 'gamesLost')), int(st(e, 'gamesDrawn')), int(st(e, 'pointsFor')), int(st(e, 'pointsAgainst')), int(st(e, 'gamesPlayed')), int(st(e, 'rank')), int(st(e, 'points'))]
out['tables']['tst'] = {'season': '2026 Nations Championship, rounds 1–3', 'rows': tt}
print('tst players', len(pl), 'no pos', sum(1 for p in pl.values() if not p['jp'] and not p['apos']))
json.dump(out, open(Path(__file__).parent / 'extra.json', 'w'), ensure_ascii=False)
