"""
schutz-github.py - macht aus den Schutzregeln (.claude/gemeinsam/data/schutz.txt) die Rulesets auf GitHub.
GitHub weist damit verbotene Pushes schon ab (Werkzeug- und Abteilungsschutz), auf allen Branches. Was erlaubt ist,
wie man einrichtet und wo die Grenzen liegen: .claude/gemeinsam/regeln/einrichtung.md, "Werkzeugschutz und
Abteilungsschutz". Die Regeln liest Regeln aus pruefen.py, immer in der Fassung von HEAD.
  python .claude/gemeinsam/scripts/schutz-github.py --zeigen
      Die Rulesets, wie sie sein sollen, als JSON (Ausnahmen mit Teamnamen statt Nummern). Ändert nichts.
  python .claude/gemeinsam/scripts/schutz-github.py --pruefen
      Vergleicht mit GitHub. Rückgabe 1 bei Abweichung, fehlendem oder überzähligem Ruleset und wenn GitHub nicht
      lesen lässt. Wer vorbei darf (bypass_actors), zeigt GitHub nur Admins: sonst wird das nicht verglichen.
      Läuft auch im Workflow "Bauen und zustellen" (Zugang: SCHUTZ_TOKEN), am Rechner mit der Git-Anmeldung.
  python .claude/gemeinsam/scripts/schutz-github.py --anwenden
      Legt die Rulesets an, ersetzt geänderte und löscht "Schutz: …", die es laut schutz.txt nicht mehr gibt.
      Andere Rulesets bleiben unberührt. Nur Werkzeug-Verantwortliche mit Admin-Recht am Repo, schutz.txt muss
      committet sein.
  --repo <owner/name>   anderes Repo (Probe), sonst das Repo aus origin.
Rulesets:
  "Schutz: Werkzeug"  Push-Ruleset: Werkzeug-Muster gesperrt, Frei-Muster ausgenommen; vorbei: werkzeug-verantwortliche.
  "Schutz: <team>"    Push-Ruleset je Team: seine Klassen und Fächer gesperrt; ausgenommen Frei-Muster und in den
                      eigenen Klassen die Fächer anderer Teams (Fachbereich vor Abteilung); vorbei: das Team und
                      werkzeug-verantwortliche.
  "Schutz: main"      Branch-Ruleset: kein Force-Push, kein Löschen, ohne Ausnahme.
  Owner der Organisation kommen an den Push-Rulesets vorbei. #Handbuch.html sperrt kein Ruleset (die automatischen
  Teile dürfen alle ändern, das von Hand Geschriebene prüft pruefen.py nach dem Push).
Tests (handbuch.test.py): BYCS_RULESETS_TEST = JSON-Datei {"rulesets": [...], "teams": {Team: Nummer}} statt GitHub.
Nur Python-Standardbibliothek (Windows, Mac, GitHub). Der Zugang wird nie ausgegeben oder gespeichert.
"""
import argparse
import importlib.util
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
PRAEFIX = 'Schutz: '
WERKZEUG, MAIN = PRAEFIX + 'Werkzeug', PRAEFIX + 'main'
HANDBUCH = '#Handbuch.html'   # nie sperren: automatische Teile für alle, der Bot committet es
ADMIN = 'OrganizationAdmin'
MAX_EINTRAEGE, MAX_ZEICHEN = 200, 200   # Grenzen von GitHub je Ruleset
DOKU = '.claude/gemeinsam/regeln/einrichtung.md, "Werkzeugschutz und Abteilungsschutz"'


class Fehler(Exception):
    pass


def _modul(name, pfad):   # Modul aus einer Datei laden (Muster wie in build-scorm.py)
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location(name, pfad)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


p = _modul('pruefen', os.path.join(HERE, 'pruefen.py'))


# ---------------------------------------------------------------- schutz.txt -> Rulesets (ohne Netz)

