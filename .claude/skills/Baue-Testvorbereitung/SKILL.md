---
name: Baue-Testvorbereitung
description: Baut eine Testvorbereitung als E-Learning (HTML nach Vorlage Fachunterricht.html) zu einem Thema aus den Unterlagen der Lehrkraft - Lernskript in Reitern, Übungen mit immer neuen Zufallsaufgaben oder Fragenpools (Prüfen, Lösung zeigen, Lösungsweg), Prüfungssimulation mit Timer, Punkten und Note nach der Schulnotenskala, Papierversion mit Varianten und Lösungsblatt. Ohne Bewertung (kein Abgeben), das beste Ergebnis der Simulation wird angezeigt. Vorbild Toleranzen 6 – Testvorbereitung. Use when the teacher says "Testvorbereitung", "Lernskript zur Testvorbereitung", "Probetest", "Prüfungssimulation", "Übungsskript für den Test", "wie die Testvorbereitung Toleranzen".
---

# Testvorbereitung bauen

Ergebnis: **eine Seite** `Unterricht/<Klasse>/<Fach>/<Abschnitt>/<Thema>-Testvorbereitung/index.html`. Sie besteht aus der Vorlage `Fachunterricht.html` (Schriftfeld, Hell/Dunkel, Lösungssperre, PDF, SCORM) und dem **Baukasten** `templates/baukasten.html`, der das Gleiche für jedes Thema mitbringt:
- **Reiter** mit den Teilthemen: Lerntext, Formeln, Tabellen, Merksätze aus den Unterlagen.
- **Übungen** unter jedem Teilthema: „Prüfen“, „Lösung zeigen“ (mit Lösungsweg), „Neue Aufgabe“, Zähler „Richtig gelöst“. Rechenbare Themen bekommen Zufallsgeneratoren, nicht rechenbare einen Fragenpool. Der Skill kann beides, auch gemischt.
- **Prüfungssimulation:** neue Aufgaben bei jedem Start, Timer, Abgeben, Punkte und Note (Schulnotenskala 92/81/67/50/30 %, wie ByCS-Kurs und ByCS-Test), Fehler mit Lösungen. Das beste Ergebnis steht in Aufgabe 1 im Kapitel.
- **Papierversion:** Dialog mit Lernskript, Übungsaufgaben je Art (Anzahl), Probetest mit Notenschlüssel, Lösungsblatt; feste **Variante**, damit das Lösungsblatt später nachgedruckt werden kann.
- **Ohne Bewertung:** Das Kapitel hat kein Eingabefeld, deshalb gibt es kein „Abgeben“; das Paket meldet nur „bearbeitet“.

Je Thema schreibt Claude nur: Schriftfeld, die Abschnitte (Block `Testvorbereitung:app`), den Lösungsvorschlag in Aufgabe 1 (Block `:main`) und den **Thema-Block** (Block `:thema`) mit den Aufgabenarten. Stil und Script des Baukastens (`:stil`, `:script`) nie in der Seite ändern. Wie das geht: **`aufgaben.md`** (vor Schritt 4 lesen).

Die Regeln aus `.claude/gemeinsam/regeln/seite.md`, `sprache.md` (Sprachhilfen stehen im Plan, Dialog 2), `ablage.md` und `abschluss.md` gelten wie bei jedem E-Learning (Passwort-Hash, keine externen Ressourcen, HTML-Prüfung, Ablage, Groß-/Kleinschreibung). Neuer interaktiver Code ist hier erlaubt (neues E-Learning aus Unterlagen), immer in zusätzlichen Blöcken nach den Vorlagenblöcken.

## Schritt 1 – Thema und Unterlagen (im Chat, zuerst)
Fehlt etwas davon in der Nachricht, im Chat fragen (eine Nachricht, nummeriert):
1. **Thema** der Testvorbereitung (z. B. „Toleranzen“, „Satz des Pythagoras“).
2. **Wo liegen die Unterlagen?** Ordner oder Dateien, z. B. `ToDo/<Thema>/` (PDFs, Skripte, Musterlösungen), vorhandene E-Learnings in `Unterricht/…`, NILS-Skripte in `Ressourcen/NILS/`. Gibt es noch keinen Ordner, `ToDo/<Thema>/` anlegen und die Lehrkraft bitten, die Unterlagen hineinzulegen (Ordner im Finder/Explorer öffnen: `open` bzw. `explorer`).
3. **Welche Teilthemen kommen im Test vor?** (Was nicht drankommt, wird nicht geübt.)
4. **Gibt es den echten Test schon?** (z. B. `Test-<Thema>/Fragen-*.xml` aus ByCS-Fragenersteller oder ein Test-PDF) Dann übernimmt die Testvorbereitung Aufgabenarten, Schwierigkeit, Hilfsmittel und Zeit, aber **keine Aufgabe des Tests** (keine gleiche Frage, keine gleichen Zahlen).

