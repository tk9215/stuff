"""
linkseite.py - holt die Download-Links der Lernpakete von der Linkseite "ByCS-Links" (Power Automate).

Jedes Lernpaket im Teamordner bekommt von selbst einen geteilten Download-Link. Die Linkseite listet sie je Dateiname.
Der Kursbau (build-mbz.py) fragt hier nach, niemand tippt oder kopiert Links. Kurse und Tests haben keinen Link:
Sie werden direkt aus dem Teamordner in die ByCS hochgeladen.

Die Adresse der Linkseite enthält einen Schlüssel. Sie steht nur an einer Stelle im Repo: im Handbuch (#Handbuch.html, Knopf
"Linkseite öffnen", Entscheidung vom 12.11.2026, das Repo ist privat). Sonst nirgends eintragen und nie ausgeben. Die Skripte lesen sie aus
  1. der Umgebung BYCS_LINKSEITE   (GitHub: Secret, der Workflow baut damit die Kurse)
  2. git config bycs.linkseite   (nur wenn von Hand gesetzt)
  3. der Verknüpfung "# ByCS-Links.url" im Teamordner BYCS-SYNC (liegt dort für alle Kolleg/innen)
Die Linkseite verlangt außerdem ein Passwort (seit 13.11.2026). Auf GitHub steht es in der Adresse im Secret (…&pw=…). Am Rechner
fragt das Skript einmal in einem Fenster danach und merkt es in .git/config (git config bycs.linkpasswort), nie im Repo, nie im Chat.

Aufruf im Projektordner (am Mac python3 statt python):
  python .claude/gemeinsam/scripts/linkseite.py             Abgleich: welches Paket hat einen Link, welches nicht
  python .claude/gemeinsam/scripts/linkseite.py <Paket>     den Link eines Pakets ausgeben (Dateiname oder Pfad)
  python .claude/gemeinsam/scripts/linkseite.py --teamordner   zeigen, ob und wo der Teamordner auf diesem Rechner liegt
                                                               (sonst die Anleitung zum Einrichten)
Nur Python-Standardbibliothek (Windows und Mac, ab Python 3.9).
"""
import datetime
import glob
import html
import os
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
VERKNUEPFUNG = '# ByCS-Links.url'
# Ordner BYCS-SYNC im Web (OneDrive/SharePoint), dort "..." > "Synchronisieren"
LINK = ('https://stadtnbg-my.sharepoint.com/shared?id=%2Fsites%2Fb2%2Dbs%2FShared%20Documents%2FBYCS%2DSYNC&listurl=https%3A%2F%2F'
        'stadtnbg%2Esharepoint%2Ecom%2Fsites%2Fb2%2Dbs%2FShared%20Documents&viewid=efeadde1%2D7051%2D47bb%2D9ea9%2Dd2ca660df3fb')
