# Baue-E-Learning – Schritte 4a, 4b, 4d: Module, eigene Interaktivität, Grafiken

Teil des Skills Baue-E-Learning (Ablauf in `SKILL.md`). Jedes interaktive Element braucht für den Leerdruck eine Papierfassung: `druckfassung.md`.

## Schritt 4a – Interaktive Module übernehmen (3D, Simulation, Spiele)
Gehört zum Original ein interaktives Modul, wird es **verbatim** übernommen:
1. Im Original suchen: die zugehörigen CSS-Regeln, das HTML des Moduls, Datenblöcke (`<script type="application/json">`, `text/plain`) und den JS-Teil. Große Datenblöcke nie ausgeben oder abtippen, sondern mit `sed`/Skript direkt in die neue Datei kopieren (Zeilennummern per Grep bestimmen).
2. CSS in ein **zusätzliches** `<style>` nach dem Vorlagen-`<style>`, Datenblöcke und JS in **zusätzliche** `<script>`-Blöcke vor `</body>`, also nach dem Vorlagen-Script. Die Vorlagen-Blöcke bleiben unverändert. Im JS-Teil nur entfernen, was auf die alte Hülle zeigt (`Abgabe`, Namensabfrage, `store`, Fortschrittszähler); eine eigene Passwortprüfung des Moduls auf den Hash umstellen (`.claude/gemeinsam/regeln/seite.md`). Der Rest bleibt, wie er ist, im selben Gültigkeitsbereich. Neu geschrieben wird nur das kleine Script aus Punkt 3.
3. Elemente mit Live-Rückmeldung (z. B. "Richtig! 3 von 8") bekommen die Klasse `no-pdf`. Das Ergebnis eines Spiels oder einer Simulation wird per Script in ein `<input type="text" readonly>` **innerhalb der Aufgabe** geschrieben (danach `input`-Ereignis auslösen): So zählt die Aufgabe als bearbeitet, wird gespeichert und steht im PDF. Schreibt das Modul ein Ergebnis wie "6 von 8", bekommt das Feld `data-score` (bzw. `data-score="richtig"` bei "x von y richtig"): Dann zählt das Ergebnis als Punkte.
4. Für den Druck unnötige Bedienelemente (Regler, Canvas, Spielfeld) bekommen `screen-only`, und die Aufgabe bekommt eine **Papierfassung** in `<div class="print-alt">` nach dem Katalog in `druckfassung.md` (z. B. Standbilder statt 3D, Nummernkästchen statt Sortieren). Ohne Papierfassung meldet `seite-pruefen.py` einen Hinweis.
5. Zusätzliche Schriftfeld-Zellen des Originals (z. B. Allgemeintoleranz) als `<div class="wide">` nach der Name-Zelle einfügen; die Zelle "Lernfeld · Blockwoche" bleibt immer erhalten.
6. **Prüfen:** `python .claude/gemeinsam/scripts/seite-pruefen.py <Seite>` (lädt die Seite headless mit WebGL, kein roter Fehlerkasten, Leerdruck und PDF-Export als Datei). Modul im Screenshot sichtbar? Wenn möglich, Ergebnisfeld und Speichern testen.

## Schritt 4b – Eigene Interaktivität bei neuen E-Learnings aus PDFs
Bei Arbeitsweise A (neues E-Learning aus PDFs) darfst du für Aufgaben, die auf Papier nur schwer zu lösen sind, zusätzliches CSS und JavaScript schreiben, z. B. Zuordnen per Klick, Reihenfolge sortieren, Bild mit anklickbaren Punkten, einfache Rechen- oder Bewegungssimulationen.
Regeln dafür:
- Eigener `<style>`- und `<script>`-Block **nach** den Blöcken der Vorlage; die Blöcke der Vorlage bleiben unverändert.
- Reines JavaScript ohne Bibliotheken, offline, keine externen Adressen, keine Cookies, nichts an Server senden.
- Das Ergebnis der Aufgabe wird in ein `<input type="text" readonly>` **innerhalb der Aufgabe** geschrieben (danach `input`-Ereignis auslösen). So zählt sie als bearbeitet, wird gespeichert und steht im PDF. Live-Rückmeldungen bekommen `no-pdf`.
- Die richtige Lösung nie im sichtbaren HTML, in eigenen `data-`-Attributen oder in eigenem Code ablegen. Erlaubt sind nur die Bewertungsangaben der Vorlage (`data-ok`, `data-tol`, `data-keys`, `data-score`) am Ergebnisfeld: Der Zusatzcode schreibt die Antwort ins Ergebnisfeld, bewertet wird dort. Für eine Selbstprüfung liest der Zusatzcode `data-ok` des Ergebnisfelds und zeigt nur das Ergebnis (z. B. "3 von 5 richtig"), nie die Lösung, solange die Sperre zu ist.
- Tastatur-bedienbar und mit Touch nutzbar halten.
- Danach die Seite im Headless-Browser laden (kein roter Fehlerkasten) und die Funktion mindestens einmal testen. Sage in der Antwort, was getestet wurde und was nicht.
- In `Allgemeinbildung.html` die fertigen Stile der Vorlage nutzen (`.fb`, `.echo`, `.marktools`/`.tool`/`.sent`, `.pool`/`.bucket`/`.item`, `ol.order`, `.sl`, `ok`/`bad`, `agree`/`differ`; Liste im Kommentar der Vorlage), statt eigenes CSS zu schreiben.


