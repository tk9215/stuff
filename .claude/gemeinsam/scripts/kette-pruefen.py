"""
kette-pruefen.py - prüft, ob die Kette Ablageort -> Steckbrief -> Lernpaket -> Kursplan zusammenpasst.
Aufruf im Projektordner (am Mac python3 statt python):
  python .claude/gemeinsam/scripts/kette-pruefen.py            alles prüfen (Rückgabe 1 bei Fehlern)
  python .claude/gemeinsam/scripts/kette-pruefen.py <Ordner>   nur diese Themenordner
  python .claude/gemeinsam/scripts/kette-pruefen.py --zugestellt [<Ordner>]   Teamordner mit den Quellen vergleichen
  Nur geänderte Dateien prüfen (vor dem Commit und auf GitHub): .claude/gemeinsam/scripts/pruefen.py (ruft pruefe_dateien auf)
Geprüft wird (Regeln in unterrichtsmaterial.py):
  1. Ablage: Alles in Unterricht/ liegt in einem Themenordner Unterricht/<Klasse>/<Fach>/<Abschnitt>/<Thema>/, die vier Namen
     folgen der Namensregel, das Fach steht in faecher.txt. Ausnahmen: Kurspläne (Kurs-….json in Klasse oder Fach), Unterricht/Offen/ (Angaben offen).
  2. Steckbrief: Die index.html eines E-Learnings nennt in <meta name="klasse|fach|abschnitt|thema"> ihren Ablageort.
  3. Paket: Ein Lernpaket ist jeder Themenordner, dessen index.html eine Version trägt. Die Pakete selbst liegen nicht in Git:
     GitHub baut sie nach dem Push aus der Quelle und stellt sie in den Teamordner zu. Geprüft wird darum, dass ein
     geändertes Lernpaket neu gebaut wurde (neue Zeile in der Änderungsliste, Skill Baue-Lernpaket).
     --zugestellt vergleicht den Teamordner mit den Quellen (nach dem Push, wenn OneDrive fertig ist): Lernpakete,
     Test-Ordner und Handbuch Byte für Byte mit dem Stand in Git, Kurse nur, ob sie da und neuer als ihr Kursplan sind.
  4. Kursplan: Unterricht/<Klasse>[/<Fach>]/Kurs-<Klasse>[-<Fach>][-<Zusatz>].json nennt nur Dateien, die es gibt, heißt nach seinem Ort
     und enthält kein Kennwort (Tests im Kurs behalten den Platzhalter "Bitte_neu_vergeben").
  5. In Git liegen weder Lernpakete noch Kurssicherungen (BYCS-SYNC/ ist ganz in .gitignore): Beides baut GitHub.
     Am Rechner gibt es kein BYCS-SYNC/ im Projektordner (lokale Bauten landen im Temp-Ordner).
Nur Python-Standardbibliothek (Windows und Mac).
"""
import importlib.util
import json
import os
import re
import subprocess
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))


def _modul(name, pfad):
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location(name, pfad)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


unterrichtsmaterial = _modul('unterrichtsmaterial', os.path.join(HERE, 'unterrichtsmaterial.py'))
ROOT = unterrichtsmaterial.ROOT
MUELL = ('.DS_Store', 'Thumbs.db', 'desktop.ini', '.gitkeep')
TEXT = ('.html', '.htm', '.js', '.css', '.svg', '.txt', '.json', '.xml', '.md', '.csv')
SCORM_API = '.claude/skills/Baue-Lernpaket/templates/scorm-api.js'
HANDBUCH = '#Handbuch.html'
ENDUNGEN_FLOW = ('.html', '.mbz', '.xml', '_scorm.zip')   # nur das nimmt der Flow im Teamordner an
RX_API_TAG = re.compile(rb'<script src="(?:\.\./)*scorm-api\.js"></script>\r?\n?')


def _abs(rel):
    return os.path.join(ROOT, *rel.split('/'))