def muster(m):
    """Muster aus schutz.txt -> Muster für GitHub (fnmatch von GitHub: * bleibt im Ordner, **/ geht über Ordner,
    "X/**/*" trifft alles unter X, auch tief und auch Dateien mit Punkt am Anfang: geprüft 15.11.2026).
    "X/" -> "X/**/*"; ein * als ganzer Ordnername -> "**"; alles andere muss ein fester Pfad sein. Fehler, wenn sich
    ein Muster nicht sicher umsetzen lässt."""
    if re.search(r'[?\[\]{}\\]', m) or m.startswith('/') or '//' in m or not m.strip('/'):
        raise Fehler('Muster "%s" in schutz.txt lässt sich nicht in ein Ruleset umsetzen (erlaubt: fester Pfad, '
                     'Ordner mit / am Ende, * als ganzer Ordnername).' % m)
    teile = (m[:-1].split('/') + ['*']) if m.endswith('/') else m.split('/')
    neu = []
    for i, t in enumerate(teile):
        letzter = i == len(teile) - 1
        if t == '*':
            neu += ['**', '*'] if letzter else ['**']
        elif '*' in t:
            raise Fehler('Muster "%s" in schutz.txt: * geht in einem Ruleset nur als ganzer Ordnername.' % m)
        else:
            neu.append(t)
    g = '/'.join(neu)
    if len(g) > MAX_ZEICHEN:
        raise Fehler('Muster "%s" ist für ein Ruleset zu lang (höchstens %d Zeichen).' % (m, MAX_ZEICHEN))
    return g


def soll_rulesets(regeln):
    """Die Rulesets, wie sie sein sollen. Jedes als dict name, target, gesperrt, ausnahmen, regeln (Typen), vorbei
    (Teamnamen und ADMIN). Reihenfolge: Werkzeug, Teams nach Namen, main. GitHub vergleicht Pfade ohne Rücksicht auf
    Groß- und Kleinschreibung (geprüft 15.11.2026), wie Regeln: Es genügt die Schreibweise aus schutz.txt."""
    klassen = {k: regeln.schreibweise[('klasse', k)] for k in regeln.klassen}
    faecher = {f: regeln.schreibweise[('fach', f)] for f in regeln.faecher}
    frei = sorted({muster(m) for m in regeln.frei})
    liste = [{'name': WERKZEUG, 'target': 'push', 'regeln': ['file_path_restriction'],
              'gesperrt': sorted({muster(m) for m in regeln.werkzeug if m != HANDBUCH}), 'ausnahmen': frei,
              'vorbei': sorted({p.TEAM_WERKZEUG, ADMIN})}]
    for team in sorted(set(regeln.klassen.values()) | set(regeln.faecher.values())):
        if PRAEFIX + team in (WERKZEUG, MAIN):
            raise Fehler('Ein Team darf nicht "%s" heißen (Name des Rulesets ist vergeben).' % team)
        eigene = [k for k in sorted(klassen) if regeln.klassen[k] == team]
        gesperrt = ['Unterricht/%s/**/*' % klassen[k] for k in eigene]
        gesperrt += ['Unterricht/*/%s/**/*' % faecher[f] for f in sorted(faecher) if regeln.faecher[f] == team]
        fremd = ['Unterricht/%s/%s/**/*' % (klassen[k], faecher[f]) for k in eigene
                 for f in sorted(faecher) if regeln.faecher[f] != team]
        liste.append({'name': PRAEFIX + team, 'target': 'push', 'regeln': ['file_path_restriction'],
                      'gesperrt': sorted(set(gesperrt)), 'ausnahmen': sorted(set(frei + fremd)),
                      'vorbei': sorted({team, p.TEAM_WERKZEUG, ADMIN})})
    liste.append({'name': MAIN, 'target': 'branch', 'regeln': ['deletion', 'non_fast_forward'],
                  'gesperrt': [], 'ausnahmen': [], 'vorbei': []})
    for r in liste:
        for art in ('gesperrt', 'ausnahmen'):
            if len(r[art]) > MAX_EINTRAEGE:
                raise Fehler('Ruleset "%s": %d Einträge bei %s, GitHub erlaubt %d.' % (r['name'], len(r[art]), art, MAX_EINTRAEGE))
            lang = [m for m in r[art] if len(m) > MAX_ZEICHEN]
            if lang:
                raise Fehler('Ruleset "%s": Muster zu lang (höchstens %d Zeichen): %s' % (r['name'], MAX_ZEICHEN, lang[0]))
    return liste