ANLEITUNG = """Teamordner "B2-BS-Kollegium - Dokumente/BYCS-SYNC" nicht gefunden. Zugestellt wird trotzdem alles (GitHub nach dem Push);
ohne Teamordner fehlen auf diesem Rechner nur die Download-Links für den Kursbau und die Dateien zum Hochladen in die ByCS.
So richtest du ihn ein:
  1. Diesen Link im Browser öffnen und mit dem Schulkonto (Stadt Nürnberg) anmelden:
     %s
     Oben in der Leiste auf "..." klicken und "Synchronisieren" wählen (fehlt es: "Verknüpfung zu Meine Dateien hinzufügen",
     dann liegt der Ordner woanders: Claude Bescheid sagen). "OneDrive öffnen?" bestätigen und warten, bis der Ordner erscheint.
  2. Nur am Mac: Systemeinstellungen > Datenschutz & Sicherheit > Festplattenvollzugriff, dort Visual Studio Code einschalten,
     dann VS Code ganz beenden (Cmd+Q) und neu öffnen. Sonst meldet der Mac "Operation not permitted".
  3. Claude Bescheid geben ("fertig"). Liegt der Ordner an einer ungewöhnlichen Stelle:
     git config bycs.ziel "<Pfad zum Ordner BYCS-SYNC>"
""" % LINK
BIBLIOTHEK = 'B2-BS-Kollegium - Dokumente'
ORDNER = 'B2-BS-Kollegium - BYCS-SYNC'           # so heißt der Ordner, wenn nur BYCS-SYNC synchronisiert wird
# Zwei Aufbauten der Linkseite: alt <tr>…value="Link"…12/31/2026 1:05 PM, neu (ab 12.11.2026) <tr data-p="Pakete/…">…
# data-link="Link"…31.12.2026 mit Ordnerpfad in der Namensspalte. Beide werden gelesen.
RX_ZEILE = re.compile(r'<tr\b[^>]*>(.*?)</tr>', re.S)
RX_NAME = re.compile(r'<td>([^<]*_scorm\.zip)\s*</td>')
RX_LINK = re.compile(r'(?:value|data-link)="(https://[^"]+)"')
RX_DATUM = re.compile(r'<td>(\d{1,2}/\d{1,2}/\d{4} \d{1,2}:\d{2} [AP]M|\d{1,2}\.\d{1,2}\.\d{4}(?: \d{1,2}:\d{2})?)</td>')   # Spalte "Geändert"
DATUMSFORMATE = ('%m/%d/%Y %I:%M %p', '%d.%m.%Y %H:%M', '%d.%m.%Y')
LOGIN = 'data-login'                             # daran ist die Anmeldeseite der Linkseite zu erkennen (statt der Tabelle)
PASSWORT = 'bycs.linkpasswort'                   # git config, nur in .git/config dieses Rechners, nie im Repo
DOPPELT = []                                   # Namen, die die Linkseite beim letzten Abruf mehrfach nannte


class LinkFehler(Exception):
    pass