def _dateien(rel):   # alle Dateien unter rel, mit / und ab rel
    liste = []
    for d, ordner, fs in os.walk(_abs(rel)):
        ordner[:] = [o for o in ordner if o != '__pycache__']
        for f in fs:
            if f not in MUELL:
                liste.append(os.path.relpath(os.path.join(d, f), _abs(rel)).replace(os.sep, '/'))
    return sorted(liste)


def _gleich(name, a, b):   # Inhalt gleich; bei Textdateien zählt das Zeilenende nicht (Windows/Mac)
    if a == b:
        return True
    return name.lower().endswith(TEXT) and a.replace(b'\r\n', b'\n') == b.replace(b'\r\n', b'\n')


def paket_abweichungen(zip_rel, ordner_rel):
    """Vergleicht ein Lernpaket mit seinem Themenordner. Rückgabe: (Fehler, Hinweise)."""
    fehler, hinweise = [], []
    try:
        with zipfile.ZipFile(zip_rel if os.path.isabs(zip_rel) else _abs(zip_rel)) as z:
            inhalt = {n: z.read(n) for n in z.namelist() if not n.endswith('/')}
    except (OSError, zipfile.BadZipFile):
        return ['%s ist kein lesbares ZIP.' % zip_rel], []
    manifest = inhalt.get('imsmanifest.xml', b'').decode('utf-8', 'replace')
    m = re.search(r'<resource\b[^>]*\bhref="([^"?]+)', manifest)
    start = m.group(1) if m else 'index.html'
    quelle = [f for f in _dateien(ordner_rel) if f not in ('imsmanifest.xml', 'scorm-api.js')]
    anders = []
    for f in quelle:
        if f not in inhalt:
            anders.append(f + ' (fehlt im Paket)')
            continue
        with open(os.path.join(_abs(ordner_rel), *f.split('/')), 'rb') as h:
            daten = h.read()
        im_paket = inhalt[f]
        if f == start and not RX_API_TAG.search(daten):   # der Bau bindet scorm-api.js in die Kopie ein
            im_paket = RX_API_TAG.sub(b'', im_paket, count=1)
        if not _gleich(f, daten, im_paket):
            anders.append(f)
    for f in sorted(set(inhalt) - set(quelle) - {'imsmanifest.xml', 'scorm-api.js'}):
        anders.append(f + ' (nur im Paket)')
    if anders:
        fehler.append('%s passt nicht mehr zur Quelle %s (%s). Paket neu bauen (Skill Baue-Lernpaket).'
                      % (zip_rel, ordner_rel, ', '.join(anders[:4]) + (' und %d weitere' % (len(anders) - 4) if len(anders) > 4 else '')))
    if os.path.isfile(_abs(SCORM_API)):
        with open(_abs(SCORM_API), 'rb') as h:
            if not _gleich('x.js', h.read(), inhalt.get('scorm-api.js', b'')):
                hinweise.append('%s: mit einer älteren scorm-api.js gebaut (beim nächsten Bau wird sie erneuert).' % zip_rel)
    return fehler, hinweise


def themenordner():
    """Alle Ordner in Unterricht/ mit Dateien: (Themenordner ab Projektordner, Fehlermeldungen)."""
    neu, falsch = set(), []
    for f in _dateien('Unterricht') if os.path.isdir(_abs('Unterricht')) else []:
        t = f.split('/')
        if t[0] in unterrichtsmaterial.SONDERORDNER or unterrichtsmaterial.ist_kursplan('Unterricht/' + f):
            continue
        if len(t) < 5:
            falsch.append('Unterricht/%s liegt in keinem Themenordner. Schema: Unterricht/<Klasse>/<Fach>/<Abschnitt>/<Thema>/' % f)
        else:
            neu.add('Unterricht/' + '/'.join(t[:4]))
    return sorted(neu), falsch


