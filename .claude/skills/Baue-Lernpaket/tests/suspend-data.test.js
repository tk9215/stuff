/*
  suspend-data.test.js - prueft Speichern und Wiederherstellen der Eingaben (cmi.suspend_data) von Fachunterricht.html mit scorm-api.js.
  Aufruf im Projektordner:
    node .claude/skills/Baue-Lernpaket/tests/suspend-data.test.js
  Ohne installiertes Node geht auch die Node-Laufzeit von VS Code (Git Bash):
    ELECTRON_RUN_AS_NODE=1 "$LOCALAPPDATA/Programs/Microsoft VS Code/Code.exe" .claude/skills/Baue-Lernpaket/tests/suspend-data.test.js
  Ablauf: lokaler Webserver + Chrome/Edge ohne Fenster. Eine Testseite stellt eine Fake-API_1484_11 bereit (wie Moodle) und laedt
  Testfassungen der Vorlage im iframe; Schliessen = iframe verlassen (pagehide, wie beim Schliessen des Moodle-Fensters).
  Die Fake-API trennt Server und Sitzung wie Moodle: Initialize laedt LMS.server, aber wie Moodle (get_scorm_default) nur bei
  cmi.exit = suspend auf dem Server; Commit ergaenzt LMS.server (alte Werte bleiben, bis sie ueberschrieben werden) oder
  scheitert bei LMS.fail (abgemeldet, Verbindung weg; Moodle antwortet dann "false").
  Ziele (cmi.objectives) prueft die Fake-API wie Moodle (scorm_13.js): Kennung nur einmal und eindeutig, Nummern lueckenlos, erst die Kennung,
  Zahlen als CMIDecimal; Initialize setzt wie Moodle das Ziel PRIMARYOBJ aus dem Manifest auf Nummer 0. Jede Ablehnung zaehlt als Fehler (Test 18).
  Test 17 prueft Punkte je Aufgabe (data-gewicht), Kennungen im Bericht "Interaktionen" und die Ziele je Niveau und je Aufgabe.
  Das alte Speicherformat { n, v } erzeugt die Vorlage aus Commit 90f815b (letzter Stand vor der Umstellung auf Schluessel).
  Anderer Browser: Umgebungsvariable CHROME=<Pfad zur exe>. Rueckgabe: Exit-Code 0 = alles bestanden.
*/
'use strict';
const fs = require('fs'), path = require('path'), http = require('http'), os = require('os'), cp = require('child_process'), crypto = require('crypto');

const repo = path.resolve(__dirname, '..', '..', '..', '..');
const OLD_COMMIT = '90f815b';
const read = p => fs.readFileSync(path.join(repo, p), 'utf8');
const git = p => cp.execSync('git show ' + OLD_COMMIT + ':' + p, { cwd: repo, maxBuffer: 1 << 26 }).toString('utf8');
const PAGE = '.claude/gemeinsam/templates/Fachunterricht.html', API = '.claude/skills/Baue-Lernpaket/templates/scorm-api.js';
/* Im alten Commit hiessen die Skills noch ToHTML und ToScorm, die Vorlage page.html */
const OLD_PAGE = '.claude/skills/ToHTML/templates/page.html', OLD_API = '.claude/skills/ToScorm/templates/scorm-api.js';

/* Testseite: 22 Felder (eines davon im Lösungsvorschlag), alle Feldarten der Vorlage */
const MAIN = `
<section class="level foundation"><h2>Einsteigerniveau</h2>
  <div class="task"><span class="tt">Aufgabe 1 - Begriffe</span>
    <p>Bauteil: <input type="text" data-ok="Passfeder"></p>
    <p>Maß: <input type="text" data-ok="12,5" data-tol="0,1"> mm</p>
  </div>
  <div class="task"><span class="tt">Aufgabe 2 - Auswahl</span><!--V2B-->
    <label><input type="radio" name="q2"> A</label>
    <label><input type="radio" name="q2" data-ok> B</label>
    <label><input type="radio" name="q2"> C</label>
  </div>
</section>
<section class="level core"><h2>Prüfungsniveau</h2>
  <div class="task"><span class="tt">Aufgabe 3 - Mehrfachauswahl</span>
    <label><input type="checkbox" data-ok> A</label>
    <label><input type="checkbox"> B</label>
    <label><input type="checkbox" data-ok> C</label><!--V2-->
  </div>
  <div class="task"><span class="tt">Aufgabe 4 - Zuordnen und Begründen</span>
    <select><option value="">-</option><option>Formschluss</option><option data-ok>Kraftschluss</option></select>
    <textarea data-keys="Formschluss; Nut"></textarea>
  </div>
  <div class="task"><span class="tt">Aufgabe 5 - Tabelle</span>
    <table><tr><td><input type="text"></td><td><input type="text"></td></tr><tr><td><input type="text"></td><td><input type="text"></td></tr></table>
  </div>
  <div class="task"><span class="tt">Aufgabe 6 - Werte</span>
    <input type="text"> <input type="text"> <input type="text"> <input type="text">
  </div>
</section>
<section class="level challenge"><h2>Profiniveau</h2>
  <div class="task"><span class="tt">Aufgabe 7 - Freitext</span>
    <textarea></textarea>
    <details class="sol"><summary>Lösungsvorschlag</summary><p>Beispiel: <input type="text"></p></details>
  </div>
  <div class="task"><span class="tt">Aufgabe 8 - Spiel</span>
    <input type="text" readonly data-score="richtig">
    <select><option value="">-</option><option>ja</option><option>nein</option></select><!--V3-->
  </div>
</section>`;
/* ganz andere Fassung: kein Schlüssel passt */
const MAIN4 = `
<section class="level core"><h2>Neu</h2>
  <div class="task" id="n1"><span class="tt">Neu 1</span><input type="text"> <input type="text"></div>
  <div class="task" id="n2"><span class="tt">Neu 2</span><textarea></textarea></div>
</section>`;
/* Punkte je Aufgabe: Gewichte 1 und 3 im Einsteigerniveau (10 und 30 P.), zwei Aufgaben mit gleicher Nummer, eine Aufgabe ohne Feld,
   Gewicht mit Komma im Profiniveau (einzige Aufgabe dort: 20 P.) */
const MAIN5 = `
<section class="level foundation"><h2>Einsteigerniveau</h2>
  <div class="task"><span class="tt">Aufgabe 1.1 - Begriff</span><input type="text" data-ok="Passfeder" data-k="a1-1"></div>
  <div class="task" data-gewicht="3"><span class="tt">Aufgabe 1.2 - Auswahl</span>
    <label><input type="radio" name="w2" data-k="a2-1"> A</label><label><input type="radio" name="w2" data-ok data-k="a2-2"> B</label></div>
</section>
<section class="level core"><h2>Prüfungsniveau</h2>
  <div class="task"><span class="tt">Aufgabe 2.1 – Zahl</span><input type="text" data-ok="12,5" data-tol="0,1" data-k="a3-1"></div>
  <div class="task"><span class="tt">Aufgabe 2.1 – Begründung</span><textarea data-k="a4-1"></textarea></div>
  <div class="task"><span class="tt">Info</span><p>ohne Feld</p></div>
</section>
<section class="level challenge"><h2>Profiniveau</h2>
  <div class="task" data-gewicht="2,5"><span class="tt">Aufgabe 3.1: Transfer</span><textarea data-keys="Formschluss; Nut" data-k="a6-1"></textarea></div>
</section>`;
/* Ganze Punkte: drei gleiche Aufgaben im Einsteigerniveau, kein Prüfungsniveau, zwei gleiche im Profiniveau.
   Niveaus 40:20 = 67 und 33; Einsteiger 22, 22, 23; Profi 16, 17 (Restpunkte an die letzten) */
