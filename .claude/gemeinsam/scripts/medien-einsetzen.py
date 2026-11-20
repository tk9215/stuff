"""
medien-einsetzen.py - eingebettete Bilder (data:-Adressen) aus einer Quelldatei auflisten, ablegen und in eine Zielseite einsetzen,
ohne dass jemand base64-Text liest oder abtippt.

Aufruf (im Projektordner, am Mac python3 statt python):
  python .claude/gemeinsam/scripts/medien-einsetzen.py --liste <quelle.html>
        Nummer, Typ, Größe und Umgebung (id, alt, Überschrift davor, Variablenname) jedes eingebetteten Mediums
  python ... --einsetzen <quelle.html> <ziel.html>
        ersetzt in der Zielseite jeden Platzhalter  nils-medium:<Nummer>  (z. B. <img src="nils-medium:12" alt="...">)
        durch die data:-Adresse Nummer <Nummer> der Quelle
  python ... --ablegen <quelle.html> <Nummer> <Datei>
        speichert Medium <Nummer> als Datei (z. B. Ressourcen/Bilder/Kugelsortiervorrichtung/Gesamtzeichnung.jpg)
  python ... --datei <Datei> <ziel.html> <Platzhalter>
        ersetzt den Platzhalter (z. B. bild:schriftfeld) in der Zielseite durch die Datei als data:-Adresse (svg, png, jpg)
Nummern zählen ab 1 in der Reihenfolge in der Quelldatei. Nur Python-Standardbibliothek.
"""
import argparse
import base64
import html
import mimetypes
import os
import re
import sys

DATA = re.compile(r'data:([a-z]+/[a-z0-9.+-]+)(;[a-z0-9=;-]+)?;base64,([A-Za-z0-9+/=]{100,})')


def lesen(p):
    with open(p, 'rb') as f:
        raw = f.read()
    return raw.decode('utf-8-sig'), raw.startswith(b'\xef\xbb\xbf')


def medien(s):
    return [(m.start(), m.end(), m.group(1), m.group(0)) for m in DATA.finditer(s)
            if not m.group(1).startswith('font/') and 'woff' not in m.group(1)]


def umgebung(s, a):
    vor = s[max(0, a - 1500):a]
    tag = s[s.rfind('<', 0, a):a][:300]
    info = []
    for attr in ('id', 'alt', 'class', 'title'):
        m = re.search(r'\s%s="([^"]{1,60})"' % attr, tag)
        if m:
            info.append('%s="%s"' % (attr, m.group(1)))
    nach = s[a:a + 400]
    m = re.search(r'(?:alt|title)="([^"]{1,60})"', DATA.sub('', nach[:0]) + s[a:s.find('>', a) + 200] if s.find('>', a) > 0 else '')
    js = re.search(r"(?:\[\s*\d+\s*,\s*'([^']{1,40})'\s*,\s*'?$)|(\w+)\s*[:=]\s*['\"]?$", vor[-120:])
    if js:
        info.append('js=' + (js.group(1) or js.group(2)))
    h = re.findall(r'<h[23][^>]*>(.*?)</h[23]>', vor, re.S)
    if h:
        info.append('nach "%s"' % html.unescape(re.sub(r'<[^>]+>', '', h[-1])).strip()[:50])
    return ' '.join(info)


def main(argv=None):
    for st in (sys.stdout, sys.stderr):
        try:
            st.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            pass
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--liste', metavar='QUELLE')
    g.add_argument('--einsetzen', nargs=2, metavar=('QUELLE', 'ZIEL'))
    g.add_argument('--ablegen', nargs=3, metavar=('QUELLE', 'NUMMER', 'DATEI'))
    g.add_argument('--datei', nargs=3, metavar=('DATEI', 'ZIEL', 'PLATZHALTER'))
    a = ap.parse_args(argv)

    if a.liste:
        s, _ = lesen(a.liste)
        for i, (st, en, mime, _) in enumerate(medien(s), 1):
            print('%3d  %-14s %7.1f KB  %s' % (i, mime, (en - st) * 0.75 / 1024, umgebung(s, st)))
        return 0
    if a.ablegen:
        s, _ = lesen(a.ablegen[0])
        n = int(a.ablegen[1])
        m = medien(s)[n - 1]
        os.makedirs(os.path.dirname(os.path.abspath(a.ablegen[2])), exist_ok=True)
        with open(a.ablegen[2], 'wb') as f:
            f.write(base64.b64decode(m[3].split('base64,', 1)[1]))
        print('Medium %d (%s) gespeichert: %s' % (n, m[2], a.ablegen[2]))
        return 0
    if a.einsetzen:
        q, _ = lesen(a.einsetzen[0])
        z, bom = lesen(a.einsetzen[1])
        liste = medien(q)

        def ers(m):
            n = int(m.group(1))
            if not 1 <= n <= len(liste):
                raise SystemExit('FEHLER: nils-medium:%d gibt es nicht (Quelle hat %d Medien)' % (n, len(liste)))
            return liste[n - 1][3]
        neu, k = re.subn(r'nils-medium:(\d+)', ers, z)
        with open(a.einsetzen[1], 'wb') as f:
            f.write((b'\xef\xbb\xbf' if bom else b'') + neu.encode('utf-8'))
        print('%d Platzhalter ersetzt in %s' % (k, a.einsetzen[1]))
        return 0
    if a.datei:
        d, ziel, ph = a.datei
        mime = 'image/svg+xml' if d.lower().endswith('.svg') else (mimetypes.guess_type(d)[0] or 'application/octet-stream')
        with open(d, 'rb') as f:
            uri = 'data:%s;base64,%s' % (mime, base64.b64encode(f.read()).decode('ascii'))
        z, bom = lesen(ziel)
        k = z.count(ph)
        if not k:
            raise SystemExit('FEHLER: Platzhalter %s nicht in %s' % (ph, ziel))
        with open(ziel, 'wb') as f:
            f.write((b'\xef\xbb\xbf' if bom else b'') + z.replace(ph, uri).encode('utf-8'))
        print('%d-mal %s eingesetzt (%d KB)' % (k, ph, len(uri) * 3 // 4096))
        return 0


if __name__ == '__main__':
    sys.exit(main())
