"""
version.py - pflegt Versionsnummer und unsichtbare Änderungsliste eines E-Learnings. build-scorm.py ruft es bei jedem Bau auf;
für Seiten ohne SCORM-Paket (z. B. ein Arbeitsblatt) geht es auch direkt (im Projektordner, am Mac python3 statt python):
  python .claude/skills/Baue-Lernpaket/scripts/version.py --file "Unterricht/.../index.html" --aenderung "Tippfehler in Aufgabe 2 korrigiert"
Schreibt in die Datei:
  - im Benennungsfeld: <span class="ver" data-datum="28.10.2026">V1.3</span> (sichtbar "V1.3", das Datum nur im Druck und im PDF)
  - nach <title> den Kommentar VERSIONEN (neueste Zeile oben, nur im Quelltext, unsichtbar im Dokument):
      V1.3 | 28.10.2026 | Commit folgt | Tippfehler in Aufgabe 2 korrigiert
      V1.2 | 21.10.2026 | Commit 9f8e7d6 | Lösungsvorschlag Aufgabe 4 ergänzt
Regeln:
  - Eine neue Version entsteht nur, wenn die letzte schon committet ist und sich das E-Learning seitdem geändert hat
    (die Änderungsliste selbst zählt nicht) oder --aenderung etwas Neues beschreibt (z. B. neue scorm-api.js). Dann ist --aenderung Pflicht.
    Ist die letzte Version noch nicht committet ("Commit folgt"), bleibt es bei ihr: Datum von heute, --aenderung wird angehängt.
  - Hauptnummer (V2.0), wenn sich Aufgaben oder Bewertung geändert haben (Aufgaben, Niveaus, Felder, data-k, data-ok, data-keys,
    data-tol, data-score, data-gewicht; in der Übungs-App Einträge und Antworten) oder mit --major. Sonst Nebennummer (V1.3).
  - Ein Commit kann seine eigene Nummer nicht enthalten: "Commit folgt" ersetzt der nächste Bau durch den Commit (kurz),
    mit dem die Zeile eingecheckt wurde.
Rückgabe von pflegen(): dict mit Version ("1.3"), Datum, Commit, Text, Neu (neue Version angelegt), Haupt (Hauptversion), Geschrieben.
Nur Python-Standardbibliothek (Windows und Mac).
"""
import argparse
import datetime
import os
import re
import shutil
import subprocess
import sys


class VersionFehler(Exception):
    pass


RX_LOG = re.compile(r'<!-- VERSIONEN:[^\r\n]*\r?\n(.*?)-->', re.S)
RX_LINE = re.compile(r'^V(\d+)\.(\d+) \| (\d{2}\.\d{2}\.\d{4}) \| Commit (\S+) \| (.*)$')
RX_SPAN = re.compile(r'<span class="ver"[^>]*>[^<]*</span>')