def fuer_github(r, team_nr):
    """Ein Soll-Ruleset als Anfrage für die GitHub-API. team_nr: {Teamname: Nummer}."""
    daten = {'name': r['name'], 'target': r['target'], 'enforcement': 'active',
             'bypass_actors': [{'actor_id': 1, 'actor_type': ADMIN, 'bypass_mode': 'always'} if wer == ADMIN else
                               {'actor_id': team_nr[wer], 'actor_type': 'Team', 'bypass_mode': 'always'}
                               for wer in r['vorbei']]}
    if r['target'] == 'push':
        daten['rules'] = [{'type': 'file_path_restriction', 'parameters': {
            'restricted_file_paths': r['gesperrt'], 'ignored_file_paths': r['ausnahmen']}}]
    else:
        daten['conditions'] = {'ref_name': {'include': ['~DEFAULT_BRANCH'], 'exclude': []}}
        daten['rules'] = [{'type': t} for t in r['regeln']]
    return daten


def von_github(ist, team_name):
    """Ein Ruleset von GitHub in der Form von soll_rulesets, zum Vergleichen. vorbei ist None, wenn GitHub das Feld
    nicht liefert (nur Admins bekommen es). team_name: {Nummer: Teamname}."""
    gesperrt, ausnahmen, typen = [], [], []
    for regel in ist.get('rules') or []:
        typen.append(regel.get('type'))
        if regel.get('type') == 'file_path_restriction':
            par = regel.get('parameters') or {}
            gesperrt += par.get('restricted_file_paths') or []
            ausnahmen += par.get('ignored_file_paths') or []
    vorbei = None
    if isinstance(ist.get('bypass_actors'), list):
        vorbei = sorted(ADMIN if a.get('actor_type') == ADMIN else
                        team_name.get(a.get('actor_id'), '%s %s' % (a.get('actor_type'), a.get('actor_id')))
                        if a.get('bypass_mode', 'always') == 'always' else
                        '%s %s (%s)' % (a.get('actor_type'), a.get('actor_id'), a.get('bypass_mode'))
                        for a in ist['bypass_actors'])
    zweige = ((ist.get('conditions') or {}).get('ref_name') or {})
    return {'name': ist.get('name'), 'target': ist.get('target'), 'regeln': sorted(typen), 'gesperrt': sorted(gesperrt),
            'ausnahmen': sorted(ausnahmen), 'vorbei': vorbei, 'aktiv': ist.get('enforcement') == 'active',
            'zweige': (sorted(zweige.get('include') or []), sorted(zweige.get('exclude') or []))}


