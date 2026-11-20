"""
sync-vorlage.py - überträgt die Vorlagenblöcke (Stil, Knopfleiste, Dialoge, Script) aus templates/Fachunterricht.html
in templates/Allgemeinbildung.html und in alle Seiten in Unterricht/. So funktionieren Bewertung, Abgabe, SCORM,
PDF-Export, Leerdruck, Hell/Dunkel und Lösungssperre überall gleich.

Aufruf (im Projektordner, am Mac python3 statt python):
  python .claude/gemeinsam/scripts/sync-vorlage.py               Probelauf: zeigt, was sich ändern würde
  python .claude/gemeinsam/scripts/sync-vorlage.py --schreiben   Seiten in Unterricht/ aktualisieren
  ... --datei Unterricht/.../index.html [--datei ...]                              nur diese Seiten (auch eine neue Seite)
  ... --diff                                                                   Unterschiede je Block zeigen
  ... --pruefen                                                                Exitcode 1, wenn eine Seite abweicht
  ... --vorlagen                                                               Fachunterricht.html -> Allgemeinbildung.html
Nach JEDER Änderung an Fachunterricht.html: erst --vorlagen, dann --schreiben (und die SCORM-Pakete neu bauen).
Nach dem Kopieren einer Vorlage für eine neue Seite: --datei <neue Seite> --schreiben (setzt u. a. die Schriften ein).

Blöcke:
  Fachunterricht.html:head|tools|modals|scripts   aus Fachunterricht.html (in jeder Seite)
  Allgemeinbildung.html:stil|script               aus Allgemeinbildung.html (nur Seiten im Layout "Lernschritte")
Seiten ohne Markierungen bekommen sie beim ersten Lauf (Blöcke über feste Ankertexte gefunden, sonst Abbruch für diese Seite).
Alles außerhalb der Blöcke bleibt Byte für Byte erhalten.

NILS-Schriften (Fachunterricht Technisches Zeichnen): Seiten mit <meta name="schrift" content="nils"> bekommen im
Platzhalter <style id="nils-schriften"></style> die Schriften aus Ressourcen/Schriften/NILS-Teilmenge-1.001 (base64)
und die Schriftzuweisung. In allen anderen Seiten und in den Vorlagen bleibt der Platzhalter leer.
Nur Python-Standardbibliothek (Windows und Mac).
"""
import argparse
import base64
import difflib
import glob
import os
import re
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HIER)
ROOT = os.path.dirname(os.path.dirname(SKILL))
TPL = os.path.join(SKILL, 'templates')
FACH = os.path.join(TPL, 'Fachunterricht.html')
ALLG = os.path.join(TPL, 'Allgemeinbildung.html')
SCHRIFTEN = os.path.join(ROOT, 'Ressourcen', 'Schriften', 'NILS-Teilmenge-1.001')

F_BLOECKE = ('head', 'tools', 'modals', 'scripts')
A_BLOECKE = ('stil', 'script')
PLATZHALTER = '<style id="nils-schriften"></style>'

# Schnitte: Datei, Familie, Gewicht, Stil
SCHNITTE = (
    ('NILSText-400-normal.woff', 'NILS Text', 400, 'normal'),
    ('NILSText-700-normal.woff', 'NILS Text', 700, 'normal'),
    ('NILSText-400-italic.woff', 'NILS Text', 400, 'italic'),
    ('NILSTextCondensed-400-normal.woff', 'NILS Text Condensed', 400, 'normal'),
    ('NILSTextCondensed-700-normal.woff', 'NILS Text Condensed', 700, 'normal'),
    ('NILSNormschrift-400-normal.woff', 'NILS Normschrift', 400, 'normal'),
)
ZUWEISUNG = (
    'body{font-family:"NILS Text",Arial,sans-serif}',
    'h1,h2,h3,table,.tb{font-family:"NILS Text Condensed","NILS Text",Arial,sans-serif}',
    '.chnum,.phnum,.score{font-family:"NILS Text Condensed","NILS Text",sans-serif}',
    'main svg text{font-family:"NILS Normschrift","NILS Text",sans-serif}',
    'main svg.text-normal text{font-family:inherit}',
    '@page{@bottom-right{font-family:"NILS Text",Arial,sans-serif}}',
)