def pruefe_ordner(rel):
    """Ein Themenordner im neuen Schema: Namen, Steckbrief, Paket. Rückgabe: (Fehler, Hinweise)."""
    fehler, hinweise = [], []
    sb = unterrichtsmaterial.aus_pfad(_abs(rel))
    namen = unterrichtsmaterial.pruefen(sb)
    fehler += ['%s: %s' % (rel, t) for t in namen]
    seite = os.path.join(_abs(rel), 'index.html')
    if os.path.isfile(seite) and unterrichtsmaterial.art(sb['thema']) not in ('Test', 'Quiz'):
        text = unterrichtsmaterial.lesen(seite)
        ist = unterrichtsmaterial.aus_seite(text)
        if 'name="loesung-hash"' in text or ist:   # Seite aus einer unserer Vorlagen
            if not namen and any(ist.get(f) != sb[f] for f in unterrichtsmaterial.FELDER):
                fehler.append('%s/index.html: Der Steckbrief %s. Schreiben mit: python .claude/gemeinsam/scripts/unterrichtsmaterial.py "%s" --schreiben'
                              % (rel, 'passt nicht zum Ablageort' if ist else 'fehlt', rel))
    return fehler, hinweise


def ist_lernpaket(rel):
    seite = os.path.join(_abs(rel), 'index.html')
    return os.path.isfile(seite) and bool(unterrichtsmaterial.stand(unterrichtsmaterial.lesen(seite)))


