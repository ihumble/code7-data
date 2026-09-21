"""Download the LATEST raw feeds for every code into data/raw/ (used by the daily refresh).
Each source is independent: a failure keeps the previous cached file and is reported, never fatal."""
import json, subprocess, sys, time, datetime, concurrent.futures as cf
from pathlib import Path
R = Path(__file__).parent / 'raw'; R.mkdir(exist_ok=True)
ok, bad = [], []
def fetch(url, name, check=None):
    print('·', name, flush=True)
    for i in range(3):
        try:
            b = subprocess.run(['curl', '-s', '-f', '--compressed', '--max-time', '40', url], capture_output=True, timeout=60).stdout
            d = json.loads(b)
            if check and not check(d): raise ValueError('unexpected content')
            (R / name).write_bytes(b); ok.append(name); return d
        except Exception as e: err = e; time.sleep(1 + 2 * i)
    bad.append(f'{name}: {err}'); return None
E = 'https://site.api.espn.com/apis/site/v2/sports/'
# ---- NBA: rosters, schedule, stats (last season + this season once it starts)
T = fetch(E + 'basketball/nba/teams', 'teams.json', lambda d: d['sports'][0]['leagues'][0]['teams'])
ids = [t['team']['id'] for t in (T or json.load(open(R / 'teams.json')))['sports'][0]['leagues'][0]['teams']]
with cf.ThreadPoolExecutor(8) as ex:
    for i in ids:
        ex.submit(fetch, E + f'basketball/nba/teams/{i}/roster', f'roster_{i}.json', lambda d: d.get('athletes'))
        ex.submit(fetch, E + f'basketball/nba/teams/{i}/schedule?season=2027&seasontype=2', f'sched_{i}.json', lambda d: 'events' in d)
BY = 'https://site.api.espn.com/apis/common/v3/sports/basketball/nba/statistics/byathlete?contentorigin=espn&isqualified=false&lang=en&region=us&season={}&seasontype=2&sort=offensive.avgPoints%3Adesc&limit=1000'
fetch(BY.format(2026), 'stats_2026.json', lambda d: d.get('athletes'))
fetch(BY.format(2027), 'stats_2027.json', lambda d: isinstance(d, dict))   # empty until opening night
# ---- NFL: Sleeper players + 2025 and 2026-to-date stats, ESPN schedules
fetch('https://api.sleeper.app/v1/players/nfl', 'sleeper_players.json', lambda d: len(d) > 1000)
fetch('https://api.sleeper.app/v1/stats/nfl/regular/2026', 'sleeper_stats26.json', lambda d: isinstance(d, dict))
with cf.ThreadPoolExecutor(8) as ex:
  for i in (R / 'nfl_ids.txt').read_text().split():
    ex.submit(fetch, E + f'football/nfl/teams/{i}/schedule?season=2026', f'nflsched_{i}.json', lambda d: 'events' in d)
# ---- EPL: FPL bootstrap, fixtures, live points for every finished gameweek
B = fetch('https://fantasy.premierleague.com/api/bootstrap-static/', 'fpl.json', lambda d: d.get('elements'))
fetch('https://fantasy.premierleague.com/api/fixtures/', 'fpl_fix.json', lambda d: isinstance(d, list) and d)
for e in (B or json.load(open(R / 'fpl.json')))['events']:
    if e['finished']: fetch(f"https://fantasy.premierleague.com/api/event/{e['id']}/live/", f"fpl_live_{e['id']}.json", lambda d: d.get('elements'))
# ---- NRL + Super Rugby: official fantasy games
fetch('https://fantasy.nrl.com/data/nrl/players.json', 'nrl_players.json', lambda d: isinstance(d, list) and d)
fetch('https://fantasy.nrl.com/data/nrl/squads.json', 'nrl_squads.json', lambda d: isinstance(d, list) and d)
for k in ('players', 'rounds', 'squads'): fetch(f'https://www.playfantasyrugby.com/json/fantasy/{k}.json', f'srp_fantasy_{k}.json', lambda d: isinstance(d, list) and d)
# ---- Test rugby: official Nations Championship fantasy, one file per gameday (stops at the first missing one)
for g in range(1, 12):
    if not fetch(f'https://fantasy.nationschampionshiprugby.com/fantasy/feeds/players/players_1_en_{g}.json', f'ncf_players_gd{g}.json', lambda d: d['Data']['Value']['Players']):
        bad.pop(); break
# ---- time-sensitive ESPN caches the builders re-read (results + tables)
for f in list(R.glob('nc_sb_2026110*.json')) + list(R.glob('nc_sb_202611[12]*.json')) + [R / 'st_nc.json']:
    f.unlink(missing_ok=True)
print(f'{datetime.datetime.utcnow():%Y-%m-%d %H:%M} UTC · fetched {len(ok)} · failed {len(bad)}')
for b in bad: print('  FAILED', b)
json.dump({'ok': len(ok), 'failed': bad, 'at': datetime.datetime.utcnow().isoformat() + 'Z'}, open(R / '_fetch_report.json', 'w'))