## Schritt 2 – Angaben klären (nur was fehlt)
Nach **`.claude/gemeinsam/regeln/dialog.md`** (Listen lesen, nur fragen, was fehlt, nie raten, Listen fortschreiben). Die Vorlage wird nicht gefragt: immer Schriftfeld (`Fachunterricht.html`).
- **Dialog 1:** Klasse, Beruf, Fach · Abschnitt, Hilfsmittel (allgemeinbildende Fächer: Kurzkopf, ohne Beruf und Hilfsmittel).
- **Dialog 2** (nach dem Einlesen, Schritt 3):
  - **Dauer** (Header „Dauer“): Arbeitszeit der Prüfungssimulation = Zeit des echten Tests. Optionen `20 Minuten`, `30 Minuten`, `45 Minuten` („(empfohlen)“ auf der Zeit aus dem echten Test, falls bekannt).
  - **Punkte** (Header „Punkte“): etwa so viele Punkte wie im echten Test. Optionen: Punktzahl des echten Tests „(wie im Test)“, falls bekannt, sonst `etwa 20`, `etwa 30`, `etwa 40`. Die genaue Summe ergibt sich aus den Aufgaben (thema-test.py zeigt sie); der Notenschlüssel ist immer die Schulnotenskala und wird nicht gefragt.
  - **Niveaus** (Header „Niveaus“, nach `dialog.md`): `Ohne Niveaus (empfohlen)` – „wie der Test, eine Prüfungssimulation für alle“ – und `Drei Niveaus` – „jede Übungsart bekommt ein Niveau-Etikett (blau, rot, schwarz); die Prüfung bleibt gleich“.
  - **Plan** (Header „Plan“): Reiter, Aufgabenarten (je Art: Generator oder Pool, Quelle), Zusammensetzung der Prüfung und Sprachhilfen im Lernskript (`dialog.md`, Sprachhilfen: in BVJ und BIK Wortliste je Reiter vorschlagen, sonst keine) als `preview`. Optionen `So bauen (empfohlen)`, `Ändern`.

## Schritt 3 – Einlesen und planen
- Unterlagen lesen wie in Baue-E-Learning, Schritt 2 (PDFs seitenweise, Scans melden, Namen von Lernenden nie übernehmen).
- Daraus eine Liste: Teilthema → Reiter; je Teilthema Lerninhalt (Formeln, Tabellen, Merksätze, Fachbegriffe) mit **Fundstelle**; Aufgabenarten aus den Aufgaben der Unterlagen (Rechenweg aus der Musterlösung).
- Je Aufgabenart entscheiden: **Generator** (Zahlen ändern sich, Rechenweg bleibt) oder **Pool** (Begriffe, Regeln, Zuordnungen). Pools aus den Unterlagen ableiten, mindestens doppelt so viele Fragen, wie eine Prüfung zieht.
- **Quellen streng:** nur Inhalte aus den Unterlagen. Fehlt eine Tabelle oder ein Wert (z. B. Abmaße einer Toleranzklasse), nicht ergänzen, sondern die Lehrkraft fragen. Bei Abweichungen zwischen Unterlagen (z. B. alte und neue Norm) fragen, welche gilt.
- Dann Dialog 2 (Schritt 2).

## Schritt 4 – Bauen
1. Seite anlegen (am Mac `python3`):
   `python .claude/skills/Baue-Testvorbereitung/scripts/neue-seite.py Unterricht/<Klasse>/<Fach>/<Abschnitt>/<Thema>-Testvorbereitung`
   Legt `index.html` an: Vorlage ohne TEMPLATE-Kommentar, Passwort-Hash, Baukasten, Gerüst. Fehlt `solution-password.txt`, die Lehrkraft `pw-hash.py` selbst ausführen lassen (`.claude/gemeinsam/regeln/einrichtung.md`).
