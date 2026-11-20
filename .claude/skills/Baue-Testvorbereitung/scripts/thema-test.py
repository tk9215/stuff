"""
thema-test.py - prüft die Aufgaben einer Testvorbereitung ohne Browser: Baukasten-Script und Thema-Block werden
aus der Seite gelesen und in einer JavaScript-Maschine ausgeführt (am Mac jsc aus macOS, sonst node).

Aufruf im Projektordner (am Mac python3 statt python):
  python .claude/skills/Baue-Testvorbereitung/scripts/thema-test.py Unterricht/.../<Thema>-Testvorbereitung/index.html [--anzahl 300]

Je Aufgabenart wird --anzahl-mal eine Aufgabe erzeugt und geprüft:
  - Titel und mindestens ein Feld; Feldtyp bekannt (zahl, wahl, text, kreuze)
  - zahl: Lösung ist eine endliche Zahl; wahl: Lösung steht in den Optionen, Optionen ohne Doppel;
    text: mindestens eine Lösung; kreuze: mindestens zwei Optionen, mindestens eine richtig
  - kein "undefined", "NaN" oder "[object" im Text
  - Math.random wird nicht direkt benutzt (gleiche Variante = gleiche Aufgabe)
Dazu: Prüfungszusammenstellung (Aufgaben aus "aufgaben" vorhanden), Punkte der Prüfung, je Art ein Beispiel.
Exitcode 1 bei einem Fehler. Nur Python-Standardbibliothek.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

JSC = '/System/Library/Frameworks/JavaScriptCore.framework/Versions/A/Helpers/jsc'

STUB = r'''
var window = this, location = { pathname: '/x' }, addEventListener = function () {};
var sessionStorage = { getItem: function () { return null; }, setItem: function () {} };
var document = { body: { classList: { contains: function () { return false; } }, insertAdjacentHTML: function () {} },
  querySelector: function () { return null; }, querySelectorAll: function () { return []; } };
var __out = typeof print === 'function' ? print : function (s) { console.log(s); };
'''

TEST = r'''
var CFG = null; TV.thema = function (c) { CFG = c; };
'''

AUSWERTEN = r'''
(function () {
  var N = __ANZAHL__, fehler = [], beispiele = {}, A = CFG.aufgaben || {};
  var typen = { zahl: 1, wahl: 1, text: 1, kreuze: 1 };
  function pruefe(id, a, nr) {
    var w = function (t) { fehler.push(id + ' #' + nr + ': ' + t); };
    if (!a || typeof a !== 'object') return w('gen() liefert kein Objekt');
    if (!a.titel) w('Titel fehlt');
    if (!a.felder || !a.felder.length) return w('keine Felder');
    var txt = JSON.stringify(a);
    if (/undefined|NaN|\[object/.test(txt)) w('enthält undefined/NaN/[object: ' + txt.slice(0, 160));
    a.felder.forEach(function (f, i) {
      var p = 'Feld ' + (i + 1) + ' (' + f.typ + ')';
      if (!typen[f.typ]) return w(p + ': unbekannter Typ');
      if (f.typ === 'zahl' && !(typeof f.loesung === 'number' && isFinite(f.loesung))) w(p + ': Lösung keine Zahl');
      if (f.typ === 'wahl') {
        if (!f.optionen || f.optionen.indexOf(f.loesung) < 0) w(p + ': Lösung nicht in den Optionen');
        else if (f.optionen.some(function (o, k) { return f.optionen.indexOf(o) !== k; })) w(p + ': Option doppelt');
      }
      if (f.typ === 'text' && ![].concat(f.loesung).filter(Boolean).length) w(p + ': keine Lösung');
      if (f.typ === 'kreuze' && !(f.optionen && f.optionen.length >= 2 && f.optionen.some(function (o) { return o[1]; }))) w(p + ': zu wenig Optionen oder keine richtig');
    });
  }
  var mr = Math.random, direkt = 0;
  Object.keys(A).forEach(function (id) {
    if (typeof A[id].gen !== 'function') { fehler.push(id + ': gen fehlt'); return; }
    if (!A[id].name) fehler.push(id + ': name fehlt');
    var vielfalt = {};
    Math.random = function () { direkt++; return mr(); };
    for (var i = 0; i < N; i++) {
      var a; try { a = A[id].gen(); } catch (e) { fehler.push(id + ' #' + i + ': Fehler ' + e); continue; }
      pruefe(id, a, i); if (i === 0) beispiele[id] = a; vielfalt[JSON.stringify(a)] = 1;
    }
    Math.random = mr;
    var a1 = TV.mitSaat(4711, A[id].gen), a2 = TV.mitSaat(4711, A[id].gen);
    if (JSON.stringify(a1) !== JSON.stringify(a2)) fehler.push(id + ': gleiche Variante ergibt verschiedene Aufgaben');
    beispiele[id].__verschieden = Object.keys(vielfalt).length;
  });
  if (direkt) fehler.push('Math.random wird direkt benutzt (' + direkt + '-mal): TV.zufall / TV.ganz / TV.wahl / TV.mische nehmen');
  var P = CFG.pruefung || {}, pk = 0, n = 0;
  if (!P.minuten) fehler.push('pruefung.minuten fehlt');
  (P.aufgaben || []).forEach(function (z) {
    if (!A[z[0]]) { fehler.push('Prüfung: Aufgabe "' + z[0] + '" fehlt in aufgaben'); return; }
    for (var i = 0; i < z[1]; i++) { pk += TV.punkte(A[z[0]].gen()); n++; }
  });
  __out(JSON.stringify({ fehler: fehler, beispiele: beispiele, pruefung: { minuten: P.minuten, aufgaben: n, punkte: pk }, titel: CFG.titel }));
})();
'''


def block(s, name):
    a, e = '<!-- Testvorbereitung:%s -->' % name, '<!-- /Testvorbereitung:%s -->' % name
    i, j = s.find(a), s.find(e)
    if i < 0 or j < i:
        raise SystemExit('Block Testvorbereitung:%s fehlt in der Seite.' % name)
    return re.sub(r'</?script>', '', s[i + len(a):j])


def maschine():
    if os.path.exists(JSC):
        return [JSC]
    n = shutil.which('node')
    if n:
        return [n]
    return None


def main():
    args = sys.argv[1:]
    if not args:
        raise SystemExit(__doc__)
    n = 300
    if '--anzahl' in args:
        k = args.index('--anzahl')
        n = int(args[k + 1])
        del args[k:k + 2]
    with open(args[0], encoding='utf-8-sig') as f:
        s = f.read()
    m = maschine()
    if not m:
        print('Hinweis: keine JavaScript-Maschine gefunden (jsc oder node). Test übersprungen, Übungen im Browser durchklicken.')
        return 0
    code = STUB + block(s, 'script') + TEST + block(s, 'thema') + AUSWERTEN.replace('__ANZAHL__', str(n))
    with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False, encoding='utf-8') as t:
        t.write(code)
    try:
        r = subprocess.run(m + [t.name], capture_output=True, text=True, timeout=120)
    finally:
        os.unlink(t.name)
    zeilen = [z for z in r.stdout.splitlines() if z.startswith('{')]
    if r.returncode or not zeilen:
        print('FEHLER beim Ausführen des Scripts:\n' + (r.stderr or r.stdout)[-2000:])
        return 1
    d = json.loads(zeilen[-1])
    print('Thema: %s' % d.get('titel'))
    for id_, a in d['beispiele'].items():
        verschieden = a.pop('__verschieden', '?')
        felder = '; '.join('%s: %s' % (f.get('label') or f['typ'], f.get('loesung', '[Kreuze]')) for f in a['felder'])
        print('  %-16s %s verschiedene in %d Läufen | Beispiel: %s | %s' % (id_, verschieden, n, a.get('titel'), felder[:150]))
    p = d['pruefung']
    print('Prüfung: %s Minuten, %s Aufgaben, %s Punkte' % (p['minuten'], p['aufgaben'], p['punkte']))
    if d['fehler']:
        print('FEHLER (%d):' % len(d['fehler']))
        for f in d['fehler'][:40]:
            print('  ' + f)
        return 1
    print('Alle Aufgaben in Ordnung.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