class Fehler(Exception):
    pass


def lesen(path):
    with open(path, 'rb') as f:
        raw = f.read()
    bom = raw.startswith(b'\xef\xbb\xbf')
    return raw.decode('utf-8-sig'), bom


def eol_von(s):
    return '\r\n' if '\r\n' in s else '\n'


def norm(s, eol):
    return re.sub(r'\r?\n', eol, s)


def finde(s, what, start=0, name='', vor=False):
    i = s.find(what, start)
    if i < 0:
        raise Fehler('Ankertext für "%s" nicht gefunden: %s' % (name, what[:50]))
    return i


def genau_einmal(s, what, name):
    n = s.count(what)
    if n != 1:
        raise Fehler('Ankertext für "%s" steht %d-mal statt einmal: %s' % (name, n, what[:50]))
    return s.find(what)


def div_ende(s, start):
    """Ende (Index nach '</div>') des <div>, das bei start beginnt (verschachtelte divs mitgezählt)."""
    tief = 0
    for m in re.compile(r'<div\b|</div>').finditer(s, start):
        tief += 1 if m.group(0) != '</div>' else -1
        if tief == 0:
            return m.end()
    raise Fehler('Schließendes </div> nicht gefunden')


# ---------- Blöcke über Markierungen ----------

def markierung(datei, name):
    return '<!-- %s:%s -->' % (datei, name), '<!-- /%s:%s -->' % (datei, name)


def bereich_markiert(s, datei, name):
    """(Anfang, Ende) des Inhalts zwischen den Markierungen oder None."""
    op, cl = markierung(datei, name)
    i = s.find(op)
    if i < 0:
        return None
    j = s.find(cl, i)
    if j < 0 or s.find(op, i + 1) >= 0 or s.find(cl, j + 1) >= 0:
        raise Fehler('Markierung %s fehlt oder steht doppelt' % op)
    a = i + len(op)
    a += 2 if s.startswith('\r\n', a) else (1 if s.startswith('\n', a) else 0)
    e = j
    if s.endswith('\r\n', 0, e):
        e -= 2
    elif s.endswith('\n', 0, e):
        e -= 1
    return a, e


# ---------- Blöcke über Ankertexte (Seiten ohne Markierungen) ----------

def bereich_anker(s, name):
    if name == 'head':
        k = genau_einmal(s, "window.addEventListener('error'", 'head')
        a = s.rfind('<script>', 0, k)
        r = finde(s, ':root { --paper:', k, 'head')
        e = finde(s, '</style>', r, 'head') + len('</style>')
        if s.find('<style id="nils-schriften">', a, e + 200) >= 0:   # Platzhalter direkt danach gehört dazu
            p = s.find('<style id="nils-schriften">', a)
            e = finde(s, '</style>', p, 'head') + len('</style>')
        blk = s[a:e]
        if '@page' not in blk or 'Lösungssperre' not in blk and 'loesung' not in blk.lower():
            raise Fehler('Kopfblock sieht nicht wie die Vorlage aus')
        return a, e
    if name == 'tools':
        a = genau_einmal(s, '<div class="tools">', 'tools')
        e = finde(s, '</div>', a, 'tools') + len('</div>')
        if 'id="pdfBtn"' not in s[a:e]:
            raise Fehler('Knopfleiste ohne "Als PDF speichern"')
        return a, e
    if name == 'modals':
        m = genau_einmal(s, '<div class="modal" id="pwModal"', 'modals')
        a = s.rfind('<!--', 0, m)
        if a < 0 or s[a:m].count('-->') != 1 or len(s[a:m].strip()) > 200:
            a = m
        sm = genau_einmal(s, '<div class="modal" id="subModal"', 'modals')
        e = div_ende(s, sm)
        if 'subCancel' not in s[a:e] and 'subOk' not in s[a:e] and 'subModal' not in s[a:e]:
            raise Fehler('Dialoge unvollständig')
        return a, e
    if name == 'scripts':
        k = genau_einmal(s, '/* Minimaler PDF-Writer', 'scripts')
        a = s.rfind('<script>', 0, k)
        e1 = finde(s, '</script>', k, 'scripts') + len('</script>')
        m = re.compile(r'\s*<script>').match(s, e1)
        if not m:
            raise Fehler('Hauptscript folgt nicht direkt auf den PDF-Writer')
        e = finde(s, '</script>', m.end(), 'scripts') + len('</script>')
        blk = s[a:e]
        if 'function printBlank' not in blk or 'function makePdf' not in blk:
            raise Fehler('Hauptscript ohne printBlank/makePdf')
        return a, e
    if name == 'stil':
        k = genau_einmal(s, '/* Layout "Lernschritte": überschreibt', 'stil')
        a = s.rfind('<style>', 0, k)
        return a, finde(s, '</style>', k, 'stil') + len('</style>')
    if name == 'script':
        k = genau_einmal(s, '/* Layout "Lernschritte": Schritt-Leiste', 'script')
        a = s.rfind('<script>', 0, k)
        return a, finde(s, '</script>', k, 'script') + len('</script>')
    raise Fehler('Unbekannter Block ' + name)


