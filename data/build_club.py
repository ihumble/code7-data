"""Club rugby union: Gallagher PREM (ESPN league 267979) and the United Rugby Championship (ESPN 270557).
- Players: every matchday 23 of the 2025-26 season (ESPN summaries): starts, bench, jersey positions, latest club.
- Results + table: 2025-26 (ESPN standings season=2026). Fixtures: the real 2026-27 regular season (ESPN), rounds = weekends.
- Top scorers: data/raw/<lid>_scorers_2025-26.json (Wikipedia season pages).
Writes data/prem.json and data/urc.json."""
import json, re, time, subprocess, unicodedata, collections, datetime
from pathlib import Path
D = Path(__file__).parent; R = D / 'raw'
def get(url, cache, refresh=False):
    if (R / cache).exists() and not refresh: return json.load(open(R / cache))
    for i in range(4):
        try:
            d = json.loads(subprocess.run(['curl', '-s', '--compressed', url], capture_output=True, timeout=60).stdout); json.dump(d, open(R / cache, 'w')); return d
        except Exception: time.sleep(1 + i)
    raise RuntimeError(url)
nrm = lambda s: re.sub(r'[^a-z ]', '', unicodedata.normalize('NFD', s).encode('ascii', 'ignore').decode().lower().replace('-', ' ')).strip()
JPOS = {1: 'PR', 3: 'PR', 2: 'HK', 4: 'LK', 5: 'LK', 6: 'LF', 7: 'LF', 8: 'LF', 9: 'SH', 10: 'FH', 12: 'MID', 13: 'MID', 11: 'OB', 14: 'OB', 15: 'OB'}
BPOS = {16: 'HK', 17: 'PR', 18: 'PR', 19: 'LK', 20: 'LF', 21: 'SH', 22: 'FH', 23: 'OB'}
POSB = {'PR': 44, 'HK': 46, 'LK': 46, 'LF': 50, 'SH': 48, 'FH': 54, 'MID': 48, 'OB': 52}
def build(lid, espn, name):
    ev = []
    for y in (2025, 2026, 2027): ev += get(f'https://site.api.espn.com/apis/site/v2/sports/rugby/{espn}/scoreboard?dates={y}&limit=400', f'{lid}_sb_{y}.json', refresh=(y != 2025)).get('events', [])
    last = [e for e in ev if '2025-08' < e['date'] < '2026-07' and e['status']['type']['name'] == 'STATUS_FINAL']
    nxt = sorted([e for e in ev if e['date'] > '2026-08'], key=lambda e: e['date'])
    cur = [e for e in nxt if e['status']['type']['name'] == 'STATUS_FINAL']      # 2026-27 games already played: newest squads + real results
    teams = {}
    for e in nxt:
        for c in e['competitions'][0]['competitors']: teams[c['team']['abbreviation']] = c['team']['displayName']
    pl = {}; tg = collections.Counter()
    for e in sorted(last + cur, key=lambda e: e['date']):
        s = get(f'https://site.api.espn.com/apis/site/v2/sports/rugby/{espn}/summary?event={e["id"]}', f'{lid}_sum_{e["id"]}.json')
        for side in s.get('rosters', []):
            t = side['team']['abbreviation']; tg[t] += 1
            for r in side['roster']:
                j = int(r.get('jersey') or 0); k = r['athlete']['id']
                p = pl.setdefault(k, {'n': r['athlete']['displayName'], 'st': 0, 'bn': 0, 'jp': collections.Counter(), 'bj': collections.Counter(), 'club': collections.Counter(), 'last': None})
                p['club'][t] += 1; p['last'] = t
                if 1 <= j <= 15: p['st'] += 1; p['jp'][JPOS[j]] += 1
                elif j in BPOS: p['bn'] += 1; p['bj'][BPOS[j]] += 1
    tab = {}
    stn = get(f'https://site.api.espn.com/apis/v2/sports/rugby/{espn}/standings?season=2026', f'{lid}_standings_2026.json')
    def walk(n):
        if 'standings' in n and 'entries' in n['standings']:
            for e in n['standings']['entries']:
                m = {x.get('name'): x.get('value') for x in e['stats']}
                tab[e['team']['abbreviation']] = [int(m.get('gamesWon') or 0), int(m.get('gamesLost') or 0), int(m.get('gamesDrawn') or 0), int(m.get('pointsFor') or 0), int(m.get('pointsAgainst') or 0), int(m.get('gamesPlayed') or 0), int(m.get('rank') or 0), int(m.get('points') or 0)]
        for c in n.get('children', []): walk(c)
    walk(stn)
    scf = R / f'{lid}_scorers_2025-26.json'; SC = json.load(open(scf)) if scf.exists() else {'points': {}, 'tries': {}}
    PTS = {nrm(k): v for k, v in SC['points'].items()}; TRY = {nrm(k): v for k, v in SC['tries'].items()}
    out = []
    for k, p in pl.items():
        t = p['last']
        if t not in teams: continue                                  # club not in the 2026-27 competition
        pos = (p['jp'].most_common(1)[0][0] if p['jp'] else p['bj'].most_common(1)[0][0] if p['bj'] else None)
        if not pos: continue
        w, l, d, pf, pa, gp = (tab.get(t) or [0, 0, 0, 0, 0, 1])[:6]; tf = 1 + max(-25, min(25, (pf - pa) / max(1, gp))) / 150
        apps = p['st'] + p['bn']; sel = (p['st'] + 0.45 * p['bn']) / max(1, tg[t])
        tries = TRY.get(nrm(p['n']), 0); pts = PTS.get(nrm(p['n']), 0)
        fp = POSB[pos] * (0.55 + 0.6 * min(1, sel * 1.15)) * tf + (tries * 4.5 + max(0, pts - tries * 5) * 0.5) / max(1, apps)
        price = int(round(max(230000, min(720000, fp * 9000)) / 1000) * 1000)
        av = round(min(0.95, 0.4 + 0.035 * apps), 2)
        out.append([p['n'], t, pos, price, 0, round(fp, 1), av, p['st'], p['bn'], tries, pts, sum(p['club'].values()), ''])
    # 2026-27 fixtures → rounds (one round per weekend; ESPN lists the full regular season)
    # rounds: one per weekend; games moved to an odd weekend (e.g. rescheduled) join the earliest round that both teams are missing
    wk = lambda iso: datetime.date.fromisoformat(iso[:10]).isocalendar()[:2]
    per = len(teams) // 2; byw = collections.OrderedDict()
    for e in nxt: byw.setdefault(wk(e['date']), []).append(e)
    rounds = []; stray = []
    for w_, es in byw.items(): (rounds.append(list(es)) if len(es) > per // 2 else stray.extend(es))
    teams_in = lambda es: {c['team']['abbreviation'] for e in es for c in e['competitions'][0]['competitors']}
    for e in stray:
        ts = {c['team']['abbreviation'] for c in e['competitions'][0]['competitors']}
        k = next((k for k, es in enumerate(rounds) if not (ts & teams_in(es))), None)
        if k is None: rounds.append([e])
        else: rounds[k].append(e)
    for _ in range(3):                                       # a team twice in one weekend → move that game to the round it's missing from
        for k, es in enumerate(rounds):
            cnt = collections.Counter(c['team']['abbreviation'] for e in es for c in e['competitions'][0]['competitors'])
            for e in [e for e in es if any(cnt[c['team']['abbreviation']] > 1 for c in e['competitions'][0]['competitors'])]:
                ts = {c['team']['abbreviation'] for c in e['competitions'][0]['competitors']}
                tgt = sorted((abs(j - k), j) for j, es2 in enumerate(rounds) if j != k and not (ts & teams_in(es2)))
                if tgt: rounds[tgt[0][1]].append(e); es.remove(e); break
    games = []; rd = []
    for n, es in enumerate(rounds, 1):
        for e in es:
            c = e['competitions'][0]; H = next(x for x in c['competitors'] if x['homeAway'] == 'home'); A = next(x for x in c['competitors'] if x['homeAway'] == 'away')
            fin = e['status']['type']['name'] == 'STATUS_FINAL'
            games.append([e['date'], H['team']['abbreviation'], A['team']['abbreviation'], n, int(H['score']) if fin else None, int(A['score']) if fin else None, e['id']])
        mode = collections.Counter(e['date'][:10] for e in es).most_common(1)[0][0]
        first = min(e['date'] for e in es if e['date'][:10] >= (datetime.date.fromisoformat(mode) - datetime.timedelta(days=3)).isoformat())
        rd.append(max(first, rd[-1] if rd else first))
    order = list(range(1, len(rounds) + 1))
    res25 = [[e['date'], *[x['team']['abbreviation'] for x in sorted(e['competitions'][0]['competitors'], key=lambda x: x['homeAway'] != 'home')], *[int(x.get('score') or 0) for x in sorted(e['competitions'][0]['competitors'], key=lambda x: x['homeAway'] != 'home')]] for e in last]
    print(lid, 'players', len(out), collections.Counter(x[1] for x in out), collections.Counter(x[2] for x in out))
    print(' rounds', len(order), collections.Counter(g[3] for g in games), 'teams', teams, 'missing table', [t for t in teams if t not in tab])
    print(' top', sorted(out, key=lambda x: -x[5])[:5])
    return {'fields': 'n t p price new fp av st bn tr pts apps nw', 'players': out, 'games': games, 'roundDates': rd, 'teams': teams,
               'table': {'season': f'2025-26 {name}', 'rows': {t: r for t, r in tab.items() if t in teams}}, 'results2025': res25,
               'source': f'ESPN {name}: every 2025-26 matchday 23 ({len(last)} games) + {len(cur)} games of 2026-27 so far — starts, bench, positions; 2025-26 table; the real 2026-27 fixture list. Top scorers: Wikipedia.'}
# ---------------- 2026-27 transfers (Wikipedia transfer lists): summer signings move clubs / leagues ----------------
CLUBS = {'prem': {'Bath': 'BAT', 'Bath Rugby': 'BAT', 'Bristol Bears': 'BRI', 'Bristol': 'BRI', 'Exeter Chiefs': 'EXE', 'Exeter': 'EXE', 'Gloucester': 'GLO', 'Gloucester Rugby': 'GLO', 'Harlequins': 'HAR', 'Leicester Tigers': 'LEI', 'Leicester': 'LEI',
                  'Newcastle Red Bulls': 'NEW', 'Newcastle Falcons': 'NEW', 'Newcastle': 'NEW', 'Northampton Saints': 'NOR', 'Northampton': 'NOR', 'Sale Sharks': 'SAL', 'Sale': 'SAL', 'Saracens': 'SAR'},
         'urc': {'Benetton': 'BEN', 'Benetton Rugby': 'BEN', 'Bulls': 'BUL', 'Cardiff': 'CAR', 'Cardiff Rugby': 'CAR', 'Connacht': 'CON', 'Connacht Rugby': 'CON', 'Dragons': 'DRA', 'Dragons RFC': 'DRA', 'Edinburgh': 'EDI', 'Edinburgh Rugby': 'EDI',
                 'Glasgow Warriors': 'GLA', 'Glasgow': 'GLA', 'Leinster': 'LEI', 'Leinster Rugby': 'LEI', 'Lions': 'LIO', 'Munster': 'MUN', 'Munster Rugby': 'MUN', 'Ospreys': 'OSP', 'Scarlets': 'SCA', 'Sharks': 'SHA', 'Stormers': 'STO', 'Ulster': 'ULS', 'Ulster Rugby': 'ULS', 'Zebre': 'ZEB', 'Zebre Parma': 'ZEB'}}
def parse_transfers(lid):
    f = R / f'{lid}_transfers_2026-27.wiki'
    if not f.exists(): return []
    out = []; club = None; direction = None
    for ln in f.read_text().split('\n'):
        m = re.match(r'^==\s*([^=].*?)\s*==\s*$', ln)
        if m: club = CLUBS[lid].get(m.group(1).strip()); continue
        m = re.match(r'^===\s*Players (in|out)\s*===', ln)
        if m: direction = m.group(1); continue
        if club and direction and ln.startswith('*'):
            links = re.findall(r'\[\[([^\]|]+)(?:\|([^\]]+))?\]\]', re.sub(r'<ref.*?(</ref>|/>)', '', ln))
            if not links: continue
            nm = links[0][1] or re.sub(r'\s*\(.*\)$', '', links[0][0])
            other = (links[1][1] or links[1][0]) if len(links) > 1 else ''
            out.append({'club': club, 'dir': direction, 'n': nm.strip(), 'other': other.strip(), 'retired': 'etire' in ln})
    return out
def estimate_row(n, t, pos, src):          # a signing with no club-rugby record in our data: rate from his Super Rugby / Test fantasy average
    fp = max(34, min(64, 30 + 0.55 * src)); return [n, t, pos, int(round(max(230000, min(720000, fp * 9000)) / 1000) * 1000), 1, round(fp, 1), 0.8, 0, 0, 0, 0, 0, 'new']
L = {'prem': build('prem', 267979, 'Gallagher PREM'), 'urc': build('urc', 270557, 'United Rugby Championship')}
OTHER = {}
for fn, lid in (('sr.json', 'srp'), ('tst.json', 'tst')):
    try:
        d = json.load(open(D / fn)); f = d['fields'].split(); ni, pi, fi = f.index('n'), f.index('p'), f.index('fp')
        for r in d['players']: OTHER.setdefault(nrm(r[ni]), (r[pi], r[fi]))
    except Exception: pass
moved = added = removed = 0; unknown = []
T = {lid: parse_transfers(lid) for lid in L}
def find(n):
    for lid, d in L.items():
        for r in d['players']:
            if nrm(r[0]) == nrm(n): return lid, r
    w = nrm(n).split(); cands = []                      # "Dan du Preez" vs ESPN "Daniel du Preez": same surname + first initial
    for lid, d in L.items():
        for r in d['players']:
            v = nrm(r[0]).split()
            if len(v) >= 2 and len(w) >= 2 and v[-1] == w[-1] and v[0][0] == w[0][0] and (len(w) < 3 or v[-2] == w[-2]): cands.append((lid, r))
    return cands[0] if len(cands) == 1 else (None, None)
for lid, tr in T.items():
    for x in tr:
        if x['dir'] != 'in': continue
        src_l, row = find(x['n'])
        if row is not None: x['ok'] = 1
        if row is not None:
            if src_l != lid or row[1] != x['club']:
                L[src_l]['players'].remove(row); row = list(row); row[1] = x['club']; row[4] = 1; row[12] = 'new'; L[lid]['players'].append(row); moved += 1
            continue
        o = OTHER.get(nrm(x['n']))
        if o: L[lid]['players'].append(estimate_row(x['n'], x['club'], o[0], o[1])); added += 1; x['ok'] = 1
        else: unknown.append(f"{x['n']} ({x['club']})")
for lid, tr in T.items():
    ins = {nrm(x['n']) for t2 in T.values() for x in t2 if x['dir'] == 'in' and x.get('ok')}
    for x in tr:
        if x['dir'] != 'out' or nrm(x['n']) in ins: continue      # moved within PREM/URC: handled by the "in" entry
        l2, r = find(x['n'])
        if r is not None and l2 == lid and r[1] == x['club']: L[lid]['players'].remove(r); removed += 1
print(f'transfers: moved {moved}, added {added} (rated from Super Rugby/Test data), removed {removed} leavers; {len(unknown)} signings not rated yet (academy/overseas):', unknown[:12])
for lid, d in L.items():
    d['source'] += f'; 2026-27 transfers applied (Wikipedia transfer lists)'
    json.dump(d, open(D / f'{lid}.json', 'w'), ensure_ascii=False)
    print(lid, len(d['players']))
