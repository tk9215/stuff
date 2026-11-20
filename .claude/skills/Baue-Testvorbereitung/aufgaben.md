# Baue-Testvorbereitung – Seite füllen: Abschnitte und Thema-Block

Teil des Skills Baue-Testvorbereitung (Ablauf in `SKILL.md`). Beispiel für ein fertiges Thema mit Rechenaufgaben,
interaktiver Tabelle und 3D-Ansicht (ältere Bauweise ohne Baukasten, gleiche Idee):
`Unterricht/MGF10/LF1/BW2/Toleranzen-6-Testvorbereitung/index.html`.

## 1. Abschnitte (Block `Testvorbereitung:app`)
```html
<section class="tv-sec" data-reiter="Grundbegriffe">
<h2>Grundbegriffe</h2>
<div class="tv-skript">            <!-- kommt auch auf die Papierversion (Lernskript) -->
  <p>Kurzer Lerntext aus den Unterlagen.</p>
  <div class="f">G<sub>o</sub> = N + ES</div>        <!-- Formel -->
  <div class="merke"><b>Merke:</b> …</div>           <!-- Merksatz -->
  <table>…</table>                                    <!-- Tabelle aus den Unterlagen -->
</div>
<div class="tv-uebung" data-aufgabe="grenzmasse"></div>   <!-- Übung zum Abschnitt -->
</section>
```
- `data-reiter`: Name des Reiters. Abschnitte mit demselben Namen stehen im selben Reiter. Reihenfolge = Reihenfolge der Reiter. Kurz halten (1–2 Wörter), damit die Reiter auf ein Handy passen.
- Der letzte Abschnitt ist immer `data-reiter="Prüfung"` mit `<div id="tvPruefung"></div>` (steht schon im Gerüst).
- `.tv-skript`: alles, was auf das Papier-Lernskript soll. Knöpfe und Eingabefelder darin werden für das Papier entfernt.
- `.tv-uebung`: `data-aufgabe="id"` oder mehrere `"id1,id2,id3"` (dann Auswahlknöpfe mit den Namen der Aufgabenarten).
- Eigene Interaktivität (Schieberegler, Tabelle zum Ablesen, Skizze) ist erlaubt: zusätzlicher `<script>` NACH dem Thema-Block, offline, ohne Bibliotheken. Mit den Haken `beiNeu(a)` und `beiLoesung(a)` einer Aufgabenart kann sie auf die aktuelle Übungsaufgabe reagieren (z. B. Werte in die Tabelle übernehmen).
- Bilder als `data:`-Adresse, Zeichnungen als Inline-SVG (Farben über `currentColor` oder die Variablen `--fg`, `--blue`, damit Hell/Dunkel stimmt).

## 2. Thema-Block (Block `Testvorbereitung:thema`)
```js
TV.thema({
  titel: 'Toleranzen',                       // Kopfzeile der Papierversion
  aufgaben: {                                // je Aufgabenart ein Eintrag; id = Kleinbuchstaben, ohne Leerzeichen
    grenzmasse: {
      name: 'Grenzmaße berechnen',           // Knopf in der Übung, Zeile im Papier-Dialog
      papier: 2,                             // Anzahl im Papier-Dialog vorbelegt (sonst 2)
      niveau: 'pruefung',                    // nur bei "Drei Niveaus": einsteiger | pruefung | profi
      gen: function () { … return aufgabe; },
      beiNeu: function (a) { },              // optional: eigene Interaktivität auf die neue Aufgabe einstellen
      beiLoesung: function (a) { }           // optional: nach "Prüfen" / "Lösung zeigen"
    }
  },
  pruefung: {
    minuten: 20,
    hilfsmittel: 'Tabellenbuch, Taschenrechner',
    text: 'Überwiegend Rechenaufgaben, dazu Theoriefragen.',     // optional, ein Satz
    aufgaben: [['grenzmasse', 2], ['theorie', 1]]               // [Aufgabenart, Anzahl], in dieser Reihenfolge
  }
});
```

