/*
  scorm-api.js - SCORM-2004-Anbindung fuer ByCS Lernplattform (Moodle). Offline-tauglich, keine Abhaengigkeiten.
  Nicht veraendern. Das E-Learning ruft nur ScormReport auf:

    ScormReport.init({ total: 10 });            // einmal beim Start: Anzahl der bewerteten Aufgaben
    ScormReport.answer('q1', true, {            // nach JEDER bewerteten Aufgabe (Teilpunkt)
      type: 'choice',                           // choice | true-false | fill-in | matching | numeric | performance
      response: 'b',                            // Antwort der Lernenden (choice: Buchstabe a, b, c ...)
      correctResponse: 'b',                     // optional: richtige Antwort
      weighting: 1                              // optional, Standard 1
    });
    ScormReport.complete();                     // nur fuer Inhalte ohne Punkte (reines Durchlesen)
    ScormReport.init({ scoring: false });       // nur Name lesen, keine Punkte (Notbehelf; Dokumente melden stattdessen ihren Bearbeitungsstand, siehe unten)
    ScormReport.studentName();                  // Name der Lernenden aus der Lernplattform
    ScormReport.saveState(obj);                 // Fortschritt (JSON-faehiges Objekt) in der Lernplattform speichern
                                                //   Schutz: Ein Stand ohne Eingaben ersetzt nie einen gespeicherten Stand mit Eingaben
                                                //   (Rueckgabe false, nichts geschrieben). Eingaben = Eintraege in obj.k (Fachunterricht.html: { f: 2, k: { Schluessel: Wert } })
                                                //   bzw. obj.v (altes Format { n, v: [[Position, Wert]] }); andere Objekte zaehlen als gefuellt, sobald sie etwas enthalten.
                                                //   true = geschrieben; ob die Lernplattform es bestaetigt hat, meldet onSaveStatus.
    ScormReport.loadState();                    // gespeicherten Fortschritt holen (oder null)
    ScormReport.stateLimit                      // erlaubte Zeichen in suspend_data (SCORM 2004: 64000)
    ScormReport.beforeFinish(fn);               // fn wird direkt vor dem Beenden aufgerufen (letztes Speichern)
    ScormReport.onSaveStatus(fn);               // fn(ok, safe) nach jedem Speichern (Commit): ok = von der Lernplattform bestaetigt,
                                                //   safe = Eingaben sind sicher (bestaetigt oder Sicherung im Browser moeglich).
                                                //   Ist das Speichern schon vorher fehlgeschlagen, kommt die Meldung sofort.
    ScormReport.fromBackup();                   // true = der Stand kam beim Start aus der Sicherung im Browser
    ScormReport.keepAlive();                    // Lebenszeichen (Commit); laeuft von selbst alle 5 Minuten, solange die Seite sichtbar ist

  Speichern abgesichert: Moodle laedt gespeicherte Werte beim Start nur, wenn auf dem Server cmi.exit = suspend steht. Deshalb setzt
    init() das sofort (finish() kann es am Ende noch auf normal setzen), und ohne jede Bearbeitung wird nichts gemeldet
    (weder suspend_data noch Status). Ein Stand, den Moodle nicht geliefert hat, bleibt so erhalten und kommt beim naechsten Oeffnen zurueck.
    Moodle antwortet auf Commit mit "false" (Fehler 101), wenn die Anmeldung abgelaufen oder die Verbindung weg ist.
    Dann legt die Schnittstelle eine Sicherung im Browser an (localStorage, Schluessel scorm-sicherung|<cmi.learner_id>|<Pfad ohne
    Revisionsnummer>, Inhalt { b: t des letzten bestaetigten Stands, sd: suspend_data, ix: Interaktionen seit dem letzten bestaetigten
    Commit }), aber nur, wenn es Ungespeichertes gibt.
    Nach dem naechsten bestaetigten Commit wird sie geloescht. Beim Start wird sie nur genommen, wenn die Lernplattform noch genau den
    Stand b hat; sonst ist sie veraltet (z. B. an einem anderen Rechner weitergearbeitet) und wird geloescht.
    suspend_data traegt dafuer t = Zeitpunkt der letzten inhaltlichen Aenderung (bleibt beim blossen Oeffnen gleich).
    Das Lebenszeichen haelt die Anmeldung wach (Moodle tut das im SCORM-Player nicht) und meldet einen Timeout, bevor weitergeschrieben wird.

  Differenzierte Aufgaben (Standard fuer neue Pakete): Einsteigerniveau (blau) 40 %, Prüfungsniveau (rot) 40 %, Profiniveau (schwarz) 20 % der Punkte.
    ScormReport.init({ levels: { foundation: 5, core: 5, challenge: 3 } });   // Anzahl bewerteter Aufgaben je Niveau
    ScormReport.answer('q1', true, { level: 'foundation', type: 'choice', response: 'b' });
  Der Anteil eines Niveaus verteilt sich gleichmaessig auf seine Aufgaben. Fehlt ein Niveau, werden die uebrigen im Verhaeltnis 40:40:20 auf 100 % hochgerechnet.
  Mit tasks (alle Seiten aus den Vorlagen) gibt es nur ganze Punkte: Die Restpunkte gehen einzeln an die groessten Reste, bei Gleichstand an die
    letzten Aufgaben (drei gleiche Aufgaben im Einsteigerniveau = 13, 13, 14; nur Einsteiger- und Profiniveau = 67 und 33). Erreichte Punkte werden je
    Aufgabe gerundet (halbe Punkte auf), die Gesamtpunkte sind ihre Summe. Die Vorlagen rechnen genauso (Test 17b in tests/suspend-data.test.js).
  Punkte je Aufgabe (aktuelle Fachunterricht.html): ScormReport.init({ levels: {...}, tasks: { a1: { level: 'foundation', weight: 2, label: 'Aufgabe-1.1' }, ... } })
    weight = Gewicht der Aufgabe im Niveau (Standard 1): Der Anteil des Niveaus verteilt sich nach den Gewichten (1, 1, 2 im Einsteigerniveau = 10, 10, 20 Punkte).
    label  = Kennung in den Moodle-Berichten; angehaengt werden Niveau und Hoechstpunkte: Aufgabe-1.1_Einsteiger_10P (Bericht "Interaktionen", Spalte Frage).
    Niveau und Gewicht kommen dann aus tasks (aktuelle Fassung der Seite); Aufgaben, die dort fehlen, zaehlen nicht mehr.
  Ziele (Moodle-Bericht "Ziele", Option Punkte anzeigen): je Niveau ein Ziel (1-Einsteigerniveau_40P, 2-Pruefungsniveau_40P, 3-Profiniveau_20P), mit tasks
    zusaetzlich je Aufgabe (Kennung wie oben). Status completed = bearbeitet (Niveau: alle Aufgaben bearbeitet), Punkte (score.raw, Anteil an 100,
    score.max = Hoechstpunkte) zusammen mit den Gesamtpunkten (im Abgabe-Modus laufend, schon vor der Abgabe).
  Dokumente (Fachunterricht.html): ScormReport.init({ levels: {...}, partial: true }) und ScormReport.answer('a1', true|false, { level: ..., type: 'performance' }) je bearbeiteter Aufgabe.
    Es gibt keine automatische Korrektur: Punkte = Bearbeitungsstand (bearbeitet = Punkte), gewichtet 40/40/20. Mit partial ist die Seite schon ab 70 % "completed" und "passed"
    (Einsteigerniveau + Prüfungsniveau bearbeitet = 80 %); das Profiniveau bringt die restlichen 20 %.
  Dokumente mit Bewertung (aktuelle Fachunterricht.html): ScormReport.init({ levels: {...}, quality: true }) und je Aufgabe
    ScormReport.task('a1', { level: 'core', done: true, score: 0.5, response: 'Antworttext', description: 'Aufgabe 1.1 - Titel', correctResponse: '...' });
    done  = Aufgabe bearbeitet (etwas eingetragen). Abgeschlossen ("completed"), sobald alle Aufgaben des Einsteiger- und Prüfungsniveaus bearbeitet sind.
    score = wie gut (0 bis 1, Teilpunkte erlaubt). null = nicht automatisch prüfbar: dann zählt bearbeitet als volle Punkte.
    Punkte 0-100 = Bewertung, gewichtet 40/40/20. Bestanden ab 70 %.
    Jede Aufgabe hat genau EINE Interaktion im Moodle-Bericht (wird bei Änderung überschrieben): Titel, Antwort der Lernenden, erwartete Antwort,
    Ergebnis (correct / incorrect / Anteil 0..1 / neutral = nur bearbeitet). task() schreibt ohne Commit; danach ScormReport.flush() oder saveState().
  Abgabe (aktuelle Fachunterricht.html): ScormReport.init({ levels: {...}, quality: true, submit: true }) und beim Klick auf "Abgeben" ScormReport.submit().
    Vor der Abgabe: "incomplete", success_status unveraendert, aber vorlaeufige Punkte (cmi.score.*, Ziele), Interaktionen und Fortschritt laufend
    (Lernpakete sind Uebungspakete: Die Lehrkraft verfolgt den Stand in der Bewertung live, Entscheidung vom 13.11.2026).
    Mit der Abgabe: "completed", Punkte, "passed" (ab 70) oder "failed". Danach nimmt die Schnittstelle keine Änderungen mehr an
    (task, saveState), bis die Lehrkraft die Abgabe zurücknimmt (unsubmit). Der Versuch bleibt "suspend", damit die Seite beim erneuten Öffnen den abgegebenen Stand zeigt.
  ScormReport.isSubmitted()                     // true, wenn schon abgegeben (auch aus einer früheren Sitzung)
  ScormReport.passMark()                        // Bestehensgrenze in % (aus cmi.scaled_passing_score der Lernplattform, Manifest 0.7; fehlt der Wert: 70)
  ScormReport.unsubmit()                        // Lehrkraft nimmt die Abgabe zurück: wieder "incomplete", Änderungen erlaubt;
                                                //   die Punkte laufen danach wieder live mit, die nächste Abgabe entscheidet über bestanden
  ScormReport.taskState('a1')                   // { d: 1/0 bearbeitet, s: 0..1 Bewertung } oder undefined
  ScormReport.state('a1')                       // 1 / 0 / undefined: bereits gemeldete Antwort (aus dem gespeicherten Fortschritt)
  Gemeldet werden immer cmi.score.raw / min / max / scaled, cmi.completion_status und cmi.success_status (ohne diese Werte zeigt Moodle 0 Punkte).
  Ohne levels: Punkte = richtige Aufgaben / total x 100 (ganze Zahl, 0 bis 100).
  Bestehensgrenze ist immer 70 % (Einsteigerniveau + Prüfungsniveau komplett = 80 %, die Mindestanforderung). Sind alle Aufgaben beantwortet: passed (ab 70) oder failed.
  Einmal bestanden bleibt bestanden. Wird die Datei ohne Lernplattform geoeffnet, passiert nichts.
*/
(function (w) {
  'use strict';

  var MASTERY = 70;   /* Bestehensgrenze in %: Standard 70, in init aus cmi.scaled_passing_score der Lernplattform (Manifest: minNormalizedMeasure) */
  var LEVEL_WEIGHT = { foundation: 40, core: 40, challenge: 20 };   // Einsteigerniveau blau, Prüfungsniveau rot, Profiniveau schwarz
  var LEVEL_NAME = { foundation: 'Einsteiger', core: 'Pruefung', challenge: 'Profi' };                            /* in Kennungen der Aufgaben */
  var LEVEL_GOAL = { foundation: '1-Einsteigerniveau', core: '2-Pruefungsniveau', challenge: '3-Profiniveau' };   /* Ziele je Niveau, im Bericht vor den Aufgaben */
  var api = null, started = false, finished = false, startMs = 0, hooks = [];
  var total = 0, levelN = null, levelOf = {}, answers = {}, pageState = null, icount = 0, wasPassed = false, wasCompleted = false, scoring = true, partial = false;
  var quality = false, done = {}, iIndex = {};   /* quality: bearbeitet (done) und Bewertung (answers) getrennt; iIndex: feste Interaktion je Aufgabe */
  var needSubmit = false, submitted = false;     /* Abgabe-Modus: Punkte und Status erst mit submit() */
  var meta = {}, hasMeta = false, levelW = null, ids = {};   /* tasks aus init: Niveau, Gewicht, Kennung je Aufgabe; levelW: Summe der Gewichte je Niveau */
  var pMax = {}, lvMax = {};                                 /* mit tasks: ganze Hoechstpunkte je Aufgabe und je Niveau (Summe 100) */
  var oIdx = {}, ocount = 0, oVal = {};                      /* Ziele: Nummer je Kennung, Anzahl, zuletzt geschriebene Werte */
  /* Speichern absichern: core = Stand ohne t, curT = t des aktuellen Stands, okT = t des letzten bestaetigten Stands */
  var KEEPALIVE_MS = 5 * 60000, core = '', curT = 0, okT = 0, lastSd = '', lastOk = true, lastSafe = true, onStatus = null;
  var store = false, bakKey = '', fromBak = false, beat = 0, lastCommit = 0, pend = {};   /* pend: Interaktionen seit dem letzten bestaetigten Commit */

  function findApi(win) {
    var hops = 0;
    try {
      while (win && !win.API_1484_11 && win.parent && win.parent !== win && hops < 20) { win = win.parent; hops++; }
      return (win && win.API_1484_11) || null;
    } catch (e) { return null; }
  }

  function call(m, arg) { try { return api ? String(api[m](arg)) : ''; } catch (e) { return ''; } }
  function get(k) { try { return api ? String(api.GetValue(k)) : ''; } catch (e) { return ''; } }
  function set(k, v) { try { if (api) { api.SetValue(k, String(v)); if (k.indexOf('cmi.interactions.') === 0) pend[k] = String(v); } } catch (e) { /* still */ } }
  function hasPend() { for (var k in pend) { if (pend.hasOwnProperty(k)) return true; } return false; }

  /* Sicherung im Browser, nur solange die Lernplattform das Speichern nicht bestaetigt hat */
  function canStore() { try { var k = 'scorm-sicherung|test'; w.localStorage.setItem(k, '1'); w.localStorage.removeItem(k); return true; } catch (e) { return false; } }
  function backupKey() { return 'scorm-sicherung|' + get('cmi.learner_id') + '|' + String(w.location.pathname || '').replace(/\/content\/\d+\//, '/content/'); }
  function readBak() { try { var v = bakKey ? w.localStorage.getItem(bakKey) : null; return v ? JSON.parse(v) : null; } catch (e) { return null; } }
  function dropBak() { try { if (bakKey) w.localStorage.removeItem(bakKey); } catch (e) { /* still */ } }
  function keepBak() { try { if (!bakKey) return false; w.localStorage.setItem(bakKey, JSON.stringify({ b: okT, sd: lastSd, ix: pend })); return true; } catch (e) { return false; } }

  /* Commit mit Pruefung: bestaetigt nur bei "true". Sonst Sicherung im Browser, falls es Ungespeichertes gibt. */
  function commit() {
    var ok = call('Commit', '') === 'true', safe = ok;
    lastCommit = new Date().getTime();
    if (ok) { okT = curT; pend = {}; dropBak(); }
    else safe = (curT === okT && !hasPend()) ? store : keepBak();
    lastOk = ok; lastSafe = safe;
    if (onStatus) { try { onStatus(ok, safe); } catch (e) { /* still */ } }
    return ok;
  }

  function sessionTime(ms) {
    var s = Math.floor(ms / 1000);
    return 'PT' + Math.floor(s / 3600) + 'H' + (Math.floor(s / 60) % 60) + 'M' + (s % 60) + 'S';
  }
  function cleanId(id) { return String(id).replace(/[^A-Za-z0-9_\-]/g, '_').substring(0, 250); }
  /* Text fuer description (CMILangString250): Moodle lehnt "{" und Zeilenumbrueche ab */
  function langStr(s, n) { return String(s).replace(/[{}]/g, '').replace(/\s+/g, ' ').trim().substring(0, n); }

  /* Aufgaben aus init({ tasks }): Niveau und Gewicht von dort (aktuelle Fassung der Seite), sonst wie gemeldet und Gewicht 1 */
  function lvOf(k) { return hasMeta && meta.hasOwnProperty(k) ? meta[k].level : (levelOf[k] || 'core'); }
  function wtOf(k) { return hasMeta && meta.hasOwnProperty(k) ? meta[k].weight : 1; }
  function counted(k) { return !hasMeta || meta.hasOwnProperty(k); }   /* mit tasks zaehlen nur Aufgaben dieser Fassung */
  function taskDone(k) { return quality ? done[k] === 1 : answers.hasOwnProperty(k); }

  function counts() {
    var c = 0, n = 0, k;
    for (k in answers) { if (answers.hasOwnProperty(k) && counted(k)) { n++; c += +answers[k] || 0; } }   /* Teilpunkte 0..1 zaehlen anteilig */
    return { correct: c, answered: n };
  }

  /* Bearbeitet-Pruefung (quality): alle Aufgaben des Einsteiger- und Prüfungsniveaus bearbeitet (fehlen beide: alle Aufgaben) */
  function allTasksDone() {
    var n = {}, k, l, need = levelN ? ((levelN.foundation || levelN.core) ? ['foundation', 'core'] : ['challenge']) : null, c = 0;
    for (k in done) { if (done.hasOwnProperty(k) && done[k] === 1 && counted(k)) { c++; l = lvOf(k); n[l] = (n[l] || 0) + 1; } }
    if (!need) return total > 0 && c >= total;
    for (k = 0; k < need.length; k++) { l = need[k]; if (levelN[l] && (n[l] || 0) < levelN[l]) return false; }
    return true;
  }
  function doneCount() { var c = 0, k; for (k in done) { if (done.hasOwnProperty(k) && done[k] === 1 && counted(k)) c++; } return c; }

  /* Punkte 0-100: mit Niveaus gewichtet (40/40/20, im Niveau nach Gewicht der Aufgabe), sonst richtige / total */
  function levelSum() { var s = 0, l; for (l in levelN) { if (levelN.hasOwnProperty(l) && levelN[l] > 0) s += LEVEL_WEIGHT[l]; } return s; }
  function okByLevel() {   /* erreicht je Niveau, in Gewichten: Bewertung 0..1 x Gewicht */
    var ok = {}, k, l;
    for (k in answers) { if (answers.hasOwnProperty(k) && counted(k) && +answers[k] > 0) { l = lvOf(k); ok[l] = (ok[l] || 0) + (+answers[k]) * wtOf(k); } }
    return ok;
  }
  function round100(x) { return Math.round(Math.round(x * 1e6) / 1e6); }
  /* Ganze Punkte, Summe genau sum (gleich wie in den Vorlagen): Anteile nach Gewicht abrunden, die Restpunkte einzeln an die
     groessten Reste, bei Gleichstand an die letzten (drei gleiche Aufgaben mit zusammen 40 = 13, 13, 14) */
  function share(sum, w) {
    var W = 0, p = [], r = [], idx = [], rest = sum, i, q, f;
    for (i = 0; i < w.length; i++) W += w[i];
    for (i = 0; i < w.length; i++) { q = W > 0 ? sum * w[i] / W : 0; f = Math.floor(q + 1e-9); p[i] = f; r[i] = Math.round((q - f) * 1e6); rest -= f; idx[i] = i; }
    idx.sort(function (a, b) { return r[b] - r[a] || b - a; });
    for (i = 0; i < rest && i < idx.length; i++) p[idx[i]]++;
    return p;
  }
  /* erreichte Punkte einer Aufgabe: Bewertung 0..1 x Hoechstpunkte, auf ganze Punkte gerundet (mit tasks) */
  function earned(k) { return round100((+answers[k] || 0) * maxPts(k)); }   /* Rundung unabhaengig von der Reihenfolge der Summe (gleich wie Fachunterricht.html) */
  function result() {
    var c = counts();
    if (!levelN) return { raw: total > 0 ? Math.min(100, Math.round(100 * c.correct / total)) : 0, answered: c.answered };
    var ok = okByLevel(), l, pts = 0, sumW = levelSum(), k;
    if (hasMeta) {   /* Punkte je Aufgabe: Gesamtpunkte = Summe der ganzen Punkte der Aufgaben */
      for (k in answers) { if (answers.hasOwnProperty(k) && counted(k)) pts += earned(k); }
      return { raw: Math.min(100, pts), answered: c.answered };
    }
    for (l in levelN) { if (levelN.hasOwnProperty(l) && levelN[l] > 0) pts += LEVEL_WEIGHT[l] * Math.min(1, (ok[l] || 0) / levelW[l]); }
    return { raw: sumW ? round100(100 * pts / sumW) : 0, answered: c.answered };
  }
  /* Hoechstpunkte einer Aufgabe (Anteil an 100): Anteil des Niveaus x Gewicht / Summe der Gewichte im Niveau */
  function maxPts(k) {
    if (hasMeta) return pMax[k] || 0;   /* ganze Punkte, in init verteilt */
    var l = lvOf(k); return levelN && levelN[l] ? 100 * LEVEL_WEIGHT[l] / levelSum() * wtOf(k) / levelW[l] : 0;
  }
  function r2(x) { return Math.round(x * 100) / 100; }
  function pText(x) { return String(Math.round(x * 10) / 10).replace('.', ','); }   /* mit tasks ganze Punkte (13), ohne tasks auch 13,3 */
  function idOf(k) { return ids.hasOwnProperty(k) ? ids[k] : k; }

  /* Ziele (Moodle-Bericht "Ziele"): je Niveau und mit tasks je Aufgabe. Moodle nimmt jede Kennung nur einmal an (write once, eindeutig,
     Nummern lueckenlos): init() liest die vorhandenen Ziele (auch PRIMARYOBJ aus dem Manifest), neue kommen hinten dazu.
     Geschrieben wird nur, was sich geaendert hat. Die Ziele ergeben sich immer neu aus dem Stand, deshalb nicht in der Sicherung im Browser. */
  function oset(n, f, v) { var k = 'cmi.objectives.' + n + '.' + f; v = String(v); if (oVal[k] !== v) { oVal[k] = v; set(k, v); } }
  function goal(id, complete, raw, max) {
    if (!oIdx.hasOwnProperty(id)) { oIdx[id] = ocount++; oset(oIdx[id], 'id', id); }
    var n = oIdx[id];
    oset(n, 'completion_status', complete ? 'completed' : 'incomplete');
    if (raw === null) return;   /* Punkte erst, wenn auch die Gesamtpunkte gemeldet werden */
    oset(n, 'score.min', 0); oset(n, 'score.max', r2(max)); oset(n, 'score.raw', r2(raw));
    oset(n, 'score.scaled', max > 0 ? Math.round(10000 * Math.min(1, raw / max)) / 10000 : 0);
  }
  function objectives(withScore) {
    if (!api || !levelN) return;
    var ok = okByLevel(), fin = {}, got = {}, sumW = levelSum(), src = quality ? done : answers, k, l, max;
    if (hasMeta) { for (k in answers) { if (answers.hasOwnProperty(k) && counted(k)) { l = lvOf(k); got[l] = (got[l] || 0) + earned(k); } } }
    for (k in src) { if (src.hasOwnProperty(k) && counted(k) && taskDone(k)) { l = lvOf(k); fin[l] = (fin[l] || 0) + 1; } }
    for (l in LEVEL_WEIGHT) {
      if (!LEVEL_WEIGHT.hasOwnProperty(l) || !levelN[l]) continue;
      max = hasMeta ? (lvMax[l] || 0) : 100 * LEVEL_WEIGHT[l] / sumW;
      goal(LEVEL_GOAL[l] + '_' + pText(max) + 'P', (fin[l] || 0) >= levelN[l],
           withScore ? (hasMeta ? Math.min(max, got[l] || 0) : max * Math.min(1, (ok[l] || 0) / levelW[l])) : null, max);
    }
    for (k in meta) { if (meta.hasOwnProperty(k)) goal(idOf(k), taskDone(k), withScore ? earned(k) : null, maxPts(k)); }
  }

  /* Enthaelt ein Zustand der Seite Eingaben? Fachunterricht.html: k = { Schluessel: Wert }, altes Format v = [[Position, Wert]]; sonst: nicht leer */
  function hasInput(o) {
    var k;
    if (o === null || o === undefined || o === '') return false;
    if (typeof o !== 'object') return true;
    if (o.k && typeof o.k === 'object') { for (k in o.k) { if (o.k.hasOwnProperty(k)) return true; } return false; }
    if (Object.prototype.toString.call(o.v) === '[object Array]') return o.v.length > 0;
    for (k in o) { if (o.hasOwnProperty(k)) return true; }
    return false;
  }

  /* suspend_data: {"a":{Aufgaben-ID:0/1},"s":<Zustand der Seite>,"t":<letzte Aenderung>}; build() ohne t */
  function build() {
    var o = {}, k, has = false;
    for (k in answers) { if (answers.hasOwnProperty(k)) { has = true; break; } }
    if (has) o.a = answers;
    if (has && levelN) o.l = levelOf;
    if (quality) { o.d = done; o.i = iIndex; }
    if (submitted) o.x = 1;
    if (pageState !== null) o.s = pageState;
    return o;
  }
  /* Stand ohne jede Bearbeitung. Dann wird nichts gemeldet (weder suspend_data noch Status): Hat Moodle einen gespeicherten Stand
     nicht geliefert (cmi.exit fehlte auf dem Server), bleibt er so erhalten und kommt beim naechsten Oeffnen zurueck. */
  function blank(c) { return c === '{}' || c === '{"d":{},"i":{}}'; }
  /* gibt false zurueck, wenn zu lang; t aendert sich nur, wenn sich der Inhalt aendert */
  function writeSuspend() {
    var o = build(), c = JSON.stringify(o), t = (c === core) ? curT : Math.max(new Date().getTime(), curT + 1);
    if (blank(c)) return true;   /* noch nichts bearbeitet: nichts schreiben (siehe blank) */
    o.t = t;
    var s = JSON.stringify(o);
    if (s.length > ScormReport.stateLimit) return false;
    core = c; curT = t; lastSd = s;
    set('cmi.suspend_data', s);
    return true;
  }

  function update(noCommit) {
    if (!api || !scoring) return;
    if (blank(JSON.stringify(build()))) { if (!noCommit) commit(); return; }   /* noch nichts bearbeitet: nur cmi.exit senden */
    var c = result(), raw = c.raw;
    if (needSubmit && !submitted) {   /* noch nicht abgegeben: Fortschritt und vorläufige Punkte (Übungspakete), Status erst mit der Abgabe */
      set('cmi.score.min', 0); set('cmi.score.max', 100); set('cmi.score.raw', raw); set('cmi.score.scaled', raw / 100);
      set('cmi.progress_measure', total > 0 ? Math.min(1, doneCount() / total) : 0);
      set('cmi.completion_status', 'incomplete');
      objectives(true);
      writeSuspend();
      if (!noCommit) commit();
      return;
    }
    var allDone = needSubmit ? true : (quality ? allTasksDone() : (partial ? raw >= MASTERY : (c.answered >= total && total > 0))), passed = raw >= MASTERY || wasPassed;
    if (allDone) { wasCompleted = true; if (passed) wasPassed = true; }
    set('cmi.score.min', 0); set('cmi.score.max', 100); set('cmi.score.raw', raw); set('cmi.score.scaled', raw / 100);
    set('cmi.progress_measure', total > 0 ? Math.min(1, (quality ? doneCount() : c.answered) / total) : 0);
    set('cmi.completion_status', (allDone || wasCompleted) ? 'completed' : 'incomplete');
    set('cmi.success_status', allDone ? (passed ? 'passed' : 'failed') : (wasPassed ? 'passed' : 'unknown'));
    objectives(true);
    writeSuspend();
    if (!noCommit) commit();
  }

  var ScormReport = {
    connected: false,
    stateLimit: 64000,

    init: function (opts) {
      if (started) return;
      started = true;
      startMs = new Date().getTime();
      scoring = !(opts && opts.scoring === false);
      partial = !!(opts && opts.partial);
      quality = !!(opts && opts.quality);
      needSubmit = !!(opts && opts.submit);
      total = (opts && opts.total) ? Math.max(1, Math.floor(opts.total)) : 0;
      if (opts && opts.levels) {
        levelN = {}; total = 0;
        for (var lv in LEVEL_WEIGHT) { if (LEVEL_WEIGHT.hasOwnProperty(lv)) { var cnt = Math.max(0, Math.floor(opts.levels[lv] || 0)); if (cnt) { levelN[lv] = cnt; total += cnt; } } }
        if (!total) levelN = null;
      }
      if (levelN) {
        levelW = {};
        for (lv in levelN) { if (levelN.hasOwnProperty(lv)) levelW[lv] = levelN[lv]; }
        if (opts.tasks && typeof opts.tasks === 'object') {   /* Punkte je Aufgabe: Niveau, Gewicht, Kennung */
          var wsum = {}, tk, tm, wt, seen = {}, tid;
          for (tk in opts.tasks) {
            if (!opts.tasks.hasOwnProperty(tk)) continue;
            tm = opts.tasks[tk] || {}; wt = +tm.weight;
            meta[cleanId(tk)] = tm = { level: LEVEL_WEIGHT[tm.level] ? tm.level : 'core', weight: wt > 0 ? wt : 1, label: String(tm.label || '').replace(/\s+/g, '-').substring(0, 200) };
            hasMeta = true;
            if (levelN[tm.level]) wsum[tm.level] = (wsum[tm.level] || 0) + tm.weight;
          }
          for (lv in levelN) { if (levelN.hasOwnProperty(lv) && wsum[lv] > 0) levelW[lv] = wsum[lv]; }
          /* ganze Punkte: 100 auf die vorhandenen Niveaus (40:40:20), den Anteil des Niveaus auf seine Aufgaben in der Reihenfolge der Seite */
          var lvs = [], lp, ks, kp, j;
          for (lv in LEVEL_WEIGHT) { if (LEVEL_WEIGHT.hasOwnProperty(lv) && levelN[lv]) lvs.push(lv); }
          lp = share(100, lvs.map(function (x) { return LEVEL_WEIGHT[x]; }));
          for (j = 0; j < lvs.length; j++) {
            lvMax[lvs[j]] = lp[j]; ks = [];
            for (tk in meta) { if (meta.hasOwnProperty(tk) && meta[tk].level === lvs[j]) ks.push(tk); }
            kp = share(lp[j], ks.map(function (x) { return meta[x].weight; }));
            for (tm = 0; tm < ks.length; tm++) pMax[ks[tm]] = kp[tm];
          }
          for (tk in meta) {   /* Kennung im Bericht: Aufgabe-1.1_Einsteiger_10P, eindeutig */
            if (!meta.hasOwnProperty(tk) || !meta[tk].label) continue;
            tid = meta[tk].label + '_' + LEVEL_NAME[meta[tk].level] + '_' + pText(maxPts(tk)) + 'P';
            if (seen[tid]) tid += '-' + tk;
            seen[tid] = 1; ids[tk] = tid;
          }
        }
      }
      api = findApi(w) || (w.opener ? findApi(w.opener) : null);
      if (!api) return;
      if (call('Initialize', '') === 'false') { api = null; return; }
      ScormReport.connected = true;
      /* gleich "suspend": Moodle (SCORM 2004, get_scorm_default) laedt die gespeicherten Werte beim naechsten Start NUR bei
         cmi.exit = suspend auf dem Server. Endet die Sitzung ohne sauberes Beenden (Timeout, Absturz), war die Seite sonst leer. */
      set('cmi.exit', 'suspend');
      var sp = parseFloat(get('cmi.scaled_passing_score'));   /* Bestehensgrenze der Lernplattform (0..1), sonst bleibt es bei 70 */
      if (sp > 0 && sp <= 1) MASTERY = Math.round(sp * 100);
      var status = get('cmi.completion_status');
      wasPassed = (get('cmi.success_status') === 'passed');
      wasCompleted = (status === 'completed');
      var sd = get('cmi.suspend_data'), lmsT = 0, bak, k;
      try { lmsT = +(JSON.parse(sd) || {}).t || 0; } catch (e) { lmsT = 0; }
      /* Sicherung im Browser nur nehmen, wenn die Lernplattform seit dem Fehler nichts Neues bekommen hat */
      store = canStore(); bakKey = backupKey(); bak = readBak();
      if (bak && typeof bak.sd === 'string' && bak.b === lmsT) { sd = bak.sd; fromBak = true; } else if (bak) dropBak();
      if (sd) { try { var o = JSON.parse(sd); if (o && typeof o === 'object') { answers = o.a || {}; levelOf = o.l || {}; done = o.d || {}; iIndex = o.i || {}; submitted = needSubmit && o.x === 1; pageState = (o.s === undefined) ? null : o.s; curT = +o.t || 0; } } catch (e) { answers = {}; done = {}; iIndex = {}; pageState = null; } }
      if (needSubmit && status === 'completed') submitted = true;   /* im Abgabe-Modus heisst "completed" immer: abgegeben */
      var n = parseInt(get('cmi.interactions._count'), 10);
      icount = isNaN(n) ? 0 : n;
      /* vorhandene Ziele (Kennungen sind in Moodle einmalig): Nummer je Kennung merken, neue kommen dahinter */
      n = parseInt(get('cmi.objectives._count'), 10);
      ocount = isNaN(n) ? 0 : n;
      for (k = 0; k < ocount; k++) { var oid = get('cmi.objectives.' + k + '.id'); if (oid) { oIdx[oid] = k; oVal['cmi.objectives.' + k + '.id'] = oid; } }
      /* aus der Sicherung: Interaktionen, die nie angekommen sind, nachtragen. Neue Nummern muessen lueckenlos an _count anschliessen
         (die Lernplattform hat seit dem Fehler nichts Neues bekommen); sonst nur Aenderungen bestehender Nummern nachtragen und
         Aufgaben ohne angekommene Interaktion neu nummerieren lassen */
      if (fromBak) {
        var ix = (bak.ix && typeof bak.ix === 'object') ? bak.ix : {}, add = {}, seq = true, m, list, i;
        for (k in ix) { if (ix.hasOwnProperty(k) && (m = /^cmi\.interactions\.(\d+)\./.exec(k)) && +m[1] >= icount) add[m[1]] = 1; }
        list = Object.keys(add).map(Number).sort(function (x, y) { return x - y; });
        for (i = 0; i < list.length; i++) { if (list[i] !== icount + i) seq = false; }
        for (k in ix) { if (ix.hasOwnProperty(k) && (m = /^cmi\.interactions\.(\d+)\./.exec(k)) && (seq || +m[1] < icount)) set(k, ix[k]); }
        if (seq) icount += list.length;
        for (k in iIndex) { if (iIndex.hasOwnProperty(k) && !(iIndex[k] < icount)) delete iIndex[k]; }
      }
      okT = lmsT; core = JSON.stringify(build());
      if (!blank(core) && (status === '' || status === 'not attempted' || status === 'unknown')) set('cmi.completion_status', 'incomplete');
      if (fromBak) writeSuspend();
      update();
      if (!scoring) commit();   /* cmi.exit (und ggf. die Sicherung) sofort zur Lernplattform */
      beat = w.setInterval(ScormReport.keepAlive, KEEPALIVE_MS);
      try { w.document.addEventListener('visibilitychange', function () { if (new Date().getTime() - lastCommit > 60000) ScormReport.keepAlive(); }); } catch (e) { /* still */ }
    },

    answer: function (id, correct, info) {
      if (!started) return;
      var key = cleanId(id);
      answers[key] = correct ? 1 : 0;
      info = info || {};
      var weight = 1;
      if (levelN) {
        levelOf[key] = LEVEL_WEIGHT[info.level] ? info.level : 'core';
        weight = r2(maxPts(key));   /* Hoechstpunkte der Aufgabe */
      }
      if (api) {
        var p = 'cmi.interactions.' + icount + '.';
        set(p + 'id', idOf(key));
        set(p + 'timestamp', new Date().toISOString().replace(/\.\d+Z$/, 'Z'));
        set(p + 'type', info.type || 'choice');
        if (info.correctResponse != null) set(p + 'correct_responses.0.pattern', String(info.correctResponse).substring(0, 255));
        set(p + 'weighting', info.weighting != null ? info.weighting : weight);
        if (info.response != null) set(p + 'learner_response', String(info.response).substring(0, 255));
        set(p + 'result', correct ? 'correct' : 'incorrect');
        icount++;
      }
      update();
    },

    /* Eine Aufgabe melden (Dokumente mit quality): bearbeitet + Bewertung + Antwort, eine feste Interaktion je Aufgabe. Ohne Commit. */
    task: function (id, info) {
      if (!started || submitted) return;   /* nach der Abgabe keine Änderungen mehr */
      info = info || {};
      var key = cleanId(id), d = info.done ? 1 : 0, checked = info.score != null;
      var s = checked ? Math.max(0, Math.min(1, +info.score || 0)) : d;
      s = Math.round(s * 100) / 100;
      answers[key] = s; done[key] = d;
      var weight = 1;
      if (levelN) {
        levelOf[key] = LEVEL_WEIGHT[info.level] ? info.level : 'core';
        weight = r2(maxPts(key));   /* Hoechstpunkte der Aufgabe */
      }
      if (api) {
        var n = iIndex.hasOwnProperty(key) ? iIndex[key] : -1;
        if (n < 0 || n >= icount) { n = icount++; iIndex[key] = n; }   /* neue Interaktion nur beim ersten Mal */
        var p = 'cmi.interactions.' + n + '.';
        set(p + 'id', idOf(key));   /* Kennung mit Niveau und Hoechstpunkten (tasks), sonst die Aufgaben-ID */
        set(p + 'type', 'other');   /* "other": freier Text bis 4000 Zeichen, von Moodle ohne Formatpruefung angenommen */
        set(p + 'timestamp', new Date().toISOString().replace(/\.\d+Z$/, 'Z'));
        set(p + 'weighting', weight);
        if (info.description) set(p + 'description', langStr(info.description, 250));
        if (info.correctResponse) set(p + 'correct_responses.0.pattern', String(info.correctResponse).substring(0, 4000));
        set(p + 'learner_response', (d ? String(info.response || 'bearbeitet') : 'offen').substring(0, 4000));
        set(p + 'result', !checked ? 'neutral' : (s >= 1 ? 'correct' : (s <= 0 ? 'incorrect' : String(s))));
      }
      update(true);
    },
    taskState: function (id) { var k = cleanId(id); return answers.hasOwnProperty(k) ? { d: done[k] === 1 ? 1 : 0, s: +answers[k] } : undefined; },
    flush: function () { if (api) commit(); },

    /* Abgabe: ab jetzt completed + Punkte + passed/failed; danach keine Änderungen mehr */
    submit: function () {
      if (!started || submitted) return;
      submitted = true;
      update();
    },
    isSubmitted: function () { return submitted; },
    passMark: function () { return MASTERY; },   /* Bestehensgrenze in % (Lernplattform, sonst 70): die Seite richtet Ampel und Ergebnis danach aus */
    /* Lehrkraft nimmt die Abgabe zurück: wieder "incomplete", Änderungen erlaubt; die nächste Abgabe entscheidet neu über bestanden */
    unsubmit: function () {
      if (!started || !submitted) return;
      submitted = false; wasCompleted = false; wasPassed = false;
      set('cmi.success_status', 'unknown');
      update();   /* noch nicht abgegeben: incomplete, suspend_data ohne Abgabe-Vermerk */
    },

    /* Reiner Lesestoff ohne bewertbare Aufgaben: abgeschlossen = 100 Punkte, bestanden */
    complete: function () {
      if (!started || !api) return;
      wasCompleted = true;
      set('cmi.completion_status', 'completed');
      if (!levelN && total === 0) {
        wasPassed = true;
        set('cmi.score.min', 0); set('cmi.score.max', 100); set('cmi.score.raw', 100); set('cmi.score.scaled', 1);
        set('cmi.progress_measure', 1);
        set('cmi.success_status', 'passed');
      }
      commit();
    },

    /* bereits gemeldete Antwort (1 richtig/bearbeitet, 0 falsch/leer, undefined = noch nie gemeldet) */
    state: function (id) { return answers[cleanId(id)]; },

    /* Name der Lernenden aus der Lernplattform ("Nachname, Vorname" wird zu "Vorname Nachname"). Nur zur Anzeige, wird nicht gespeichert. */
    studentName: function () {
      var n = get('cmi.learner_name').trim(), p;
      if (n.indexOf(',') > -1) { p = n.split(','); n = (p.slice(1).join(',').trim() + ' ' + p[0].trim()).trim(); }
      return n;
    },

    /* Zustand der Seite (Eingaben) speichern. true = geschrieben (Bestaetigung der Lernplattform: onSaveStatus),
       false = nicht moeglich, zu lang oder leer statt gespeicherter Eingaben. */
    saveState: function (obj) {
      if (!api || submitted) return false;
      if (!hasInput(obj) && hasInput(pageState)) return false;   /* nie gespeicherte Eingaben durch einen leeren Stand ersetzen */
      var keep = pageState;
      pageState = obj;
      if (!writeSuspend()) { pageState = keep; return false; }
      commit();
      return true;
    },
    loadState: function () { return pageState; },
    beforeFinish: function (fn) { hooks.push(fn); },
    onSaveStatus: function (fn) { onStatus = fn; if (fn && !lastOk) { try { fn(false, lastSafe); } catch (e) { /* still */ } } },
    fromBackup: function () { return fromBak; },

    /* Lebenszeichen: haelt die Anmeldung wach und meldet einen Timeout frueh (nur sichtbar, offen und nicht abgegeben) */
    keepAlive: function () {
      if (!api || finished || submitted) return;
      try { if (w.document.hidden) return; } catch (e) { /* still */ }
      commit();
    },

    finish: function () {
      if (finished || !started) return;
      finished = true;
      if (beat) w.clearInterval(beat);
      hooks.forEach(function (fn) { try { fn(); } catch (e) { /* still */ } });
      if (!api) return;
      var st = get('cmi.completion_status');
      set('cmi.session_time', sessionTime(new Date().getTime() - startMs));
      /* Abgabe-Modus: immer suspend, damit der abgegebene Stand (Bewertung, Lösungen) beim erneuten Öffnen erhalten bleibt */
      set('cmi.exit', (needSubmit || st === 'incomplete' || st === 'unknown') ? 'suspend' : 'normal');
      commit();
      call('Terminate', '');
    },

    letter: function (i) { return 'abcdefghijklmnopqrstuvwxyz'.charAt(i); }
  };

  w.ScormReport = ScormReport;
  w.addEventListener('pagehide', ScormReport.finish);
  w.addEventListener('beforeunload', ScormReport.finish);
  w.addEventListener('unload', ScormReport.finish);
})(window);
