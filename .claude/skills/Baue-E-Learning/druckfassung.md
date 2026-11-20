# Baue-E-Learning – Druckfassung: das leere Arbeitsblatt

Teil des Skills Baue-E-Learning (Ablauf in `SKILL.md`). Vorbild sind die Druckfassungen der NILS-Skripte (`C:\git\NILS-Skripte`, Werkzeuge `mkpdf_tz1.mjs`, `printdom.js`, `tz3/printdom_tz3.js`): Jede Aufgabe muss sich auf Papier lösen lassen, nicht nur am Bildschirm.

Der Knopf **„Leeres Arbeitsblatt drucken“** (Lehrkraft-Modus) druckt die Seite ohne Einträge und ohne Lösungen. Im Druckdialog lässt sich auch „Als PDF speichern“ wählen.

## 1. Was die Vorlage automatisch macht
Dafür musst du nichts tun:

| Am Bildschirm | Im leeren Arbeitsblatt |
|---|---|
| Name-Zelle im Schriftfeld | Schreiblinie, darunter die Zeile **Name / Klasse / Datum** mit Linien; „Name: ___“ oben rechts auf jeder Seite |
| `<select>` mit kurzer Auswahl (zusammen höchstens 30 Zeichen) | Linie + „(a / b / c)“ dahinter |
| mindestens 3 `<select>` mit gleicher Auswahl in einer Aufgabe, oder gleiche Auswahl in Tabellenzellen | Linien, und unter dem Aufgabentitel **ein** Kasten „Auswahl: a · b · c“ |
| sonstige `<select>` | Linie mit Nummer ①, ② … und am Ende der Aufgabe der Kasten „Auswahl für die nummerierten Lücken“ (je Nummer die Optionen alphabetisch) |
| `<select style="position:absolute">` über einem Bild | leerer Kasten an derselben Stelle, nummeriert |
| Checkbox / Radio | leeres Kästchen bzw. leerer Kreis |
| `<textarea>` | Schreiblinien: `data-zeilen="n"`, sonst `rows` (mindestens 3), ohne Angabe 5 |
| `<input type="text">` | Linie |
| `<input readonly data-score>` (Spielergebnis) | fehlt |
| `details.sol`, `section.answers`, `.sol-only` | fehlen |

Die Breite einer Linie richtet sich nach der längsten Option (16–60 mm).

## 2. Was du für interaktive Aufgaben ergänzt
Eine Aufgabe, die nur am Bildschirm geht, braucht eine **Papierfassung**:
- **`<div class="print-alt">…</div>`** in der Aufgabe: erscheint **nur** im leeren Arbeitsblatt.
  - Nur fester Inhalt: Text, Tabellen, Bilder, Linien, Kästchen.
  - **Nie Eingabefelder** (`input`, `select`, `textarea`), denn sie würden mitgezählt und gespeichert. `seite-pruefen.py` prüft das.
  - Inline geht als `<span class="print-alt">`.
- **`class="screen-only"`** an allem, was auf Papier sinnlos ist: Spielfeld, 3D-Fenster, Regler, Knöpfe „Prüfen“, Hinweise wie „Tippe …“, „Drehe das 3D-Modell …“, das Ergebnisfeld eines Spiels samt Beschriftung.
- **Ereignis `leerdruck`:** Ein Modul, das seine Papierfassung selbst bauen will (z. B. alle Zustände nacheinander zeichnen), hört auf `document.addEventListener('leerdruck', e => e.detail.an ? … : …)`. Elemente, die es dabei erzeugt, bekommen das Attribut `data-blank`, dann entfernt die Vorlage sie nach dem Druck.
- **Bilder für die Papierfassung** (Standbilder von 3D-Modellen, Szenen eines Films) als `data:`-Bild in die Seite einbauen und zusätzlich unter `Ressourcen/Bilder/<Thema>/` ablegen.

Hilfsklassen der Vorlage: `.nbox` (Nummernkasten), `.pcircle` (leerer Kreis), `ol.psteps` (Schrittliste), `.pgrid` (Bildtafel mit 4 Spalten), `.pfig2` (zwei Bilder nebeneinander), `.lines` (Schreiblinien), `.pblank` (Linie im Text).

