"""
paket-zustellen.py - baut, was abgeleitet ist, und schickt alles, was in den Teamordner BYCS-SYNC gehört, an den Flow
(Power Automate), der es dort ablegt. In Git liegen nur die Quellen:
  - Lernpakete: aus dem Themenordner gebaut (build-scorm.py --nur-packen)       -> Pakete/<Klasse>/<Fach>/…_scorm.zip
  - Kurse: aus Unterricht/<Klasse>[/<Fach>]/Kurs-….json gebaut (build-mbz.py)       -> Kurse/<Klasse>[/<Fach>]/Kurs-….mbz
  - Test-Ordner (Unterricht/**/Test-<Thema>/: Test-.mbz, Fragen-XML, Anleitung, Vorschau.html, so wie in Git)
                                                                              -> Tests/<gleicher Pfad wie unter Unterricht/>
  - das Handbuch (#Handbuch.html, so wie in Git)                              -> ganz oben
Läuft auf GitHub nach jedem Push auf main (.github/workflows/paket-zustellen.yml, "Bauen und zustellen"). Kein Rechner
kopiert selbst in den Teamordner.
Aufruf (im Projektordner, am Mac python3 statt python):
  python .claude/skills/Baue-Lernpaket/scripts/paket-zustellen.py <Was> [weitere …]
      <Was>: Themenordner "Unterricht/<Klasse>/<Fach>/<Abschnitt>/<Thema>", Test-Ordner "Unterricht/…/Test-<Thema>",
             Kurs (Pfad des Kursplans oder sein Name wie Kurs-ALLE10-PuG, "Kurse" für alle Kurse), "Handbuch", oder "alle"
  --seit <Commit>   alles, was sich seit diesem Commit geändert hat (so ruft es der Workflow auf)
  --ohne <Datei>    zurückgehaltene Ordner und Dateien (aus pruefen.py --zurueckhalten) auslassen, dazu jeden Kurs,
                    der etwas davon mitliefert
  --alle      alle Lernpakete, Kurse, Test-Ordner und das Handbuch (z. B. nach einer Änderung an scorm-api.js)
  --probe     legt alles unter <Bereich>/_Pilot/… ab statt am echten Ort (nichts in der ByCS wird berührt; Handbuch: Pakete/_Pilot/)
  --trocken   nur bauen und zeigen, was geschickt würde
Reihenfolge: Lernpakete, dann Kurse (ein Kurs braucht den Download-Link eines neuen Pakets: Der entsteht erst, wenn das
Paket im Teamordner liegt, deshalb wird bis zu 5 Minuten nachgefragt), dann Tests und Handbuch.
Ein Kurs wird neu gebaut, wenn sich sein Kursplan geändert hat, eine Datei, die er ohne Link nennt (Banner, Test-.mbz,
Dateien, mitgelieferte Lernpakete), oder das Bauskript. Lernpakete mit Link holt Moodle selbst: kein Neubau.
Adresse und Schlüssel des Flows kommen aus der Umgebung (FLOW_URL, FLOW_SCHLUESSEL: GitHub-Secrets), die Linkseite aus
BYCS_LINKSEITE; nie aus dem Repo und nie in die Ausgabe. Der Flow nimmt in Pakete/, Kurse/ und Tests/ (samt Unterordnern)
nur .html, .mbz, .xml und _scorm.zip an, ganz oben nur das Handbuch, und ersetzt eine vorhandene Datei an Ort und Stelle
(der Download-Link bleibt gleich). Der Flow löscht nie: Was im Repo gelöscht oder umbenannt wird, bleibt im Teamordner
liegen, bis es dort jemand löscht.
Nur Python-Standardbibliothek.
"""
import argparse
import base64
import contextlib
import hashlib
import importlib.util
import io
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
KURSBAU = os.path.join(HERE, '..', '..', 'Baue-Kurs', 'scripts', 'build-mbz.py')
KOPF = 'X-B2-Schluessel'
PROBE = '_Pilot'
BEREICHE = ('Pakete', 'Kurse', 'Tests')              # so heißen die Ordner im Teamordner
ENDUNGEN = ('.html', '.mbz', '.xml', '_scorm.zip')   # nur das nimmt der Flow an
HANDBUCH = '#Handbuch.html'
KURSBAU_REL = '.claude/skills/Baue-Kurs/scripts/build-mbz.py'
LINK_WARTEN = 5   # Minuten, die ein Kurs auf den Download-Link eines neuen Pakets wartet