const MAIN6 = `
<section class="level foundation"><h2>Einsteigerniveau</h2>
  <div class="task"><span class="tt">Aufgabe 1.1 - A</span><input type="text" data-ok="a" data-k="a1-1"></div>
  <div class="task"><span class="tt">Aufgabe 1.2 - B</span><input type="text" data-ok="b" data-k="a2-1"></div>
  <div class="task"><span class="tt">Aufgabe 1.3 - C</span><input type="text" data-ok="c" data-k="a3-1"></div>
</section>
<section class="level challenge"><h2>Profiniveau</h2>
  <div class="task"><span class="tt">Aufgabe 3.1 - D</span><textarea data-keys="Formschluss; Nut" data-k="a4-1"></textarea></div>
  <div class="task"><span class="tt">Aufgabe 3.2 - E</span><textarea data-keys="Formschluss; Nut" data-k="a5-1"></textarea></div>
</section>`;
const variant = (m, r) => Object.keys(r || {}).reduce((s, k) => s.replace('<!--' + k + '-->', r[k]), m).replace(/<!--V\w+-->/g, '');
/* Test-Passwort der Lehrkraft (Eingabe wird wie auf der Seite getrimmt und groß geschrieben) */
const PW = 'test', PW_HASH = crypto.createHash('sha256').update('bs-lernpaket|' + PW.toUpperCase()).digest('hex');
function page(tpl, main) {
  const h = tpl.replace(/<main class="wrap">[\s\S]*?<\/main>/, '<main class="wrap">' + main + '\n</main>')
    .replace('<meta name="loesung-hash" content="">', '<meta name="loesung-hash" content="' + PW_HASH + '">');
  return h.replace('</head>', '<script src="scorm-api.js"></script>\n</head>');   /* wie build-scorm.py */
}

/* Eingaben der Lernenden in v1 (Reihenfolge aller Felder; Radio/Checkbox 1/0, Auswahl = Index) */
const A = ['Passfeder', '12,5', 0, 1, 0, 1, 0, 1, 2, 'Formschluss mit Nut', 'A1', 'B2', '', 'D4', 'x', '', 'z', 'w',
  'Zwei Zeilen\nmit Umlauten äöü ß und „Zitat“', '', '6 von 8 richtig', 1];
const ins = (a, i, v) => a.slice(0, i).concat([v], a.slice(i));
const cfg = {
  A, pw: PW, warn: 'Gespeicherter Stand passt nicht ganz zu dieser Version – bitte Lehrkraft informieren.',
  v2: ins(A, 8, ''), v2b: ins(A, 2, ''), v3: A.concat(['']), v4: ['', '', ''],
  /* v5: 1.1 richtig (10), 1.2 falsch (0 von 30), 2.1 richtig (20), 2.1-2 ohne Bewertung (20), 3.1 ein Begriff von zwei (10) = 60; ohne Gewichte 70 */
  A5: ['Passfeder', 1, 0, '12,5', 'Eigene Begründung', 'Formschluss mit Passfeder'],
  /* v6: 1.1 richtig (22), 1.2 richtig (22), 1.3 falsch (0 von 23), 3.1 halb (8 von 16), 3.2 halb (8,5 -> 9 von 17) = 61 */
  A6: ['a', 'b', 'x', 'Formschluss ja', 'Formschluss ja'],
  keep5min: /KEEPALIVE_MS = 5 \* 60000/.test(read(API)) && /setInterval\(ScormReport\.keepAlive, KEEPALIVE_MS\)/.test(read(API))
};

const files = {
  '/harness.html': '<!doctype html><meta charset="utf-8"><title>SCORM-Test</title><iframe id="fr" style="width:1000px;height:700px"></iframe>' +
    '<script>(' + harnessMain.toString() + ')(' + JSON.stringify(cfg) + ');</script>',
  '/new/scorm-api.js': read(API),
  '/old/scorm-api.js': git(OLD_API)
};
const tplNew = read(PAGE), tplOld = git(OLD_PAGE);
files['/new/v1.html'] = page(tplNew, variant(MAIN));
files['/new/v2.html'] = page(tplNew, variant(MAIN, { V2: '<p>Begründung: <input type="text"></p>' }));
files['/new/v2b.html'] = page(tplNew, variant(MAIN, { V2B: '<p>Notiz: <input type="text" data-k="a2-notiz"></p>' }));
files['/new/v3.html'] = page(tplNew, variant(MAIN, { V3: ' <input type="text">' }));
files['/new/v4.html'] = page(tplNew, MAIN4);
files['/new/v5.html'] = page(tplNew, MAIN5);
files['/new/v6.html'] = page(tplNew, MAIN6);
files['/old/v1.html'] = page(tplOld, variant(MAIN));

