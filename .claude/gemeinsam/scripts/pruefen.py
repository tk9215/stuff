"""
pruefen.py - prüft geänderte Dateien, bevor sie zu den Kolleg/innen und den Schülerinnen und Schülern kommen.
Ersetzt den früheren Git-Hook pre-commit. Läuft an zwei Stellen mit denselben Regeln:
  python .claude/gemeinsam/scripts/pruefen.py [--erneuern] [--intern]
      Claude vor dem Commit: Arbeitsstand gegen den letzten Commit (geänderte und neue Dateien).
  python .claude/gemeinsam/scripts/pruefen.py --seit <Commit> [--erneuern] [--zurueckhalten <Datei>]
      GitHub vor dem Zustellen (Workflow "Bauen und zustellen"): alles, was sich seit <Commit> bis HEAD geändert hat.
      --zurueckhalten: Fehler im Abteilungs- und Notizschutz halten nur den betroffenen Bereich an. Die Ordner
      (Themen- bzw. Test-Ordner, mit / am Ende) und Dateien stehen dann zeilenweise in <Datei>, paket-zustellen.py
      lässt sie aus (--ohne), der Workflow macht den Lauf danach rot. Alle anderen Fehler halten weiter alles an.
  python .claude/gemeinsam/scripts/pruefen.py --rechte
      Nur Auskunft am Rechner: Werkzeug-Verantwortliche ja/nein, eigene Teams, eigener Name (für Claude und Skills,
      statt git config selbst zu lesen). Prüft nichts.
  python .claude/gemeinsam/scripts/pruefen.py --von-hand
      GitHub, Lauf von Hand (Run workflow): Fehler, wenn ihn nicht Werkzeug-Verantwortliche gestartet haben.
  --erneuern  Handbuch (automatische Teile) und die Vorschau.html geänderter Test-XML neu schreiben. Committet nichts:
              Vor dem Commit nimmt Claude die Dateien mit, auf GitHub committet der Workflow sie.
  --intern    rein interne Änderung ohne Bedeutung fürs Kollegium: Mitdokumentieren wird nicht verlangt
              (auf GitHub: "[intern]" in der Commit-Nachricht).
Geprüft wird:
  1. Ablage, Steckbrief, Kursplan; ein geändertes Lernpaket hat eine neue Version; in Git liegen keine Lernpakete und
     keine Kurssicherungen (kette-pruefen.py, pruefe_dateien).
  2. Jede geänderte Test-XML ist lesbares Moodle-XML (sonst scheitert auch der Import in die ByCS).
  3. Das Handbuch: Fragen, Links, ids, Format der Neuigkeiten, Kurztext je Skill (handbuch.py).
  4. Mitdokumentieren: Ändern sich Regeln oder Werkzeuge (Muster PFLICHT in handbuch.py), muss auch die Dokumentation
     dabei sein (neuigkeiten.txt, Handbuch, fragen.txt, skills.txt). Vor dem Commit ist das ein Fehler, auf GitHub nur eine
     Warnung (und nur für Commits von Claude, erkennbar an "Co-Authored-By: Claude").
  5.-7. Werkzeug-, Abteilungs- und Notizschutz (geschuetzt). Was erlaubt ist, wie man freigibt und wo die Grenzen
     liegen, steht nur in .claude/gemeinsam/regeln/einrichtung.md, "Werkzeugschutz und Abteilungsschutz". Hier nur, wo
     es im Code steckt:
     - Vor dem Push sperrt GitHub selbst (Rulesets aus schutz.txt, schutz-github.py). Werkzeug- und Abteilungsschutz
       hier sind dafür die zweite Sicherung, Notizschutz und Handbuch (von Hand) kann nur diese Prüfung.
     - Regeln: SCHUTZ (schutz.txt) über Regeln und schutzregeln; auf GitHub aus dem letzten grünen Lauf.
     - Am Rechner (_am_rechner): wer man ist, fragt rechte (meine_teams: GitHub mit der gespeicherten Git-Anmeldung,
       sonst git config bycs.werkzeug); ohne GitHub Hinweis aus teams_aus_geschichte.
     - Auf GitHub (_auf_github): pushes_im_lauf (BYCS_PUSHES), freigeber (Re-run), mitglieder_von (TEAM_TOKEN der
       GitHub-App), --zurueckhalten (zurueck_pfad), --von-hand (von_hand).
     - Notizschutz: todo_fehler und notizen_fehler prüfen den Inhalt von ToDo/; wem ein Eintrag gehört, sagen
       ersteller (Name, @login) und Ich (Login zählt, ältere Einträge ohne Login: der Name; mein_login am Rechner).
     - Tests: handbuch.test.py ersetzt GitHub durch eine Teams-Datei (BYCS_TEAMS_TEST, am Rechner dazu BYCS_ICH).
Rückgabe 1 bei einem Fehler. Die letzte Zeile sagt, ob ein Lernpaket betroffen ist: Dann fragt Claude vor dem Push
(nach dem Push ist die Änderung sofort bei den Schülerinnen und Schülern).
Nur Python-Standardbibliothek (Windows, Mac, GitHub).
"""
import argparse
import fnmatch
import importlib.util
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
QUIZ = os.path.join(ROOT, '.claude', 'skills', 'ByCS-Fragenersteller', 'scripts', 'quiz-vorschau.py')
HANDBUCH = os.path.join(ROOT, '.claude', 'handbuch', 'handbuch.py')
AUF_GITHUB = os.environ.get('GITHUB_ACTIONS') == 'true'
# Werkzeug- und Abteilungsschutz: die eine Liste der Regeln (Werkzeug, Frei, Klasse, Fach), siehe Regeln
SCHUTZ = '.claude/gemeinsam/data/schutz.txt'
# Nur wenn SCHUTZ fehlt oder kein Werkzeug nennt: Dann ist wenigstens das Werkzeug geschützt. Maßgeblich ist SCHUTZ.
NOTFALL_WERKZEUG = ('CLAUDE.md', '.gitignore', '.claude/', '.github/', '#Handbuch.html')
TEAM_WERKZEUG = 'werkzeug-verantwortliche'   # GitHub-Team: darf das Werkzeug und jeden Unterricht ändern
# Notizschutz: Notizzettel und Themenordner in ToDo/
NOTIZEN = 'ToDo/NOTIZEN.md'
EINGANG, ERLEDIGT = 'Eingang (unsortiert)', 'Erledigt'
ERSTELLER = re.compile(r'Ersteller:\s*([^)\n]*)')   # "Ersteller: Vorname Nachname, @login" (ältere: nur der Name)
LOGIN = re.compile(r'@([A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?)')
FORM = '- [ ] **Titel (JJJJ-MM-TT, Ersteller: Vorname Nachname, @login):** Text'
NICHT_LESBAR = ('GitHub konnte die Mitglieder des Teams "%s" nicht lesen, deshalb wird nichts zugestellt. '
                'Werkzeug-Verantwortliche: GitHub-App und Secrets TEAM_APP_ID, TEAM_APP_KEY prüfen, gibt es das Team? '
                '(.claude/gemeinsam/regeln/einrichtung.md, "Werkzeugschutz und Abteilungsschutz"), dann den Lauf wiederholen.')