2. `<title>` = `Testvorbereitung <Thema>` (ergibt den PDF-Namen). Schriftfeld: Titel `Testvorbereitung <Thema>`, Untertitel `<Thema> · Lernskript mit Übungen und Prüfungssimulation`, Beruf, Ausbildungsjahr, Lernfeld · Blockwoche, Hilfsmittel. `span.ver` bleibt leer.
3. Block `Testvorbereitung:app` füllen: Einleitungssatz (`.lead`), je Teilthema ein `section.tv-sec` mit `.tv-skript` und `.tv-uebung`; der Abschnitt „Prüfung“ bleibt am Ende (`aufgaben.md`, Abschnitt 1).
4. Block `Testvorbereitung:main`: Aufgabe 1 bleibt ohne Eingabefeld (keine Bewertung). Im `details.sol` die Formeln, Regeln und Rechenwege aus den Unterlagen als Kurzfassung (Lösungsvorschlag mit Quelle, `seite.md`). Minuten und Hilfsmittel im Aufgabentext eintragen, wenn sie dort genannt werden.
5. Block `Testvorbereitung:thema`: Aufgabenarten, Prüfung, Titel (`aufgaben.md`, Abschnitt 2 und 3). Über jeder Aufgabenart `/* Quelle: … */`.

## Schritt 5 – Prüfen (Pflicht)
1. `python .claude/skills/Baue-Testvorbereitung/scripts/thema-test.py <Seite>`: erzeugt jede Aufgabenart 300-mal und prüft Felder, Lösungen, Varianten, Prüfungssumme. Fehler beheben, bis „Alle Aufgaben in Ordnung“. Die Beispiele und die Punktsumme mit dem Plan vergleichen.
2. **Fachlich nachrechnen:** je Aufgabenart drei Beispiele aus der Ausgabe von Hand mit den Unterlagen nachrechnen bzw. im Pool gegen die Fundstelle prüfen.
3. **Abgrenzung zum Test** (wenn es ihn gibt): Fragetexte des Tests gegen die Pools greppen (markante Wörter), keine Übereinstimmung.
4. `python .claude/gemeinsam/scripts/seite-pruefen.py <Seite> --arbeitsordner <Scratchpad>/pruefen` (Prüfung nach `.claude/gemeinsam/regeln/abschluss.md` mit Browser-Test). Findet das Skript keinen Browser (Edge/Chrome), das im Bericht sagen und die Seite zur Kontrolle öffnen (Schritt 6).
5. Mit Grep: keine Platzhalter (`Teilthema 1`, `Beispielaufgabe`, `Lerninhalt aus den Unterlagen`, `Kurzfassung der Formeln`), kein `Math.random` im Thema-Block.
Dann in einer Zeile sagen, welche Prüfungen bestanden sind.

## Schritt 6 – Abschluss
- „Doppelklick auf `Unterricht/…/index.html` zum Öffnen. Mit 'Papierversion drucken / als PDF' druckst du Übungsblätter und Probetests mit Lösungsblatt.“ Dann die Seite im integrierten Browser öffnen (`code -r "<Seite>"`, `abschluss.md`) und bitten, einmal Übung, Prüfung (Abgeben) und Papierversion durchzuklicken.
- Reiter, Aufgabenarten (Generator/Pool, Anzahl Pool-Fragen), Prüfung (Minuten, Aufgaben, Punkte), Niveaus.
- **Quellen:** je Aufgabenart die Fundstelle; was gefehlt hat und nicht eingebaut wurde.
- Offene Punkte, Annahmen.
- Nächster Schritt: „Soll ich daraus mit Baue-Lernpaket ein SCORM-Paket bauen?“ (Das Paket meldet nur „bearbeitet“, keine Punkte.)

## Baukasten ändern
Änderungen an Aussehen oder Verhalten nur in `templates/baukasten.html` (Blöcke `stil` und `script`), dann
`python .claude/skills/Baue-Testvorbereitung/scripts/neue-seite.py --aktualisieren` (alle Testvorbereitungen in `Unterricht/`), thema-test.py für jede Seite, Pakete neu bauen (Nebenversion). Vorlagenblöcke von `Fachunterricht.html` pflegt weiter `sync-vorlage.py` (Skill Baue-E-Learning); beide Werkzeuge lassen die Blöcke des anderen in Ruhe.

## Grenzen (offen sagen)
- Die Lösungen der Übungen stehen im Quelltext (Absicht: Selbstkontrolle). Für bewertete Tests den Skill ByCS-Test nehmen.
- Eingaben in Übung und Prüfung werden nicht gespeichert; nach dem Neuladen beginnt die Übung neu. Gespeichert wird nur das beste Ergebnis (im SCORM-Paket).
- Generatoren rechnen mit Gleitkommazahlen: Ergebnisse immer mit `TV.runde` auf die Stellen der Aufgabe bringen.
- Ohne Edge/Chrome läuft der Browser-Test nicht; dann bleibt die Kontrolle im integrierten Browser durch die Lehrkraft.