def bloecke_aus(s, datei, namen):
    """Inhalt der Blöcke einer Vorlage (über Markierungen, sonst Ankertexte)."""
    out = {}
    for n in namen:
        b = bereich_markiert(s, datei, n)
        if b is None:
            b = bereich_anker(s, n)
        out[n] = s[b[0]:b[1]]
    return out


# ---------- Schriften ----------

_schrift_css = None


def schrift_css():
    global _schrift_css
    if _schrift_css is None:
        zeilen = ['<style id="nils-schriften">',
                  '/* NILS-Schriften 1.001 (Teilmenge aus den NILS-Skripten), eingesetzt von sync-vorlage.py aus '
                  'Ressourcen/Schriften/NILS-Teilmenge-1.001. NILS Text/Condensed: SIL Open Font License 1.1 (aus DINish); '
                  'NILS Normschrift: LGPL 3 mit Font-Ausnahme (aus osifont). Lizenztexte: Ressourcen/Schriften/NILS-Schriften-1.001/lizenzen */']
        for datei, fam, w, st in SCHNITTE:
            p = os.path.join(SCHRIFTEN, datei)
            if not os.path.exists(p):
                raise Fehler('Schriftdatei fehlt: ' + p)
            with open(p, 'rb') as f:
                b64 = base64.b64encode(f.read()).decode('ascii')
            zeilen.append('@font-face{font-family:"%s";font-weight:%d;font-style:%s;font-display:swap;'
                          'src:url(data:font/woff;base64,%s) format("woff")}' % (fam, w, st, b64))
        zeilen.extend(ZUWEISUNG)
        zeilen.append('</style>')
        _schrift_css = '\n'.join(zeilen)
    return _schrift_css


def will_nils(s):
    kopf = s[:s.find('</head>')] if '</head>' in s else s
    return re.search(r'<meta\s+name="schrift"\s+content="nils"\s*/?>', re.sub(r'(?s)<!--.*?-->', '', kopf)) is not None


# ---------- Seite aktualisieren ----------

def ist_lernschritte(s):
    return ('Allgemeinbildung.html:stil' in s or '/* Layout "Lernschritte": überschreibt' in s)


def sollbloecke(fach, allg, seite):
    soll = dict(fach)
    if will_nils(seite):
        if PLATZHALTER not in soll['head']:
            raise Fehler('Platzhalter für die NILS-Schriften fehlt in Fachunterricht.html')
        soll['head'] = soll['head'].replace(PLATZHALTER, schrift_css())
    namen = [('Fachunterricht.html', n) for n in F_BLOECKE]
    if ist_lernschritte(seite):
        for n in A_BLOECKE:
            soll[n] = allg[n]
        namen += [('Allgemeinbildung.html', n) for n in A_BLOECKE]
    return soll, namen


