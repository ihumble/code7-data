"""Super Rugby Pacific from the OFFICIAL Super Rugby Pacific Fantasy game (playfantasyrugby.com, 2026 season, end of regular season):
real fantasy prices, positions, total/avg points and every round score. Moana Pasifika excluded (not in the 2027 competition).
Refresh: curl https://www.playfantasyrugby.com/json/fantasy/{players,rounds,squads}.json into data/raw/srp_fantasy_*.json. Writes data/sr.json."""
import json, statistics
from pathlib import Path
D = Path(__file__).parent; R = D / 'raw'
P = json.load(open(R / 'srp_fantasy_players.json')); SQ = {s['id']: s['abbreviation'] for s in json.load(open(R / 'srp_fantasy_squads.json'))}
RD = json.load(open(R / 'srp_fantasy_rounds.json'))
T = {'HIGH': 'HIG', 'CRUS': 'CRU', 'WARA': 'WAR', 'REDS': 'RED', 'FDRU': 'DRU', 'BLUE': 'BLU', 'CHIE': 'CHI', 'FORC': 'FOR', 'BRUM': 'BRU', 'HURR': 'HUR'}
POS = {'prop': 'PR', 'hooker': 'HK', 'lock': 'LK', 'loose_forward': 'LF', 'scrum_half': 'SH', 'fly_half': 'FH', 'center': 'MID', 'outside_back': 'OB'}
tg = {}   # games each team actually played in the 16 regular-season rounds
for r in RD:
    for g in r['tournaments']:
        if g['status'] == 'completed':
            for a in (g['homeSquadAbbr'], g['awaySquadAbbr']): tg[a] = tg.get(a, 0) + 1
med = {}
for p in P:
    s = p['stats']; 
    if s['scores'] and len(s['scores']) >= 5: med.setdefault(POS[p['position']], []).append(s['avgPoints'])
med = {k: statistics.median(v) for k, v in med.items()}
out = []; games = []
for p in P:
    ab = SQ[p['squadId']]
    if ab not in T: continue
    s = p['stats']; sc = s['scores'] or {}; gp = len(sc); pos = POS[p['position']]
    prior = med[pos] * 0.6; k = 1.5
    fp = (sum(sc.values()) / gp if gp >= 5 else (sum(sc.values()) + prior * k) / (gp + k)) if gp else prior * 0.8     # official average; only <5-game samples shrunk toward a bench-level score
    av = round(max(0.35, min(0.95, gp / max(1, tg.get(ab, 14)) + 0.1)), 2) if gp else 0.35
    out.append([(p['firstName'] + ' ' + p['lastName']).strip(), T[ab], pos, p['cost'], 0, round(fp, 1), av, gp, s['totalPoints'] or 0, max(sc.values()) if sc else 0, round(s['avgPoints'] or 0, 1)])
for r in RD:
    for g in r['tournaments']:
        games.append([g['date'], T.get(g['homeSquadAbbr'], g['homeSquadAbbr']), T.get(g['awaySquadAbbr'], g['awaySquadAbbr']), r['number'], g.get('homeScore'), g.get('awayScore')])
json.dump({'fields': 'n t p price new fp av gp tot high avg', 'players': out, 'results2026': games,
           'source': 'Official Super Rugby Pacific Fantasy 2026 (playfantasyrugby.com): prices, positions and every round score, end of 2026 regular season'}, open(D / 'sr.json', 'w'), ensure_ascii=False)
import collections; print(len(out), collections.Counter(x[1] for x in out), collections.Counter(x[2] for x in out), 'price', min(x[3] for x in out), max(x[3] for x in out))
print(sorted(out, key=lambda x: -x[5])[:6])