def vergleich(soll, ist_liste, team_name):
    """(Abweichungen, Namen der Rulesets ohne geprüfte Ausnahmen). ist_liste: Rulesets von GitHub (vollständig)."""
    ist = {r.get('name'): von_github(r, team_name) for r in ist_liste if str(r.get('name', '')).startswith(PRAEFIX)}
    ab, ungeprueft = [], []
    for s in soll:
        i = ist.pop(s['name'], None)
        if i is None:
            ab.append('"%s" fehlt auf GitHub.' % s['name'])
            continue
        if not i['aktiv']:
            ab.append('"%s" ist nicht aktiv.' % s['name'])
        if i['target'] != s['target'] or i['regeln'] != sorted(s['regeln']):
            ab.append('"%s": andere Regeln (%s, %s).' % (s['name'], i['target'], ', '.join(map(str, i['regeln']))))
        for art, text in (('gesperrt', 'gesperrte Pfade'), ('ausnahmen', 'Ausnahmen bei den Pfaden')):
            fehlt, zuviel = sorted(set(s[art]) - set(i[art])), sorted(set(i[art]) - set(s[art]))
            if fehlt or zuviel:
                ab.append('"%s", %s:%s%s' % (s['name'], text, ' fehlt ' + ', '.join(fehlt) if fehlt else '',
                                            ' zu viel ' + ', '.join(zuviel) if zuviel else ''))
        if s['target'] == 'branch' and i['zweige'] != (['~DEFAULT_BRANCH'], []):
            ab.append('"%s" gilt nicht (nur) für den Hauptzweig.' % s['name'])
        if i['vorbei'] is None:
            ungeprueft.append(s['name'])
        elif i['vorbei'] != sorted(s['vorbei']):
            ab.append('"%s": vorbei dürfen %s, es sollen sein: %s.' % (
                s['name'], ', '.join(i['vorbei']) or 'niemand', ', '.join(sorted(s['vorbei'])) or 'niemand'))
    ab += ['"%s" gibt es auf GitHub, laut schutz.txt aber nicht mehr.' % name for name in sorted(ist)]
    return ab, ungeprueft


# ---------------------------------------------------------------- GitHub

def api(methode, pfad, zugang, daten=None):
    """Anfrage an die GitHub-API: (Status, Antwort). Status 0 = keine Verbindung. Der Zugang wird nie ausgegeben."""
    anfrage = urllib.request.Request(
        'https://api.github.com' + pfad, method=methode,
        data=json.dumps(daten).encode('utf-8') if daten is not None else None,
        headers={'Authorization': 'Bearer ' + zugang, 'Accept': 'application/vnd.github+json',
                 'X-GitHub-Api-Version': '2022-11-28', 'User-Agent': 'schutz-github.py'})
    try:
        with urllib.request.urlopen(anfrage, timeout=30) as r:
            text = r.read().decode('utf-8')
            return r.status, json.loads(text) if text.strip() else None
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode('utf-8'))
        except (OSError, ValueError):
            return e.code, None
    except (OSError, ValueError):
        return 0, None


def meldung(status, antwort):
    """Fehlertext von GitHub, kurz."""
    if status == 0:
        return 'keine Verbindung zu GitHub'
    text = str(antwort.get('message', '')) if isinstance(antwort, dict) else ''
    mehr = antwort.get('errors') if isinstance(antwort, dict) else None
    return ('Status %d %s %s' % (status, text, json.dumps(mehr, ensure_ascii=False) if mehr else '')).strip()


def repo_name(angabe=None):
    """owner/name: aus --repo, auf GitHub aus der Umgebung, sonst aus der Adresse von origin."""
    name = angabe or os.environ.get('GITHUB_REPOSITORY', '').strip()
    if not name:
        m = re.search(r'github\.com[:/]+([^/\s]+/[^/\s]+?)(?:\.git)?/?\s*$', p.git('remote', 'get-url', 'origin')[1])
        name = m.group(1) if m else ''
    if not re.fullmatch(r'[\w.-]+/[\w.-]+', name):
        raise Fehler('Das Repo auf GitHub ist nicht zu erkennen (--repo <owner/name> angeben).')
    return name


def zugang():
    """Im Workflow SCHUTZ_TOKEN, am Rechner die gespeicherte Git-Anmeldung. '' wenn nichts da ist."""
    return os.environ.get('SCHUTZ_TOKEN', '').strip() if p.AUF_GITHUB else p._anmeldung()


def _test():
    """Nur für handbuch.test.py: Inhalt der Datei BYCS_RULESETS_TEST statt GitHub. None ohne Test, False wenn die
    Datei fehlt (wie "GitHub lässt nicht lesen")."""
    pfad = os.environ.get('BYCS_RULESETS_TEST')
    if not pfad:
        return None
    try:
        with open(pfad, encoding='utf-8') as f:
            return json.load(f)
    except (OSError, ValueError):
        return False


