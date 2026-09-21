"""News + injuries for every code → data/news.json (merged into the app's data by merge.py).
- Headlines: ESPN news (NBA, NFL, NRL, EPL). Rugby union has no ESPN feed, so its "news" is built from facts we already
  hold: 2026-27 transfers (Premiership/URC) and official Nations Championship fantasy status (injured / suspended / not in squad).
- Availability: ESPN injury reports (NBA with return dates, NFL), official FPL news + chance of playing (EPL), official
  Nations Championship fantasy status (Tests). NRL / Super Rugby statuses are end-of-2026-season and ignored until 2027.
Only availability changes the game; headlines are shown with a link to the full story."""
import json, re, subprocess, time, datetime, unicodedata
from pathlib import Path
D = Path(__file__).parent; R = D / 'raw'
NOW = datetime.datetime.utcnow().replace(microsecond=0)
iso = lambda d: d.strftime('%Y-%m-%dT%H:%MZ')
def get(url):
    for i in range(3):
        try:
            b = subprocess.run(['curl', '-s', '-f', '--compressed', '--max-time', '40', url], capture_output=True, timeout=60).stdout
            return json.loads(b)
        except Exception: time.sleep(1 + i)
    return None
nrm = lambda s: re.sub(r'[^a-z ]', '', unicodedata.normalize('NFD', s or '').encode('ascii', 'ignore').decode().lower().replace('-', ' ')).strip()
TEAMS = {x['id']: x['teams'] for x in json.load(open(D / 'teams.json'))}
def team_code(lid, text):
    t = nrm(text)
    for k, v in TEAMS[lid].items():
        if nrm(v) and (nrm(v) == t or nrm(v) in t.split() or (len(nrm(v)) > 4 and nrm(v) in t)): return k
    return None
out = {'at': iso(NOW)}
def espn_news(lid, path):
    d = get(f'https://site.api.espn.com/apis/site/v2/sports/{path}/news?limit=40') or {}
    items = []
    for a in d.get('articles', []):
        if a.get('type') not in ('Story', 'HeadlineNews', 'Recap', 'Preview', None) and not a.get('headline'): continue
        cats = a.get('categories') or []
        items.append({'h': a.get('headline', '')[:140], 'd': (a.get('description') or '')[:220], 'at': (a.get('published') or '')[:16] + 'Z',
                      'u': ((a.get('links') or {}).get('web') or {}).get('href', ''), 'src': 'ESPN',
                      'p': [c['description'] for c in cats if c.get('type') == 'athlete' and c.get('description')][:6],
                      'tm': [x for x in {team_code(lid, c.get('description', '')) for c in cats if c.get('type') == 'team'} if x][:6]})
    return items[:30]
def espn_inj(lid, path, rule):
    d = get(f'https://site.api.espn.com/apis/site/v2/sports/{path}/injuries') or {}
    inj = {}
    for t in d.get('injuries', []):
        for x in t.get('injuries', []):
            r = rule(x)
            if not r: continue
            a = x.get('athlete') or {}; det = x.get('details') or {}
            note = (x.get('shortComment') or '')[:200]; kind = ' '.join(filter(None, [det.get('side'), det.get('type'), det.get('detail')]))
            inj[a.get('displayName', '')] = dict(r, note=note, what=kind, tm=(a.get('team') or {}).get('abbreviation'), rep=(x.get('date') or '')[:10])
    return inj
def nba_rule(x):
    ret = (x.get('details') or {}).get('returnDate'); s = x.get('status')
    if ret and ret > NOW.strftime('%Y-%m-%d'): return {'s': 'Out until ' + ret, 'c': 0, 'until': ret + 'T00:00Z'}
    if s == 'Out': return {'s': 'Out', 'c': 0}
    if s == 'Day-To-Day': return {'s': 'Day-to-day', 'c': 0.6}
