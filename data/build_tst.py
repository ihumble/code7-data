"""Test Rugby (2026 Nations Championship) from the OFFICIAL Nations Championship Fantasy game
(fantasy.nationschampionshiprugby.com feeds: players_1_en_<gameday>.json): official prices ($2M–$8.5M, $100M for 16),
positions, season points, tries, assists, metres, and each round's points. ESPN July matchday 23s add starts/bench/age/height/weight.
Refresh: fetch https://fantasy.nationschampionshiprugby.com/fantasy/feeds/players/players_1_en_<N>.json for N = 1.. into data/raw/ncf_players_gd<N>.json. Writes data/tst.json."""
import json, re, glob, unicodedata
from pathlib import Path
D = Path(__file__).parent; R = D / 'raw'; X = json.load(open(D / 'extra.json'))
nrm = lambda s: re.sub(r'[^a-z ]', '', unicodedata.normalize('NFD', s).encode('ascii', 'ignore').decode().lower().replace('-', ' ')).strip()
POS = {'PROP': 'PR', 'HOOKER': 'HK', 'LOCK': 'LK', 'LOOSE FORWARD': 'LF', 'SCRUM-HALF': 'SH', 'FLY-HALF': 'FH', 'CENTRE': 'MID', 'BACK THREE': 'OB'}
gds = sorted(int(re.search(r'gd(\d+)', f).group(1)) for f in glob.glob(str(R / 'ncf_players_gd*.json')))
P = {g: {p['id']: p for p in json.load(open(R / f'ncf_players_gd{g}.json'))['Data']['Value']['Players']} for g in gds}
latest = P[gds[-1]]
rpts = {}                                              # round → {player id: points}; each gameday file carries the last completed round's points
for g in gds:
    for pid, p in P[g].items():
        r = p.get('cur_gameday_id')
        if r: rpts.setdefault(r, {})[pid] = float(p.get('cur_gd_points') or 0)
ESP = {nrm(p['n']): p for p in X['tst']['players']}
out = []
for pid, p in latest.items():
    if not p.get('is_active'): continue
    t = p['team_short_code'].upper(); pos = POS[p['skill_desc']]
    rounds = [rpts[r].get(pid, 0) for r in sorted(rpts)]; gp = sum(1 for x in rounds if x)
    tot = p['ov_points'] or 0; avg = tot / gp if gp else 0
    fp = avg if gp >= 2 else ((tot + 22 * 1.5) / (gp + 1.5) if gp else 18)      # official average; 0–1 game samples pulled toward a bench-level score
    e = ESP.get(nrm(p['full_name']), {})
    out.append([p['full_name'], t, pos, int(round(p['value'] * 1e6)), 0, round(fp, 1), round(min(0.95, 0.35 + 0.2 * gp), 2), e.get('starts', 0), e.get('bench', 0),
                tot, p.get('try_scored') or 0, p.get('try_assist') or 0, p.get('metres_gained') or 0, gp, e.get('age'), e.get('ht'), e.get('wt'), p.get('sel_percentage') or 0])
json.dump({'fields': 'n t p price new fp av st bn tot tr ta mg gp age ht wt sel', 'players': out, 'games': X['tst']['games'],
           'source': 'OFFICIAL Nations Championship Fantasy 2026 (prices, positions, points after round 3) + ESPN matchday squads, results and fixtures'},
          open(D / 'tst.json', 'w'), ensure_ascii=False)
import collections; print(len(out), collections.Counter(x[1] for x in out), collections.Counter(x[2] for x in out), 'price', min(x[3] for x in out), max(x[3] for x in out), 'rounds', sorted(rpts))
print(sorted(out, key=lambda x: -x[5])[:6])