def aktualisiere(s, fach, allg):
    """Neuer Text und Bericht je Block."""
    s = s.replace('<!-- Seite.html:', '<!-- Fachunterricht.html:').replace('<!-- /Seite.html:', '<!-- /Fachunterricht.html:')
    eol = eol_von(s)
    soll, namen = sollbloecke(fach, allg, s)
    stellen = []
    for datei, n in namen:
        b = bereich_markiert(s, datei, n)
        neu_markiert = b is None
        if b is None:
            b = bereich_anker(s, n)
        stellen.append((b[0], b[1], datei, n, neu_markiert))
    stellen.sort()
    for x, y in zip(stellen, stellen[1:]):
        if x[1] > y[0]:
            raise Fehler('Blöcke %s und %s überlappen' % (x[3], y[3]))
    out, pos, bericht = [], 0, []
    for a, e, datei, n, neu_markiert in stellen:
        alt = s[a:e]
        neu = norm(soll[n], eol)
        out.append(s[pos:a])
        if neu_markiert:
            op, cl = markierung(datei, n)
            out.append(op + eol + neu + eol + cl)
        else:
            out.append(neu)
        pos = e
        if alt == neu:
            st = 'gleich' + (', Markierung ergänzt' if neu_markiert else '')
        else:
            al, nl = alt.splitlines(), neu.splitlines()
            plus = sum(1 for l in difflib.ndiff(al, nl) if l.startswith('+ '))
            minus = sum(1 for l in difflib.ndiff(al, nl) if l.startswith('- ')) if len(al) + len(nl) < 6000 else 0
            st = 'aktualisiert (+%d/-%d Zeilen)' % (plus, minus) + (', Markierung ergänzt' if neu_markiert else '')
        bericht.append((n, st, alt, neu))
    out.append(s[pos:])
    return ''.join(out), bericht


def pruefe_ergebnis(alt, neu, nils):
    if not neu.lstrip('﻿').lower().startswith('<!doctype html>'):
        raise Fehler('Erste Zeile ist nicht <!doctype html>')
    if not neu.rstrip().endswith('</html>'):
        raise Fehler('Datei endet nicht mit </html>')
    for tag in ('<script', '<style'):
        d = neu.count(tag) - alt.count(tag)
        erlaubt = (0, 1) if tag == '<style' else (0,)
        if d not in erlaubt:
            raise Fehler('Anzahl %s ändert sich um %d' % (tag, d))
    for t in ('function printBlank', 'id="pwModal"', 'id="pdfBtn"'):
        if neu.count(t) != 1:
            raise Fehler('%s steht %d-mal in der Seite' % (t, neu.count(t)))
    if nils and '@font-face{font-family:"NILS Text"' not in neu:
        raise Fehler('NILS-Schriften wurden nicht eingesetzt')


def schreiben(path, text, bom):
    data = (b'\xef\xbb\xbf' if bom else b'') + text.encode('utf-8')
    tmp = path + '.__sync__'
    with open(tmp, 'wb') as f:
        f.write(data)
    os.replace(tmp, path)


def kurz(zeile):
    if 'base64,' in zeile and len(zeile) > 200:
        return re.sub(r'base64,[A-Za-z0-9+/=]{40,}', 'base64,[…]', zeile)[:200]
    return zeile[:200]