/* ---------- läuft im Browser (Testseite mit Fake-LMS) ---------- */
function harnessMain(cfg) {
  const LMS = { data: {}, server: {}, fail: false, commits: 0, errors: [] };   /* errors: abgelehnte SetValue, bleibt über alle Tests (Test 18) */
  const copy = o => Object.assign({}, o);
  const count = (what) => { let n = 0; const rx = new RegExp('^cmi\\.' + what + '\\.(\\d+)\\.id$'); for (const k in LMS.data) { const m = rx.exec(k); if (m) n = Math.max(n, +m[1] + 1); } return n; };
  const err = (k, v, why) => { LMS.errors.push(k + ' = ' + v + ': ' + why); return 'false'; };
  const DEC = /^-?\d{1,5}(\.\d{1,18})?$/;
  window.API_1484_11 = {
    Initialize: () => {
      LMS.data = LMS.server['cmi.exit'] === 'suspend' ? copy(LMS.server) : { 'cmi.learner_name': LMS.server['cmi.learner_name'], 'cmi.learner_id': LMS.server['cmi.learner_id'] };
      if (LMS.pass) LMS.data['cmi.scaled_passing_score'] = LMS.pass;   /* Bestehensgrenze aus dem Manifest, nur lesbar */
      LMS.data['cmi.objectives.0.id'] = 'PRIMARYOBJ';   /* wie Moodle (get_scorm_default): Ziel aus dem Manifest, nach den gespeicherten Werten */
      return 'true';
    },
    Terminate: () => 'true',
    Commit: () => { LMS.commits++; if (LMS.fail) return 'false'; Object.assign(LMS.server, LMS.data); return 'true'; },
    GetValue: k => k === 'cmi.interactions._count' ? String(count('interactions')) : k === 'cmi.objectives._count' ? String(count('objectives')) : (k in LMS.data ? LMS.data[k] : ''),
    SetValue: (k, v) => {
      v = String(v);
      let m = /^cmi\.objectives\.(\d+)\.(.+)$/.exec(k);
      if (m) {   /* wie Moodle (scorm_13.js) */
        const n = +m[1], c = count('objectives'), f = m[2];
        if (f === 'id') {
          if (!/^\S{1,4000}$/.test(v)) return err(k, v, '406 Kennung mit Leerzeichen');
          if (n > c) return err(k, v, '351 Nummer nicht lückenlos');
          if (n < c && LMS.data[k] !== v) return err(k, v, '351 Kennung nur einmal (write once)');
          if (n === c && Object.keys(LMS.data).some(x => /^cmi\.objectives\.\d+\.id$/.test(x) && LMS.data[x] === v)) return err(k, v, '351 Kennung doppelt');
        } else {
          if (n >= c) return err(k, v, '408 erst die Kennung');
          if (/^score\.(raw|min|max)$/.test(f) && !DEC.test(v)) return err(k, v, '406 keine Dezimalzahl');
          if (f === 'score.scaled' && (!DEC.test(v) || Math.abs(+v) > 1)) return err(k, v, '407 scaled außerhalb -1..1');
          if (f === 'completion_status' && !/^(completed|incomplete|not attempted|unknown)$/.test(v)) return err(k, v, '406 Status');
        }
      }
      m = /^cmi\.interactions\.\d+\.(id|weighting)$/.exec(k);
      if (m && m[1] === 'id' && !/^\S{1,4000}$/.test(v)) return err(k, v, '406 Kennung mit Leerzeichen');
      if (m && m[1] === 'weighting' && !DEC.test(v)) return err(k, v, '406 keine Dezimalzahl');
      LMS.data[k] = v; return 'true';
    },
    GetLastError: () => '0', GetErrorString: () => '', GetDiagnostic: () => ''
  };
  const fr = document.getElementById('fr'), results = [];
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const open = url => new Promise(r => { fr.onload = () => setTimeout(r, 150); fr.src = url + '?t=' + Math.random(); });
  const close = () => new Promise(r => { fr.onload = () => setTimeout(r, 50); fr.src = 'about:blank'; });
  const doc = () => fr.contentDocument, win = () => fr.contentWindow;
  const BAK = 'scorm-sicherung|';
  const baks = () => Object.keys(localStorage).filter(k => k.indexOf(BAK) === 0);
  const reset = () => {
    LMS.server = { 'cmi.learner_name': 'Test, Person', 'cmi.learner_id': '4711' }; LMS.data = copy(LMS.server); LMS.fail = false; LMS.commits = 0; LMS.pass = '0.7';
    baks().forEach(k => localStorage.removeItem(k));
  };
  const fields = () => [].slice.call(doc().querySelectorAll('main input:not([type=button]):not([type=submit]):not([type=hidden]), main textarea, main select'));
  const values = () => fields().map(f => f.tagName === 'SELECT' ? f.selectedIndex : (f.type === 'checkbox' || f.type === 'radio') ? (f.checked ? 1 : 0) : f.value);
  function fill(vals) {
    fields().forEach((f, i) => {
      const v = vals[i];
      if (v === undefined) return;
      if (f.tagName === 'SELECT') { if (!v) return; f.selectedIndex = v; }
      else if (f.type === 'checkbox' || f.type === 'radio') { if (!v) return; f.checked = true; }
      else { if (v === '') return; f.value = v; }
      f.dispatchEvent(new Event('input', { bubbles: true })); f.dispatchEvent(new Event('change', { bubbles: true }));
    });
  }
  const sd = () => LMS.data['cmi.suspend_data'] || '';
  const state = () => { try { return JSON.parse(sd()).s; } catch (e) { return undefined; } };
  const inter = () => JSON.stringify(Object.keys(LMS.data).filter(k => k.indexOf('cmi.interactions.') === 0).sort().map(k => [k, LMS.data[k]]));
  const srvState = () => { try { return JSON.parse(LMS.server['cmi.suspend_data']).s; } catch (e) { return undefined; } };
  const info = () => doc().getElementById('saveInfo');
  const alarm = () => doc().getElementById('saveAlarm'), alarmOn = () => !!alarm() && !alarm().hidden;
  const type = (i, v) => { const f = fields()[i]; f.value = v; f.dispatchEvent(new Event('input', { bubbles: true })); };
  const same = (a, b) => JSON.stringify(a) === JSON.stringify(b);
  const noError = () => { const b = doc().getElementById('page-error'); return !b || b.style.display !== 'block'; };

  async function test(name, fn) {
    const t = { name, checks: [] }; results.push(t);
    const check = (ok, msg, extra) => t.checks.push({ ok: !!ok, msg, extra: ok ? undefined : extra });
    try { await fn(check); } catch (e) { check(false, 'Ausnahme: ' + e.message); }
    try { if (fr.src !== 'about:blank') await close(); } catch (e) { /* still */ }
  }

  (async function () {
    await test('1. Eingaben speichern, neu laden: alle Werte wieder da', async check => {
      reset(); await open('/new/v1.html'); check(noError(), 'kein roter Fehlerkasten');
      fill(cfg.A); await sleep(1100);
      const s = state();
      check(s && s.f === 2 && s.k && !('v' in s), 'gespeichert im neuen Format { f: 2, k }', s);
      check(s && s.k['a1-1'] === 'Passfeder' && s.k['a2-2'] === 1 && s.k['a4-1'] === 2 && s.k['a8-1'] === '6 von 8 richtig', 'Schlüssel Aufgabe-Nr. (a1-1, a2-2, a4-1, a8-1)', s && s.k);
      check(s && !Object.keys(s.k).some(k => k.indexOf('a7-2') === 0), 'Feld im Lösungsvorschlag wird nicht gespeichert', s && s.k);
      await close();
      check(LMS.data['cmi.exit'] === 'suspend', 'cmi.exit = suspend (Abgabe-Modus)', LMS.data['cmi.exit']);
      await open('/new/v1.html');
      check(same(values(), cfg.A), 'alle Werte wiederhergestellt', values());
      check(info().className.indexOf('bad') < 0, 'kein Warnhinweis', info().textContent);
      check(noError(), 'kein roter Fehlerkasten');
    });

    await test('2. Gespeicherter Stand + Fassung mit einem Feld mehr: alte Werte da, neues Feld leer, nichts überschrieben', async check => {
      reset(); await open('/new/v1.html'); fill(cfg.A); await close();
      const k0 = state().k, i0 = inter();
      await open('/new/v2.html');
      check(same(values(), cfg.v2), 'Werte wiederhergestellt, neues Feld (Ende Aufgabe 3) leer', values());
      check(info().className.indexOf('bad') < 0, 'kein Warnhinweis (alle gespeicherten Werte zugeordnet)', info().textContent);
      check(same(state().k, k0), 'gespeicherte Eingaben unverändert', state());
      check(inter() === i0, 'Interaktionen unverändert');
      await close();
      check(same(state().k, k0), 'nach dem Schließen unverändert', state());
      await open('/new/v2b.html');
      check(same(values(), cfg.v2b), 'neues Feld mit eigenem data-k am Anfang von Aufgabe 2: übrige Werte bleiben richtig', values());
      check(noError(), 'kein roter Fehlerkasten');
    });

    await test('3. Altes Format {n:22, v:[...]} in Fassung mit 23 Feldern: Werte da, danach neues Format', async check => {
      reset(); await open('/old/v1.html'); fill(cfg.A); await close();
      const s0 = state();
      check(s0 && s0.n === 22 && Array.isArray(s0.v) && s0.v.length > 0, 'alte Vorlage hat im alten Format gespeichert (n = 22)', s0);
      const legacy = sd();
      await open('/new/v3.html');
      check(same(values(), cfg.v3), 'Werte nach Position wiederhergestellt, Feld 23 leer', values());
      const s1 = state();
      check(s1 && s1.f === 2 && !('v' in s1) && s1.k['a1-1'] === 'Passfeder' && s1.k['a8-2'] === 1, 'suspend_data jetzt im neuen Format', s1);
      check(info().textContent === cfg.warn, 'Hinweis "passt nicht ganz" (Feldanzahl geändert, Zuordnung nach Position)', info().textContent);
      await close(); await open('/new/v3.html');
      check(same(values(), cfg.v3), 'erneut geöffnet: Werte da', values());
      check(info().className.indexOf('bad') < 0, 'erneut geöffnet: kein Hinweis mehr', info().textContent);
      await close();
      /* 3a: gleiche Feldanzahl (neu gebautes Paket, Seite unverändert) */
      LMS.server['cmi.suspend_data'] = legacy;
      await open('/new/v1.html');
      check(same(values(), cfg.A), '3a: altes Format, gleiche Fassung: alle Werte da', values());
      check(info().className.indexOf('bad') < 0, '3a: kein Hinweis', info().textContent);
      check(state().f === 2, '3a: ins neue Format umgeschrieben', state());
      check(noError(), 'kein roter Fehlerkasten');
    });

    await test('4. Gespeicherter Stand, aber kein Wert passt: suspend_data und Interaktionen bleiben unverändert', async check => {
      reset(); await open('/new/v1.html'); fill(cfg.A); await close();
      const sd0 = sd(), i0 = inter();
      check(i0.indexOf('Passfeder') > 0, 'Interaktionen mit Antworten vorhanden');
      await open('/new/v4.html');
      check(same(values(), cfg.v4), 'Felder leer', values());
      check(info().textContent === cfg.warn && info().className.indexOf('bad') > -1, 'Hinweis "passt nicht ganz" (rot)', info().textContent);
      check(sd() === sd0, 'suspend_data unverändert nach dem Öffnen');
      check(inter() === i0, 'Interaktionen unverändert nach dem Öffnen (keine Meldung "offen")');
      await sleep(1200);
      check(sd() === sd0 && inter() === i0, 'unverändert nach 1,2 s');
      await close();
      check(sd() === sd0 && inter() === i0, 'unverändert nach dem Schließen');
      await open('/new/v4.html');
      const f = fields()[0]; f.value = 'neu'; f.dispatchEvent(new Event('input', { bubbles: true })); await sleep(1100);
      check(state() && state().k['n1-1'] === 'neu', 'erst nach eigener Eingabe wird wieder gespeichert', state());
      check(info().textContent === cfg.warn, 'Hinweis bleibt in dieser Sitzung stehen', info().textContent);
      check(noError(), 'kein roter Fehlerkasten');
    });

    await test('5. Nach submit() ändert nichts mehr suspend_data', async check => {
      reset(); await open('/new/v1.html'); fill(cfg.A); await sleep(900);
      doc().getElementById('subBtn').click(); doc().getElementById('subOk').click(); await sleep(100);
      const sd0 = sd(), s0 = state();
      check(LMS.data['cmi.completion_status'] === 'completed' && JSON.parse(sd0).x === 1 && s0.sub === 1, 'abgegeben (completed, Abgabe-Vermerk)', sd0.slice(0, 200));
      check(fields().every(f => f.readOnly || f.disabled), 'alle Felder gesperrt');
      const f = fields()[0]; f.value = 'geändert'; f.dispatchEvent(new Event('input', { bubbles: true })); await sleep(1100);
      check(win().ScormReport.saveState({ f: 2, k: { 'a1-1': 'x' } }) === false, 'saveState nach der Abgabe abgelehnt');
      win().ScormReport.task('a1', { level: 'foundation', done: true, score: 0, response: 'x' }); win().ScormReport.flush();
      check(sd() === sd0, 'suspend_data unverändert nach Eingabe, saveState und task');
      await close();
      check(sd() === sd0, 'unverändert nach dem Schließen');
      check(LMS.data['cmi.exit'] === 'suspend', 'cmi.exit bleibt suspend', LMS.data['cmi.exit']);
      await open('/new/v1.html');
      check(doc().body.classList.contains('submitted') && same(values(), cfg.A), 'erneut geöffnet: abgegebener Stand gesperrt sichtbar', values());
      await close();
      check(sd() === sd0, 'unverändert nach erneutem Öffnen und Schließen');
    });

    await test('6. scorm-api.js: leerer Stand ersetzt keine gespeicherten Eingaben', async check => {
      reset(); await open('/new/v1.html'); fill(cfg.A.slice(0, 2)); await sleep(1100);
      const sd0 = sd(), R = win().ScormReport;
      check(state() && state().k['a1-1'] === 'Passfeder', 'Ausgangsstand gespeichert', state());
      check(R.saveState({ f: 2, k: {} }) === false && sd() === sd0, 'saveState({ f: 2, k: {} }) abgelehnt, nichts geschrieben');
      check(R.saveState({ n: 22, v: [] }) === false && sd() === sd0, 'saveState({ n, v: [] }) abgelehnt');
      check(R.saveState({ f: 2, k: { 'a1-1': 'neu' } }) === true && state().k['a1-1'] === 'neu', 'Stand mit Eingaben wird gespeichert');
      fields().slice(0, 2).forEach(f => { f.value = ''; f.dispatchEvent(new Event('input', { bubbles: true })); }); await sleep(1100);
      check(state().k['a1-1'] === 'neu', 'Seite: alles gelöscht -> gespeicherter Stand bleibt', state());
    });

    await test('7. Bestehendes: zu langer Stand wird nicht gespeichert (stateLimit)', async check => {
      reset(); await open('/new/v1.html'); fill(cfg.A.slice(0, 2)); await sleep(1100);
      const s0 = state(), t = fields()[9];
      t.value = new Array(65001).join('x'); t.dispatchEvent(new Event('input', { bubbles: true })); await sleep(1100);
      check(same(state(), s0) && sd().length < 64000, 'gespeicherte Eingaben unverändert, suspend_data unter 64000 Zeichen', sd().length);
      check(/Zu viele Zeichen/.test(info().textContent) && info().className.indexOf('bad') > -1, 'roter Hinweis "Zu viele Zeichen"', info().textContent);
    });

    await test('8. Lehrkraft nimmt die Abgabe zurück: weiterarbeiten, neu abgeben', async check => {
      const $ = s => doc().querySelector(s), sub = () => doc().body.classList.contains('submitted');
      const pw = async v => { $('#unsubBtn').click(); $('#pwIn').value = v; $('#pwForm').requestSubmit(); await sleep(100); };
      const free = () => { const ff = fields(), sc = ff.filter(f => f.hasAttribute('data-score')); return ff.every(f => sc.indexOf(f) > -1 || (!f.readOnly && !f.disabled)) && sc.every(f => f.readOnly); };
      reset(); await open('/new/v1.html'); fill(cfg.A); await sleep(900);
      check($('#unsubBtn').hidden, 'vor der Abgabe kein "Abgabe zurücknehmen"');
      $('#subBtn').click(); $('#subOk').click(); await sleep(100);
      const raw0 = LMS.data['cmi.score.raw'];
      check(sub() && !$('#unsubBtn').hidden && $('#subBtn').hidden, 'nach der Abgabe: "Abgabe zurücknehmen" statt "Abgeben"');
      await pw('falsch');
      check(sub() && /Falsches Passwort/.test($('#pwErr').textContent), 'falsches Passwort: bleibt abgegeben', $('#pwErr').textContent);
      check($('#pwT').textContent.indexOf('Abgabe zurücknehmen') === 0, 'Dialog heißt "Abgabe zurücknehmen"', $('#pwT').textContent);
      $('#pwCancel').click();
      await pw(' ' + cfg.pw + ' ');
      check(!sub() && !doc().body.classList.contains('solOpen'), 'zurückgenommen, Lehrkraft-Modus aus');
      check(free(), 'Felder wieder frei, Spielergebnis (readonly data-score) bleibt readonly');
      check(!$('#subBtn').hidden && $('#unsubBtn').hidden && !$('#subNote') && $('#resultInfo').textContent === '', 'Knöpfe und Hinweise wie vor der Abgabe');
      check(LMS.data['cmi.completion_status'] === 'incomplete' && LMS.data['cmi.success_status'] === 'unknown', 'Lernplattform: incomplete, success unknown',
        [LMS.data['cmi.completion_status'], LMS.data['cmi.success_status']]);
      check(!('x' in JSON.parse(sd())) && !state().sub, 'suspend_data ohne Abgabe-Vermerk', sd().slice(0, 200));
      check(LMS.data['cmi.score.raw'] === raw0, 'gleiche Eingaben: vorläufige Punkte unverändert', LMS.data['cmi.score.raw']);
      $('#unsubBtn').hidden = false; await pw(cfg.pw); $('#unsubBtn').hidden = true;
      check(!sub() && LMS.data['cmi.completion_status'] === 'incomplete', 'zweites Zurücknehmen ändert nichts');
      const f = fields()[0]; f.value = 'Keil'; f.dispatchEvent(new Event('input', { bubbles: true })); await sleep(1100);
      check(state().k['a1-1'] === 'Keil', 'Änderung nach dem Zurücknehmen gespeichert', state());
      check(LMS.data['cmi.score.raw'] !== raw0 && LMS.data['cmi.completion_status'] === 'incomplete', 'Punkte laufen nach dem Zurücknehmen live mit, weiter incomplete', [raw0, LMS.data['cmi.score.raw']]);
      await close(); await open('/new/v1.html');
      check(!sub() && fields()[0].value === 'Keil' && free(), 'neu geöffnet: nicht abgegeben, Änderung da, Felder frei', values());
      $('#subBtn').click(); $('#subOk').click(); await sleep(100);
      const raw1 = LMS.data['cmi.score.raw'];
      check(sub() && LMS.data['cmi.completion_status'] === 'completed' && raw1 !== raw0, 'neu abgegeben: completed, neue Punkte', [raw0, raw1]);
      check(LMS.data['cmi.success_status'] === (+raw1 >= 70 ? 'passed' : 'failed'), 'bestanden / nicht bestanden nach der neuen Bewertung', LMS.data['cmi.success_status']);
      await close(); await open('/new/v1.html');
      check(sub(), 'abgegeben aus früherer Sitzung: gesperrt');
      await pw(cfg.pw);
      check(!sub() && free() && LMS.data['cmi.completion_status'] === 'incomplete', 'auch nach erneutem Öffnen zurücknehmbar');
      await close(); await open('/new/v1.html');
      check(!sub() && same(values(), ['Keil'].concat(cfg.A.slice(1))), 'danach neu geöffnet: nicht abgegeben, alle Werte da', values());
      check(noError(), 'kein roter Fehlerkasten');
    });

    await test('9. ByCS speichert nicht mehr (abgemeldet): roter Hinweis, Sicherung im Browser, nach Neuanmeldung alles da', async check => {
      reset(); await open('/new/v1.html'); fill(cfg.A.slice(0, 4)); await sleep(1100);
      check(srvState() && srvState().k['a1-1'] === 'Passfeder', 'Ausgangsstand in der ByCS', srvState());
      check(!alarmOn() && baks().length === 0, 'solange das Speichern klappt: kein Hinweis, keine Sicherung', baks());
      LMS.fail = true;
      fill(cfg.A.map((v, i) => i < 4 ? undefined : v)); await sleep(1100);
      check(alarmOn() && /Nicht gespeichert/.test(alarm().textContent) && /in diesem Browser gesichert/.test(alarm().textContent),
        'roter Hinweis unten: nicht gespeichert, Eingaben im Browser gesichert', alarm() && alarm().textContent);
      check(info().textContent === 'Nicht gespeichert' && info().className.indexOf('bad') > -1, 'Knopfleiste: "Nicht gespeichert" (rot)', info().textContent);
      check(baks().length === 1 && baks()[0] === BAK + '4711|/new/v1.html', 'eine Sicherung je Person und Seite', baks());
      const b = baks().length ? JSON.parse(localStorage.getItem(baks()[0])) : { sd: '{}' };
      check(JSON.parse(b.sd).s && JSON.parse(b.sd).s.k['a4-2'] === 'Formschluss mit Nut', 'Sicherung enthält die neuen Eingaben', b.sd.slice(0, 200));
      check(!srvState().k['a4-2'], 'ByCS hat die neuen Eingaben nicht', srvState());
      await close();
      check(baks().length === 1, 'nach dem Schließen: Sicherung bleibt');
      LMS.fail = false; await open('/new/v1.html');
      check(same(values(), cfg.A), 'neu angemeldet und geöffnet: alle Werte da', values());
      check(/Sicherung im Browser/.test(info().textContent) && !alarmOn(), 'Meldung "aus der Sicherung im Browser wiederhergestellt", kein roter Hinweis', info().textContent);
      check(srvState() && same(srvState().k, state().k) && srvState().k['a4-2'] === 'Formschluss mit Nut', 'ByCS hat jetzt alle Eingaben', srvState());
      check(baks().length === 0, 'Sicherung gelöscht', baks());
      const ids = Object.keys(LMS.server).filter(k => /^cmi\.interactions\.\d+\.id$/.test(k)).map(k => LMS.server[k]);
      check(ids.length > 0 && new Set(ids).size === ids.length, 'Interaktionen in der ByCS, jede Aufgabe nur einmal', ids);
      check(Object.keys(LMS.server).some(k => /\.learner_response$/.test(k) && LMS.server[k].indexOf('Formschluss mit Nut') > -1), 'Interaktion mit der neuen Antwort in der ByCS');
      check(noError(), 'kein roter Fehlerkasten');
    });

    await test('10. Verbindung kurz weg, dann wieder da: Hinweis verschwindet, Sicherung gelöscht', async check => {
      reset(); await open('/new/v1.html'); fill(cfg.A.slice(0, 2)); await sleep(1100);
      LMS.fail = true; type(0, 'Keil'); await sleep(1100);
      check(alarmOn() && baks().length === 1, 'Hinweis und Sicherung');
      LMS.fail = false; type(0, 'Keil2'); await sleep(1100);
      check(!alarmOn() && info().textContent === 'Fortschritt gespeichert' && info().className.indexOf('bad') < 0, 'Hinweis weg, "Fortschritt gespeichert"', info().textContent);
      check(baks().length === 0 && srvState().k['a1-1'] === 'Keil2', 'Sicherung gelöscht, ByCS hat den neuen Stand', srvState());
      LMS.fail = true; await close();
      check(baks().length === 0, 'Schließen ohne Änderung, Commit scheitert: keine Sicherung (nichts Ungespeichertes)', baks());
      LMS.fail = false; await open('/new/v1.html');
      check(fields()[0].value === 'Keil2' && !/Sicherung/.test(info().textContent), 'neu geöffnet: Stand aus der ByCS', info().textContent);
    });

    await test('11. Veraltete Sicherung (inzwischen woanders gespeichert): Stand der ByCS gilt, Sicherung gelöscht', async check => {
      reset(); await open('/new/v1.html'); fill(cfg.A.slice(0, 2)); await sleep(1100);
      LMS.fail = true; type(0, 'alt'); await sleep(1100); await close();
      check(baks().length === 1, 'Sicherung vorhanden');
      const o = JSON.parse(LMS.server['cmi.suspend_data']); o.s.k['a1-1'] = 'anderer Rechner'; o.t = o.t + 5000;   /* anderer Rechner speichert */
      LMS.server['cmi.suspend_data'] = JSON.stringify(o);
      LMS.fail = false; await open('/new/v1.html');
      check(fields()[0].value === 'anderer Rechner' && !/Sicherung/.test(info().textContent), 'Stand aus der ByCS', values());
      check(baks().length === 0, 'veraltete Sicherung gelöscht', baks());
    });

    await test('12. Abgabe bei unterbrochener Verbindung: nach Neuanmeldung nachgeholt', async check => {
      reset(); await open('/new/v1.html'); fill(cfg.A); await sleep(1100);
      LMS.fail = true; type(0, 'Zylinderstift'); await sleep(1100);
      doc().getElementById('subBtn').click(); doc().getElementById('subOk').click(); await sleep(100);
      check(LMS.server['cmi.completion_status'] !== 'completed', 'ByCS hat die Abgabe nicht', LMS.server['cmi.completion_status']);
      check(alarmOn() && baks().length === 1, 'Hinweis und Sicherung');
      await close();
      LMS.fail = false; await open('/new/v1.html');
      check(doc().body.classList.contains('submitted') && same(values(), ['Zylinderstift'].concat(cfg.A.slice(1))), 'abgegebener Stand gesperrt sichtbar', values());
      check(Object.keys(LMS.server).some(k => /\.learner_response$/.test(k) && LMS.server[k].indexOf('Zylinderstift') > -1), 'Antwort aus der Zeit ohne Verbindung im Bericht (Interaktion)');
      check(LMS.server['cmi.completion_status'] === 'completed' && LMS.server['cmi.score.raw'] !== undefined && JSON.parse(LMS.server['cmi.suspend_data']).x === 1,
        'ByCS: completed, Punkte, Abgabe-Vermerk', [LMS.server['cmi.completion_status'], LMS.server['cmi.score.raw']]);
      check(baks().length === 0, 'Sicherung gelöscht', baks());
    });

    await test('13. Lebenszeichen alle 5 Minuten: Commit ohne Eingabe, meldet Timeout sofort, nach der Abgabe still', async check => {
      check(cfg.keep5min, 'scorm-api.js: setInterval(keepAlive) mit 5 Minuten');
      reset(); await open('/new/v1.html'); fill(cfg.A.slice(0, 2)); await sleep(1100);
      const R = win().ScormReport, sd0 = LMS.server['cmi.suspend_data'];
      let c = LMS.commits; R.keepAlive();
      check(LMS.commits === c + 1 && !alarmOn(), 'keepAlive: ein Commit, kein Hinweis');
      check(LMS.server['cmi.suspend_data'] === sd0, 'Stand unverändert (gleiches t)');
      LMS.fail = true; R.keepAlive();
      check(alarmOn() && baks().length === 0, 'Verbindung weg: Hinweis ohne eigene Eingabe, keine Sicherung (nichts Ungespeichertes)', baks());
      LMS.fail = false; R.keepAlive();
      check(!alarmOn() && info().className.indexOf('bad') < 0, 'Verbindung wieder da: Hinweis weg', info().textContent);
      doc().getElementById('subBtn').click(); doc().getElementById('subOk').click(); await sleep(100);
      c = LMS.commits; R.keepAlive();
      check(LMS.commits === c, 'nach der Abgabe kein Lebenszeichen');
      check(noError(), 'kein roter Fehlerkasten');
    });

    await test('14. Sitzung endet ohne sauberes Schließen (Timeout, Absturz): beim nächsten Öffnen ist alles da', async check => {
      reset(); await open('/new/v1.html');
      check(LMS.server['cmi.exit'] === 'suspend', 'cmi.exit = suspend schon beim Öffnen auf dem Server (Moodle lädt sonst nichts)', LMS.server['cmi.exit']);
      fill(cfg.A); await sleep(1100);
      LMS.fail = true; await close();   /* Schließen kommt nicht mehr an */
      LMS.fail = false; await open('/new/v1.html');
      check(same(values(), cfg.A), 'neu angemeldet und geöffnet: alle Werte da', values());
      check(noError(), 'kein roter Fehlerkasten');
    });

    await test('15. Moodle liefert nichts (cmi.exit fehlte, alter Stand auf dem Server): Öffnen überschreibt nichts, danach wieder da', async check => {
      reset(); await open('/new/v1.html'); fill(cfg.A); await close();
      const sd0 = LMS.server['cmi.suspend_data'], i0 = JSON.stringify(Object.keys(LMS.server).filter(k => k.indexOf('cmi.interactions.') === 0).map(k => LMS.server[k]));
      delete LMS.server['cmi.exit'];   /* wie mit dem alten Paket nach einem Timeout */
      await open('/new/v1.html');
      check(values().every(v => v === '' || v === 0), 'Moodle liefert nichts: Seite leer', values());
      await sleep(1100); await close();
      check(LMS.server['cmi.suspend_data'] === sd0, 'gespeicherter Stand auf dem Server nicht überschrieben');
      check(JSON.stringify(Object.keys(LMS.server).filter(k => k.indexOf('cmi.interactions.') === 0).map(k => LMS.server[k])) === i0, 'Interaktionen unverändert');
      check(LMS.server['cmi.exit'] === 'suspend', 'cmi.exit jetzt suspend');
      await open('/new/v1.html');
      check(same(values(), cfg.A), 'nächstes Öffnen: alle Werte wieder da', values());
    });

    await test('16. Abgegeben, Schließen kam nicht an, erneut geöffnet: Status, Punkte und Abgabe bleiben (nicht "unvollständig")', async check => {
      reset(); await open('/new/v1.html'); fill(cfg.A); await sleep(1100);
      doc().getElementById('subBtn').click(); doc().getElementById('subOk').click(); await sleep(100);
      await close();
      const keys = ['cmi.completion_status', 'cmi.success_status', 'cmi.score.raw', 'cmi.progress_measure', 'cmi.suspend_data'], s0 = keys.map(k => LMS.server[k]);
      check(s0[0] === 'completed', 'abgegeben: completed', s0);
      delete LMS.server['cmi.exit'];   /* wie mit dem alten Paket, wenn das Schließen nicht ankam */
      await open('/new/v1.html');
      check(values().every(v => v === '' || v === 0), 'Moodle liefert nichts: Seite leer', values());
      await sleep(1100); await close();
      check(same(keys.map(k => LMS.server[k]), s0), 'Status, Bewertung, Fortschritt und Stand auf dem Server unverändert', keys.map(k => LMS.server[k]));
      await open('/new/v1.html');
      check(doc().body.classList.contains('submitted') && same(values(), cfg.A), 'nächstes Öffnen: abgegebener Stand wieder da', values());
      check(LMS.server['cmi.completion_status'] === 'completed' && LMS.server['cmi.score.raw'] === s0[2], 'weiter completed mit gleichen Punkten');
      check(noError(), 'kein roter Fehlerkasten');
    });

    await test('17. Punkte je Aufgabe: Gewichte, Anzeige, Kennungen im Bericht "Interaktionen", Ziele je Niveau und je Aufgabe', async check => {
      const $ = s => doc().querySelector(s), T = () => [].slice.call(doc().querySelectorAll('main .task'));
      const pts = a => T().map(t => t.getAttribute(a)), before = t => win().getComputedStyle(t, '::before').content;
      const goals = () => {   /* Kennung -> Nummer, Status, Punkte, Höchstpunkte */
        const o = {};
        Object.keys(LMS.data).forEach(k => {
          const m = /^cmi\.objectives\.(\d+)\.id$/.exec(k); if (!m) return;
          const p = 'cmi.objectives.' + m[1] + '.';
          o[LMS.data[k]] = { n: +m[1], st: LMS.data[p + 'completion_status'], raw: LMS.data[p + 'score.raw'], max: LMS.data[p + 'score.max'] };
        });
        return o;
      };
      const iid = () => Object.keys(LMS.data).filter(k => /^cmi\.interactions\.\d+\.id$/.test(k)).map(k => LMS.data[k]).sort();
      const IDS = ['Aufgabe-1.1_Einsteiger_10P', 'Aufgabe-1.2_Einsteiger_30P', 'Aufgabe-2.1_Pruefung_20P', 'Aufgabe-2.1-2_Pruefung_20P', 'Aufgabe-3.1_Profi_20P'];
      const LV = ['1-Einsteigerniveau_40P', '2-Pruefungsniveau_40P', '3-Profiniveau_20P'];
      reset(); await open('/new/v5.html');
      check(noError(), 'kein roter Fehlerkasten');
      check(same(pts('data-pts'), ['10 P.', '30 P.', '20 P.', '20 P.', null, '20 P.']), 'Höchstpunkte: Gewichte 1 und 3 = 10 und 30 P., Gewicht "2,5" allein im Niveau = 20 P., Aufgabe ohne Feld ohne Punkte', pts('data-pts'));
      check(before(T()[1]) === '"30 P."', 'Punkte oben rechts an der Aufgabe sichtbar', before(T()[1]));
      check(Object.keys(goals()).length === 1, 'ohne Bearbeitung keine neuen Ziele (nur PRIMARYOBJ)', goals());
      fill(cfg.A5); await sleep(1100);
      check(same(iid(), IDS.slice().sort()), 'Kennungen im Bericht "Interaktionen": Titel bis zum Gedankenstrich, Niveau, Höchstpunkte, gleiche Nummer eindeutig', iid());
      const w2 = Object.keys(LMS.data).find(k => /^cmi\.interactions\.\d+\.id$/.test(k) && LMS.data[k] === IDS[1]);
      check(w2 && LMS.data[w2.replace(/id$/, 'weighting')] === '30', 'weighting der Interaktion = Höchstpunkte (30)', w2 && LMS.data[w2.replace(/id$/, 'weighting')]);
      let g = goals();
      check(g.PRIMARYOBJ && g.PRIMARYOBJ.n === 0 && LV.concat(IDS).every(id => g[id] && g[id].n > 0), 'Ziele je Niveau und je Aufgabe hinter PRIMARYOBJ', g);
      check(LV.concat(IDS).every(id => g[id] && g[id].st === 'completed'), 'alle bearbeitet: Status completed', g);
      check(LMS.data['cmi.score.raw'] === '60' && LMS.data['cmi.completion_status'] === 'incomplete' && LMS.data['cmi.success_status'] === undefined,
        'vor der Abgabe: vorläufige Punkte (60), Status incomplete, kein bestanden', [LMS.data['cmi.score.raw'], LMS.data['cmi.completion_status'], LMS.data['cmi.success_status']]);
      check(IDS.map(id => g[id] ? g[id].raw + '/' + g[id].max : '-').join(' ') === '10/10 0/30 20/20 20/20 10/20', 'vor der Abgabe: Punkte je Aufgabe in den Zielen', g);
      check(same(pts('data-ptsq'), ['10 von 10 P.', '0 von 30 P.', '20 von 20 P.', '20 von 20 P.', null, '10 von 20 P.']), 'erreichte Punkte je Aufgabe (data-ptsq)', pts('data-ptsq'));
      check(before(T()[1]) === '"30 P."', 'Die Lernenden sehen vor der Abgabe nur die Höchstpunkte', before(T()[1]));
      $('#subBtn').click(); $('#subOk').click(); await sleep(100);
      check(LMS.data['cmi.score.raw'] === '60' && /: 60 %/.test($('#resultInfo').textContent), 'Gesamtpunkte gewichtet: 60 (ohne Gewichte wären es 70), gleich auf der Seite', [LMS.data['cmi.score.raw'], $('#resultInfo').textContent]);
      check(before(T()[1]) === '"0 von 30 P."' && before(T()[5]) === '"10 von 20 P."', 'nach der Abgabe: erreichte Punkte an der Aufgabe', [before(T()[1]), before(T()[5])]);
      g = goals();
      const sc = id => g[id] ? g[id].raw + '/' + g[id].max : '-';
      check(same(LV.map(sc), ['10/40', '40/40', '10/20']), 'Ziele je Niveau: erreichte / höchste Punkte', LV.map(sc));
      check(same(IDS.map(sc), ['10/10', '0/30', '20/20', '20/20', '10/20']), 'Ziele je Aufgabe: erreichte / höchste Punkte', IDS.map(sc));
      const n0 = Object.keys(g).length;
      await close(); await open('/new/v5.html');
      g = goals();
      check(Object.keys(g).length === n0 && same(IDS.map(sc), ['10/10', '0/30', '20/20', '20/20', '10/20']), 'erneut geöffnet: keine doppelten Ziele, Punkte unverändert', g);
      check(noError(), 'kein roter Fehlerkasten');
      await close();
      /* neuer Versuch: nur Aufgabe 1.1 bearbeitet und abgegeben */
      reset(); await open('/new/v5.html'); fill(['Passfeder']); await sleep(1100);
      $('#subBtn').click(); $('#subOk').click(); await sleep(100);
      g = goals();
      check(LMS.data['cmi.score.raw'] === '10' && g[IDS[1]] && g[IDS[1]].st === 'incomplete' && sc(IDS[1]) === '0/30', 'nicht bearbeitete Aufgabe: Status incomplete, 0 Punkte', [LMS.data['cmi.score.raw'], g[IDS[1]]]);
      check(g[LV[0]] && g[LV[0]].st === 'incomplete' && sc(LV[0]) === '10/40', 'Niveau nicht vollständig bearbeitet: incomplete, 10 von 40', g[LV[0]]);
    });

    await test('17b. Ganze Punkte: Summe 100, Restpunkte an die letzten Aufgaben, Teilpunkte je Aufgabe gerundet, Seite = ByCS', async check => {
      const $ = s => doc().querySelector(s), T = () => [].slice.call(doc().querySelectorAll('main .task'));
      const pts = a => T().map(t => t.getAttribute(a));
      const goals = () => {
        const o = {};
        Object.keys(LMS.data).forEach(k => {
          const m = /^cmi\.objectives\.(\d+)\.id$/.exec(k); if (!m) return;
          const p = 'cmi.objectives.' + m[1] + '.';
          o[LMS.data[k]] = LMS.data[p + 'score.raw'] + '/' + LMS.data[p + 'score.max'];
        });
        return o;
      };
      reset(); await open('/new/v6.html');
      check(noError(), 'kein roter Fehlerkasten');
      check(same(pts('data-pts'), ['22 P.', '22 P.', '23 P.', '16 P.', '17 P.']), 'Höchstpunkte ganz, Summe 100: 67 (22, 22, 23) und 33 (16, 17)', pts('data-pts'));
      fill(cfg.A6); await sleep(1100);
      check(same(pts('data-ptsq'), ['22 von 22 P.', '22 von 22 P.', '0 von 23 P.', '8 von 16 P.', '9 von 17 P.']), 'erreichte Punkte ganz (8,5 wird 9)', pts('data-ptsq'));
      $('#subBtn').click(); $('#subOk').click(); await sleep(100);
      check(LMS.data['cmi.score.raw'] === '61' && /: 61 %/.test($('#resultInfo').textContent), 'Gesamtpunkte = Summe der Aufgaben = 61, gleich auf der Seite', [LMS.data['cmi.score.raw'], $('#resultInfo').textContent]);
      const g = goals();
      check(g['1-Einsteigerniveau_67P'] === '44/67' && g['3-Profiniveau_33P'] === '17/33', 'Ziele je Niveau: 44/67 und 17/33', g);
      check(g['Aufgabe-1.3_Einsteiger_23P'] === '0/23' && g['Aufgabe-3.1_Profi_16P'] === '8/16' && g['Aufgabe-3.2_Profi_17P'] === '9/17', 'Ziele je Aufgabe mit ganzen Punkten in der Kennung', g);
      check(Object.keys(LMS.data).every(k => !/score\.(raw|max)$/.test(k) || /^\d+$/.test(LMS.data[k])), 'alle gemeldeten Punkte ohne Komma');
      await close();
    });

    await test('17c. Ampel: rot unter 40, gelb bis unter 70, grün ab 70, über 90 Stern; bleibt nach der Abgabe', async check => {
      const $ = s => doc().querySelector(s), amp = () => { const a = $('#ampel'); return a && !a.hidden ? a.className + ':' + a.textContent : '-'; };
      const put = (i, v) => { const f = fields()[i]; f.value = v; f.dispatchEvent(new Event('input', { bubbles: true })); };
      reset(); await open('/new/v6.html');
      check(amp() === 'rot:Es ist noch viel zu tun', 'leer: rot', amp());
      check(win().getComputedStyle($('#ampel')).position === 'fixed', 'Overlay bleibt beim Scrollen sichtbar (position fixed)');
      put(0, 'a'); await sleep(50); check(amp() === 'rot:Es ist noch viel zu tun', '22 Punkte: rot', amp());
      put(1, 'b'); await sleep(50); check(amp() === 'gelb:Es ist nicht mehr weit', '44 Punkte: gelb', amp());
      put(2, 'c'); await sleep(50); check(amp() === 'gelb:Es ist nicht mehr weit', '67 Punkte: gelb', amp());
      put(3, 'Formschluss mit Nut'); await sleep(50); check(amp() === 'gruen:Bestehensgrenze erreicht', '83 Punkte: grün', amp());
      put(4, 'Formschluss mit Nut'); await sleep(1100); check(amp() === 'stern:Profilevel erreicht', '100 Punkte: Stern', amp());
      check(win().getComputedStyle($('#ampel'), '::before').content === '"★"', 'Stern wird als Zeichen ★ gezeichnet', win().getComputedStyle($('#ampel'), '::before').content);
      check(+win().getComputedStyle($('#ampel'), '::before').fontSize.replace('px', '') >= 24, 'Stern groß (mind. 24 px)', win().getComputedStyle($('#ampel'), '::before').fontSize);
      check(LMS.data['cmi.score.raw'] === '100' && LMS.data['cmi.completion_status'] === 'incomplete', 'ByCS: vorläufig 100, noch incomplete', [LMS.data['cmi.score.raw'], LMS.data['cmi.completion_status']]);
      $('#subBtn').click(); $('#subOk').click(); await sleep(100);
      check(amp() === 'stern:Profilevel erreicht', 'nach der Abgabe weiter sichtbar', amp());
      await close();
    });

    await test('17d. Bestehensgrenze aus der Lernplattform (scaled_passing_score): Ampel, Ergebnis und bestanden richten sich danach; ohne Wert 70', async check => {
      const $ = s => doc().querySelector(s), amp = () => { const a = $('#ampel'); return a && !a.hidden ? a.className : '-'; };
      const put = (i, v) => { const f = fields()[i]; f.value = v; f.dispatchEvent(new Event('input', { bubbles: true })); };
      reset(); LMS.pass = '0.6'; await open('/new/v6.html');
      check(win().ScormReport.passMark() === 60, 'passMark = 60', win().ScormReport.passMark());
      put(0, 'a'); put(1, 'b'); put(2, 'c'); await sleep(50);
      check(amp() === 'gruen', '67 Punkte bei Grenze 60: grün', amp());
      put(2, ''); await sleep(50);
      check(amp() === 'gelb', '44 Punkte bei Grenze 60: gelb', amp());
      put(2, 'c'); put(3, 'Formschluss'); await sleep(1100);
      $('#subBtn').click(); $('#subOk').click(); await sleep(100);
      check(LMS.data['cmi.success_status'] === 'passed' && /bestanden/.test($('#resultInfo').textContent) && !/nicht bestanden/.test($('#resultInfo').textContent), 'nach der Abgabe bei Grenze 60: bestanden', [LMS.data['cmi.success_status'], $('#resultInfo').textContent]);
      await close();
      reset(); LMS.pass = '0.9'; await open('/new/v6.html');
      put(0, 'a'); put(1, 'b'); put(2, 'c'); put(3, 'Formschluss mit Nut'); await sleep(50);
      check(amp() === 'gelb', '83 Punkte bei Grenze 90: noch gelb', amp());
      put(4, 'Formschluss mit Nut'); await sleep(50);
      check(amp() === 'stern', '100 Punkte bei Grenze 90: Stern', amp());
      await close();
      reset(); LMS.pass = ''; await open('/new/v6.html');
      check(win().ScormReport.passMark() === 70, 'ohne Wert der Lernplattform: 70', win().ScormReport.passMark());
      await close(); LMS.pass = '0.7';
    });

    await test('18. Fake-ByCS hat in keinem Test einen Wert abgelehnt (Ziele, Kennungen, Zahlenformat)', async check => {
      check(LMS.errors.length === 0, 'keine abgelehnten SetValue-Aufrufe', LMS.errors.slice(0, 10));
    });

    await fetch('/result', { method: 'POST', body: JSON.stringify(results) });
  })();
}

