"""
neue-seite.py - setzt eine Testvorbereitung aus der Vorlage Fachunterricht.html (Skill Baue-E-Learning) und dem
Baukasten templates/baukasten.html zusammen, oder erneuert den Baukasten in fertigen Seiten.

Aufruf im Projektordner (am Mac python3 statt python):
  python .claude/skills/Baue-Testvorbereitung/scripts/neue-seite.py Unterricht/<Klasse>/<Fach>/<Abschnitt>/<Thema>-Testvorbereitung
      legt dort index.html an (bricht ab, wenn es sie schon gibt): Vorlage ohne TEMPLATE-Kommentar, Passwort-Hash,
      Baukasten-Stil und -Script, Gerüst für Reiter, Kapitel und Thema. Danach läuft sync-vorlage.py --datei.
  python .claude/skills/Baue-Testvorbereitung/scripts/neue-seite.py --aktualisieren [Seite ...]
      erneuert die Blöcke Testvorbereitung:stil und :script aus dem Baukasten (ohne Angabe: alle Seiten in Unterricht/,
      die diese Blöcke haben). Inhalt (app, main, thema) bleibt unverändert. Danach Pakete neu bauen (Nebenversion).
Nur Python-Standardbibliothek.
"""
import argparse
import glob
import os
import re
import subprocess
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HIER)
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(SKILL)))
BAUKASTEN = os.path.join(SKILL, 'templates', 'baukasten.html')
ELEARN = os.path.join(ROOT, '.claude', 'gemeinsam')
FACH = os.path.join(ELEARN, 'templates', 'Fachunterricht.html')
PW = os.path.join(ELEARN, 'data', 'solution-password.txt')
SYNC = os.path.join(ELEARN, 'scripts', 'sync-vorlage.py')


def lesen(p):
    with open(p, encoding='utf-8-sig', newline='') as f:
        return f.read()


def schreiben(p, s):
    with open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(s)


def block(s, name, mit_markierung=True):
    a, e = '<!-- Testvorbereitung:%s -->' % name, '<!-- /Testvorbereitung:%s -->' % name
    i, j = s.find(a), s.find(e)
    if i < 0 or j < i:
        raise SystemExit('Block Testvorbereitung:%s nicht gefunden.' % name)
    return s[i:j + len(e)] if mit_markierung else s[i + len(a):j]


def genau_einmal(s, was, name):
    n = s.count(was)
    if n != 1:
        raise SystemExit('Vorlage: "%s" kommt %d-mal vor (erwartet 1): %s' % (was, n, name))


def neu(ziel):
    seite = os.path.join(ziel, 'index.html')
    if os.path.exists(seite):
        raise SystemExit('Gibt es schon: %s (nichts überschrieben).' % seite)
    bk, s = lesen(BAUKASTEN), lesen(FACH)
    s = s.replace('\r\n', '\n')
    # TEMPLATE-Kommentar entfernen
    s = re.sub(r'\A(<!doctype html>\n)<!--\s*TEMPLATE.*?-->\n', r'\1', s, count=1, flags=re.S | re.I)
    if 'TEMPLATE für jedes Dokument' in s:
        raise SystemExit('TEMPLATE-Kommentar nicht gefunden.')
    # Passwort-Hash
    if os.path.exists(PW):
        h = re.search(r'^hash=(\S+)', lesen(PW), re.M)
        if h:
            s = s.replace('<meta name="loesung-hash" content="">', '<meta name="loesung-hash" content="%s">' % h.group(1), 1)
    else:
        print('Hinweis: solution-password.txt fehlt, der Hash bleibt leer (Lehrkraft führt pw-hash.py selbst aus).')
    # Stil nach dem Kopf der Vorlage
    a = '<!-- /Fachunterricht.html:head -->'
    genau_einmal(s, a, 'head')
    s = s.replace(a, a + '\n' + block(bk, 'stil'), 1)
    # Gerüst statt des leeren <main>
    m = re.search(r'<main class="wrap">\s*<!-- content goes here -->\s*</main>', s)
    if not m:
        raise SystemExit('Leeres <main> der Vorlage nicht gefunden.')
    s = s[:m.start()] + block(bk, 'app') + '\n' + block(bk, 'main') + s[m.end():]
    # Script und Thema nach den Scripts der Vorlage
    a = '<!-- /Fachunterricht.html:scripts -->'
    genau_einmal(s, a, 'scripts')
    s = s.replace(a, a + '\n' + block(bk, 'script') + '\n' + block(bk, 'thema'), 1)
    os.makedirs(ziel, exist_ok=True)
    schreiben(seite, s)
    print('Angelegt: %s' % os.path.relpath(seite, ROOT))
    r = subprocess.run([sys.executable, SYNC, '--datei', seite, '--schreiben'], cwd=ROOT)
    if r.returncode:
        raise SystemExit('sync-vorlage.py meldet einen Fehler.')


def aktualisieren(seiten):
    bk = lesen(BAUKASTEN)
    if not seiten:
        seiten = [p for p in glob.glob(os.path.join(ROOT, 'Unterricht', '**', 'index.html'), recursive=True)
                  if '<!-- Testvorbereitung:script -->' in lesen(p)]
    for p in seiten:
        s = lesen(p)
        neu_s = s
        for name in ('stil', 'script'):
            neu_s = neu_s.replace(block(neu_s, name), block(bk, name), 1)
        if neu_s != s:
            schreiben(p, neu_s)
            print('aktualisiert: %s' % os.path.relpath(p, ROOT))
        else:
            print('schon aktuell: %s' % os.path.relpath(p, ROOT))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('ziel', nargs='*', help='Zielordner (neu) bzw. Seiten (--aktualisieren)')
    ap.add_argument('--aktualisieren', action='store_true')
    o = ap.parse_args()
    if o.aktualisieren:
        aktualisieren([os.path.abspath(p) for p in o.ziel])
    elif len(o.ziel) == 1:
        neu(os.path.abspath(o.ziel[0]))
    else:
        ap.error('genau einen Zielordner angeben')


if __name__ == '__main__':
    main()
