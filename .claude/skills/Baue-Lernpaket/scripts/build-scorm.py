"""
build-scorm.py - baut aus einem E-Learning-Ordner ein SCORM-2004-Paket (ZIP) für die ByCS Lernplattform.
Aufruf (im Projektordner, am Mac python3 statt python):
  python .claude/skills/Baue-Lernpaket/scripts/build-scorm.py --source "Unterricht/MGF10/LF1/BW2/<Thema>" --aenderung "Erste Fassung"
Name, Ablageort und Titel des Pakets werden nie eingetippt: Klasse, Fach, Abschnitt und Thema kommen aus dem Ablageort
(Unterricht/<Klasse>/<Fach>/<Abschnitt>/<Thema>/, Regeln in .claude/gemeinsam/scripts/unterrichtsmaterial.py), der Titel aus <title> der Startdatei.
Ergebnis: BYCS-SYNC/Pakete/<Klasse>/<Fach>/<Klasse>_<Fach>_<Abschnitt>_<Thema>_scorm.zip, im Projektordner NUR auf GitHub.
Auf jedem anderen Rechner landet das ZIP im Temp-Ordner (unterrichtsmaterial.gebaut), nie im Repo: Lernpakete entstehen nur über GitHub
(nach dem Push bauen und in den Teamordner zustellen, der ByCS-Link bleibt gleich). Lokal zählen nur Prüfung, Version und Änderungsliste.
Der Quellordner wird nicht verändert, außer Steckbrief (<meta name="klasse|fach|abschnitt|thema">), Version und Änderungsliste
in der Startdatei (unterrichtsmaterial.py, version.py, vor dem Kopieren):
--aenderung "Tippfehler in Aufgabe 2 korrigiert" beschreibt die neue Version (Pflicht, sobald sich das E-Learning seit der
letzten committeten Version geändert hat), --major erzwingt eine Hauptversion (sonst automatisch bei geänderten Aufgaben/Bewertung).
--nur-packen schreibt nichts in die Quelle (Bau ohne Eingaben, z. B. auf einem Server): Steckbrief und Version müssen schon stimmen.
Bestehensgrenze 70 ist in imsmanifest.xml und scorm-api.js festgelegt.
Nur Python-Standardbibliothek (Windows und Mac).
"""
import argparse
import hashlib
import importlib.util
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.parse
import xml.dom.minidom
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(HERE))))   # scripts -> Skill -> skills -> .claude -> Projektordner
TPL_DIR = os.path.join(os.path.dirname(HERE), 'templates')


class BauFehler(Exception):
    pass


def warn(msg):
    print('WARNUNG: ' + msg)


def _modul(name, pfad):   # Modul aus einer Datei laden (geht auch mit python -I)
    sys.dont_write_bytecode = True   # kein __pycache__ im Skill-Ordner
    spec = importlib.util.spec_from_file_location(name, pfad)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _version_modul():
    return _modul('version', os.path.join(HERE, 'version.py'))


unterrichtsmaterial = _modul('unterrichtsmaterial', os.path.join(ROOT, '.claude', 'gemeinsam', 'scripts', 'unterrichtsmaterial.py'))


UML = [('ä', 'ae'), ('ö', 'oe'), ('ü', 'ue'), ('Ä', 'Ae'), ('Ö', 'Oe'), ('Ü', 'Ue'), ('ß', 'ss')]


def get_slug(s):
    s = s.lower()
    for a, b in UML[:3] + UML[6:]:
        s = s.replace(a, b)
    s = re.sub(r'[^a-z0-9]+', '-', s).strip('-')
    if len(s) > 40:
        s = s[:40].strip('-')
    return s


def get_file_name_part(s):   # wie get_slug, aber Groß-/Kleinschreibung bleibt und nichts wird gekürzt
    for a, b in UML:
        s = s.replace(a, b)
    return re.sub(r'[^A-Za-z0-9]+', '-', s).strip('-')