def _git(cwd, args):   # Ausgabe als UTF-8 lesen; ohne git oder außerhalb eines Repos: Code -1
    if not shutil.which('git'):
        return -1, ''
    try:
        r = subprocess.run(['git', '-C', cwd] + args, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    except OSError:
        return -1, ''
    out = r.stdout.decode('utf-8', 'replace').replace('\r\n', '\n')
    if out.endswith('\n'):
        out = out[:-1]
    return r.returncode, out


def _clean(s):   # Text für eine Zeile der Änderungsliste: einzeilig, ohne | und ohne -- (würde den Kommentar beenden)
    s = re.sub(r'\s+', ' ', s).replace('|', '/').strip()
    while '--' in s:
        s = s.replace('--', '–')
    return s


def _strip(s):   # Vergleich ohne Änderungsliste und Zeilenende-Unterschiede
    return RX_LOG.sub('', s.replace('\r\n', '\n'), count=1).rstrip()


def _struct(s):   # Fingerabdruck von Aufgaben und Bewertung: ändert er sich, ist es eine Hauptversion
    s = s.replace('\r\n', '\n')
    app = re.search(r'<script id="app-data" type="application/json">(.*?)</script>', s, re.S)
    m = re.search(r'<main\b.*?</main>', s, re.S)
    if m:
        s = m.group(0)
    s = re.sub(r'<!--.*?-->|<script\b.*?</script>|<style\b.*?</style>', '', s, flags=re.S)
    p = ['Aufgaben %d' % len(re.findall(r'class="task[\s"]', s)),
         'Felder %d' % len(re.findall(r'<(?:input|textarea|select)\b', s))]
    for lv in ('foundation', 'core', 'challenge'):
        p.append('%s %d' % (lv, len(re.findall(r'class="level ' + lv + r'[\s"]', s))))
    p.append(' '.join(m.group(0).strip() for m in re.finditer(r'\sdata-(?:k|ok|keys|tol|score|gewicht)(?:="[^"]*")?(?=[\s>/])', s)))
    if app:   # Übungs-App: Zahl der Einträge, Antworten, Gruppen und Niveaus
        j = app.group(1)
        p.append('Eintraege %d' % len(re.findall(r'"(?:question|front|left|text)"\s*:', j)))
        p.append(' '.join(re.sub(r'\s+', '', m.group(0)) for m in
                          re.finditer(r'"(?:type|answer|group|groups|level)"\s*:\s*(?:"[^"]*"|\d+|\[[^\]]*\])', j)))
    return '; '.join(p)


def _lesen(path):
    with open(path, 'rb') as f:
        return f.read().decode('utf-8-sig')   # ohne BOM, Zeilenenden bleiben


def _schreiben(path, text):
    with open(path, 'wb') as f:
        f.write(text.encode('utf-8'))   # UTF-8 ohne BOM


def lesen_stand(file):
    """Neueste Zeile der Änderungsliste, ohne etwas zu schreiben (Bau mit --nur-packen). None, wenn es keine gibt."""
    lm = RX_LOG.search(_lesen(os.path.abspath(file)))
    for ln in re.split(r'\r?\n', lm.group(1) if lm else ''):
        e = RX_LINE.match(ln.strip())
        if e:
            return {'Version': '%d.%d' % (int(e.group(1)), int(e.group(2))), 'Datum': e.group(3), 'Commit': e.group(4),
                    'Text': e.group(5).strip(), 'Neu': False, 'Haupt': False, 'Geschrieben': False}
    return None


def pflegen(file, aenderung='', major=False):
    path = os.path.abspath(file)
    if not os.path.isfile(path):
        raise VersionFehler('Datei nicht gefunden: %s' % file)
    d = os.path.dirname(path)
    leaf = os.path.basename(path)
    html = _lesen(path)
    orig = html
    nl = '\r\n' if '\r\n' in html else '\n'
    today = datetime.date.today().strftime('%d.%m.%Y')

    # 1. Änderungsliste lesen
    entries = []
    lm = RX_LOG.search(html)
    if lm:
        for ln in re.split(r'\r?\n', lm.group(1)):
            e = RX_LINE.match(ln.strip())
            if e:
                entries.append({'Ma': int(e.group(1)), 'Mi': int(e.group(2)), 'Datum': e.group(3),
                                'Commit': e.group(4), 'Text': e.group(5).strip()})

    # 2. "Commit folgt" nachtragen: der Commit, der die Zeile so eingecheckt hat (ältester Treffer)
    for e in entries:
        if e['Commit'] != 'folgt':
            continue
        code, out = _git(d, ['log', '--reverse', '--format=%h', '-S',
                             'V%d.%d | %s | Commit folgt' % (e['Ma'], e['Mi'], e['Datum']), '--', leaf])
        if code == 0 and out.strip():
            e['Commit'] = out.strip().split('\n')[0].strip()

    # 3. Stand bestimmen: neu (noch keine Liste), offen (neueste Zeile noch nicht committet) oder fertig (committet)
    top = entries[0] if entries else None
    base = None
    if top and top['Commit'] == 'folgt':
        if len(entries) > 1:
            base = entries[1]
    elif top:
        base = top
    base_html = None
    if base and base['Commit'] != 'folgt':
        code, out = _git(d, ['show', base['Commit'] + ':./' + leaf])
        if code == 0:
            base_html = out.lstrip('﻿')
    haupt = bool(major)
    if base_html is not None and _struct(html) != _struct(base_html):
        haupt = True
    text = _clean(aenderung or '')
    neu = False

    def naechste(b):
        return (b['Ma'] + 1, 0) if haupt else (b['Ma'], b['Mi'] + 1)

    if not top:
        entries = [{'Ma': 1, 'Mi': 0, 'Datum': today, 'Commit': 'folgt', 'Text': text or 'Erste Fassung'}]
        neu = True
        haupt = False
    elif top['Commit'] == 'folgt':
        if base:
            top['Ma'], top['Mi'] = naechste(base)
        else:
            haupt = False
        top['Datum'] = today
        if text and text not in top['Text']:
            top['Text'] = top['Text'] + '; ' + text
    else:
        changed = base_html is None or _strip(html) != _strip(base_html)
        if not changed:
            dc, _ = _git(d, ['diff', '--quiet', top['Commit'], '--', '.', ':(exclude)' + leaf])
            _, uo = _git(d, ['ls-files', '--others', '--exclude-standard', '--', '.'])
            changed = dc == 1 or bool(uo.strip())
        if text and text not in top['Text']:
            changed = True
        if changed:
            if not text:
                raise VersionFehler('Das E-Learning hat sich seit V%d.%d (Commit %s) geändert. Bitte mit --aenderung "<was geändert wurde>" aufrufen.'
                                    % (top['Ma'], top['Mi'], top['Commit']))
            ma, mi = naechste(top)
            entries = [{'Ma': ma, 'Mi': mi, 'Datum': today, 'Commit': 'folgt', 'Text': text}] + entries
            neu = True
        else:
            haupt = False
    top = entries[0]

    # 4. Änderungsliste und Anzeige im Benennungsfeld schreiben
    lines = ['V%d.%d | %s | Commit %s | %s' % (e['Ma'], e['Mi'], e['Datum'], e['Commit'], e['Text']) for e in entries]
    block = ('<!-- VERSIONEN: neueste oben. Nur im Quelltext, unsichtbar im Dokument. Pflegt build-scorm.py (Skill Baue-Lernpaket), nicht von Hand ändern.'
             + nl + nl.join(lines) + nl + '-->')
    if lm:
        html = html[:lm.start()] + block + html[lm.end():]
    else:
        t = re.search(r'</title>', html, re.I) or re.search(r'<head[^>]*>', html, re.I)
        if not t:
            raise VersionFehler('Startdatei hat weder <title> noch <head>: Änderungsliste kann nicht eingetragen werden.')
        html = html[:t.end()] + nl + block + html[t.end():]
    span = '<span class="ver" data-datum="%s">V%d.%d</span>' % (top['Datum'], top['Ma'], top['Mi'])
    n = html.find('<div class="name"')   # erst ab dem Benennungsfeld suchen (nicht im Vorlagen-Kommentar)
    sm = RX_SPAN.search(html, n) if n >= 0 else RX_SPAN.search(html)
    if sm:
        html = html[:sm.start()] + span + html[sm.end():]
    else:
        s = html.find('</small>', n) if n >= 0 else -1
        if s >= 0:
            html = html[:s] + span + html[s:]
        else:
            print('WARNUNG: Kein Benennungsfeld (div.name mit small) gefunden: Die Version steht nur in der Änderungsliste.')
    written = html != orig
    if written:
        _schreiben(path, html)

    return {'Version': '%d.%d' % (top['Ma'], top['Mi']), 'Datum': top['Datum'], 'Commit': top['Commit'],
            'Text': top['Text'], 'Neu': neu, 'Haupt': haupt, 'Geschrieben': written}


def main(argv=None):
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            pass
    ap = argparse.ArgumentParser(description='Version und Änderungsliste eines E-Learnings pflegen.')
    ap.add_argument('--file', required=True, help='Startdatei des E-Learnings (z. B. Unterricht/.../index.html)')
    ap.add_argument('--aenderung', default='', help='was sich geändert hat (Pflicht, sobald sich das E-Learning geändert hat)')
    ap.add_argument('--major', action='store_true', help='Hauptversion erzwingen')
    a = ap.parse_args(argv)
    try:
        r = pflegen(a.file, a.aenderung, a.major)
    except VersionFehler as e:
        print('FEHLER: %s' % e)
        return 1
    print('V%s vom %s, Commit %s%s: %s' % (r['Version'], r['Datum'], r['Commit'],
                                           (' (neue Hauptversion)' if r['Haupt'] else ' (neue Version)') if r['Neu'] else '', r['Text']))
    print('Datei geändert.' if r['Geschrieben'] else 'Datei unverändert.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
