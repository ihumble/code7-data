# Builds data/nba.json: Tom's 2026-27 roster list, cross-checked against ESPN's live rosters,
# with real 2025-26 (fallback 2024-25) per-game stats and the real 2026-27 regular-season schedule.
import json, glob, re, unicodedata, pathlib
R = pathlib.Path(__file__).parent / 'raw'
MAP = {'GS': 'GSW', 'NO': 'NOP', 'NY': 'NYK', 'SA': 'SAS', 'UTAH': 'UTA', 'WSH': 'WAS'}
ab = lambda a: MAP.get(a, a)
def norm(n):
    n = unicodedata.normalize('NFKD', n).encode('ascii', 'ignore').decode().lower()
    n = re.sub(r'[\.\'’`-]', '', n); n = re.sub(r'\b(jr|sr|ii|iii|iv)\b', '', n)
    return re.sub(r'\s+', ' ', n).strip()
teams = {t['team']['id']: ab(t['team']['abbreviation']) for t in json.load(open(R/'teams.json'))['sports'][0]['leagues'][0]['teams']}
# ESPN rosters
espn = {}
for f in glob.glob(str(R/'roster_*.json')):
    d = json.load(open(f)); tm = ab(d['team']['abbreviation'])
    for a in d['athletes']:
        pos = (a.get('position') or {}).get('abbreviation', 'F')
        espn[norm(a['displayName'])] = dict(id=a['id'], name=a['displayName'], team=tm, pos=pos, jersey=a.get('jersey'), age=a.get('age'),
            exp=(a.get('experience') or {}).get('years'), ht=a.get('displayHeight'), inj=[i.get('status') for i in a.get('injuries') or []])
# stats
def stats(season):
    out = {}
    for a in json.load(open(R/f'stats_{season}.json')).get('athletes', []):
        c = {x['name']: x['values'] for x in a['categories']}
        g, o, df = c['general'], c['offensive'], c['defensive']
        out[a['athlete']['id']] = dict(gp=g[0], mpg=round(g[1], 1), reb=round(g[11], 2), pts=round(o[0], 2), ast=round(o[10], 2), tov=round(o[11], 2), stl=round(df[0], 2), blk=round(df[1], 2), dd=g[6], td=g[7], team=a['athlete'].get('teamShortName'), name=a['athlete']['displayName'])
    return out
S26, S25 = stats(2026), stats(2025)
try: S27 = stats(2027)                       # the 2026-27 season so far (empty until opening night)
except Exception: S27 = {}
byname27 = {norm(v['name']): (k, v) for k, v in S27.items()}
byname26 = {norm(v['name']): (k, v) for k, v in S26.items()}; byname25 = {norm(v['name']): (k, v) for k, v in S25.items()}
# Tom's list
src = (pathlib.Path(__file__).parent.parent / 'src' / 'nba-roster.js').read_text()
tom = {}
for tm, body in re.findall(r"\n  ([A-Z]{3}): '((?:[^'\\]|\\.)*)'", src):
    for e in body.replace("\\'", "'").split(';'):
        e = e.strip()
        if not e: continue
        nm = e.split('|')[0]; new = nm.startswith('*'); nm = nm.lstrip('*')
        tom[norm(nm)] = dict(name=nm, team=tm, new=new)
report = {'tom_only': [], 'team_mismatch': [], 'espn_only': []}
players = []
for k, t in tom.items():
    e = espn.get(k)
    if not e: report['tom_only'].append(f"{t['name']} ({t['team']})")
    elif e['team'] != t['team']: report['team_mismatch'].append(f"{t['name']}: Tom {t['team']} / ESPN {e['team']}")
    if e: players.append((k, e['name'], e['team'], t['new'], e)); e['tl'] = 1  # ESPN live roster is the source of truth for team
for k, e in espn.items():
    if k not in tom:
        report['espn_only'].append(f"{e['name']} ({e['team']})")
        players.append((k, e['name'], e['team'], (e.get('exp') == 0), e))