def pruefe_gebaut(rel, alt='HEAD', neu=None):
    """Ein geändertes Lernpaket braucht eine neue Zeile in der Änderungsliste. alt: Commit vorher; neu: Commit nachher,
    None = Arbeitsstand (vor dem Commit). Rückgabe: Fehler."""
    def zeile(ref):
        if ref is None:
            p = os.path.join(_abs(rel), 'index.html')
            return unterrichtsmaterial.stand(unterrichtsmaterial.lesen(p)) if os.path.isfile(p) else None
        try:
            r = subprocess.run(['git', 'show', ref + ':' + rel + '/index.html'], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        except OSError:
            return None
        return unterrichtsmaterial.stand(r.stdout.decode('utf-8-sig', 'replace')) if r.returncode == 0 else None
    jetzt, vorher = zeile(neu), zeile(alt)
    if jetzt and vorher and jetzt == vorher:
        return ['%s: Das Lernpaket ist geändert, aber nicht neu gebaut (die Version %s stand schon vorher in der Seite). '
                'Neu bauen (Skill Baue-Lernpaket), sonst bekommen die Schülerinnen und Schüler eine Änderung ohne neue Version.'
                % (rel, jetzt.split(' | ')[0])]
    return []


def pruefe_zugestellt(ordner=None):
    """Vergleicht die Pakete im Teamordner mit den Quellen. Rückgabe: (Fehler, Hinweise)."""
    linkseite = _modul('linkseite', os.path.join(HERE, 'linkseite.py'))
    team = linkseite.teamordner()
    if not team:
        return ['Teamordner BYCS-SYNC nicht gefunden (Einrichtung: .claude/gemeinsam/regeln/einrichtung.md).'], []
    fehler, hinweise = [], []
    for rel in ordner or unterrichtsmaterial.lernpakete():
        paket = unterrichtsmaterial.paketpfad(unterrichtsmaterial.aus_pfad(_abs(rel)))
        z = os.path.join(team, *paket.split('/')[1:])
        if not os.path.isfile(z):
            fehler.append('%s: noch nicht im Teamordner (%s).' % (rel, '/'.join(paket.split('/')[1:])))
            continue
        f, h = paket_abweichungen(z, rel)
        fehler += [t.replace(' Paket neu bauen (Skill Baue-Lernpaket).', ' Im Teamordner liegt ein anderer Stand: gepusht? GitHub-Lauf grün? OneDrive fertig?') for t in f]
        hinweise += h
    if ordner:
        return fehler, hinweise
    # Test-Ordner und Handbuch liegen in Git: Im Teamordner muss der Stand des letzten Commits liegen (verglichen mit Git,
    # nicht mit der Arbeitskopie; bei Textdateien zählt das Zeilenende nicht, ältere Kopien vom Rechner haben CRLF).
    for p in _git('ls-files', '-z', '--', HANDBUCH, ':(glob)%s/**/Test-*/**' % unterrichtsmaterial.ORDNER):
        if not p.lower().endswith(ENDUNGEN_FLOW):
            continue   # nimmt der Flow nicht an (z. B. Bilder)
        ziel = HANDBUCH if p == HANDBUCH else 'Tests/' + p.split('/', 1)[1]
        z = os.path.join(team, *ziel.split('/'))
        if not os.path.isfile(z):
            fehler.append('%s: noch nicht im Teamordner (%s).' % (p, ziel))
            continue
        r = subprocess.run(['git', 'show', 'HEAD:' + p], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        with open(z, 'rb') as h:
            if not _gleich(p, h.read(), r.stdout):
                fehler.append('%s: Im Teamordner (%s) liegt ein anderer Stand: gepusht? GitHub-Lauf grün? OneDrive fertig?' % (p, ziel))
    # Kurse: Jeder Bau ergibt eine andere Datei (Zeitstempel). Geprüft wird nur, ob sie da und neuer als der Kursplan ist.
    for plan in kursplaene():
        ziel = unterrichtsmaterial.kursdatei(plan).split('/', 1)[1]
        z = os.path.join(team, *ziel.split('/'))
        r = subprocess.run(['git', 'log', '-1', '--format=%ct', '--', plan], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        geaendert = int(r.stdout.strip() or 0)
        if not os.path.isfile(z):
            fehler.append('%s: Kurs noch nicht im Teamordner (%s).' % (plan, ziel))
        elif os.path.getmtime(z) + 60 < geaendert:
            fehler.append('%s: Die Kurssicherung im Teamordner (%s) ist älter als der letzte Commit am Kursplan: gepusht? GitHub-Lauf grün?' % (plan, ziel))
    return fehler, hinweise


def pruefe_kursplan(rel):
    fehler = []
    try:
        plan = json.loads(unterrichtsmaterial.lesen(_abs(rel)))
    except ValueError as e:
        return ['%s: kein gültiges JSON (%s).' % (rel, e)]
    kurs = plan.get('kurs') or {}
    fehler += unterrichtsmaterial.kursplan_fehler(rel)
    eintraege = list(plan.get('allgemein', [])) + [e for a in plan.get('abschnitte', []) for e in a.get('dateien', [])]
    dateien = [e.get('datei', '') for e in eintraege] + ([kurs['banner']] if kurs.get('banner') else [])
    for d in dateien:
        if not d or re.match(r'^([A-Za-z]:|/|\\)', d):
            fehler.append('%s: "%s" ist kein Pfad ab dem Projektordner (z. B. BYCS-SYNC/... oder Unterricht/...).' % (rel, d))
        elif not os.path.isfile(_abs(d.replace('\\', '/'))):
            quelle = unterrichtsmaterial.paket_quelle(d) if d.replace('\\', '/').startswith('BYCS-SYNC/Pakete/') else None
            if quelle and ist_lernpaket(quelle) and d.replace('\\', '/') == unterrichtsmaterial.paketpfad(unterrichtsmaterial.aus_pfad(_abs(quelle))):
                continue   # Lernpakete liegen nicht in Git: Der Kursbau baut sie aus der Quelle
            fehler.append('%s: Die Datei %s gibt es nicht%s.' % (rel, d, ' (kein Lernpaket unter %s)' % quelle if quelle else ''))
    if any(e.get('passwort') for e in eintraege):
        fehler.append('%s: Ein Kennwort steht im Kursplan. Das Feld "passwort" gibt es nicht mehr: Tests im Kurs behalten den '
                      'Platzhalter "Bitte_neu_vergeben", das echte Kennwort vergibt die Lehrkraft nach dem Wiederherstellen in der ByCS.' % rel)
    return fehler


def kursplaene():
    return unterrichtsmaterial.kursplaene()


def _git(*args):
    try:
        r = subprocess.run(['git', '-c', 'core.quotePath=false'] + list(args), cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    except OSError:
        return []
    return [z for z in r.stdout.decode('utf-8', 'replace').split('\0') if z]


def pruefe(ordner=None, plaene=None):
    """Alles (ohne Angaben) oder nur das Genannte. Rückgabe: (Fehler, Hinweise)."""
    fehler, hinweise = [], []
    alles = ordner is None
    if alles:
        ordner, falsch = themenordner()
        fehler += falsch
        plaene = kursplaene()
    for o in ordner:
        f, h = pruefe_ordner(o)
        fehler += f
        hinweise += h
    for p in plaene or []:
        fehler += pruefe_kursplan(p)
    return fehler, hinweise


def in_git_verboten():
    """Lernpakete und Kurssicherungen liegen nie in Git (GitHub baut sie). Rückgabe: Fehler."""
    fehler = ['%s: gehört nicht in Git (GitHub baut es aus der Quelle). Herausnehmen: git rm --cached "%s"' % (p, p)
              for p in _git('ls-files', '-z', '--', 'BYCS-SYNC')]
    if os.environ.get('GITHUB_ACTIONS') != 'true' and os.path.isdir(os.path.join(unterrichtsmaterial.ROOT, 'BYCS-SYNC')):
        fehler.append('BYCS-SYNC/ liegt im Projektordner: Pakete und Kurse entstehen nur über GitHub. Den Ordner löschen '
                      '(alter Rest; lokale Bauten landen im Temp-Ordner).')
    return fehler


def pruefe_dateien(dateien, alt='HEAD', neu=None):
    """Prüft, was diese geänderten Dateien berühren (Pfade ab Projektordner). alt/neu wie bei pruefe_gebaut.
    Rückgabe: (Fehler, Lernpakete unter den geänderten Themenordnern)."""
    fehler = in_git_verboten()
    if any(p in (unterrichtsmaterial.FAECHER, '.claude/gemeinsam/scripts/unterrichtsmaterial.py') for p in dateien):
        f, _ = pruefe()   # Regel geändert: alles prüfen
        fehler += f
    ordner, plaene = set(), set()
    for p in dateien:
        t = p.split('/')
        if t[0] != unterrichtsmaterial.ORDNER or len(t) < 2:
            continue
        if unterrichtsmaterial.ist_kursplan(p):
            plaene.add(p)
        elif t[1] not in unterrichtsmaterial.SONDERORDNER:
            if len(t) < 6 and not os.path.isfile(_abs(p)):
                pass   # gelöschte Datei
            elif len(t) < 6:
                fehler.append('%s liegt in keinem Themenordner. Schema: Unterricht/<Klasse>/<Fach>/<Abschnitt>/<Thema>/' % p)
            else:
                ordner.add('/'.join(t[:5]))
    vorhanden = sorted(o for o in ordner if os.path.isdir(_abs(o)))
    plaene = sorted(p for p in plaene if os.path.isfile(_abs(p)))
    f, _ = pruefe(vorhanden, plaene)
    fehler += f
    pakete = [o for o in vorhanden if ist_lernpaket(o)]
    for o in pakete:
        fehler += pruefe_gebaut(o, alt, neu)
    return list(dict.fromkeys(fehler)), pakete


def main(argv=None):
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            pass
    argv = list(sys.argv[1:] if argv is None else argv)
    ordner = [a for a in argv if not a.startswith('--')]
    try:
        if '--zugestellt' in argv:
            fehler, hinweise = pruefe_zugestellt([unterrichtsmaterial.aus_pfad(o)['ordner'] for o in ordner] or None)
        elif ordner:
            fehler, hinweise = pruefe([unterrichtsmaterial.aus_pfad(o)['ordner'] for o in ordner], [])
        else:
            fehler, hinweise = pruefe()
            fehler += in_git_verboten()
    except unterrichtsmaterial.UnterrichtsmaterialFehler as e:
        print('FEHLER: %s' % e)
        return 1
    for t in hinweise:
        print('Hinweis: ' + t)
    for t in fehler:
        print('FEHLER: ' + t)
    print('Kette: %s' % ('alle Prüfungen bestanden.' if not fehler else '%d Fehler.' % len(fehler)))
    return 1 if fehler else 0


if __name__ == '__main__':
    sys.exit(main())