## 3. Katalog: Bildschirm → Papier (aus den NILS-Skripten)

| Am Bildschirm | Auf Papier | NILS-Beispiel |
|---|---|---|
| Teile im 3D-Modell oder Bild antippen | Tabelle *Bauteil – Pos.-Nr.* zum Eintragen + „kennzeichne das Teil mit Hinweislinie und Positionsnummer“ | TZ1 Aufgabe 1.1 |
| Explosionszeichnung mit Hotspots | dieselbe Zeichnung mit leeren Kreisen (`.pcircle`) zum Eintragen der Positionsnummern | TZ1 Kap. 2 |
| Reihenfolge sortieren (Ziehen) | Liste mit Nummernkasten (`.nbox`) vor jedem Schritt, „1 = zuerst“ | TZ1 Montage |
| Zeichnen Schritt für Schritt (Knöpfe Schritt 1 … n) | `ol.psteps` „Arbeitsschritte – zeichne Schritt für Schritt auf deinem Zeichenblatt:“ mit den Schritttexten; Musterblätter entfallen | TZ1 Kap. 10, TZ2 Kap. 8, TZ3 Kap. 9 |
| Animierte Schritte einer Konstruktion | alle Schritte als Bildfolge nebeneinander (`.pgrid`), neue Linien farbig | TZ3 Kap. 4 |
| Fehlerbild mit anklickbaren Fehlern | Bild ohne Hotspots, „In dieser Zeichnung stecken n Fehler. Kreise sie ein und beschreibe sie:“ + n Zeilen `.lines` | TZ3 Kap. 7 |
| Regler (z. B. Schraffurabstand) | drei feste Varianten nebeneinander mit ☐ a) b) c) zum Ankreuzen + „Begründung:“ + 2 Zeilen | TZ3 Kap. 3 |
| Restkonturen / Linien antippen | angebotene Linien gestrichelt, „Ziehe die richtigen mit breiter Volllinie nach. Nicht jede Linie ist richtig.“ | TZ3 Kap. 5 |
| Kanten im Raster antippen | alle Werkstücke als Raster untereinander: „Zeichne jede sichtbare Kante blau mit Volllinie, jede verdeckte rot gestrichelt.“ | TZ2 Kap. 7 |
| Flächen färben per Klick | „Male die n sichtbaren Flächen mit Buntstiften aus … übertrage die Farben in die Ansichten“ | TZ2 Kap. 4 |
| Umschalten zwischen Darstellungen (Chips) | alle Darstellungen nebeneinander, je mit ihrem Text | TZ2 Kap. 2 |
| Lernfilm / Animation | Bildfolge „Bild 1 von n“ mit Text je Bild, 2 Spalten | TZ2 Kap. 3 |
| 3D-Modell drehen, aufschneiden, auseinanderziehen | Standbilder (ganz, aufgeschnitten, Explosion) als `.pfig2` / `.pgrid`; Text „In der digitalen Version kannst du es drehen …“ | TZ1 Kap. 1, TZ3 Kap. 1 |
| Zoom auf eine Zeichnung | dieselbe Zeichnung als festes Bild in voller Breite | TZ1 Gesamtzeichnung |
| Bilder-Test (Vorbild A–E, je Bild auswählen) | Bildtafel: Vorbilder A–E in einer Reihe, darunter jedes Testbild mit Nummer und Linie, Kasten „Auswahl: …“ | TZ2 Kap. 9 |
| Normblätter durchblättern | alle Blätter untereinander als Bild | TZ2 Normen-Detektiv |
| Checkliste mit Haken | Kästchen ☐ vor jedem Punkt (macht die Vorlage für Checkboxen selbst) | TZ3 Kap. 12 |
| Rechner, Vorlesen, reine Bildschirmhilfe | entfällt (`screen-only`) | TZ1 Maßstabsrechner |

## 4. Bausteine zum Kopieren