def get_title_part(s):   # Namensteil aus dem Titel: Schreibweise bleibt, höchstens 40 Zeichen wie get_slug
    s = get_file_name_part(s)
    if len(s) > 40:
        s = s[:40].strip('-')
    return s


def set_first_upper(s):   # erstes Wort im Datei- oder Ordnernamen groß
    return s[:1].upper() + s[1:] if s else s


def xml_escape(s):
    return (s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
             .replace('"', '&quot;').replace("'", '&apos;'))


def get_href(rel):
    return '/'.join(urllib.parse.quote(p, safe='') for p in rel.split('/'))


def lesen(path):
    with open(path, 'rb') as f:
        return f.read().decode('utf-8-sig')


def schreiben(path, text):
    with open(path, 'wb') as f:
        f.write(text.encode('utf-8'))


def bauen(source, start='index.html', aenderung='', major=False, nur_packen=False):
    start = start.replace('\\', '/')
    src = os.path.abspath(source)
    start_quelle = os.path.join(src, *start.split('/'))
    if not os.path.isfile(start_quelle):
        raise BauFehler("Startdatei '%s' nicht im Quellordner gefunden." % start)

    # Name, Ablageort und Titel: aus dem Steckbrief (Ablageort)
    try:
        sb = unterrichtsmaterial.aus_pfad(src)
    except unterrichtsmaterial.UnterrichtsmaterialFehler as e:
        raise BauFehler(str(e))
    fehler = unterrichtsmaterial.pruefen(sb)
    if fehler:
        raise BauFehler('%s passt nicht zur Namensregel: %s' % (sb['ordner'], ' '.join(fehler)))
    if os.path.normcase(os.path.join(unterrichtsmaterial.ROOT, *sb['ordner'].split('/'))) != os.path.normcase(src):
        raise BauFehler('--source muss der Themenordner sein: %s' % sb['ordner'])
    if nur_packen:
        if any(unterrichtsmaterial.aus_seite(lesen(start_quelle)).get(f) != sb[f] for f in unterrichtsmaterial.FELDER):
            raise BauFehler('Der Steckbrief in %s passt nicht zum Ablageort. Erst ohne --nur-packen bauen.' % start)
    else:
        try:
            unterrichtsmaterial.schreibe_steckbrief(src, start)
        except unterrichtsmaterial.UnterrichtsmaterialFehler as e:
            raise BauFehler(str(e))
    title = unterrichtsmaterial.titel(lesen(start_quelle))
    if not title or re.match(r'\[.*\]$', title):
        raise BauFehler('Die Startdatei hat keinen Titel (<title>): Er wird der Name des Pakets in der ByCS.')
    ident = 'SCORM-' + '-'.join(sb[f] for f in unterrichtsmaterial.FELDER)
    zip_rel = unterrichtsmaterial.paketpfad(sb)

    # 0. Version und Änderungsliste in der Startdatei der Quelle pflegen (Anzeige "V1.3" im Benennungsfeld, Kommentar VERSIONEN)
    version = _version_modul()
    if nur_packen:
        ver = version.lesen_stand(start_quelle)
        if not ver:
            raise BauFehler('Die Startdatei hat noch keine Version. Erst ohne --nur-packen bauen.')
    else:
        try:
            ver = version.pflegen(start_quelle, aenderung, major)
        except version.VersionFehler as e:
            raise BauFehler(str(e))
    ver_text = 'V%s vom %s, Commit %s' % (ver['Version'], ver['Datum'], ver['Commit'])
    print('Version: %s%s: %s' % (ver_text, (' (neue Hauptversion)' if ver['Haupt'] else ' (neue Version)') if ver['Neu'] else '', ver['Text']))
    if ver['Haupt']:
        warn('V%s ist eine Hauptversion (Aufgaben oder Bewertung geändert): nicht mitten in einer Bearbeitungsphase hochladen, laufende Versuche können durcheinanderkommen.' % ver['Version'])

    # 1. Kopie anlegen (Quelle bleibt sonst unverändert)
    work = tempfile.mkdtemp(prefix='scorm_')
    try:
        shutil.copytree(src, work, dirs_exist_ok=True)
        for n in ('imsmanifest.xml', 'scorm-api.js'):
            p = os.path.join(work, n)
            if os.path.isfile(p):
                os.remove(p)
        shutil.copy2(os.path.join(TPL_DIR, 'scorm-api.js'), os.path.join(work, 'scorm-api.js'))

        # 2. scorm-api.js in die Startdatei einbinden (falls noch nicht geschehen)
        start_path = os.path.join(work, *start.split('/'))
        html = lesen(start_path)
        prefix = '../' * (len(start.split('/')) - 1)
        if not re.search(r'<script[^>]+src\s*=\s*["\'][^"\']*scorm-api\.js', html, re.I):
            tag = '<script src="' + prefix + 'scorm-api.js"></script>'
            if not re.search(r'</head>', html, re.I):
                raise BauFehler('Startdatei hat kein </head>: scorm-api.js kann nicht eingebunden werden.')
            html = re.sub(r'</head>', lambda _: tag + '\r\n</head>', html, count=1, flags=re.I)
            schreiben(start_path, html)
        def has(pat):   # Suche ohne Groß-/Kleinschreibung
            return re.search(pat, html, re.I) is not None
        if has(r'window.ScormReport'):
            if has(r'quality: true'):
                n_ok = len(re.findall(r'\sdata-(?:ok|keys|score)[\s=>]', html))
                print('Hinweis: Dokument aus Fachunterricht.html/Allgemeinbildung.html erkannt - meldet je Aufgabe bearbeitet/offen, Bewertung und Antwort (Moodle-Bericht "Interaktionen"). Felder mit hinterlegter Lösung: %d.' % n_ok)
                if has(r'submit: true'):
                    print('Hinweis: Mit Abgabe-Button (ein Versuch). Abgeschlossen, Punkte (40/40/20) und bestanden ab 70 erst nach der Abgabe. In Moodle: Anzahl der Versuche 1, Neuen Versuch erzwingen Nein, Nach dem letzten Versuch sperren Nein.')
                if has(r'tasks: taskInfo'):
                    n_w = len(re.findall(r'\sdata-gewicht\s*=', html))
                    print('Hinweis: Punkte je Aufgabe im Moodle-Bericht "Ziele" (je Niveau und je Aufgabe, Option Punkte anzeigen); Kennungen wie Aufgabe-1.1_Einsteiger_10P. Aufgaben mit eigenem Gewicht (data-gewicht): %d.' % n_w)
                else:
                    print('Hinweis: Älterer Stand der Vorlage: Im Bericht "Ziele" stehen nur die Punkte je Niveau, nicht je Aufgabe. Für Punkte je Aufgabe den Script-Block aus der aktuellen .claude/gemeinsam/templates/Fachunterricht.html übernehmen.')
                if n_ok == 0:
                    warn('Keine Aufgabe hat eine hinterlegte Lösung (data-ok / data-keys): Punkte = nur Bearbeitungsstand, keine Bewertung.')
            elif has(r'partial: true'):
                warn('Das Dokument nutzt eine ältere Vorlage: Es meldet nur den Bearbeitungsstand, keine Bewertung und keine Antworten im Bericht. Für Bewertung den Script-Block aus der aktuellen .claude/gemeinsam/templates/Fachunterricht.html übernehmen.')
            else:
                warn('Das Dokument nutzt noch die alte Vorlage (ohne Punktemeldung): Moodle bekommt KEINE Punkte. Bitte auf die aktuelle .claude/gemeinsam/templates/Fachunterricht.html umbauen.')
        else:
            if not has(r'ScormReport.answer'):
                warn('Die Startdatei ruft ScormReport.answer nicht auf: es werden KEINE Punkte gemeldet.')
            if not has(r'ScormReport.init'):
                warn('Die Startdatei ruft ScormReport.init nicht auf: SCORM wird nicht gestartet.')

        # 3. Dateiliste und Manifest
        files = []
        for d, _, fs in os.walk(work):
            for f in fs:
                rel = os.path.relpath(os.path.join(d, f), work).replace(os.sep, '/')
                if rel != 'imsmanifest.xml':
                    files.append(rel)
        files.sort(key=lambda s: (s.lower(), s))
        file_lines = '\r\n'.join('      <file href="' + xml_escape(get_href(f)) + '"/>' for f in files)
        manifest = lesen(os.path.join(TPL_DIR, 'imsmanifest.xml'))
        manifest = manifest.replace('{{IDENTIFIER}}', xml_escape(ident))
        manifest = manifest.replace('{{TITLE}}', xml_escape(title))
        manifest = manifest.replace('{{START_FILE}}', xml_escape(get_href(start)))
        manifest = manifest.replace('{{FILES}}', file_lines)
        manifest = manifest.replace('{{VERSION}}', re.sub(r'-{2,}', '-', ver_text))   # steht in einem XML-Kommentar: kein --
        try:
            xml.dom.minidom.parseString(manifest.encode('utf-8'))   # Fehler, wenn das XML nicht wohlgeformt ist
        except Exception as e:
            raise BauFehler('imsmanifest.xml ist kein gültiges XML: %s' % e)
        schreiben(os.path.join(work, 'imsmanifest.xml'), manifest)

        # 4. ZIP schreiben (Pfade mit /, imsmanifest.xml zuerst)
        zip_path = unterrichtsmaterial.gebaut(zip_rel)   # nur auf GitHub im Projektordner, sonst im Temp-Ordner
        os.makedirs(os.path.dirname(zip_path), exist_ok=True)
        if os.path.exists(zip_path):
            os.remove(zip_path)
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
            for rel in ['imsmanifest.xml'] + files:
                z.write(os.path.join(work, *rel.split('/')), rel)

        # 5. Prüfen
        with zipfile.ZipFile(zip_path) as z:
            names = z.namelist()
            if names[0] != 'imsmanifest.xml':
                raise BauFehler('imsmanifest.xml liegt nicht ganz oben im ZIP.')
            if start not in names:
                raise BauFehler('Startdatei fehlt im ZIP.')
            if 'scorm-api.js' not in names:
                raise BauFehler('scorm-api.js fehlt im ZIP.')
            for f in files:
                if f not in names:
                    raise BauFehler('Im Manifest, aber nicht im ZIP: %s' % f)
            if any('\\' in n for n in names):
                raise BauFehler('ZIP enthält Backslashes in Pfaden.')
            for e in names:
                if re.search(r'\.(html?|css|js)$', e) and 'scorm-api' not in e:
                    t = z.read(e).decode('utf-8', 'replace')
                    if re.search(r'(src|href)\s*=\s*["\']https?://', t, re.I):
                        warn('Externer Verweis in %s: bitte prüfen (muss offline laufen).' % e)
            print('OK: %d Dateien, Manifest oben, Startdatei und scorm-api.js vorhanden.' % len(names))

        print(zip_path)
        return zip_path
    finally:
        shutil.rmtree(work, ignore_errors=True)


def main(argv=None):
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            pass
    ap = argparse.ArgumentParser(description='SCORM-2004-Paket für die ByCS Lernplattform bauen.')
    ap.add_argument('--source', required=True, help='Themenordner mit dem E-Learning (Unterricht/<Klasse>/<Fach>/<Abschnitt>/<Thema>)')
    ap.add_argument('--start', default='index.html', help='Startdatei (Standard: index.html)')
    ap.add_argument('--aenderung', default='', help='was sich geändert hat (für die Änderungsliste)')
    ap.add_argument('--major', action='store_true', help='Hauptversion erzwingen')
    ap.add_argument('--nur-packen', action='store_true', help='nichts in die Quelle schreiben (Steckbrief und Version müssen stimmen)')
    a = ap.parse_args(argv)
    try:
        bauen(a.source, a.start, a.aenderung, a.major, a.nur_packen)
    except BauFehler as e:
        print('FEHLER: %s' % e)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