### Eine Aufgabe (Rückgabe von `gen`)
```js
{
  titel: 'Grenzmaße berechnen',
  frage: 'Berechne Höchstmaß, Mindestmaß und Toleranz der Bohrung.',   // HTML erlaubt
  gegeben: 'Ø40' + TV.gegeben('Bohrung'),                              // optional: großer Kasten mit den Angaben
  felder: [
    { typ: 'zahl', label: 'Höchstmaß G<sub>o</sub>', loesung: 40.15, einheit: 'mm', stellen: 2 },
    { typ: 'wahl', label: 'Passungsart', optionen: ['Spielpassung', 'Übergangspassung', 'Übermaßpassung'], loesung: 'Spielpassung' },
    { typ: 'text', label: 'Fachbegriff', loesung: ['Toleranz', 'Maßtoleranz'] },
    { typ: 'kreuze', label: 'Kreuze alle richtigen an.', optionen: [['Aussage A', true], ['Aussage B', false]] }
  ],
  weg: 'G<sub>o</sub> = 40 + 0,15 = 40,15 mm',   // Lösungsweg: nach falscher Antwort, bei "Lösung zeigen", im Lösungsblatt
  hinweis: 'Achte auf das Vorzeichen.'           // optional: Tipp nach falscher Antwort
}
```
Feldtypen und Punkte (Prüfung und Probetest):
| typ | Eingabe | richtig, wenn | Punkte |
|---|---|---|---|
| `zahl` | Textfeld, Komma erlaubt | Abweichung ≤ halbe letzte Stelle (`stellen`, Vorgabe 2) oder ≤ `tol` | 1 |
| `wahl` | Auswahlliste | genau `loesung` | 1 |
| `text` | Textfeld | eine der Lösungen, ohne Groß/klein und doppelte Leerzeichen | 1 |
| `kreuze` | Kästchen | alle richtig (2 P.), ein Fehler 1 P. | 2 |
Andere Punkte je Feld: `punkte: 3`. `vorzeichen: true` zeigt die Lösung mit `+` (Abmaße).

### Werkzeuge
- Zufall **nur** über `TV.zufall()`, `TV.ganz(a, b)`, `TV.wahl(liste)`, `TV.mische(liste)`. Nie `Math.random`: Sonst passt das Lösungsblatt nicht zur Variante (thema-test.py meldet das).
- Zahlen: `TV.zahl(x, stellen, plus)` → deutsches Format (`40,15`, `−0,09`, `+0,15`), `TV.runde(x, stellen)`, `TV.lies('12,5')`.
- `TV.gegeben('Bohrung')` → Kärtchen im Angabekasten.
- **Fragenpool** für Theorie und Begriffe (nicht rechenbare Themen):
  ```js
  theorie: { name: 'Theoriefragen', gen: TV.auswahl('Theoriefragen', [
      ['Was ist die Toleranz?', 'Differenz zwischen Höchstmaß und Mindestmaß', 'Abstand zum Nennmaß', 'das gemessene Maß'],
      …                                      // [Frage, richtige Antwort, falsche, falsche, …]
    ], 5) }                                   // 5 Fragen je Aufgabe, zufällig gezogen und gemischt
  ```
  Ganze Aufgaben als Pool: `gen: TV.pool([ {titel, frage, felder, weg}, …, function () { … } ])`.
  Ein Pool braucht mindestens doppelt so viele Einträge, wie in einer Prüfung gezogen werden, sonst wiederholen sich die Prüfungen zu schnell.

## 3. Regeln für die Aufgaben
- **Quellen streng:** Jeder Wert, jede Tabelle, jede Formel, jede richtige Antwort steht in den Unterlagen der Lehrkraft. Über jeder Aufgabenart ein Kommentar `/* Quelle: <Datei>, S. <n> */`. Nichts aus dem Gedächtnis, keine Tabellenwerte aus dem Web. Fehlt etwas, die Lehrkraft fragen.
- **Zufallsbereiche nur dort, wo die Quelle trägt:** Werte nur aus Bereichen, die die Tabellen der Unterlagen abdecken; Ergebnisse sinnvoll (keine negativen Längen, keine 12 Nachkommastellen; mit `TV.runde` arbeiten und `stellen` passend setzen).
- **Wie der Test, aber nicht der Test:** gleiche Aufgabenarten, gleiche Schwierigkeit, gleiche Hilfsmittel und Zeit wie der echte Test; keine Frage wörtlich oder mit gleichen Zahlen aus dem Test (Skill ByCS-Fragenersteller, `Test-<Thema>/Fragen-*.xml`).
- **Falsche Antworten (Distraktoren)** sind typische Schülerfehler (Vorzeichen vergessen, Einheit verwechselt, Begriffe vertauscht), keine Unsinnsantworten.
- **Sprache:** kurze Sätze, Du-Form, Fachbegriffe wie in den Unterlagen.
- **Prüfung:** Punkte ≈ Zeit des echten Tests (Faustregel 1 Punkt pro Minute bei Rechenaufgaben, 2 Wahlfragen pro Minute). thema-test.py zeigt die Summe.
