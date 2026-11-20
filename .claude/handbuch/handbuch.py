"""
handbuch.py - hält das Handbuch für Kolleg/innen (#Handbuch.html) aktuell und prüft es.
Aufruf im Projektordner (am Mac python3 statt python):
  python .claude/handbuch/handbuch.py            automatische Teile erneuern und prüfen
  python .claude/handbuch/handbuch.py --pruefen  nur prüfen, nichts schreiben (Rückgabe 1 bei Fehlern)
  Auf GitHub erneuert der Workflow "Bauen und zustellen" das Handbuch nach jedem Push (pruefen.py --erneuern) und committet es.
Automatische Teile im Handbuch (zwischen <!-- AUTO:name --> und <!-- /AUTO:name -->, nie von Hand ändern):
  stand   Datum der letzten Änderung am Handbuch
  zahlen  Zahl der Lernpakete und Skills im Kopf (eine Paketliste gibt es nicht mehr: Die Links stehen auf der Linkseite)
  navi    Seitenleiste aus den Überschriften (h2, h3 mit id; kurzer Name in data-nav), je Gruppe mit dem data-weg des Kapitels
  neu     "Was ist neu": sichtbar die neuesten Änderungen an Lernpaketen, eingeklappt alles Ältere und die Neuigkeiten
          zum Werkzeug aus .claude/handbuch/neuigkeiten.txt
  fragen  "Häufige Fragen" aus .claude/handbuch/fragen.txt mit Link auf den Abschnitt, der sie beantwortet (unsichtbar, nur für die Suche)
  skills  alle Skills: Kurztexte aus .claude/handbuch/skills.txt, sonst Beschreibung und Auslöser aus der SKILL.md (Helfer stehen nicht im Handbuch)
Prüfungen: jede Frage und jeder interne Link hat ein Ziel, ids sind eindeutig, Anfang und Ende der Seite, Tags geschlossen,
keine Platzhalter und Markdown-Zeichen, keine externen Ressourcen, "die KI" statt Produktname.
Mitdokumentieren prüft .claude/gemeinsam/scripts/pruefen.py (Muster PFLICHT und DOKU stehen hier).
Nur Python-Standardbibliothek (Windows und Mac).
"""
import argparse
import datetime
import glob
import html
import importlib.util
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATEI = '#Handbuch.html'
FRAGEN = '.claude/handbuch/fragen.txt'
SKILLS = '.claude/handbuch/skills.txt'
NEU = '.claude/handbuch/neuigkeiten.txt'
DOKU = (DATEI, FRAGEN, SKILLS, NEU)
# Ändert sich davon etwas, muss es dokumentiert werden
PFLICHT = re.compile(r'^(CLAUDE\.md$|\.claude/settings\.json$|\.claude/agents/|\.claude/skills/[^/]+/[^/]+\.md$'
                     r'|\.claude/skills/[^/]+/templates/|\.claude/skills/[^/]+/scripts/|\.claude/gemeinsam/|\.github/)')
OFFEN_NEU = 3      # so viele Einträge in "Was ist neu" sind sichtbar, der Rest ist eingeklappt
MAX_NEU = 60
SAMMEL = 5         # gleiche Änderung an so vielen Paketen: Sammeländerung (technisch), steht nur unter "Ältere Änderungen"