## Schritt 4d – Alte Grafiken und Zeichnungen neu zeichnen und putzen
Gilt bei Arbeitsweise A und B: Jede Grafik oder Zeichnung aus altem Material (Scan, PDF, Foto eines Blatts, alte HTML-Datei) kommt neu gezeichnet oder geputzt in die Seite, nie unbearbeitet. Fertige Seiten in `Unterricht/` stellst du nicht von selbst um, nur wenn die Lehrkraft eine Seite oder Zeichnung nennt.

| Grafik | Vorgehen |
|---|---|
| Technische Zeichnung, Skizze, Diagramm, Schaubild, Symbol | neu als SVG zeichnen (Standard) |
| Tabelle oder reiner Text im Bild | als HTML-Tabelle bzw. Text abtippen |
| Foto, Screenshot, 3D-Darstellung | nicht nachzeichnen, nur putzen |
| Zeichnung, die sich nicht treu nachzeichnen lässt (Vergleich unten fällt durch, z. B. Freiformen, sehr viele Details) | putzen, im Bericht begründen |
| Bild in einem Modul aus Schritt 4a, Bild mit anklickbaren Punkten, Logo der Vorlage | bleibt unverändert |

**Der Inhalt bleibt gleich:**
- Gleiche Ansichten, Anordnung und Proportionen. Alle Maße, Toleranzen, Oberflächen- und Form-/Lagesymbole, Positionsnummern und Beschriftungen wörtlich. Auch Schriftfeld-Angaben, die die Aufgabe braucht (z. B. ISO 2768-m, Werkstoff, Maßstab), bleiben erhalten.
- Weg kommen nur Scanrauschen, Grauschleier, Flecken, Knicke, Lochung, Seitenzahlen, Stempel, handschriftliche Notizen und Namen von Schülerinnen und Schülern. Eine Quellenangabe (Verlag, Norm, Fotograf/in) bleibt, notfalls als `<figcaption>`.
- Eine unlesbare Stelle nie raten: erst in Musterlösung, Aufgabentext und anderen Ansichten nachsehen, sonst die Lehrkraft fragen.
- Offensichtliche Fehler (z. B. ein fehlendes Ø) korrigieren und im Bericht melden.
- Keine Lösung im Bild und nicht im `alt`: Eintragungen aus der Musterlösung entfernen, eine Lösungszeichnung gehört in `details.sol`. Gesuchte Größen bleiben Buchstaben ("a", "x").

**SVG zeichnen** (Vorbild: Aufgaben 1.3 und 4.2 in `Unterricht/MGF10/LF1/BW2/Toleranzen-4-Pruefmasse-berechnen-und-Prueftabelle/index.html`):
- Einbetten als `<figure class="fig"><img src="data:image/svg+xml;base64,..." alt="..." style="max-width:420px"></figure>`, nicht als Inline-`<svg>`: So bleibt der Grund auch im Dunkelmodus weiß, und `<pattern>`-Kennungen mehrerer Zeichnungen stören sich nicht.
- Hat die Seite das CSS dafür noch nicht, kommt es in einen zusätzlichen `<style>` nach dem Vorlagenblock:
  ```css
  figure.fig { margin:10px 0 14px; }
  figure.fig img { display:block; max-width:100%; height:auto; background:#fff; border:1px solid var(--line); padding:4px; border-radius:2px; }
  @media print { figure.fig img { border:0; padding:0; } }
  ```