def _modul(name, pfad):
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location(name, pfad)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _git(unterrichtsmaterial, *args):
    """Einträge einer git-Ausgabe mit -z. None, wenn Git scheitert (z. B. unbekannter Commit)."""
    r = subprocess.run(['git', '-c', 'core.quotePath=false'] + list(args), cwd=unterrichtsmaterial.ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if r.returncode != 0:
        return None
    return [p for p in r.stdout.decode('utf-8', 'replace').split('\0') if p]


def geaendert(unterrichtsmaterial, seit):
    """Alle seit dem Commit geänderten oder neuen Dateien. None, wenn Git den Commit nicht kennt."""
    return _git(unterrichtsmaterial, 'diff', '--name-only', '-z', '--diff-filter=ACMR', seit, 'HEAD')


def lernpakete_geaendert(unterrichtsmaterial, liste):
    """Themenordner mit Lernpaket, in denen sich etwas geändert hat."""
    ordner = {'/'.join(p.split('/')[:5]) for p in liste if p.startswith(unterrichtsmaterial.ORDNER + '/') and len(p.split('/')) > 5}
    return sorted(ordner & set(unterrichtsmaterial.lernpakete()))


def kursplaene(unterrichtsmaterial):
    return unterrichtsmaterial.kursplaene()


def kurs_quellen(unterrichtsmaterial, kurs):
    """Dateien und Themenordner, von denen ein Kurs abhängt (Pfade ab Projektordner, Ordner mit / am Ende)."""
    plan = json.loads(unterrichtsmaterial.lesen(os.path.join(unterrichtsmaterial.ROOT, *kurs.split('/'))))
    quellen = {kurs}
    eintraege = list(plan.get('allgemein', [])) + [e for a in plan.get('abschnitte', []) for e in a.get('dateien', [])]
    banner = (plan.get('kurs') or {}).get('banner')
    for d, mit_link in [(banner, False)] + [(e.get('datei', ''), bool(e.get('link'))) for e in eintraege]:
        d = (d or '').replace('\\', '/')
        if not d:
            continue
        if d.startswith('BYCS-SYNC/Pakete/'):
            q = unterrichtsmaterial.paket_quelle(d)
            if q and not mit_link:   # mitgeliefertes Paket: steckt im Kurs, Änderung braucht Neubau
                quellen.add(q + '/')
        else:
            quellen.add(d)
    return quellen


def kurse_geaendert(unterrichtsmaterial, liste):
    """Kurse (Pfad des Kursplans), die neu gebaut werden müssen, weil sich eine ihrer Quellen geändert hat."""
    alle = KURSBAU_REL in liste
    kurse = []
    for kurs in kursplaene(unterrichtsmaterial):
        try:
            quellen = kurs_quellen(unterrichtsmaterial, kurs)
        except (OSError, ValueError):
            kurse.append(kurs)   # kaputter Plan: der Bau meldet den Fehler
            continue
        if alle or any(p in quellen or any(q.endswith('/') and p.startswith(q) for q in quellen) for p in liste):
            kurse.append(kurs)
    return kurse


def gehalten(p, zurueck):
    """True, wenn die Datei oder der Ordner p (mit / am Ende) zurückgehalten ist oder Zurückgehaltenes enthält."""
    return any(p == h or (h.endswith('/') and p.startswith(h)) or (p.endswith('/') and h.startswith(p)) for h in zurueck)


def ohne_zurueckgehaltene(unterrichtsmaterial, themen, kurse, dateien, zurueck):
    """(themen, kurse, dateien, ausgelassen) ohne Zurückgehaltenes. Ein Kurs bleibt weg, wenn eine seiner Quellen
    (Kursplan, Banner, mitgelieferte Pakete, Dateien) zurückgehalten ist: Er würde sie sonst mit ausliefern."""
    if not zurueck:
        return themen, kurse, dateien, []

    def kurs_gehalten(kurs):
        try:
            return any(gehalten(q, zurueck) for q in kurs_quellen(unterrichtsmaterial, kurs))
        except (OSError, ValueError):
            return gehalten(kurs, zurueck)

    weg = [t for t in themen if gehalten(t.strip().strip('/') + '/', zurueck)]
    weg += [k for k in kurse if kurs_gehalten(k)]
    weg += [p for p in dateien if gehalten(p, zurueck)]
    return ([t for t in themen if t not in weg], [k for k in kurse if k not in weg],
            [p for p in dateien if p not in weg], weg)


def ziel(zip_pfad, probe=False):
    """(pfad, datei) für den Flow aus dem Ort des Pakets: …/BYCS-SYNC/Pakete/<Klasse>/<Fach>/<Name>_scorm.zip."""
    teile = os.path.abspath(zip_pfad).replace('\\', '/').split('/')
    klasse, fach, datei = teile[-3:]
    if teile[-5:-3] != ['BYCS-SYNC', 'Pakete'] or not datei.endswith('_scorm.zip'):
        raise ValueError('Kein Lernpaket unter BYCS-SYNC/Pakete/<Klasse>/<Fach>/: %s' % zip_pfad)
    return '/'.join(['Pakete'] + ([PROBE] if probe else []) + [klasse, fach]), datei


def ziel_kurs(unterrichtsmaterial, kurs, probe=False):
    """(pfad, datei) für den Flow aus dem Kursplan: Kurse/<Klasse>[/<Fach>]/Kurs-….mbz, wie der Ort unter Unterricht/."""
    teile = unterrichtsmaterial.kursdatei(kurs).split('/')[1:]   # ohne BYCS-SYNC
    if probe:
        teile.insert(1, PROBE)
    return '/'.join(teile[:-1]), teile[-1]


def ziel_datei(rel, probe=False, wurzel='Unterricht'):
    """(pfad, datei) für eine Datei aus Git (Test-Ordner, Handbuch). None, wenn sie nicht in den Teamordner gehört."""
    teile = rel.split('/')
    if rel == HANDBUCH:
        return ('Pakete/' + PROBE if probe else ''), HANDBUCH
    if teile[0] == wurzel and any(t.startswith('Test-') for t in teile[1:-1]):
        ordner = ['Tests'] + teile[1:-1]
        if probe:
            ordner.insert(1, PROBE)
        return '/'.join(ordner), teile[-1]
    return None


def erlaubt(pfad, datei):
    """Dieselben Regeln wie im Flow, damit ein Fehler schon hier und mit Namen gemeldet wird."""
    if '..' in pfad or '\\' in pfad or '/' in datei or '\\' in datei or '..' in datei:
        return False
    if not pfad:
        return datei.endswith('Handbuch.html')
    return pfad.split('/')[0] in BEREICHE and datei.endswith(ENDUNGEN)


def git_dateien(unterrichtsmaterial, liste=None, wuensche=None):
    """Dateien aus Git für den Teamordner (Test-Ordner, Handbuch): aus der Liste geänderter Dateien oder aus Git."""
    if liste is None:
        liste = _git(unterrichtsmaterial, 'ls-files', '-z', '--', *(wuensche or [HANDBUCH, ':(glob)%s/**/Test-*/**' % unterrichtsmaterial.ORDNER])) or []
    return sorted(p for p in liste if ziel_datei(p, wurzel=unterrichtsmaterial.ORDNER))


def einordnen(unterrichtsmaterial, wunsch):
    """('kurs'|'datei'|'thema', Pfad) für einen Eintrag von Hand."""
    w = wunsch.strip().replace('\\', '/').strip('/')
    if w.lower() in ('handbuch', 'handbuch.html', HANDBUCH.lower()):
        return 'datei', HANDBUCH
    kurse = kursplaene(unterrichtsmaterial)
    if w.lower() in ('kurse', 'bycs-sync/kurse', unterrichtsmaterial.ORDNER.lower() + '/kurse'):
        return 'kurse', ''
    for k in kurse:
        if w in (k, k.rsplit('/', 1)[-1], unterrichtsmaterial.kursname(k)):
            return 'kurs', k
    if any(t.startswith('Test-') for t in w.split('/')):
        return 'datei', w
    return 'thema', w


def schicken(url, schluessel, pfad, datei, inhalt):
    daten = json.dumps({'pfad': pfad, 'datei': datei, 'inhalt': base64.b64encode(inhalt).decode('ascii')}).encode('utf-8')
    req = urllib.request.Request(url, data=daten, method='POST',
                                 headers={'Content-Type': 'application/json', KOPF: schluessel})
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            return r.status, r.read(500).decode('utf-8', 'replace')
    except urllib.error.HTTPError as e:
        return e.code, e.read(500).decode('utf-8', 'replace')
    except urllib.error.URLError as e:   # die Adresse nie ausgeben
        return 0, 'Flow nicht erreichbar (%s)' % type(e.reason).__name__


def kurs_bauen(kursbau, kurs, warten):
    """Baut einen Kurs und prüft ihn. Fehlt ein Download-Link (neues Paket), bis zu LINK_WARTEN Minuten nachfragen.
    Rückgabe: (Pfad der .mbz oder None, Meldung)."""
    for versuch in range(LINK_WARTEN + 1 if warten else 1):
        aus = io.StringIO()
        try:
            with contextlib.redirect_stdout(aus):
                mbz = kursbau.bauen_aus_plan(kurs)
                ok = kursbau.pruefen(mbz) == 0
        except SystemExit as e:
            text = str(e.code)
            if 'noch keinen Download-Link' in text and versuch < LINK_WARTEN and warten:
                print('Warte auf den Download-Link eines neuen Pakets (%d/%d Minuten) …' % (versuch + 1, LINK_WARTEN))
                time.sleep(60)
                continue
            if 'noch keinen Download-Link' in text:
                text += ' Den Lauf in etwa 10 Minuten wiederholen (Re-run jobs).'
            return None, text
        if not ok:
            return None, 'Die Prüfung der Kurssicherung ist nicht bestanden:\n' + aus.getvalue()
        return mbz, aus.getvalue().strip().splitlines()[0] if aus.getvalue().strip() else ''
    return None, 'unerwartet'


def main(argv=None):
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            pass
    ap = argparse.ArgumentParser(description='Lernpakete und Kurse bauen und mit Test-Ordnern und Handbuch an den Flow für den Teamordner schicken.')
    ap.add_argument('was', nargs='*', help='Themenordner, Test-Ordner, Kurs (Name wie Kurs-ALLE10-PuG), Kurse, Handbuch oder alle')
    ap.add_argument('--seit', help='alles, was sich seit diesem Commit geändert hat')
    ap.add_argument('--alle', action='store_true', help='alle Lernpakete, Kurse, Test-Ordner und das Handbuch')
    ap.add_argument('--probe', action='store_true', help='unter <Bereich>/%s/ ablegen statt am echten Ort' % PROBE)
    ap.add_argument('--trocken', action='store_true', help='nur bauen, nichts schicken')
    ap.add_argument('--ohne', metavar='DATEI', help='zurückgehaltene Pfade auslassen (aus pruefen.py --zurueckhalten)')
    a = ap.parse_args(argv)

    url = os.environ.get('FLOW_URL', '').strip()
    schluessel = os.environ.get('FLOW_SCHLUESSEL', '').strip()
    if not a.trocken and not (url and schluessel):
        print('FEHLER: FLOW_URL oder FLOW_SCHLUESSEL fehlt (GitHub: Settings > Environments > zustellung).')
        return 1

    bau = _modul('build_scorm', os.path.join(HERE, 'build-scorm.py'))
    unterrichtsmaterial = bau.unterrichtsmaterial
    wuensche = [w for w in a.was if w.lower() != 'alle']
    if a.alle or len(wuensche) < len(a.was):
        themen, kurse, dateien = unterrichtsmaterial.lernpakete(), kursplaene(unterrichtsmaterial), git_dateien(unterrichtsmaterial)
    elif a.seit:
        liste = geaendert(unterrichtsmaterial, a.seit)
        if liste is None:
            print('FEHLER: Den Commit %s kennt Git hier nicht (z. B. nach einem erzwungenen Push). '
                  'Das Geänderte von Hand zustellen (Werkzeug-Verantwortliche): Actions > "Bauen und zustellen" > Run workflow.' % a.seit)
            return 1
        themen, kurse, dateien = lernpakete_geaendert(unterrichtsmaterial, liste), kurse_geaendert(unterrichtsmaterial, liste), git_dateien(unterrichtsmaterial, liste)
    else:
        themen, kurse, dateien = [], [], []
        for w in wuensche:
            art, p = einordnen(unterrichtsmaterial, w)
            if art == 'kurse':
                kurse += kursplaene(unterrichtsmaterial)
            elif art == 'kurs':
                kurse.append(p)
            elif art == 'datei':
                gefunden = git_dateien(unterrichtsmaterial, wuensche=[p])
                if not gefunden:
                    print('FEHLER: Unter "%s" liegt in Git nichts für den Teamordner (Test-Ordner, Handbuch).' % p)
                    return 1
                dateien += gefunden
            else:
                themen.append(p)
        kurse = sorted(set(kurse))
    if a.ohne:
        try:
            with open(a.ohne, encoding='utf-8') as f:
                zurueck = {z.strip() for z in f if z.strip()}
        except OSError:
            zurueck = set()
        themen, kurse, dateien, weg = ohne_zurueckgehaltene(unterrichtsmaterial, themen, kurse, dateien, zurueck)
        if weg:
            print('Zurückgehalten (pruefen.py, nicht zugestellt): %s' % ', '.join(weg))
    if not (themen or kurse or dateien):
        print('Nichts für den Teamordner geändert: nichts zuzustellen.')
        return 0
    fehler = 0

    def zustellen(pfad, datei, inhalt):
        """Schickt eine Datei. Gibt 1 bei einem Fehler zurück, sonst 0."""
        print('Ziel: %s (%d Bytes, SHA-256 %s)' % ('/'.join(t for t in (pfad, datei) if t), len(inhalt), hashlib.sha256(inhalt).hexdigest()))
        if not erlaubt(pfad, datei):
            print('FEHLER: Das nimmt der Flow nicht an (nur .html, .mbz, .xml und _scorm.zip in Pakete/, Kurse/ und Tests/).')
            return 1
        if a.trocken:
            print('Trocken: nichts geschickt.')
            return 0
        status, antwort = schicken(url, schluessel, pfad, datei, inhalt)
        if status == 200:
            print('Zugestellt (Antwort 200).')
            return 0
        print('FEHLER: Der Flow antwortet mit %s: %s' % (status or 'keiner Verbindung', antwort.strip()))
        return 1

    if themen:
        print('%d Lernpaket(e): %s' % (len(themen), ', '.join(t.strip().strip('/').rsplit('/', 1)[-1] for t in themen)))
    for ordner in themen:
        ordner = ordner.strip().strip('/')
        print('== %s' % ordner)
        try:
            zip_pfad = bau.bauen(os.path.join(unterrichtsmaterial.ROOT, *ordner.split('/')), nur_packen=True)
            pfad, datei = ziel(zip_pfad, a.probe)
        except (bau.BauFehler, ValueError) as e:
            print('FEHLER: %s' % e)
            fehler += 1
            continue
        with open(zip_pfad, 'rb') as f:
            fehler += zustellen(pfad, datei, f.read())

    if kurse:
        print('%d Kurs(e): %s' % (len(kurse), ', '.join(unterrichtsmaterial.kursname(k) for k in kurse)))
        kursbau = _modul('build_mbz', os.path.abspath(KURSBAU))
    for kurs in kurse:
        print('== %s' % kurs)
        mbz, meldung = kurs_bauen(kursbau, kurs, warten=bool(themen) and not a.trocken)
        if mbz is None:
            print('FEHLER: %s' % meldung)
            fehler += 1
            continue
        print(meldung)
        with open(mbz, 'rb') as f:
            fehler += zustellen(*ziel_kurs(unterrichtsmaterial, kurs, a.probe), f.read())

    if dateien:
        print('%d Datei(en) aus Git (Tests, Handbuch)' % len(dateien))
    for rel in dateien:
        print('== %s' % rel)
        pfad, datei = ziel_datei(rel, a.probe, unterrichtsmaterial.ORDNER)
        if not datei.endswith(ENDUNGEN):   # z. B. ein Bild im Test-Ordner: kein Fehler, aber sagen
            print('HINWEIS: nicht zugestellt, diese Endung nimmt der Flow nicht an.')
            continue
        try:
            with open(os.path.join(unterrichtsmaterial.ROOT, *rel.split('/')), 'rb') as f:
                inhalt = f.read()
        except OSError as e:
            print('FEHLER: %s' % e)
            fehler += 1
            continue
        fehler += zustellen(pfad, datei, inhalt)
    return 1 if fehler else 0


if __name__ == '__main__':
    sys.exit(main())
