"""
unterrichtsmaterial.test.py - prüft Namensregel und Steckbrief (unterrichtsmaterial.py) und den Paketvergleich (kette-pruefen.py).
Aufruf im Projektordner (am Mac python3 statt python):  python .claude/gemeinsam/scripts/unterrichtsmaterial.test.py
Arbeitet nur im Speicher und in einem temporären Ordner, im Projekt wird nichts geändert.
"""
import importlib.util
import os
import shutil
import sys
import tempfile
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
FEHLER = []


def modul(name):
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location(name.replace('-', '_'), os.path.join(HERE, name + '.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def pruefe(ok, text):
    print(('  ok      ' if ok else '  FEHLER  ') + text)
    if not ok:
        FEHLER.append(text)


def main():
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            pass
    m = modul('unterrichtsmaterial')
    k = modul('kette-pruefen')

    print('Namensregel')
    pruefe(m.namensteil('prüfen, Messen & Lehren') == 'Pruefen-Messen-Lehren', 'namensteil: Umlaute, Trennzeichen, erstes Zeichen groß')
    fach = m.faecher()[0]
    gut = {'klasse': (fach['klassen'] or ['ALLE10'])[0], 'fach': fach['kuerzel'], 'abschnitt': 'BW2', 'thema': 'Toleranzen-1-Pruefen-Messen-Lehren'}
    pruefe(m.pruefen(gut) == [], 'gültiger Steckbrief ohne Meldung')
    for feld, wert in (('klasse', '10'), ('klasse', 'mgf10'), ('fach', 'Gibt-es-nicht'), ('fach', 'XYZ9'), ('abschnitt', 'B1'),
                       ('abschnitt', 'Blockwoche-1'), ('thema', 'kleines-thema'), ('thema', 'Thema_mit_Strich'), ('thema', 'Thema mit Leerzeichen')):
        pruefe(len(m.pruefen(dict(gut, **{feld: wert}))) >= 1, 'abgelehnt: %s "%s"' % (feld, wert))
    for a in ('BW12', 'LS3', 'M-3D-Druck', 'R-Toleranzen'):
        pruefe(m.pruefen(dict(gut, abschnitt=a)) == [], 'Abschnitt %s gültig' % a)
    pruefe(m.paketname(gut) == '%s_%s_BW2_Toleranzen-1-Pruefen-Messen-Lehren_scorm.zip' % (gut['klasse'], gut['fach']), 'Paketname aus dem Steckbrief')
    pruefe(m.paketpfad(gut) == 'BYCS-SYNC/Pakete/%s/%s/%s' % (gut['klasse'], gut['fach'], m.paketname(gut)), 'Paket liegt im Unterordner je Klasse und Fach')
    zurueck = m.aus_paketname(m.paketpfad(gut))
    pruefe(zurueck and all(zurueck[f] == gut[f] for f in m.FELDER), 'Paketname zurück zum Steckbrief')
    pruefe(m.aus_paketname('kaputt_scorm.zip') is None, 'Paketname ohne vier Felder: nicht lesbar')
    pruefe(m.ausbildungsjahr('MGF10') == '1. Jahr' and m.ausbildungsjahr('BFS11') == '2. Jahr' and m.ausbildungsjahr('ALLE') == 'alle Jahrgänge', 'Ausbildungsjahr aus der Klasse')
    pruefe(m.klassenname('ALLE') == 'Alle Klassen' and m.klassenname('ALLE10') == 'Alle 10. Klassen' and m.klassenname('MGF10') == 'Klasse MGF10', 'Klassenname fürs Handbuch')
    pruefe(m.art('Test-Bohren') == 'Test' and m.art('Bohren-Quiz') == 'Quiz' and m.art('Bohren-1') == 'E-Learning', 'Art aus dem Ordnernamen')
    pruefe(m.kursdatei('Unterricht/ALLE10/PuG/Kurs-ALLE10-PuG.json') == 'BYCS-SYNC/Kurse/ALLE10/PuG/Kurs-ALLE10-PuG.mbz', 'Kursdatei heißt wie der Kursplan, im Unterordner Klasse/Fach')
    pruefe(m.kursdatei('Unterricht/ALLE10/Kurs-ALLE10.json') == 'BYCS-SYNC/Kurse/ALLE10/Kurs-ALLE10.mbz', 'Kurs über mehrere Fächer: Unterordner Klasse')
    pruefe(m.kursdatei('Kurs-Probe.json') == 'BYCS-SYNC/Kurse/Kurs-Probe.mbz', 'Kursplan an anderem Ort: direkt in Kurse/')
    pruefe(m.ist_kursplan('Unterricht/MGF10/Kurs-MGF10.json') and not m.ist_kursplan('Unterricht/MGF10/LF1/BW1/Kurs-x.json'), 'Kursplan liegt in Klasse oder Fach')
    pruefe(m.kursplan_fehler('Unterricht/ALLE/BerHan/Kurs-ALLE-BerHan-3D-Druck.json') == [] and m.kursplan_fehler('Unterricht/MGF10/Kurs-MGF10.json') == [], 'Kursname nach Ort, Zusatz erlaubt')
    pruefe(m.kursplan_fehler('Unterricht/ALLE10/PuG/Kurs-PuG10.json') and m.kursplan_fehler('Unterricht/ALLE10/PuG/Kurs-ALLE10-PuG-26-27.json') and m.kursplan_fehler('Unterricht/ALLE10/PuG/Kurs-ALLE10-PuG-2026.json'), 'falscher Name und Jahreszahl: Fehler')
    try:
        m.aus_pfad(os.path.join(m.ROOT, 'Unterricht', 'ALLE10', 'Eth'))
        pruefe(False, 'zu kurzer Pfad abgelehnt')
    except m.UnterrichtsmaterialFehler:
        pruefe(True, 'zu kurzer Pfad abgelehnt')
    sb = m.aus_pfad(os.path.join(m.ROOT, 'Unterricht', 'ALLE10', 'Eth', 'BW1', 'Thema', 'bilder', 'a.png'))
    pruefe(sb['ordner'] == 'Unterricht/ALLE10/Eth/BW1/Thema' and sb['thema'] == 'Thema', 'Steckbrief aus einer Datei im Themenordner')

    print('Steckbrief in der Seite')
    for nl in ('\n', '\r\n'):
        seite = nl.join(['<!doctype html>', '<!-- TEMPLATE: <title> ersetzen, <meta name="klasse" content="FALSCH"> -->', '<html><head>',
                         '<meta charset="utf-8">', '<title>Prüfen &amp; Messen</title>', '</head><body></body></html>', ''])
        neu = m.in_seite(seite, gut)
        pruefe(m.aus_seite(neu) == gut, 'geschrieben und gelesen (%s)' % ('CRLF' if nl == '\r\n' else 'LF'))
        pruefe(m.in_seite(neu, gut) == neu, 'zweimal schreiben ändert nichts')
        anders = m.in_seite(neu, dict(gut, abschnitt='BW3'))
        pruefe(m.aus_seite(anders)['abschnitt'] == 'BW3' and anders.count('name="abschnitt"') == 1 and len(anders) == len(neu), 'vorhandene Zeile wird ersetzt')
        pruefe('content="FALSCH"' in neu and neu.index('name="thema"') < neu.index('<title>Prüfen'), 'Kommentar bleibt, Steckbrief steht vor <title>')
        pruefe(m.titel(neu) == 'Prüfen & Messen', 'Titel aus <title>, nicht aus dem Kommentar')

    print('Lernpaket erkennen')
    liste = '<!-- VERSIONEN: neueste oben\r\nV1.3 | 11.11.2026 | Commit folgt | Neu\r\nV1.2 | 01.11.2026 | Commit abc1234 | Alt\r\n-->'
    pruefe(m.stand(liste) == 'V1.3 | 11.11.2026 | Commit folgt | Neu', 'neueste Zeile der Änderungsliste')
    pruefe(m.stand('<!-- VERSIONEN: neueste oben\n-->') == '' and m.stand('<html></html>') == '', 'ohne Version: kein Lernpaket')
    pruefe(m.paket_quelle(m.paketpfad(gut)) == 'Unterricht/' + '/'.join(gut[f] for f in m.FELDER) and m.paket_quelle('x.zip') is None, 'Themenordner aus dem Paketnamen')

    print('Paket und Quelle')
    tmp = tempfile.mkdtemp(prefix='unterrichtsmaterial-test-')
    try:
        k.ROOT = tmp
        os.makedirs(os.path.join(tmp, 'q', 'bilder'))
        with open(os.path.join(tmp, 'q', 'index.html'), 'wb') as f:
            f.write(b'<html><head>\r\n<title>x</title>\r\n</head></html>\r\n')
        with open(os.path.join(tmp, 'q', 'bilder', 'a.png'), 'wb') as f:
            f.write(b'\x89PNG')

        def packe(seite, mehr=()):
            with zipfile.ZipFile(os.path.join(tmp, 'p.zip'), 'w') as z:
                z.writestr('imsmanifest.xml', '<manifest><resources><resource href="index.html"/></resources></manifest>')
                z.writestr('scorm-api.js', 'x')
                z.writestr('index.html', seite)
                z.writestr('bilder/a.png', b'\x89PNG')
                for n in mehr:
                    z.writestr(n, 'x')
        packe(b'<html><head>\n<title>x</title>\n<script src="scorm-api.js"></script>\n</head></html>\n')
        pruefe(k.paket_abweichungen('p.zip', 'q')[0] == [], 'gleich trotz eingebundener scorm-api.js und anderem Zeilenende')
        packe(b'<html><head>\n<title>y</title>\n<script src="scorm-api.js"></script>\n</head></html>\n')
        pruefe('index.html' in ''.join(k.paket_abweichungen('p.zip', 'q')[0]), 'geänderte Seite erkannt')
        packe(b'<html><head>\n<title>x</title>\n<script src="scorm-api.js"></script>\n</head></html>\n', ['alt.png'])
        pruefe('alt.png (nur im Paket)' in ''.join(k.paket_abweichungen('p.zip', 'q')[0]), 'überzählige Datei im Paket erkannt')
        with open(os.path.join(tmp, 'q', 'neu.png'), 'wb') as f:
            f.write(b'1')
        pruefe('neu.png (fehlt im Paket)' in ''.join(k.paket_abweichungen('p.zip', 'q')[0]), 'neue Datei in der Quelle erkannt')
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print('%d Fehler.' % len(FEHLER) if FEHLER else 'Alle Prüfungen bestanden.')
    return 1 if FEHLER else 0


if __name__ == '__main__':
    sys.exit(main())