- Aufbau: `viewBox` plus `width` und `height`, als Erstes `<rect width="..." height="..." fill="#fff"/>`. Kein Rasterbild im SVG, nichts Externes.
- Farbe: Zeichnungen nur `#000` auf Weiß, Farbe nur, wenn sie etwas aussagt (z. B. Baugruppen).
- Linien: Körperkanten `stroke-width="2.6"`, Maß-, Hilfs- und Mittellinien `1.1`, Schraffur `0.9` unter 45° (`<pattern>`), Mittellinien zusätzlich `stroke-dasharray="22 4 2 4"`, Maßpfeile als gefüllte `<polygon>`.
- **Technisches Zeichnen (Seiten mit `<meta name="schrift" content="nils">`):** Zeichnungen als **Inline-`<svg>`** (erstes Element `<rect … fill="#fff"/>`, alle `id` in `<pattern>`/`<marker>` mit eindeutigem Präfix je Zeichnung, z. B. `k4z2-hatch`), damit die Seite sie automatisch in **NILS Normschrift** setzt (`main svg text`). Eine als `<img>` eingebettete SVG kann die Seitenschrift nicht nutzen. Durchmesser immer `⌀` (U+2300), nie `Ø`. Für alle anderen Seiten gilt:
- Schrift: `<text>` mit `font-family="Arial, Helvetica, sans-serif" font-style="italic" font-size="22"`, Zeichen wie ⌀, ×, °, − als Unicode. `viewBox`-Breite und `max-width` so wählen, dass die Schrift in der Anzeige mindestens 15 px groß ist (22 × `max-width` ÷ `viewBox`-Breite).
- `alt`: sagt, was zu sehen ist, und nennt alle Maße.

**Putzen (Rastergrafik):**
- Beste Quelle nehmen: das eingebettete Bild oder die PDF-Seite mit 300 dpi, kein Bildschirmfoto.
- Zuschneiden, Schräglage ausrichten, längste Kante höchstens 1600 px. Strichzeichnungen: Graustufen, Medianfilter, Kontrast, heller Grund auf Reinweiß, als PNG. Fotos: nur Zuschnitt, Ausrichtung und Helligkeit, als JPEG.
- Die Richtung geben die Maßzahlen vor, nicht das Schriftfeld: Es darf quer liegen, dann wird das Blatt nicht gedreht.

**Technik:**
- Alte Bilder ansehen: `data:`-Bilder per Python-Skript im Scratchpad als Dateien auspacken und mit Read ansehen. PDF-Seite als Bild: `gswin64c -q -dNOPAUSE -dBATCH -sDEVICE=png16m -r300 -dFirstPage=3 -dLastPage=3 -sOutputFile=seite3.png quelle.pdf` (am Mac `gs`).
- SVG mit einem kleinen Python-Skript im Scratchpad erzeugen und per Skript als Base64 in die Seite schreiben (`.claude/gemeinsam/scripts/medien-einsetzen.py --datei <bild.svg> <Seite> <Platzhalter>`). Base64 nie ausgeben oder abtippen. Bilder aus einer Quelldatei: `medien-einsetzen.py --liste <Quelle>`, dann `src="nils-medium:<Nr>"` in die Seite schreiben und `--einsetzen <Quelle> <Seite>`.
- Fertige Zeichnungen, Standbilder und geputzte Bilder, die wieder gebraucht werden könnten, zusätzlich unter `Ressourcen/Bilder/<Thema>/` ablegen und in `Ressourcen/Inhalt.md` eintragen.
- Putzen mit Pillow. Fehlt es, in einer venv im Scratchpad installieren (`python -m venv`, dann `pip install pillow`).
- **Vergleich:** Original und neue Fassung nebeneinander auf eine Testseite im Scratchpad legen, im Headless-Browser als Bild speichern und mit Read ansehen: `msedge --headless=new --disable-gpu --user-data-dir=<Scratchpad>\edge-profil --window-size=1200,420 --screenshot=<Scratchpad>\vergleich.png file:///<Scratchpad>/vergleich.html` (Windows: `C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe`, am Mac Edge oder Chrome).