**Nummern eintragen statt sortieren:**
```html
<div class="task" id="a1-8"><span class="tt">Aufgabe 1.8 – Montageplan</span>
  <div class="screen-only"><p class="hint">Ziehe die Schritte in die richtige Reihenfolge.</p> … Sortier-Modul … </div>
  <p class="screen-only">Ergebnis: <input type="text" readonly data-score data-k="a1-8-1"></p>
  <div class="print-alt">
    <p>Nummeriere die Arbeitsschritte in einer sinnvollen Reihenfolge (1 = zuerst).</p>
    <ol style="list-style:none;padding:0"><li><span class="nbox"></span>Zylinderstift einpressen</li> … </ol>
  </div>
  <details class="sol"><summary>Lösungsvorschlag</summary> … </details>
</div>
```

**Zeichenschritte als Liste:**
```html
<div class="print-alt">
  <p><b>Arbeitsschritte – zeichne Schritt für Schritt auf deinem Zeichenblatt:</b></p>
  <ol class="psteps"><li><b>Blatteinteilung:</b> …</li><li><b>Mittellinien:</b> …</li> … </ol>
</div>
```

**Fehlerbild:**
```html
<div class="print-alt">
  <p>In dieser Zeichnung stecken vier Fehler. Kreise sie in der Zeichnung ein und beschreibe sie:</p>
  <ol><li><div class="lines"></div></li><li><div class="lines"></div></li><li><div class="lines"></div></li><li><div class="lines"></div></li></ol>
</div>
```

**Regler → drei Varianten:**
```html
<div class="print-alt">
  <div class="pgrid" style="grid-template-columns:repeat(3,1fr)">
    <figure><img src="data:…" alt="Abstand 1 mm"><figcaption>☐ a)</figcaption></figure> … b) … c)
  </div>
  <p>Begründung:</p><div class="lines"></div><div class="lines"></div>
</div>
```

**3D-Standbilder:**
```html
<div class="screen-only"> … 3D-Fenster … </div>
<div class="print-alt pfig2">
  <figure><img src="data:image/png;base64,…" alt="3D-Modell der KSV"><figcaption>3D-Modell der KSV</figcaption></figure>
  <figure><img src="data:image/png;base64,…" alt="Explosion"><figcaption>Auseinandergezogen (Explosion)</figcaption></figure>
</div>
```

## 5. Standbilder erzeugen (3D, Animation)
Dafür eine **Kopie** der Seite im Scratchpad nehmen, nie die Seite selbst:
1. In die Kopie vor `</body>` ein kleines Script setzen, das den gewünschten Zustand herstellt, z. B. Ansicht „iso“ klicken, Explosionsregler auf 70 setzen oder Schritt 3 wählen.
2. Mit Edge headless ein Bild machen: `msedge --headless=new --enable-unsafe-swiftshader --use-angle=swiftshader --window-size=1200,900 --virtual-time-budget=6000 --screenshot=<Scratchpad>\bild.png file:///<Scratchpad>/kopie.html` (Windows: `C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe`, am Mac Edge oder Chrome).
3. Das Bild mit Read ansehen und zuschneiden (Pillow in einer venv im Scratchpad).
4. Mit `scripts/medien-einsetzen.py --datei <bild.png> <Seite> <Platzhalter>` einsetzen und unter `Ressourcen/Bilder/<Thema>/` ablegen.

Liegen die Standbilder schon in einer NILS-PDF-Druckfassung, kannst du sie dort entnehmen (`ausgabe/NILS_*_PDF_*.pdf`).

## 6. Prüfen
`python .claude/gemeinsam/scripts/seite-pruefen.py <Seite>` legt `<name>-leerdruck.pdf` im Arbeitsordner ab. Seiten ansehen: im Scratchpad mit pypdfium2 in Bilder umwandeln (venv) und mit Read öffnen. Achte auf:
- Name/Klasse/Datum vorhanden.
- Keine Lösung zu sehen.
- Jede Aufgabe auf Papier lösbar, also keine leere Spielfläche und kein „Tippe …“.
- Auswahlkästen vollständig.
- Genug Schreiblinien.
- Keine Aufgabe zerrissen.

Hinweise „Spielergebnis ohne Papierfassung“ beheben oder im Bericht begründen.