def rulesets_lesen(repo, token):
    """Alle Rulesets "Schutz: …" des Repos, vollständig (die Liste von GitHub nennt nur Namen, darum einzeln).
    Fehler, wenn GitHub nicht lesen lässt."""
    test = _test()
    if test is not None:
        if test is False:
            raise Fehler('GitHub ließ die Rulesets nicht lesen (Test).')
        return test.get('rulesets', [])
    if not token:
        raise Fehler('Kein Zugang zu GitHub (im Workflow SCHUTZ_TOKEN, am Rechner die gespeicherte Git-Anmeldung).')
    alle, seite = [], 1
    while True:
        status, daten = api('GET', '/repos/%s/rulesets?includes_parents=false&per_page=100&page=%d' % (repo, seite), token)
        if status != 200 or not isinstance(daten, list):
            raise Fehler('GitHub ließ die Rulesets von %s nicht lesen (%s).' % (repo, meldung(status, daten)))
        alle += daten
        if len(daten) < 100:
            break
        seite += 1
    voll = []
    for r in alle:
        if not str(r.get('name', '')).startswith(PRAEFIX):
            continue
        status, daten = api('GET', '/repos/%s/rulesets/%s' % (repo, r.get('id')), token)
        if status != 200 or not isinstance(daten, dict):
            raise Fehler('GitHub ließ das Ruleset "%s" nicht lesen (%s).' % (r.get('name'), meldung(status, daten)))
        voll.append(daten)
    return voll


def team_nummern(repo, token, teams):
    """{Teamname: Nummer} für die Ausnahmen. Fehler, wenn ein Team fehlt oder nicht lesbar ist."""
    test = _test()
    if test:
        nr = {str(k).lower(): v for k, v in (test.get('teams') or {}).items()}
    else:
        org, nr = repo.split('/')[0], {}
        for team in sorted(teams):
            status, daten = api('GET', '/orgs/%s/teams/%s' % (org, urllib.parse.quote(team)), token)
            if status == 200 and isinstance(daten, dict) and daten.get('id'):
                nr[team] = daten['id']
    fehlt = sorted(set(teams) - set(nr))
    if fehlt:
        raise Fehler('Team nicht gefunden oder nicht lesbar: %s. Gibt es das Team in der Organisation, ist es '
                     'sichtbar (nicht geheim), stimmt der Name in schutz.txt? (%s)' % (', '.join(fehlt), DOKU))
    return nr


# ---------------------------------------------------------------- Aufrufe

def soll_aus_head():
    return soll_rulesets(p.schutzregeln('HEAD'))


def zeigen():
    print(json.dumps(soll_aus_head(), ensure_ascii=False, indent=2))
    return 0


def pruefen(repo):
    soll, token = soll_aus_head(), ('' if _test() is not None else zugang())   # im Test nie die echte Anmeldung holen
    ist = rulesets_lesen(repo, token)
    teams = {t for r in soll for t in r['vorbei'] if t != ADMIN}
    nr = team_nummern(repo, token, teams) if any(isinstance(r.get('bypass_actors'), list) for r in ist) else {}
    ab, ungeprueft = vergleich(soll, ist, {v: k for k, v in nr.items()})
    if ab:
        print('FEHLER: Die Rulesets auf GitHub passen nicht zu schutz.txt, deshalb wird nichts zugestellt:')
        for a in ab:
            print('  - ' + a)
        print('Werkzeug-Verantwortliche mit Admin-Recht am Repo: python .claude/gemeinsam/scripts/schutz-github.py '
              '--anwenden (%s).' % DOKU)
        return 1
    print('Rulesets auf GitHub passen zu schutz.txt (%d Rulesets "Schutz: …").' % len(soll))
    if ungeprueft:
        print('Wer vorbei darf, ist hier nicht geprüft (das zeigt GitHub nur Admins): --pruefen am Rechner eines Admins.')
    return 0