# draft slots for 2026 rookies (Wikipedia 2026 NBA draft, picks 1-10) + default rookie estimate
TOP = {'aj dybantsa': 1, 'darryn peterson': 2, 'cameron boozer': 3, 'caleb wilson': 4, 'keaton wagler': 5, 'mikel brown': 6, 'darius acuff': 7, 'kingston flemings': 8, 'morez johnson': 9, 'brayden burries': 10}
POS = {'PG': 'G', 'SG': 'G', 'G': 'G', 'SF': 'F', 'PF': 'F', 'F': 'F', 'C': 'C'}
out = []
for k, name, team, new, e in players:
    sid = e['id'] if e else None
    s = S26.get(sid) if sid else None; src_season = '2025-26'
    if not s and k in byname26: s = byname26[k][1]
    s25 = S25.get(sid) if sid else (byname25.get(k) or (None, None))[1]
    if (not s or s['gp'] < 10) and s25 and s25['gp'] >= 10: s, src_season = s25, '2024-25'
    rookie = s is None or s['gp'] == 0
    if rookie:
        pk = next((v for kk, v in TOP.items() if k.startswith(kk)), None)
        f = 30 if pk and pk <= 1 else 27 if pk and pk <= 3 else 22 if pk and pk <= 10 else 12 if new else 7
        mpg = 30 if pk and pk <= 3 else 25 if pk else 16 if new else 10
        p = POS.get(e['pos'] if e else 'F', 'F')
        sh = {'G': (0.52, 0.12, 0.22, 0.06, 0.03), 'F': (0.52, 0.22, 0.11, 0.05, 0.05), 'C': (0.46, 0.30, 0.07, 0.04, 0.09)}[p]
        s = dict(gp=0, mpg=mpg, pts=round(f * sh[0], 1), reb=round(f * sh[1], 1), ast=round(f * sh[2] / 2, 1), stl=round(f * sh[3] / 3, 2), blk=round(f * sh[4] / 3, 2), tov=1, dd=0, td=0); src_season = 'rookie estimate' + (f' (#{pk} pick)' if pk else '')
    gp_rate = (s['gp'] / 82) if src_season == '2025-26' else (s['gp'] / 82 if src_season == '2024-25' else 0.8)
    if s25 and src_season == '2025-26' and s25.get('gp'): gp_rate = 0.65 * gp_rate + 0.35 * (s25['gp'] / 82)
    c = S27.get(sid) if sid else None
    if not c and k in byname27: c = byname27[k][1]
    if c and c['gp'] >= 1:                     # blend THIS season's real averages in as games are played (8-game prior weight)
        w = c['gp'] / (c['gp'] + (8 if not rookie else 2)); s = dict(s)
        for kk in ('mpg', 'pts', 'reb', 'ast', 'stl', 'blk', 'tov'): s[kk] = round(w * c[kk] + (1 - w) * s[kk], 2)
        s['gp'] = c['gp']; src_season = f"2026-27 ({int(c['gp'])} gp) + {src_season}"; rookie = False
    fp = s['pts'] + s['reb'] + 2 * s['ast'] + 3 * s['stl'] + 3 * s['blk']
    out.append(dict(n=name, t=team, p=POS.get(e['pos'] if e else 'F', 'F'), pe=e['pos'] if e else None, id=sid, j=e['jersey'] if e else None, age=e['age'] if e else None, ht=e['ht'] if e else None,
        tl=1 if (e and e.get('tl')) else 0, new=bool(new), inj=(e['inj'] if e else []), src=src_season, gp=int(s['gp']), av=round(max(0.3, min(0.97, gp_rate if not rookie else 0.85)), 2),
        m=s['mpg'], pts=s['pts'], reb=s['reb'], ast=s['ast'], stl=s['stl'], blk=s['blk'], tov=s['tov'], fp=round(fp, 1), dd=int(s.get('dd') or 0), td=int(s.get('td') or 0)))
# schedule
games = {}
for f in glob.glob(str(R/'sched_*.json')):
    for ev in json.load(open(f)).get('events', []):
        c = ev['competitions'][0]; h = a = None
        for tm in c['competitors']:
            x = ab(tm['team']['abbreviation'])
            if tm['homeAway'] == 'home': h = x
            else: a = x
        games[ev['id']] = dict(id=ev['id'], d=ev['date'], h=h, a=a)
g = sorted(games.values(), key=lambda x: (x['d'], x['id']))
json.dump({'players': out, 'games': g, 'report': report}, open(pathlib.Path(__file__).parent / 'nba.json', 'w'), ensure_ascii=False)
print('players', len(out), 'games', len(g))
for k, v in report.items(): print(k, len(v), v[:60])