def nfl_rule(x):
    s = x.get('status')
    return {'Out': {'s': 'Out', 'c': 0}, 'Injured Reserve': {'s': 'Injured reserve', 'c': 0, 'days': 28}, 'Doubtful': {'s': 'Doubtful', 'c': 0.25}, 'Questionable': {'s': 'Questionable', 'c': 0.65}, 'Suspended': {'s': 'Suspended', 'c': 0}}.get(s)
out['nba'] = {'items': espn_news('nba', 'basketball/nba'), 'inj': espn_inj('nba', 'basketball/nba', nba_rule)}
out['nfl'] = {'items': espn_news('nfl', 'football/nfl'), 'inj': espn_inj('nfl', 'football/nfl', nfl_rule)}
out['nrl'] = {'items': espn_news('nrl', 'rugby-league/3'), 'inj': {}}
# EPL: ESPN headlines + official FPL availability
fpl = json.load(open(R / 'fpl.json')); tm = {t['id']: t['short_name'] for t in fpl['teams']}; einj = {}
for e in fpl['elements']:
    if not e.get('news') or e['status'] == 'u': continue
    c = e.get('chance_of_playing_next_round'); c = 1 if c is None else c / 100
    if c >= 1 and e['status'] == 'a': continue
    einj[e['web_name']] = {'s': e['news'][:80], 'c': round(c, 2), 'note': e['news'], 'tm': tm[e['team']], 'fid': e['id'], 'rep': (e.get('news_added') or '')[:10], 'days': 8}
out['epl'] = {'items': espn_news('epl', 'soccer/eng.1'), 'inj': einj}
# Tests: official Nations Championship fantasy status
tinj = {}; titems = []
try:
    import glob
    last = sorted(glob.glob(str(R / 'ncf_players_gd*.json')), key=lambda f: int(re.search(r'gd(\d+)', f).group(1)))[-1]
    for p in json.load(open(last))['Data']['Value']['Players']:
        s = p.get('player_status') or ''
        m = {'I': ('Injured', 0.1), 'S': ('Suspended', 0), 'NIS': ('Not in the squad', 0.3)}.get(s)
        if m: tinj[p['full_name']] = {'s': m[0], 'c': m[1], 'tm': p['team_short_code'].upper(), 'note': f"Official Nations Championship Fantasy status: {m[0].lower()}", 'days': 21}
    for n, x in list(tinj.items())[:25]: titems.append({'h': f"{n} ({x['tm']}) — {x['s'].lower()}", 'd': 'Official Nations Championship Fantasy player status.', 'at': out['at'], 'u': 'https://fantasy.nationschampionshiprugby.com/', 'src': 'Nations Championship Fantasy', 'p': [n], 'tm': [x['tm']]})
except Exception as e: print('tests status skipped', e)
out['tst'] = {'items': titems, 'inj': tinj}
# Premiership / URC: the summer's real transfers as the news feed
def transfer_news(lid):
    items = []
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location('bc', D / 'build_club.py'); src = (D / 'build_club.py').read_text()
        ns = {'re': re, 'R': R, 'json': json}; exec(src[src.index('CLUBS = '):src.index('def estimate_row')], ns)
        for x in ns['parse_transfers'](lid):
            if x['dir'] != 'in': continue
            name = TEAMS[lid].get(x['club'], x['club'])
            items.append({'h': f"{x['n']} joins {name}" + (f" from {x['other']}" if x['other'] and 'Academy' not in x['other'] else ''), 'd': 'Confirmed 2026-27 signing (Wikipedia transfer list).', 'at': out['at'], 'u': '', 'src': 'Transfers', 'p': [x['n']], 'tm': [x['club']]})
    except Exception as e: print(lid, 'transfer news skipped', e)
    return items[:40]
out['prem'] = {'items': transfer_news('prem'), 'inj': {}}
out['urc'] = {'items': transfer_news('urc'), 'inj': {}}
out['srp'] = {'items': [], 'inj': {}}
json.dump(out, open(D / 'news.json', 'w'), ensure_ascii=False)
print({k: (len(v['items']), len(v['inj'])) for k, v in out.items() if k != 'at'})