def anwenden(repo):
    if p.AUF_GITHUB:
        raise Fehler('--anwenden läuft nur am Rechner, nie im Workflow.')
    if not p.rechte()[0]:
        raise Fehler('Rulesets ändern nur Werkzeug-Verantwortliche (python .claude/gemeinsam/scripts/pruefen.py --rechte).')
    if p.git('status', '--porcelain', '--', p.SCHUTZ)[1].strip():
        raise Fehler('schutz.txt ist geändert, aber nicht committet. Angewendet wird die Fassung im letzten Commit: '
                     'erst committen.')
    soll, token = soll_aus_head(), zugang()
    if not token:
        raise Fehler('Keine gespeicherte Git-Anmeldung für github.com gefunden.')
    status, daten = api('GET', '/repos/%s' % repo, token)
    if status != 200 or not isinstance(daten, dict):
        raise Fehler('GitHub ließ das Repo %s nicht lesen (%s).' % (repo, meldung(status, daten)))
    if not (daten.get('permissions') or {}).get('admin'):
        raise Fehler('Rulesets ändern kann nur, wer Admin am Repo %s ist. Bitte den Admin, --anwenden auszuführen '
                     '(%s).' % (repo, DOKU))
    nr = team_nummern(repo, token, {t for r in soll for t in r['vorbei'] if t != ADMIN})
    name = {v: k for k, v in nr.items()}
    ist = {r.get('name'): r for r in rulesets_lesen(repo, token)}
    fehler = 0
    for s in soll:
        da = ist.pop(s['name'], None)
        if da is not None and not vergleich([s], [da], name)[0] and von_github(da, name)['vorbei'] is not None:
            print('unverändert: %s' % s['name'])
            continue
        if da is None:
            status, antwort = api('POST', '/repos/%s/rulesets' % repo, token, fuer_github(s, nr))
        else:
            status, antwort = api('PUT', '/repos/%s/rulesets/%s' % (repo, da.get('id')), token, fuer_github(s, nr))
        ok = status in (200, 201)
        fehler += not ok
        print('%s: %s%s' % ('angelegt' if da is None else 'ersetzt', s['name'], '' if ok else '  FEHLER: ' + meldung(status, antwort)))
    for rest, da in sorted(ist.items()):
        status, antwort = api('DELETE', '/repos/%s/rulesets/%s' % (repo, da.get('id')), token)
        ok = status in (200, 204)
        fehler += not ok
        print('gelöscht: %s%s' % (rest, '' if ok else '  FEHLER: ' + meldung(status, antwort)))
    if fehler:
        print('FEHLER: %d Ruleset(s) konnten nicht geschrieben werden. Der Schutz ist unvollständig: Ursache beheben '
              'und --anwenden wiederholen.' % fehler)
        return 1
    print('Fertig. Kontrolle: python .claude/gemeinsam/scripts/schutz-github.py --pruefen')
    return 0


def main(argv=None):
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            pass
    ap = argparse.ArgumentParser(description='Rulesets auf GitHub aus schutz.txt erzeugen, prüfen, anwenden.')
    was = ap.add_mutually_exclusive_group(required=True)
    was.add_argument('--zeigen', action='store_true', help='Rulesets als JSON zeigen, nichts ändern')
    was.add_argument('--pruefen', action='store_true', help='mit GitHub vergleichen (Rückgabe 1 bei Abweichung)')
    was.add_argument('--anwenden', action='store_true', help='Rulesets auf GitHub anlegen, ersetzen, löschen')
    ap.add_argument('--repo', help='owner/name (Probe), sonst das Repo aus origin')
    a = ap.parse_args(argv)
    try:
        if a.zeigen:
            return zeigen()
        repo = repo_name(a.repo)
        return pruefen(repo) if a.pruefen else anwenden(repo)
    except Fehler as e:
        print('FEHLER: %s' % e)
        return 1


if __name__ == '__main__':
    sys.exit(main())