/* ---------- Node: Server, Browser, Ausgabe ---------- */
function findBrowser() {
  const c = [process.env.CHROME, 'C:/Program Files/Google/Chrome/Application/chrome.exe', 'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe',
    'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe', 'C:/Program Files/Microsoft/Edge/Application/msedge.exe',
    '/usr/bin/google-chrome', '/usr/bin/chromium', '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'];
  return c.find(p => p && fs.existsSync(p));
}
const browser = findBrowser();
if (!browser) { console.error('Kein Chrome/Edge gefunden. CHROME=<Pfad> setzen.'); process.exit(2); }
const profile = fs.mkdtempSync(path.join(os.tmpdir(), 'scorm-test-'));
let proc = null;
const timer = setTimeout(() => finish(null, 'Zeitüberschreitung (90 s)'), 90000);
const server = http.createServer((req, res) => {
  const u = new URL(req.url, 'http://localhost');
  if (req.method === 'POST' && u.pathname === '/result') {
    let b = ''; req.on('data', c => { b += c; }); req.on('end', () => { res.end('ok'); finish(JSON.parse(b)); }); return;
  }
  const body = files[u.pathname];
  if (body === undefined) { res.statusCode = 404; res.end('404'); return; }
  res.setHeader('Content-Type', (u.pathname.endsWith('.js') ? 'text/javascript' : 'text/html') + '; charset=utf-8');
  res.setHeader('Cache-Control', 'no-store');
  res.end(body);
});
server.listen(0, '127.0.0.1', () => {
  const url = 'http://127.0.0.1:' + server.address().port + '/harness.html';
  proc = cp.spawn(browser, ['--headless=new', '--disable-gpu', '--no-first-run', '--no-default-browser-check', '--disable-extensions',
    '--user-data-dir=' + profile, url], { stdio: 'ignore' });
});
function finish(results, err) {
  clearTimeout(timer);
  try { if (proc) proc.kill(); } catch (e) { /* still */ }
  server.close();
  setTimeout(() => { try { fs.rmSync(profile, { recursive: true, force: true }); } catch (e) { /* still */ } }, 500);
  if (!results) { console.error('FEHLER: ' + err); process.exitCode = 1; return; }
  let bad = 0, n = 0;
  results.forEach(t => {
    const ok = t.checks.every(c => c.ok); console.log((ok ? 'BESTANDEN  ' : 'FEHLER     ') + t.name);
    t.checks.forEach(c => { n++; if (!c.ok) bad++; console.log('   ' + (c.ok ? 'ok    ' : 'FEHLT ') + c.msg + (c.ok || c.extra === undefined ? '' : '  -> ' + JSON.stringify(c.extra))); });
  });
  console.log('\n' + (n - bad) + ' von ' + n + ' Prüfungen bestanden.');
  process.exitCode = bad ? 1 : 0;
}