def _unterrichtsmaterial():   # Namensregel und Fächer: .claude/gemeinsam/scripts/unterrichtsmaterial.py
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location('unterrichtsmaterial', os.path.join(ROOT, '.claude', 'gemeinsam', 'scripts', 'unterrichtsmaterial.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


unterrichtsmaterial = _unterrichtsmaterial()


def lesen(rel):
    with open(os.path.join(ROOT, rel), 'rb') as f:
        return f.read().decode('utf-8-sig')


def schreiben(rel, text):
    with open(os.path.join(ROOT, rel), 'wb') as f:
        f.write(text.encode('utf-8'))


def git_roh(*args):   # (Rückgabecode, Ausgabe als Bytes)
    try:
        r = subprocess.run(['git', '-c', 'core.quotePath=false'] + list(args), cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    except OSError:
        return -1, b''
    return r.returncode, r.stdout


def git(*args):   # (Rückgabecode, Ausgabe als UTF-8)
    code, aus = git_roh(*args)
    return code, aus.decode('utf-8', 'replace')


def zeilen(rel):   # Zeilen ohne Kommentare und Leerzeilen, an | getrennt
    return [[t.strip() for t in z.split('|')] for z in lesen(rel).splitlines() if z.strip() and not z.lstrip().startswith('#')]


def kopf(rel):   # Felder name und description aus dem Kopf (frontmatter), dazu der ganze Text
    s = lesen(rel).replace('\r\n', '\n')
    m = re.match(r'---\n(.*?)\n---', s, re.S)
    k = {}
    for z in (m.group(1).split('\n') if m else []):
        if ':' in z:
            a, b = z.split(':', 1)
            k[a.strip()] = b.strip()
    return k, s


def wofuer(desc):   # erster Satz der Beschreibung, ohne Klammern und ohne "Use when ..."
    t = re.split(r'\s(?:Use when|Verwenden)\b', desc)[0]
    t = re.sub(r'\s*\([^()]*\)', '', t).strip()
    m = re.match(r'(.+?[.!?])(?:\s|$)', t)
    return m.group(1) if m else t


def beispiel(desc, text):   # erster Satz in Anführungszeichen aus "## Auslöser" oder "Use when ..."
    m = re.search(r'^## Auslöser\n((?:- .*\n?)+)', text, re.M)
    teil = m.group(1) if m else (desc.split('Use when', 1)[1] if 'Use when' in desc else '')
    q = re.findall(r'"([^"]+)"', teil)
    return q[0].rstrip(' .') if q else ''


def bloecke_skills():
    kurz = {z[0]: z for z in zeilen(SKILLS) if len(z) >= 3}
    alle = {}
    for w in sorted(glob.glob(os.path.join(ROOT, '.claude', 'skills', '*', 'SKILL.md'))):
        k, s = kopf(os.path.relpath(w, ROOT).replace(os.sep, '/'))
        alle[k.get('name') or os.path.basename(os.path.dirname(w))] = (k.get('description', ''), s)
    namen = [n for n in kurz if n in alle] + sorted(n for n in alle if n not in kurz)
    teile = ['<div class="karten">']
    for n in namen:
        d, s = alle[n]
        was = kurz[n][1] if n in kurz else wofuer(d)
        bsp = kurz[n][2] if n in kurz else (beispiel(d, s) or '/' + n)
        teile.append('<div class="karte"><code class="name">/%s</code><p>%s</p><p class="prompt">%s</p></div>' % (html.escape(n), html.escape(was), html.escape(bsp)))
    teile.append('</div>')
    return '\n'.join(teile), len(alle), [n for n in alle if n not in kurz]


def liste_fragen():
    teile = ['<ul class="fragen">']
    for z in zeilen(FRAGEN):
        teile.append('<li><a href="#%s">%s</a></li>' % (html.escape(z[1] if len(z) > 1 else ''), html.escape(z[0])))
    return '\n'.join(teile + ['</ul>'])


def slug(t):
    for a, b in (('ä', 'ae'), ('ö', 'oe'), ('ü', 'ue'), ('Ä', 'Ae'), ('Ö', 'Oe'), ('Ü', 'Ue'), ('ß', 'ss')):
        t = t.replace(a, b)
    return re.sub(r'[^A-Za-z0-9]+', '-', t).strip('-').lower()


def tag_nr(datum):   # 29.10.2026 -> 20261029 zum Sortieren
    m = re.match(r'(\d{2})\.(\d{2})\.(\d{4})$', datum)
    return int(m.group(3) + m.group(2) + m.group(1)) if m else 0


def natuerlich(t):   # Kapitel 2 vor Kapitel 10
    return [(0, int(x)) if x.isdigit() else (1, x.lower()) for x in re.split(r'(\d+)', t) if x]


def lernpakete():   # aus den Themenordnern in Unterricht/ mit Version: Seiten in Git oder neu (nicht ignoriert), im Arbeitsstand
    _, liste = git('ls-files', '--cached', '--others', '--exclude-standard', '--', unterrichtsmaterial.ORDNER)
    pakete = []
    for p in sorted(set(liste.splitlines())):
        t = p.split('/')
        if len(t) != 6 or t[5] != 'index.html' or t[1] in unterrichtsmaterial.SONDERORDNER:
            continue
        try:
            seite = unterrichtsmaterial.lesen(os.path.join(ROOT, p))
        except OSError:
            continue
        if not unterrichtsmaterial.stand(seite):   # noch nie als Lernpaket gebaut
            continue
        sb = dict(zip(unterrichtsmaterial.FELDER, t[1:5]))
        versionen = []
        lm = unterrichtsmaterial.RX_VERSIONEN.search(seite)
        for z in re.split(r'\r?\n', lm.group(1) if lm else ''):
            e = re.match(r'V(\d+\.\d+) \| (\d{2}\.\d{2}\.\d{4}) \| Commit \S+ \| (.*)$', z.strip())
            if e:
                versionen.append({'v': e.group(1), 'datum': e.group(2), 'text': e.group(3).strip()})
        lernfeld = unterrichtsmaterial.fachname(sb['fach'], sb['klasse']) or sb['fach']
        klasse = unterrichtsmaterial.klassenname(sb['klasse'])
        pakete.append({'stufe': sb['klasse'], 'klasse': klasse, 'lernfeld': lernfeld, 'bw': sb['abschnitt'],
                       'titel': unterrichtsmaterial.titel(seite) or sb['thema'].replace('-', ' '),
                       'datei': unterrichtsmaterial.paketname(sb), 'versionen': versionen})
    pakete.sort(key=lambda x: (x['stufe'], x['lernfeld'], natuerlich(x['bw']), natuerlich(x['titel'])))
    return pakete


def zaehle_gleiche(pakete):   # (Datum, Text) -> Pakete mit genau dieser Änderung
    gleich = {}
    for p in pakete:
        for v in p['versionen']:
            gleich.setdefault((v['datum'], v['text']), []).append('%s V%s' % (p['titel'], v['v']))
    return gleich


def block_neu(pakete):
    liste = []   # (Tag, Vorrang, Datum, Art, Wer, Text, Sammeländerung); eine Änderung an vielen Paketen wird zu einer Zeile
    for z in zeilen(NEU):
        if len(z) >= 2:
            liste.append((tag_nr(z[0]), 1, z[0], 'System', '', ' | '.join(z[1:]), False))
    for (datum, text), wer in zaehle_gleiche(pakete).items():
        liste.append((tag_nr(datum), 0, datum, 'Lernpaket', wer[0] if len(wer) == 1 else '%d Lernpakete' % len(wer), text, len(wer) >= SAMMEL))
    liste.sort(key=lambda e: (-e[0], -e[1]))
    liste = liste[:MAX_NEU]
    sichtbar = [e for e in liste if e[3] == 'Lernpaket' and not e[6]][:OFFEN_NEU]   # Neuigkeiten zum Werkzeug stehen eingeklappt
    aelter = [e for e in liste if e not in sichtbar]

    def zeile(e):
        art = 'neu-system' if e[3] == 'System' else 'neu-paket'
        wer = '<b>%s:</b> ' % html.escape(e[4]) if e[4] else ''
        return '<li class="%s"><time>%s</time><span class="art">%s</span><p>%s%s</p></li>' % (art, html.escape(e[2]), e[3], wer, html.escape(e[5]))
    teile = ['<ol class="zeitleiste">'] + [zeile(e) for e in sichtbar] + ['</ol>']
    if aelter:
        teile += ['<details class="aelter"><summary>Ältere Änderungen und Neues am Werkzeug</summary><ol class="zeitleiste">'] + [zeile(e) for e in aelter] + ['</ol></details>']
    return '\n'.join(teile)


def block_navi(s):   # aus den Überschriften mit id: h2 = Gruppe (mit dem data-weg des Kapitels), h3 = Eintrag
    teile, offen, weg = [], False, ''
    ohne = s[s.find('<main'):]
    for m in re.finditer(r'<section\b([^>]*)>|<h([23])\b([^>]*)>(.*?)</h\2>', ohne, re.S):
        if m.group(2) is None:
            w = re.search(r'\bdata-weg="([^"]+)"', m.group(1))
            weg = w.group(1) if w else ''
            continue
        i = re.search(r'\bid="([^"]+)"', m.group(3))
        if not i:
            continue
        kurz = re.search(r'\bdata-nav="([^"]+)"', m.group(3))
        nr = re.search(r'<span class="nr">(.*?)</span>', m.group(4))
        text = kurz.group(1) if kurz else re.sub(r'<[^>]+>', '', m.group(4)).strip()
        if m.group(2) == '2':
            if offen:
                teile.append('</div>')
            teile.append('<div class="navgruppe"%s><a class="navkopf" href="#%s">%s</a>' % (' data-weg="%s"' % weg if weg else '', i.group(1), text))
            offen = True
        else:
            teile.append('<a href="#%s">%s%s</a>' % (i.group(1), '<span>%s</span> ' % nr.group(1) if nr else '', text))
    if offen:
        teile.append('</div>')
    return '\n'.join(teile)


def ersetze(s, name, inhalt):
    a, b = '<!-- AUTO:%s -->' % name, '<!-- /AUTO:%s -->' % name
    i, j = s.find(a), s.find(b)
    if i < 0 or j < i:
        raise SystemExit('FEHLER: %s: Markierung AUTO:%s fehlt.' % (DATEI, name))
    return s[:i + len(a)] + inhalt + s[j:]


def ohne_stand(s):   # Vergleich ohne Datum und ohne Unterschiede im Zeilenende
    return re.sub(r'(<!-- AUTO:stand -->).*?(<!-- /AUTO:stand -->)', r'\1\2', s.replace('\r\n', '\n'), flags=re.S)


def erneuern(s):
    nl = '\r\n' if '\r\n' in s else '\n'

    def block(t):
        return nl + t.replace('\n', nl) + nl
    skills, n_skills, fehlen = bloecke_skills()
    pakete = lernpakete()
    neu = ersetze(s, 'fragen', block(liste_fragen()))
    neu = ersetze(neu, 'skills', block(skills))
    neu = ersetze(neu, 'neu', block(block_neu(pakete)))
    neu = ersetze(neu, 'zahlen', '<b>%d</b> Lernpakete · <b>%d</b> Skills' % (len(pakete), n_skills))
    neu = ersetze(neu, 'navi', block(block_navi(neu)))
    code, alt = git('show', 'HEAD:' + DATEI)
    if code == 0 and ohne_stand(alt) == ohne_stand(neu):   # nichts geändert: Stand bleibt
        m = re.search(r'<!-- AUTO:stand -->(.*?)<!-- /AUTO:stand -->', alt, re.S)
        heute = m.group(1) if m else ''
    else:
        heute = datetime.date.today().strftime('%d.%m.%Y')
    return ersetze(neu, 'stand', heute), fehlen


def pruefen(s):
    f = []
    if not s.startswith('<!doctype html>'):
        f.append('Die erste Zeile ist nicht <!doctype html>.')
    if not s.rstrip().endswith('</html>'):
        f.append('Die Seite endet nicht mit </html>: abgeschnitten?')
    body = re.sub(r'<!--.*?-->|<script\b.*?</script>|<style\b.*?</style>', '', s, flags=re.S)
    for t in ('section', 'div', 'table', 'ol', 'ul', 'details', 'article'):
        a, b = len(re.findall(r'<%s[\s>]' % t, body)), len(re.findall(r'</%s>' % t, body))
        if a != b:
            f.append('Tags nicht geschlossen: <%s> %d-mal, </%s> %d-mal.' % (t, a, t, b))
    m = re.search(r'\[(?:Titel|Untertitel|Beruf|Thema)[^\]]*\]|\bTODO\b|\*\*|(?:^|\s)##\s', body)
    if m:
        f.append('Platzhalter oder Markdown-Zeichen im Text: %s' % m.group(0).strip())
    m = re.search(r'\bClaude\b(?! Code“)', body)
    if m:
        f.append('Im Handbuch heißt es "die KI", nicht "Claude" (auch in %s): …%s…' % (NEU, body[max(0, m.start() - 40):m.end() + 20].replace('\n', ' ')))
    if re.search(r'''(?:\bsrc=|<link\b[^>]*\bhref=)["']https?:''', body):
        f.append('Externe Ressource in src= oder <link>: Die Seite muss offline laufen.')
    alle = re.findall(r'\bid="([^"]+)"', body)
    ids = set(alle)
    for i in sorted(ids):
        if alle.count(i) > 1:
            f.append('id doppelt vergeben: %s' % i)
    for z in zeilen(FRAGEN):
        if len(z) < 2 or z[1] not in ids:
            f.append('Frage ohne Abschnitt im Handbuch: "%s" -> %s' % (z[0], z[1] if len(z) > 1 else '(keine id)'))
    for z in sorted(set(re.findall(r'href="#([^"]*)"', body))):
        if z not in ids:
            f.append('Link ohne Ziel: #%s' % z)
    for z in zeilen(NEU):
        if len(z) < 2 or not tag_nr(z[0]):
            f.append('Zeile in %s nicht im Format "TT.MM.JJJJ | Text": %s' % (NEU, ' | '.join(z)))
    return f


def main(argv=None):
    for st in (sys.stdout, sys.stderr):
        try:
            st.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            pass
    ap = argparse.ArgumentParser(description='Handbuch erneuern und prüfen.')
    ap.add_argument('--pruefen', action='store_true', help='nur prüfen, nichts schreiben')
    a = ap.parse_args(argv)
    if not os.path.isfile(os.path.join(ROOT, DATEI)):
        print('FEHLER: %s nicht gefunden.' % DATEI)
        return 1
    s = lesen(DATEI)
    neu, fehlen = erneuern(s)
    fehler = pruefen(neu)
    for n in fehlen:
        print('Hinweis: Skill %s hat keinen Kurztext in %s.' % (n, SKILLS))
    for t in fehler:
        print('ACHTUNG %s: %s' % (DATEI, t))
    if a.pruefen:
        if neu != s:
            print('ACHTUNG %s: Automatische Teile sind veraltet: python .claude/handbuch/handbuch.py ausführen.' % DATEI)
            fehler.append('veraltet')
    elif neu != s:
        schreiben(DATEI, neu)
        print('%s: automatische Teile erneuert.' % DATEI)
    if not fehler:
        print('%s: alle Prüfungen bestanden.' % DATEI)
    return 1 if fehler else 0


if __name__ == '__main__':
    sys.exit(main())