def _git_config(name):
    try:
        r = subprocess.run(['git', 'config', '--get', name], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    except OSError:
        return ''
    return r.stdout.decode('utf-8', 'replace').strip()


def teamordner():
    """Pfad des Teamordners BYCS-SYNC auf diesem Rechner, '' wenn er nicht synchronisiert ist."""
    z = _git_config('bycs.ziel')
    if z:
        m = re.match(r'/([A-Za-z])/(.*)$', z) if os.name == 'nt' else None   # Git-Bash-Pfad /c/Users/...
        z = '%s:/%s' % (m.group(1), m.group(2)) if m else z
        return z if os.path.isdir(z) else ''
    basis = glob.escape(os.path.expanduser('~'))
    for muster in ('*/%s/BYCS-SYNC' % BIBLIOTHEK, 'Library/CloudStorage/*/%s/BYCS-SYNC' % BIBLIOTHEK,
                   '*/%s' % ORDNER, 'Library/CloudStorage/*/%s' % ORDNER):
        for z in sorted(glob.glob(os.path.join(basis, *muster.split('/')))):
            if os.path.isdir(z):
                return z
    return ''


def adresse():
    a = os.environ.get('BYCS_LINKSEITE', '').strip() or _git_config('bycs.linkseite')   # GitHub: Secret BYCS_LINKSEITE
    if a:
        return a
    t = teamordner()
    if not t:
        raise LinkFehler(ANLEITUNG)
    p = os.path.join(t, VERKNUEPFUNG)
    if not os.path.isfile(p):
        raise LinkFehler('Die Verknüpfung "%s" fehlt im Teamordner (%s).' % (VERKNUEPFUNG, t))
    with open(p, 'rb') as f:
        m = re.search(r'^URL=(\S+)', f.read().decode('utf-8-sig', 'replace'), re.M)
    if not m or not m.group(1).startswith('https://'):
        raise LinkFehler('In "%s" steht keine https-Adresse.' % VERKNUEPFUNG)
    return m.group(1)


def aus_seite(text):
    """Links aus dem HTML der Linkseite: {Dateiname: Link}.

    Steht ein Name mehrfach da (alte Datei noch im Teamordner), gilt die Datei unter Pakete/ (die neue Seite nennt den Ordner),
    sonst die zuletzt geänderte: Die Zustellung (GitHub, Power Automate) aktualisiert nur die Datei unter Pakete/. Unklar: Fehler.
    """
    funde = {}
    for z in RX_ZEILE.findall(text):
        n, l, d = RX_NAME.search(z), RX_LINK.search(z), RX_DATUM.search(z)
        if not n or not l:
            continue
        pfad = html.unescape(n.group(1)).strip().replace(chr(92), '/')
        name = pfad.split('/')[-1]
        datum = None
        for fmt in DATUMSFORMATE if d else ():
            try:
                datum = datetime.datetime.strptime(d.group(1), fmt)
                break
            except ValueError:
                pass
        funde.setdefault(name, {})[html.unescape(l.group(1))] = (datum, pfad.startswith('Pakete/'))
    links, unklar = {}, []
    del DOPPELT[:]
    for name, f in funde.items():
        if len(f) > 1:
            DOPPELT.append(name)
            unter_pakete = [k for k, (_, p) in f.items() if p]   # nennt die Seite den Ordner: die Datei unter Pakete/ gilt
            if len(unter_pakete) == 1:
                links[name] = unter_pakete[0]
                continue
        f = {k: d for k, (d, p) in f.items() if p or not any(q for _, q in f.values())}
        if len(f) > 1:
            daten = sorted((d for d in f.values() if d), reverse=True)
            if len(daten) < len(f) or daten[0] == daten[1]:
                unklar.append(name)
                continue
        links[name] = max(f, key=lambda k: f[k] or datetime.datetime.min)
    if unklar:
        raise LinkFehler('Die Linkseite nennt diese Pakete mehrfach und gleich alt, der richtige Link ist nicht erkennbar '
                         '(alte Datei im Teamordner löschen): ' + ', '.join(sorted(unklar)))
    return links


def _abruf(a):
    try:
        with urllib.request.urlopen(urllib.request.Request(a, headers={'User-Agent': 'Mozilla/5.0'}), timeout=120) as r:
            return r.read().decode('utf-8', 'replace')
    except (urllib.error.URLError, OSError) as e:
        raise LinkFehler('Die Linkseite ist nicht erreichbar (%s).' % getattr(e, 'reason', e))   # nie die Adresse ausgeben


def _mit_passwort(a, pw):
    return a + ('&' if '?' in a else '?') + 'pw=' + urllib.parse.quote(pw, safe='')


def _fragen(falsch):
    """Fragt die Lehrkraft nach dem Passwort der Linkseite: Fenster, sonst Terminal. None: Fragen geht hier nicht oder abgebrochen.

    Das Fenster erscheint auch, wenn Claude das Skript startet. So kommt das Passwort nie in den Chat."""
    if os.environ.get('GITHUB_ACTIONS') or os.environ.get('CI'):
        return None
    text = ('Das Passwort war falsch. ' if falsch else '') + 'Passwort der Linkseite "ByCS-Links" (wird auf diesem Rechner gemerkt):'
    try:
        import tkinter
        from tkinter import simpledialog
        w = tkinter.Tk()
        w.withdraw()
        w.attributes('-topmost', True)
        try:
            return simpledialog.askstring('ByCS-Links', text, show='*', parent=w) or None
        finally:
            w.destroy()
    except Exception:                                # kein tkinter oder kein Bildschirm
        pass
    if sys.stdin and sys.stdin.isatty():
        import getpass
        try:
            return getpass.getpass(text + ' ') or None
        except (EOFError, KeyboardInterrupt):
            return None
    return None


def _anmelden(a):
    """Die Linkseite verlangt ein Passwort: gemerktes nehmen (Umgebung BYCS_LINKPASSWORT, git config bycs.linkpasswort),
    sonst fragen und in .git/config dieses Rechners merken. Gibt den Text der Seite zurück."""
    if re.search(r'[?&]pw=', a):
        raise LinkFehler('Das Passwort in der gespeicherten Adresse der Linkseite stimmt nicht mehr '
                         '(GitHub: Secret BYCS_LINKSEITE, am Rechner: git config bycs.linkseite).')
    pw = os.environ.get('BYCS_LINKPASSWORT', '').strip() or _git_config(PASSWORT)
    falsch = False
    for _ in range(4):
        if pw:
            text = _abruf(_mit_passwort(a, pw))
            if LOGIN not in text:
                if pw != _git_config(PASSWORT) and not os.environ.get('BYCS_LINKPASSWORT'):
                    subprocess.run(['git', 'config', '--local', PASSWORT, pw], cwd=ROOT)
                return text
            falsch = True
        pw = _fragen(falsch)
        if not pw:
            break
    raise LinkFehler(('Das Passwort der Linkseite ist falsch.' if falsch else 'Die Linkseite verlangt ein Passwort.')
                     + ' Einmal im eigenen Terminal eintragen (nie im Chat): git config %s "<Passwort>". '
                       'Kurse baut auch GitHub nach dem Push, dafür braucht es das nicht.' % PASSWORT)


def holen():
    """Alle Links von der Linkseite: {Dateiname des Pakets: Download-Link}."""
    a = adresse()
    text = _abruf(a)
    if LOGIN in text:                                # seit 13.11.2026 hat die Linkseite eine Passwortabfrage
        text = _anmelden(a)
    links = aus_seite(text)
    if not links:
        raise LinkFehler('Die Linkseite nennt kein Lernpaket (Aufbau geändert?).')
    return links


def link(paket, links=None):
    """Download-Link eines Pakets (Dateiname oder Pfad). Fehler, wenn die Linkseite es nicht kennt."""
    name = os.path.basename(paket.replace('\\', '/'))
    links = holen() if links is None else links
    if name not in links:
        raise LinkFehler('%s hat noch keinen Download-Link. Liegt das Paket schon im Teamordner (gepusht, GitHub-Lauf grün)? '
                         'Der Link entsteht kurz danach von selbst.' % name)
    return links[name]


def _pakete():   # Namen aller Lernpakete: aus den Themenordnern in Unterricht/ (die ZIPs liegen nicht in Git)
    import importlib.util
    spec = importlib.util.spec_from_file_location('unterrichtsmaterial', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'unterrichtsmaterial.py'))
    unterrichtsmaterial = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(unterrichtsmaterial)
    return sorted(unterrichtsmaterial.paketname(unterrichtsmaterial.aus_pfad(os.path.join(ROOT, *o.split('/')))) for o in unterrichtsmaterial.lernpakete())


def main(argv=None):
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            pass
    argv = list(sys.argv[1:] if argv is None else argv)
    if '--teamordner' in argv:
        t = teamordner()
        print('Teamordner gefunden: %s' % t if t else ANLEITUNG)
        return 0 if t else 1
    try:
        links = holen()
        if argv:
            for a in argv:
                print(link(a, links))
            return 0
    except LinkFehler as e:
        print('FEHLER: %s' % e)
        return 1
    pakete = _pakete()
    ohne = [p for p in pakete if p not in links]
    fremd = sorted(n for n in links if n not in pakete)
    print('Linkseite: %d Links, %d Lernpakete in Unterricht/, davon %d mit Link.' % (len(links), len(pakete), len(pakete) - len(ohne)))
    for p in ohne:
        print('  ohne Link: ' + p)
    if DOPPELT:
        print('  %d Pakete stehen doppelt auf der Linkseite (alte Datei noch im Teamordner). Genommen ist der Link der neueren Datei.' % len(DOPPELT))
    for n in fremd:
        print('  Link ohne Paket im Repo (alte Datei im Teamordner?): ' + n)
    return 1 if ohne else 0


if __name__ == '__main__':
    sys.exit(main())