def vorlagen_sync(fach_s):
    allg_s, bom = lesen(ALLG)
    eol = eol_von(allg_s)
    allg_s = allg_s.replace('<!-- Seite.html:', '<!-- Fachunterricht.html:').replace('<!-- /Seite.html:', '<!-- /Fachunterricht.html:')
    fach = bloecke_aus(fach_s, 'Fachunterricht.html', F_BLOECKE)
    neu = allg_s
    for n in F_BLOECKE:
        b = bereich_markiert(neu, 'Fachunterricht.html', n)
        if b is None:
            raise Fehler('Allgemeinbildung.html: Markierung Fachunterricht.html:%s fehlt' % n)
        neu = neu[:b[0]] + norm(fach[n], eol) + neu[b[1]:]
        print('%-8s %7d Zeichen aus Fachunterricht.html' % (n, len(fach[n])))
    for n in A_BLOECKE:   # eigene Blöcke von Allgemeinbildung.html markieren (einmalig)
        if bereich_markiert(neu, 'Allgemeinbildung.html', n) is None:
            a, e = bereich_anker(neu, n)
            op, cl = markierung('Allgemeinbildung.html', n)
            neu = neu[:a] + op + eol + neu[a:e] + eol + cl + neu[e:]
            print('%-8s Markierung ergänzt' % n)
    if neu != allg_s:
        schreiben(ALLG, neu, bom)
        print('Allgemeinbildung.html aktualisiert.')
    else:
        print('Allgemeinbildung.html ist aktuell.')


def main(argv=None):
    for st in (sys.stdout, sys.stderr):
        try:
            st.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            pass
    ap = argparse.ArgumentParser(description='Vorlagenblöcke in Allgemeinbildung.html und die Seiten in Unterricht/ übertragen.')
    ap.add_argument('--schreiben', action='store_true', help='Seiten wirklich ändern (sonst Probelauf)')
    ap.add_argument('--datei', action='append', default=[], help='nur diese Seite(n)')
    ap.add_argument('--diff', action='store_true', help='Unterschiede je Block zeigen')
    ap.add_argument('--pruefen', action='store_true', help='Exitcode 1, wenn eine Seite von der Vorlage abweicht')
    ap.add_argument('--vorlagen', action='store_true', help='nur Fachunterricht.html -> Allgemeinbildung.html')
    a = ap.parse_args(argv)

    fach_s, _ = lesen(FACH)
    if a.vorlagen:
        try:
            vorlagen_sync(fach_s)
        except Fehler as e:
            print('FEHLER: ' + str(e))
            return 2
        return 0

    allg_s, _ = lesen(ALLG)
    fach = bloecke_aus(fach_s, 'Fachunterricht.html', F_BLOECKE)
    allg = bloecke_aus(allg_s, 'Allgemeinbildung.html', A_BLOECKE)

    if a.datei:
        seiten = [os.path.abspath(p) for p in a.datei]
    else:
        seiten = sorted(glob.glob(os.path.join(ROOT, 'Unterricht', '**', '*.html'), recursive=True))
    abweichend, fehler, geaendert = 0, 0, 0
    for p in seiten:
        rel = os.path.relpath(p, ROOT)
        s, bom = lesen(p)
        if '/* Minimaler PDF-Writer' not in s:
            if a.datei:
                print('%s: keine Seite aus der Vorlage (übersprungen)' % rel)
            continue
        try:
            neu, bericht = aktualisiere(s, fach, allg)
            pruefe_ergebnis(s, neu, will_nils(s))
        except Fehler as e:
            fehler += 1
            print('FEHLER %s: %s (Seite nicht geändert)' % (rel, e))
            continue
        layout = 'Lernschritte' if ist_lernschritte(s) else 'Schriftfeld'
        print('%s  [%s%s]' % (rel, layout, ', NILS-Schriften' if will_nils(s) else ''))
        for n, st, alt, nn in bericht:
            print('    %-8s %s' % (n, st))
            if a.diff and alt != nn:
                for z in difflib.unified_diff(alt.splitlines(), nn.splitlines(), 'Seite', 'Vorlage', n=1, lineterm=''):
                    print('      ' + kurz(z))
        if neu != s:
            abweichend += 1
            if a.schreiben:
                schreiben(p, neu, bom)
                geaendert += 1
                print('    -> geschrieben (%d KB)' % (len(neu.encode('utf-8')) // 1024))
    print()
    print('%d Seiten weichen ab, %d geschrieben, %d Fehler.%s' % (
        abweichend, geaendert, fehler, '' if a.schreiben or not abweichend else ' Probelauf: mit --schreiben übernehmen.'))
    if fehler:
        return 2
    if a.pruefen and abweichend:
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