STOPP = ' Es wird nichts zugestellt.'
ZURUECK = (' Zurückgehalten wird nur das Betroffene (%s), alles andere wird zugestellt. Der Lauf bleibt rot, bis es '
           'freigegeben ist.')
LOESEN = (' %s: Änderung ansehen, dann den Lauf wiederholen (Re-run jobs), oder die Änderung zurücknehmen (git revert) '
          'und pushen.')
NOTIZ = ('Notizschutz: %s Ohne Werkzeugrecht in ToDo/ erlaubt: neuer Eintrag im Eingang, eigene Einträge abhaken, '
         'eigene Themenordner (Skill Notizen). Sonst den Wunsch an die Werkzeug-Verantwortlichen weitergeben '
         '(.claude/gemeinsam/regeln/einrichtung.md, "Notizschutz").')


def _modul(name, pfad):
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location(name, pfad)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def git(*args):
    """(Rückgabecode, Liste der Einträge) für Befehle mit -z, sonst Text."""
    r = subprocess.run(['git', '-c', 'core.quotePath=false'] + list(args), cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    aus = r.stdout.decode('utf-8', 'replace')
    return r.returncode, ([z for z in aus.split('\0') if z] if '-z' in args else aus)


def geaenderte_dateien(seit=None, auch_geloeschte=False):
    """Geänderte und neue Dateien (ab Projektordner), mit auch_geloeschte auch gelöschte (Umbenennen = alter Name
    gelöscht, neuer Name neu). Ohne seit: Arbeitsstand gegen HEAD. None, wenn Git den Commit nicht kennt."""
    auswahl = '--no-renames' if auch_geloeschte else '--diff-filter=ACMR'
    if seit:
        code, d = git('diff', '--name-only', '-z', auswahl, seit, 'HEAD')
        return sorted(d) if code == 0 else None
    _, d = git('diff', '--name-only', '-z', auswahl, 'HEAD')
    _, neu = git('ls-files', '-z', '--others', '--exclude-standard')
    return sorted(set(d) | set(neu))


def kurz(dateien):
    """Die ersten sechs Dateien, dahinter "und n weitere"."""
    dateien = list(dateien)
    return ', '.join(dateien[:6]) + (' und %d weitere' % (len(dateien) - 6) if len(dateien) > 6 else '')


def doku_fehlt(hb, dateien, seit=None, intern=False):
    """Geänderte Regel- oder Werkzeugdateien ohne Dokumentation. Rückgabe: Liste der Dateien (leer = in Ordnung)."""
    if intern:
        return []
    if not seit:
        pflicht = [p for p in dateien if hb.PFLICHT.match(p)]
        return pflicht if pflicht and not any(p in hb.DOKU for p in dateien) else []
    # GitHub: nur Commits von Claude zählen, "[intern]" in der Nachricht nimmt einen Commit aus
    code, log = git('log', '--format=%H%x00%B%x01', '%s..HEAD' % seit)
    if code != 0:
        return []
    pflicht = []
    for eintrag in log.split('\x01'):
        if '\x00' not in eintrag:
            continue
        h, text = eintrag.strip().split('\x00', 1)
        if not re.search(r'^Co-Authored-By: Claude', text, re.M | re.I) or '[intern]' in text:
            continue
        _, d = git('diff-tree', '--no-commit-id', '--name-only', '-r', '-z', h)
        pflicht += [p for p in d if hb.PFLICHT.match(p)]
    return sorted(set(pflicht)) if pflicht and not any(p in hb.DOKU for p in dateien) else []


class Regeln:
    """Die Schutzregeln aus SCHUTZ: Muster für Werkzeug und Frei, Teams je Klasse und Fach (Kürzel klein).
    schreibweise: ('klasse' oder 'fach', Kürzel klein) -> Kürzel wie in SCHUTZ (für die Rulesets, schutz-github.py)."""

    def __init__(self, text):
        self.werkzeug, self.frei, self.klassen, self.faecher, self.schreibweise = [], [], {}, {}, {}
        for z in text.splitlines():
            t = [x.strip() for x in z.split('|')]
            art = t[0].lower()
            if z.lstrip().startswith('#'):
                continue
            if art in ('werkzeug', 'frei') and len(t) == 2 and t[1]:
                (self.werkzeug if art == 'werkzeug' else self.frei).append(t[1])
            elif art in ('klasse', 'fach') and len(t) == 3 and t[1] and t[2]:
                (self.klassen if art == 'klasse' else self.faecher)[t[1].lower()] = t[2].lower()
                self.schreibweise[(art, t[1].lower())] = t[1]
        if not self.werkzeug:
            self.werkzeug = list(NOTFALL_WERKZEUG)

    @staticmethod
    def _passt(pfad, muster):
        """Muster mit / am Ende: der Ordner samt allem darin; sonst der Pfad, * für beliebige Zeichen."""
        return pfad.startswith(muster) if muster.endswith('/') else fnmatch.fnmatchcase(pfad, muster)

    def ist_frei(self, pfad):
        return any(self._passt(pfad, m) for m in self.frei)

    def ist_werkzeug(self, pfad):
        return not self.ist_frei(pfad) and any(self._passt(pfad, m) for m in self.werkzeug)

    def team(self, pfad):
        """Zuständiges Team: '' = frei (kein Unterricht oder "Frei"), None = Unterricht ohne Zuordnung."""
        t = pfad.split('/')
        if t[0] != 'Unterricht' or len(t) < 3 or self.ist_frei(pfad):
            return ''
        fach = self.faecher.get(t[2].lower()) if len(t) > 3 else None   # Kursplan direkt in der Klasse: kein Fach
        return fach or self.klassen.get(t[1].lower())

    def bedarf(self, dateien):
        """({Team: [Dateien]}, {Ordner ohne Zuordnung}) für geänderte Pfade."""
        bedarf, ohne = {}, set()
        for p in sorted(dateien):
            team = self.team(p)
            if team is None:
                ohne.add('/'.join(p.split('/')[:3]))
            elif team:
                bedarf.setdefault(team, []).append(p)
        return bedarf, ohne


def schutzregeln(commit='HEAD'):
    """Regeln aus SCHUTZ in der Fassung von commit, nicht aus dem Arbeitsstand: Auf GitHub ist commit der letzte grüne
    Lauf, eine Änderung an den Regeln wirkt also erst nach der Freigabe (sonst könnte ein Push "Werkzeug | .claude/"
    streichen und wäre selbst frei). Fehlt SCHUTZ dort, gilt nur NOTFALL_WERKZEUG."""
    code, text = git('show', '%s:%s' % (commit, SCHUTZ))
    return Regeln(text if code == 0 else '')


def _api(url, zugang, timeout=20):
    """GET bei der GitHub-API: (Status, Daten). Status 0 = keine Verbindung. Der Zugang wird nie ausgegeben."""
    anfrage = urllib.request.Request(url, headers={
        'Authorization': 'Bearer ' + zugang, 'Accept': 'application/vnd.github+json', 'User-Agent': 'pruefen.py'})
    try:
        with urllib.request.urlopen(anfrage, timeout=timeout) as r:
            return r.status, json.loads(r.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        return e.code, None
    except (OSError, ValueError):   # auch URLError
        return 0, None


def _github(pfad):
    """Antwort von GitHub als dict, False bei 404, None wenn GitHub nicht lesen lässt."""
    token, org = os.environ.get('TEAM_TOKEN', '').strip(), os.environ.get('GITHUB_REPOSITORY_OWNER', '').strip()
    if not token or not org:
        return None
    status, daten = _api('https://api.github.com/orgs/%s/%s' % (urllib.parse.quote(org), pfad), token)
    return daten if status == 200 else (False if status == 404 else None)


def _test_teams():
    """Nur für handbuch.test.py: {Team: {GitHub-Namen}} aus der Datei BYCS_TEAMS_TEST (Zeilen "team: name, name")
    statt GitHub, für den Lauf (mitglieder_von) wie für den Rechner (meine_teams mit BYCS_ICH). None ohne Test."""
    pfad = os.environ.get('BYCS_TEAMS_TEST')
    if not pfad:
        return None
    teams = {}
    with open(pfad, encoding='utf-8') as f:
        for z in f:
            if ':' in z:
                team, namen = z.split(':', 1)
                teams[team.strip().lower()] = {n.strip().lower() for n in namen.split(',')} - {''}
    return teams


_MITGLIEDER = {}   # Team -> GitHub-Namen der Mitglieder, einmal je Lauf von GitHub gelesen


def mitglieder_von(team, wer):
    """Wer aus der Menge wer (GitHub-Namen, klein) im Team ist, Unterteams eingeschlossen. Liest die Mitglieder einmal
    je Team (alle Seiten) und merkt sie. None, wenn GitHub das Team nicht lesen lässt (fehlt, Zugang reicht nicht)."""
    test = _test_teams()
    if test is not None:
        return wer & test[team] if team in test else None
    if team not in _MITGLIEDER:
        namen, seite = set(), 1
        while True:
            daten = _github('teams/%s/members?per_page=100&page=%d' % (urllib.parse.quote(team), seite))
            if not isinstance(daten, list):   # False (404: Team fehlt) oder None (nicht lesbar)
                return None
            namen |= {str(m.get('login', '')).lower() for m in daten if isinstance(m, dict)} - {''}
            if len(daten) < 100:
                break
            seite += 1
        _MITGLIEDER[team] = namen
    return wer & _MITGLIEDER[team]


def handbuch_von_hand(hb, alt_commit, neu_commit=None):
    """True, wenn sich am Handbuch mehr geändert hat als die automatischen Teile (alt_commit gegen neu_commit,
    ohne neu_commit gegen den Arbeitsstand)."""
    code, alt = git('show', '%s:%s' % (alt_commit, hb.DATEI))
    if neu_commit:
        c, neu = git('show', '%s:%s' % (neu_commit, hb.DATEI))
        if c != 0:
            return True   # gelöscht
    else:
        try:
            neu = hb.lesen(hb.DATEI)
        except OSError:
            return True   # gelöscht
    if code != 0:
        return True   # neu
    try:   # beide Fassungen mit denselben automatischen Teilen füllen: Was dann noch abweicht, ist von Hand
        return hb.ohne_stand(hb.erneuern(alt)[0]) != hb.ohne_stand(hb.erneuern(neu)[0])
    except SystemExit:
        return True   # eine AUTO-Markierung fehlt


def _name(text):
    """Name zum Vergleichen: klein, ohne doppelte Leerzeichen."""
    return ' '.join(text.split()).casefold()


def ersteller(text):
    """(Name, Login) aus "Ersteller: Vorname Nachname, @login" (erste Fundstelle, zum Vergleichen klein), ('', '')
    wenn keiner dasteht. Ältere Einträge haben nur den Namen, der Login ist dann ''."""
    m = ERSTELLER.search(text or '')
    if not m:
        return '', ''
    login = LOGIN.search(m.group(1))
    return _name(re.split(r'[,@]', m.group(1), 1)[0]), (login.group(1).lower() if login else '')


class Ich:
    """Wer gerade ändert: Namen und GitHub-Logins (klein). Steht beim Ersteller ein Login, zählt nur der Login (den
    bestätigt GitHub beim Push); ältere Einträge ohne Login gehören dem Namen. logins None = Login unbekannt (am Rechner
    ohne Verbindung zu GitHub): Dann zählt vorerst der Name, verbindlich prüft GitHub."""

    def __init__(self, namen, logins):
        self.namen, self.logins = set(namen) - {''}, (None if logins is None else set(logins) - {''})

    def meins(self, wer):
        name, login = wer
        if login and self.logins is not None:
            return login in self.logins
        return bool(name) and name in self.namen

    def ohne_login(self, wer):
        """True, wenn bei einem neuen Eintrag oder Ordner der Login fehlt, obwohl er sich prüfen lässt."""
        return not wer[1] and self.logins is not None


def notizen_teile(text):
    """Notizzettel zerlegen: (Überschriften, {Abschnitt: fester Text}, [(Abschnitt, Eintrag, Ersteller)]).
    Ein Eintrag ist eine Zeile "- [ ] …" samt den eingerückten Folgezeilen, fester Text der Rest ohne Leerzeilen."""
    abschnitt, koepfe, fest, eintraege = '', [], {'': []}, []
    for z in text.splitlines():
        if z.startswith('## '):
            abschnitt = z[3:].strip()
            koepfe.append(abschnitt)
            fest.setdefault(abschnitt, [])
        elif re.match(r'- \[.\]', z):
            eintraege.append([abschnitt, z.rstrip()])
        elif z[:1] in (' ', '\t') and z.strip() and eintraege and eintraege[-1][0] == abschnitt:
            eintraege[-1][1] += '\n' + z.rstrip()
        elif z.strip():
            fest[abschnitt].append(z.rstrip())
    return koepfe, fest, [(a, t, ersteller(t.split('\n', 1)[0])) for a, t in eintraege]


def notizen_fehler(alt_commit, ich):
    """Was am Notizzettel ohne Werkzeugrecht nicht erlaubt ist (Liste von Texten, leer = in Ordnung)."""
    code, alt = git('show', '%s:%s' % (alt_commit, NOTIZEN))
    if code != 0:
        return ['%s ist neu. Den Notizzettel legen nur Werkzeug-Verantwortliche an.' % NOTIZEN]
    try:
        with open(os.path.join(ROOT, NOTIZEN), encoding='utf-8') as f:
            neu = f.read()
    except OSError:
        return ['%s ist gelöscht. Den Notizzettel löschen nur Werkzeug-Verantwortliche.' % NOTIZEN]
    k_alt, f_alt, e_alt = notizen_teile(alt)
    k_neu, f_neu, e_neu = notizen_teile(neu)
    fehler = []
    if k_alt != k_neu:
        fehler.append('Überschriften geändert (nur Werkzeug-Verantwortliche).')
    elif f_alt != f_neu:
        fehler.append('Text außerhalb der Einträge geändert (Abschnitt "%s", nur Werkzeug-Verantwortliche).'
                      % next(a for a in k_neu + [''] if f_alt.get(a) != f_neu.get(a)))
    rest = list(e_neu)
    fremd, eigen = [], []   # alte Einträge, die sich geändert haben oder fehlen
    for a, t, e in e_alt:
        if (a, t, e) in rest:
            rest.remove((a, t, e))
        elif ich.meins(e):
            eigen.append((a, e))
        else:
            fremd.append(t.split('\n', 1)[0][:90])
    if fremd:
        fehler.append('Fremde Einträge geändert, verschoben oder gelöscht: %s. Ändern dürfen das nur die Person, die '
                      'unter "Ersteller" steht, oder Werkzeug-Verantwortliche.' % '; '.join(fremd[:3]))
    for a, e in eigen:   # eigene Einträge dürfen sich ändern, aber nicht verschwinden
        treffer = [x for x in rest if ich.meins(x[2])]   # auch mit nachgetragenem Login
        passt = [x for x in treffer if x[0] in (a, ERLEDIGT)]
        if passt:
            rest.remove(passt[0])
        elif treffer:
            rest.remove(treffer[0])
            fehler.append('Eigener Eintrag in einen anderen Abschnitt verschoben (erlaubt: bleibt in "%s" oder '
                          'kommt nach "%s"). Sortieren dürfen nur Werkzeug-Verantwortliche.' % (a, ERLEDIGT))
        else:
            fehler.append('Eigener Eintrag gelöscht (Abschnitt "%s"). Abhaken statt löschen: [x], Datum, nach "%s".'
                          % (a, ERLEDIGT))
    for a, t, e in rest:   # neue Einträge
        kopf = t.split('\n', 1)[0]
        if a != EINGANG:
            fehler.append('Neuer Eintrag im Abschnitt "%s": %s. Neue Einträge kommen unter "%s".' % (a, kopf[:90], EINGANG))
        elif not any(e) or not re.search(r'\d{4}-\d{2}-\d{2}', kopf):
            fehler.append('Neuer Eintrag ohne Datum oder Ersteller: %s. Form: %s' % (kopf[:90], FORM))
        elif ich.ohne_login(e):
            fehler.append('Neuer Eintrag ohne GitHub-Login beim Ersteller: %s. Form: %s (den eigenen Login zeigt '
                          'pruefen.py --rechte).' % (kopf[:90], FORM))
        elif not ich.meins(e):
            fehler.append('Neuer Eintrag mit fremdem Ersteller: %s. Als Ersteller stehen der eigene Name und Login '
                          '(pruefen.py --rechte).' % kopf[:90])
    return fehler


def todo_fehler(d, alt_commit, ich):
    """Notizschutz für alle geänderten Pfade unter ToDo/ (Liste von Texten, leer = in Ordnung). ich: Ich."""
    pfade = sorted(p for p in d if p.startswith('ToDo/'))
    if not pfade:
        return []
    fehler, ordner = [], {}
    for p in pfade:
        t = p.split('/')
        if p == NOTIZEN:
            fehler += notizen_fehler(alt_commit, ich)
        elif len(t) == 2:
            fehler.append('%s liegt direkt in ToDo/. Dort steht nur der Notizzettel, Material gehört in einen '
                          'Themenordner ToDo/<Thema>/.' % p)
        else:
            ordner.setdefault(t[1], []).append(p)
    for thema, dateien in sorted(ordner.items()):
        uebergabe = 'ToDo/%s/Uebergabe.md' % thema
        gab_es = bool(git('ls-tree', '-z', '--name-only', alt_commit, 'ToDo/%s/' % thema)[1])
        if gab_es:   # bestehender Ordner: Wer in der alten Uebergabe.md steht, darf ihn pflegen
            code, text = git('show', '%s:%s' % (alt_commit, uebergabe))
            wer = ersteller(text) if code == 0 else ('', '')
        else:   # neuer Ordner: die neue Uebergabe.md nennt den Ersteller
            try:
                with open(os.path.join(ROOT, uebergabe), encoding='utf-8') as f:
                    wer = ersteller(f.read())
            except OSError:
                wer = ('', '')
        if ich.meins(wer) and not (not gab_es and ich.ohne_login(wer)):
            continue
        if gab_es:
            fehler.append('Fremder Themenordner ToDo/%s/ geändert (%s). Ändern darf ihn nur, wer in seiner Uebergabe.md '
                          'als Ersteller steht, oder Werkzeug-Verantwortliche.' % (thema, ', '.join(dateien[:3])))
        else:
            fehler.append('Neuer Themenordner ToDo/%s/ ohne %s mit dem eigenen Namen und Login ("Ersteller: Vorname '
                          'Nachname, @login", den Login zeigt pruefen.py --rechte).' % (thema, uebergabe))
    return fehler


def organisation():
    """GitHub-Organisation des Repos: auf GitHub aus der Umgebung, am Rechner aus der Adresse von origin."""
    org = os.environ.get('GITHUB_REPOSITORY_OWNER', '').strip()
    if org:
        return org
    m = re.search(r'github\.com[:/]+([^/]+)/', git('remote', 'get-url', 'origin')[1])
    return m.group(1) if m else ''


_ANMELDUNG = []   # gespeicherte Git-Anmeldung für github.com, einmal je Aufruf geholt, nur im Speicher


def _anmeldung():
    """Am Rechner: Zugang aus der gespeicherten Git-Anmeldung (dieselbe wie beim Push, git credential fill, ohne
    Rückfrage). '' wenn keine da ist. Wird nie ausgegeben oder gespeichert."""
    if not _ANMELDUNG:
        umgebung = dict(os.environ, GIT_TERMINAL_PROMPT='0', GCM_INTERACTIVE='never')
        try:
            r = subprocess.run(['git', 'credential', 'fill'], cwd=ROOT, input=b'protocol=https\nhost=github.com\n\n',
                               env=umgebung, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20)
            werte = dict(z.split('=', 1) for z in r.stdout.decode('utf-8', 'replace').splitlines() if '=' in z)
            _ANMELDUNG.append(werte.get('password', '') if r.returncode == 0 else '')
        except (OSError, subprocess.SubprocessError):
            _ANMELDUNG.append('')
    return _ANMELDUNG[0]


def mein_login():
    """Am Rechner: eigener GitHub-Login (klein, für "Ersteller: …, @login"). None, wenn GitHub nicht erreichbar ist."""
    ich = os.environ.get('BYCS_ICH')   # nur für handbuch.test.py, "-" = nicht erreichbar
    if ich is not None:
        return None if ich.strip() in ('', '-') else ich.strip().lower()
    zugang = _anmeldung()
    if not zugang:
        return None
    status, daten = _api('https://api.github.com/user', zugang, timeout=10)
    login = str(daten.get('login', '')).lower() if status == 200 and isinstance(daten, dict) else ''
    return login or None


def meine_teams():
    """Am Rechner: Teams der Organisation, in denen die angemeldete Person ist (Menge der Kürzel, klein).
    Fragt GitHub mit der gespeicherten Git-Anmeldung (git credential fill, ohne Rückfrage). Die Anmeldung bleibt nur
    im Speicher, sie wird nie ausgegeben oder gespeichert. None, wenn das nicht geht (offline, keine Anmeldung, die
    Anmeldung darf keine Teams lesen)."""
    ich = os.environ.get('BYCS_ICH')   # nur für handbuch.test.py: GitHub-Name aus BYCS_TEAMS_TEST, "-" = nicht erreichbar
    if ich is not None:
        test = _test_teams()
        if ich.strip() == '-' or test is None:
            return None
        return {team for team, namen in test.items() if ich.strip().lower() in namen}
    org, zugang = organisation(), _anmeldung()
    if not org or not zugang:
        return None
    status, daten = _api('https://api.github.com/user/teams?per_page=100', zugang, timeout=10)
    if status != 200 or not isinstance(daten, list):
        return None
    return {str(t.get('slug', '')).lower() for t in daten if isinstance(t, dict)
            and str((t.get('organization') or {}).get('login', '')).lower() == org.lower()} - {''}


def rechte():
    """Am Rechner: (Werkzeug-Verantwortliche?, woher das stammt, eigene Teams oder None, bycs.werkzeug "ja"?).
    GitHub geht vor (meine_teams). Nur wenn GitHub nicht erreichbar ist, entscheidet git config bycs.werkzeug."""
    meine = meine_teams()
    eingerichtet = git('config', '--get', 'bycs.werkzeug')[1].strip().lower() == 'ja'
    if meine is not None:
        return TEAM_WERKZEUG in meine, 'laut GitHub', meine, eingerichtet
    return eingerichtet, 'GitHub nicht erreichbar, laut git config bycs.werkzeug', None, eingerichtet


def rechte_zeigen():
    """Ausgabe für --rechte."""
    werkzeug, quelle, meine, eingerichtet = rechte()
    print('Werkzeug-Verantwortliche: %s (%s)' % ('ja' if werkzeug else 'nein', quelle))
    print('Teams: %s' % (', '.join(sorted(meine)) or 'keine') if meine is not None else
          'Teams: unbekannt (GitHub nicht erreichbar, verbindlich prüft GitHub nach dem Push)')
    name, login = git('config', '--get', 'user.name')[1].strip(), mein_login()
    print('Name: %s (git config user.name)' % (name or 'fehlt'))
    print('Login: @%s (laut GitHub)' % login if login else
          'Login: unbekannt (GitHub nicht erreichbar; neue Notizen erst eintragen, wenn GitHub erreichbar ist)')
    if login:
        print('Ersteller in Notizen: "Ersteller: %s, @%s"' % (name or 'Vorname Nachname', login))
    if eingerichtet and not werkzeug:
        print('WARNUNG: bycs.werkzeug steht auf "ja", laut GitHub bist du aber nicht im Team "%s".' % TEAM_WERKZEUG)


def teams_aus_geschichte(regeln):
    """Am Rechner, wenn GitHub nicht erreichbar ist: Teams, in deren Unterricht user.email schon Commits hat."""
    email = git('config', '--get', 'user.email')[1].strip().lower()
    if not email:
        return set()
    _, log = git('log', '--format=%x01%ae', '--name-only', 'HEAD', '--', 'Unterricht/')
    teams, meins = set(), False
    for z in log.splitlines():
        if z.startswith('\x01'):
            meins = z[1:].strip().lower() == email
        elif meins and z.strip():
            team = regeln.team(z.strip())
            if team:
                teams.add(team)
    return teams


def _vorfahr(a, b):
    """True, wenn Commit a in der Geschichte von b liegt (auch a == b)."""
    return git('merge-base', '--is-ancestor', a, b)[0] == 0


def pushes_im_lauf(seit):
    """GitHub: [(von, bis, Person, {Dateien})] je Push seit dem letzten grünen Lauf, älteste zuerst.
    BYCS_PUSHES (Workflow): "<Commit>:<GitHub-Name> …" der früheren Läufe seit dem letzten grünen Lauf, älteste zuerst.
    Dazu kommt dieser Lauf (HEAD, GITHUB_ACTOR). Ein Push bekommt die Dateien zwischen dem vorigen Push und seinem
    Commit (auch Commits ohne eigenen Lauf, z. B. das Handbuch von GitHub). Leer, wenn nicht auf GitHub."""
    liste = [(c, n.strip().lower()) for c, _, n in (x.partition(':') for x in os.environ.get('BYCS_PUSHES', '').split())
             if c and n.strip()]
    kopf, ich = git('rev-parse', 'HEAD')[1].strip(), os.environ.get('GITHUB_ACTOR', '').strip().lower()
    if ich and (not liste or liste[-1][0] != kopf):
        liste.append((kopf, ich))
    pushes, vorher = [], seit
    for commit, person in liste:
        if not _vorfahr(commit, 'HEAD') or _vorfahr(commit, vorher):
            continue   # nicht mehr auf main (erzwungener Push) oder schon vor dem Vergleichsstand
        von = vorher if _vorfahr(vorher, commit) else seit
        _, d = git('diff', '--name-only', '-z', '--no-renames', von, commit)
        pushes.append((von, commit, person, set(d)))
        vorher = commit
    return pushes


def freigeber():
    """GitHub: Wer den Lauf wiederholt hat (Re-run jobs, ab dem zweiten Versuch). Sonst ''."""
    try:
        versuch = int(os.environ.get('GITHUB_RUN_ATTEMPT', '1'))
    except ValueError:
        versuch = 1
    return os.environ.get('GITHUB_TRIGGERING_ACTOR', '').strip().lower() if versuch > 1 else ''


def von_hand():
    """GitHub, Lauf von Hand (Run workflow): Nur Werkzeug-Verantwortliche dürfen ihn starten, denn er stellt zu, was auf
    main liegt, auch das, was ein roter Lauf angehalten hat. Rückgabe 1, wenn nicht."""
    wer = (os.environ.get('GITHUB_TRIGGERING_ACTOR') or os.environ.get('GITHUB_ACTOR') or '').strip().lower()
    fehler = '::error::' if AUF_GITHUB else 'FEHLER: '
    if not wer:
        print(fehler + '--von-hand gibt es nur auf GitHub (Lauf von Hand, Run workflow).')
        return 1
    drin = mitglieder_von(TEAM_WERKZEUG, {wer})
    if drin is None:
        print(fehler + NICHT_LESBAR % TEAM_WERKZEUG)
        return 1
    if not drin:
        print(fehler + 'Einen Lauf von Hand (Run workflow) starten nur Werkzeug-Verantwortliche (Team "%s"), gestartet hat '
              'ihn %s. Es wird nichts zugestellt. Lernpakete, Kurse und Tests stellt GitHub nach jedem Push von selbst zu. '
              'Soll etwas neu zugestellt werden, die Werkzeug-Verantwortlichen fragen.' % (TEAM_WERKZEUG, wer))
        return 1
    print('Lauf von Hand, gestartet von %s (Werkzeug-Verantwortliche): Zugestellt wird, was auf main liegt, auch '
          'Änderungen, die ein roter Lauf angehalten hat.' % wer)
    return 0


def zurueck_pfad(p):
    """Was für eine geänderte Datei zurückgehalten wird: ihr Themen- bzw. Test-Ordner (Unterricht/<Klasse>/<Fach>/
    <Abschnitt>/<Ordner>/, wird als Ganzes gebaut und zugestellt), sonst die Datei selbst (z. B. ein Kursplan)."""
    t = p.split('/')
    return '/'.join(t[:5]) + '/' if t[0] == 'Unterricht' and len(t) > 5 else p


def geschuetzt(hb, seit=None, zurueckhalten=False):
    """Werkzeug-, Abteilungs- und Notizschutz. Rückgabe: (Fehler, Warnungen, zurückgehaltene Pfade).
    Am Rechner: Arbeitsstand gegen HEAD, Regeln aus HEAD. Auf GitHub (seit): alles seit dem letzten grünen Lauf, Regeln
    in dessen Fassung. Mit zurueckhalten (nur GitHub) halten Fehler im Abteilungs- und Notizschutz nur ihren Bereich an."""
    regeln = schutzregeln(seit or 'HEAD')
    d = set(geaenderte_dateien(seit, auch_geloeschte=True) or [])
    werkzeug = sorted(p for p in d if regeln.ist_werkzeug(p)
                      and (p != hb.DATEI or handbuch_von_hand(hb, seit or 'HEAD')))   # Handbuch: nur von Hand
    if seit:
        return _auf_github(hb, regeln, d, werkzeug, seit, zurueckhalten)
    return _am_rechner(regeln, d, werkzeug) + (set(),)


def _am_rechner(regeln, d, werkzeug):
    """Vor dem Commit, für alle außer Werkzeug-Verantwortliche (rechte). Rückgabe: (Fehler, Warnungen).
    Die eigenen Teams kommen von GitHub (verbindlich: Fehler). Ist GitHub nicht erreichbar, gibt es für den
    Abteilungsschutz nur einen Hinweis aus der Git-Geschichte (teams_aus_geschichte). Verbindlich prüft GitHub."""
    bedarf, _ = regeln.bedarf(d)
    notizen = any(p.startswith('ToDo/') for p in d)
    if not (werkzeug or bedarf or notizen):
        return [], []
    recht, _, meine, eingerichtet = rechte()   # meine None = GitHub nicht erreichbar
    if recht:
        return [], []
    warnungen = ['Auf diesem Rechner steht bycs.werkzeug "ja", laut GitHub bist du aber nicht im Team "%s". '
                 'Werkzeug-, Notiz- und Abteilungsschutz gelten deshalb wie für alle.' % TEAM_WERKZEUG] if eingerichtet else []
    fehler = ['Werkzeug geändert (%s). Das Werkzeug (Skills, Vorlagen, Skripte, Regeln, Einstellungen, Handbuch) ändern '
              'nur Werkzeug-Verantwortliche. Änderung zurücknehmen und den Wunsch an die Werkzeug-Verantwortlichen '
              'weitergeben. Eigene Skills gehören in den eigenen Ordner ~/.claude/skills/, nicht ins Projekt. '
              'Werkzeug-Verantwortliche: .claude/gemeinsam/regeln/einrichtung.md, "Werkzeugschutz".' % kurz(werkzeug)] if werkzeug else []
    if notizen:
        login = mein_login()
        ich = Ich({_name(git('config', '--get', 'user.name')[1])}, {login} if login else None)
        fehler += [NOTIZ % t for t in todo_fehler(d, 'HEAD', ich)]
    if meine is not None:
        fehler += ['Unterricht des Teams "%s" geändert (%s), du bist laut GitHub aber nicht in diesem Team. Nach dem Push '
                   'würde nichts zugestellt. Änderung zurücknehmen oder ein Mitglied des Teams "%s" bzw. die '
                   'Werkzeug-Verantwortlichen bitten (.claude/gemeinsam/regeln/einrichtung.md, "Abteilungsschutz").'
                   % (team, kurz(dateien), team) for team, dateien in sorted(bedarf.items()) if team not in meine]
    elif bedarf:
        bekannt = teams_aus_geschichte(regeln)
        warnungen += ['GitHub war nicht erreichbar, die Teams sind nicht geprüft. Im Unterricht des Teams "%s" (%s) gibt es '
                      'noch keine Änderung von dir. Bist du nicht in diesem Team, hält GitHub nach dem Push die Zustellung an.'
                      % (team, kurz(dateien)) for team, dateien in sorted(bedarf.items()) if team not in bekannt]
    return fehler, warnungen


def _auf_github(hb, regeln, d, werkzeug, seit, zurueckhalten):
    """Nach dem Push: jeder Push für sich (pushes_im_lauf), Freigabe nur per Re-run (freigeber).
    Rückgabe: (Fehler, Warnungen, zurückgehaltene Pfade)."""
    pushes = pushes_im_lauf(seit)
    if not pushes:   # nicht auf GitHub
        return [], [], set()
    _, ohne = regeln.bedarf(d)   # Ordner ohne Zuordnung
    warnungen = ['Ohne Zuordnung zu einer Abteilung oder einem Fachbereich, deshalb für alle frei: %s. '
                 'Werkzeug-Verantwortliche tragen Klasse oder Fach in %s ein.' % (', '.join(sorted(ohne)), SCHUTZ)] if ohne else []
    # Je Push: welches Team braucht er für welche Dateien? Es zählt nur, was sich seit dem letzten grünen Lauf wirklich
    # geändert hat (Zurückgenommenes nicht), das Handbuch nur, wenn dieser Push es von Hand geändert hat.
    noetig = {}   # Team -> {Person: [Dateien]}
    for von, bis, person, dateien in pushes:
        dateien &= d
        for team, liste in regeln.bedarf(dateien)[0].items():
            noetig.setdefault(team, {}).setdefault(person, []).extend(liste)
        wz = sorted(p for p in dateien if p in werkzeug and (p != hb.DATEI or handbuch_von_hand(hb, von, bis)))
        if wz:
            noetig.setdefault(TEAM_WERKZEUG, {}).setdefault(person, []).extend(wz)
    todo = sorted({person for _, _, person, dateien in pushes if any(p.startswith('ToDo/') for p in dateien)})
    if not noetig and not todo:
        return [], warnungen, set()
    frei = freigeber()
    alle = {person for _, _, person, _ in pushes} | ({frei} - {''})
    chefs = mitglieder_von(TEAM_WERKZEUG, alle)
    if chefs is None:
        return [NICHT_LESBAR % TEAM_WERKZEUG], warnungen, set()
    if frei in chefs:   # Werkzeug-Verantwortliche haben den Lauf wiederholt: alles freigegeben
        return [], warnungen, set()

    def von_wem(fremde):
        return '; '.join('%s (%s)' % (person, kurz(sorted(set(dateien)))) for person, dateien in sorted(fremde.items()))

    fehler, zurueck = [], set()

    def anhalten(text, pfade, wer):
        """Fehler im Abteilungs- oder Notizschutz: mit zurueckhalten nur den Bereich anhalten, sonst alles."""
        if zurueckhalten:
            bereich = sorted({zurueck_pfad(p) for p in pfade})
            zurueck.update(bereich)
            warnungen.append('ZURUECK:' + text + ZURUECK % kurz(bereich) + LOESEN % wer)
        else:
            fehler.append(text + STOPP + LOESEN % wer)

    if todo and not set(todo) <= chefs:   # Notizschutz: eigene Logins = wer in ToDo/ gepusht hat (bestätigt GitHub),
        _, autoren = git('log', '-z', '--format=%an', '%s..HEAD' % seit, '--', 'ToDo/')   # Namen nur für ältere Einträge
        for t in todo_fehler(d, seit, Ich({_name(a) for a in autoren}, todo)):
            anhalten((NOTIZ % t) + ' Gepusht von %s.' % ', '.join(p for p in todo if p not in chefs),
                     [p for p in d if p.startswith('ToDo/')], 'Werkzeug-Verantwortliche')
    for team, wer_was in sorted(noetig.items()):
        fremde = {person: dateien for person, dateien in wer_was.items() if person not in chefs}
        if not fremde:
            continue
        if team == TEAM_WERKZEUG:
            fehler.append(('Werkzeug geändert von %s, das dürfen aber nur Werkzeug-Verantwortliche (Team "%s").'
                           % (von_wem(fremde), TEAM_WERKZEUG)) + STOPP + LOESEN % 'Werkzeug-Verantwortliche')
            continue
        drin = mitglieder_von(team, alle)
        if drin is None:
            fehler.append(NICHT_LESBAR % team)
            continue
        if frei in drin:   # ein Mitglied des Teams hat den Lauf wiederholt: Bereich freigegeben
            continue
        fremde = {person: dateien for person, dateien in fremde.items() if person not in drin}
        if fremde:
            anhalten('Unterricht des Teams "%s" geändert von %s, niemand davon ist in diesem Team.' % (team, von_wem(fremde)),
                     [p for dateien in fremde.values() for p in dateien],
                     'Mitglieder des Teams "%s" oder Werkzeug-Verantwortliche' % team)
    return fehler, warnungen, zurueck


def main(argv=None):
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            pass
    ap = argparse.ArgumentParser(description='Geänderte Dateien prüfen (vor dem Commit und auf GitHub).')
    ap.add_argument('--seit', help='alle Änderungen seit diesem Commit bis HEAD (GitHub)')
    ap.add_argument('--erneuern', action='store_true', help='Handbuch und Vorschau.html neu schreiben')
    ap.add_argument('--intern', action='store_true', help='Mitdokumentieren nicht verlangen')
    ap.add_argument('--rechte', action='store_true', help='nur zeigen: Werkzeug-Verantwortliche?, eigene Teams, Name')
    ap.add_argument('--von-hand', action='store_true', help='GitHub: Lauf von Hand nur für Werkzeug-Verantwortliche')
    ap.add_argument('--zurueckhalten', metavar='DATEI', help='GitHub: Abteilungs- und Notizschutz halten nur ihren Bereich '
                    'an, die Pfade kommen in DATEI (für paket-zustellen.py --ohne)')
    a = ap.parse_args(argv)
    if a.rechte:
        rechte_zeigen()
        return 0
    if a.von_hand:
        return von_hand()

    dateien = geaenderte_dateien(a.seit)
    if dateien is None:
        print('FEHLER: Den Commit %s kennt Git hier nicht.' % a.seit)
        return 1
    kette = _modul('kette_pruefen', os.path.join(HERE, 'kette-pruefen.py'))
    quiz = _modul('quiz_vorschau', QUIZ)
    hb = _modul('handbuch', HANDBUCH)
    fehler, warnungen = [], []

    # 1. Ablage, Steckbrief, Kursplan, Version, nichts Gebautes in Git
    f, pakete = kette.pruefe_dateien(dateien, alt=a.seit or 'HEAD', neu='HEAD' if a.seit else None)
    fehler += f

    # 2. Test-XML lesbar, Vorschau erneuern
    xml = [p for p in dateien if quiz.ist_quiz(p) and os.path.isfile(os.path.join(ROOT, p))]
    if quiz.VORLAGE_REL in dateien:   # neue Vorlage: alle Vorschauen
        xml = sorted(set(xml) | {q.relative_to(quiz.REPO).as_posix() for q in quiz.alle_quizze()})
    neu_geschrieben = []
    for p in xml:
        try:
            if a.erneuern:
                ziel = quiz.schreiben(quiz.REPO / p)
                neu_geschrieben.append(ziel.relative_to(quiz.REPO).as_posix())
            else:
                quiz.bauen(quiz.REPO / p)
        except quiz.QuizFehler as e:
            fehler.append(str(e))

    # 3. Handbuch
    s = hb.lesen(hb.DATEI)
    neu, fehlen = hb.erneuern(s)
    fehler += ['%s: %s' % (hb.DATEI, t) for t in hb.pruefen(neu)]
    fehler += ['Skill %s hat keinen Kurztext in %s.' % (n, hb.SKILLS) for n in fehlen]
    if neu != s:
        if a.erneuern:
            hb.schreiben(hb.DATEI, neu)
            neu_geschrieben.append(hb.DATEI)
        elif not a.seit:
            warnungen.append('%s: Automatische Teile sind veraltet (mit --erneuern neu schreiben).' % hb.DATEI)

    # 4. Mitdokumentieren
    ohne = doku_fehlt(hb, dateien, a.seit, a.intern)
    if ohne:
        text = ('Regeln oder Werkzeuge geändert, aber nicht dokumentiert: %s. In %s oben eine Zeile eintragen '
                '(TT.MM.JJJJ | was sich für Kolleg/innen ändert, ein Satz ohne Technik), bei geänderter Bedienung auch das Handbuch. '
                'Nur intern: --intern bzw. "[intern]" in der Commit-Nachricht.' % (', '.join(ohne), hb.NEU))
        (warnungen if a.seit else fehler).append(text)

    # 5. bis 7. Werkzeugschutz, Abteilungsschutz, Notizschutz
    f, w, zurueck = geschuetzt(hb, a.seit, bool(a.zurueckhalten and a.seit))
    fehler += f
    warnungen += w
    if a.zurueckhalten:   # immer schreiben (auch leer): Der Workflow liest die Datei nach dem Zustellen
        with open(a.zurueckhalten, 'w', encoding='utf-8', newline='\n') as datei:
            datei.write(''.join(p + '\n' for p in sorted(zurueck)))

    for t in warnungen:
        if t.startswith('ZURUECK:'):   # zurückgehalten: als Fehler zeigen, hält aber nur den Bereich an
            print(('::error::' if AUF_GITHUB else 'FEHLER: ') + t[len('ZURUECK:'):])
            continue
        print(('::warning::' if AUF_GITHUB else 'WARNUNG: ') + t)
    for t in fehler:
        print(('::error::' if AUF_GITHUB else 'FEHLER: ') + t)
    for p in neu_geschrieben:
        print('Erneuert: %s' % p)
    print('Prüfung: %s (%d geänderte Dateien).' % ('%d Fehler' % len(fehler) if fehler else 'bestanden' + (
        ', zurückgehalten: %s' % ', '.join(sorted(zurueck)) if zurueck else ''), len(dateien)))
    print('Lernpaket betroffen: %s' % (('ja (%s)' % ', '.join(p.rsplit('/', 1)[-1] for p in pakete)) if pakete else 'nein'))
    return 1 if fehler else 0


if __name__ == '__main__':
    sys.exit(main())
