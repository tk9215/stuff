---
name: Baue-E-Learning
description: Baut aus PDFs (Aufgabenblatt für Schülerinnen und Schüler plus Musterlösung) ein E-Learning als HTML nach einer der beiden Vorlagen in .claude/gemeinsam/templates/ (Fachunterricht.html = Schriftfeld-Seite, Allgemeinbildung.html = Lernschritte mit Schritt-Leiste, Phasen und Timer), oder baut eine bestehende HTML-Datei nach einer dieser Vorlagen um. Die Lehrkraft wählt die Vorlage im Auswahldialog. Die Musterlösung wird mit den Aufgaben verknüpft und bleibt hinter der Lehrkraft-Passwortsperre. Use when the teacher says "mach aus dem PDF ein E-Learning", "PDF in HTML umwandeln", "Musterlösung einbauen", "HTML auf die Vorlage umbauen", "Lernschritte-Vorlage", "wie das Ethik-E-Learning" or gives PDFs / a HTML file to convert.
---

# PDF oder HTML in ein E-Learning nach Vorlage umwandeln

Du baust aus Unterrichtsmaterial ein E-Learning, das genauso aussieht und funktioniert wie jedes andere Dokument aus der gewählten Vorlage (Schriftfeld, Aufgaben mit Eingabefeldern, PDF-Export, Hell/Dunkel, Lösungssperre). Das fertige Ergebnis kann danach mit dem Skill **Baue-Lernpaket** zu einem SCORM-Paket werden.

**Das Grundgerüst (Stil und Script der Vorlage) bleibt unverändert.** Du kopierst die gewählte Vorlage (`.claude/gemeinsam/templates/Fachunterricht.html` oder `Allgemeinbildung.html`) und füllst Kopf und `<main>`. Interaktive Module aus dem Original (3D-Ansicht, Simulationen, Spiele) werden **übernommen, nicht weggelassen** (Schritt 4a). Bei **neuen E-Learnings aus PDFs** darfst du zusätzliches CSS und eigenes JavaScript schreiben, um Aufgaben interaktiv zu machen (Schritt 4b). Die Bausteine stehen im Kommentar am Anfang der Vorlage.

## Zwei Arbeitsweisen
- **A. Aus PDFs:** ein Aufgabenblatt (Schülerversion, zum Ausfüllen) und eine Musterlösung. Beide werden gelesen und zusammengeführt.
- **B. Aus bestehender HTML-Datei:** Inhalt übernehmen, in die Struktur der Vorlage umbauen.

## Zwei Vorlagen (Layout)
- **Schriftfeld** (`Fachunterricht.html`): technisches Schriftfeld, eine lange Seite mit Kapiteln und Niveaus. Für Arbeitsblätter, Lernskripte, Übungen für eine Stunde.
- **Lernschritte** (`Allgemeinbildung.html`): dunkles Kopfband, Schritt-Leiste, eine Bildschirmseite je Schritt, Phasen mit Timer, Ergebnis-Seite (Beispiel: `Unterricht/ALLE10/Eth/BW1/Die-ethische-Brille/index.html`). Für Unterrichtsfolgen über mehrere Stunden.

Beide haben dieselben Funktionen (gleiche Style- und Script-Blöcke). Alles hier gilt für beide, die Unterschiede stehen in Schritt 4c und Schritt 5.

**Vorlage geändert?** Ablauf in `.claude/gemeinsam/regeln/seite.md` (Abschnitt Vorlage). Markierte Bereiche nie von Hand ändern.

Annahme bei "Schülerlösung": gemeint ist das **Aufgabenblatt für die Schülerinnen und Schüler** (ohne Lösungen). Ist stattdessen eine **ausgefüllte Schülerarbeit** gemeint, frage nach, wofür sie gebraucht wird. Ausgefüllte Arbeiten werden nie als Vorgabewerte in das E-Learning übernommen.

## Teile dieses Skills
| Datei | Inhalt |
|---|---|
| `.claude/gemeinsam/regeln/dialog.md` | Schritt 1: Auswahldialog für alle Skills (Vorlage, Klasse, Beruf, Fach · Abschnitt, Hilfsmittel, Niveaus), Listen, Ablageort |
| `bausteine.md` | Schritt 4: Bausteine der Vorlage, Regeln für Lösungsvorschläge, Bewertung, Punkte, Schlüssel; 4c Lernschritte |
| `module-grafiken.md` | 4a Module übernehmen, 4b eigene Interaktivität, 4d Grafiken neu zeichnen und putzen |
| `druckfassung.md` | Leeres Arbeitsblatt: was die Vorlage automatisch macht, Papierfassungen (`.print-alt`, `.screen-only`), Katalog aus den NILS-Skripten |
| `skript-uebernahme.md` | einen neueren Quelltext (z. B. NILS-Skript) in bestehende Abschnitte übernehmen, Zuordnung SuS/Lös, Rückmeldung an den Ersteller |

Regeln für alle Skills in `.claude/gemeinsam/regeln/`: `ablage.md`, `seite.md`, `sprache.md`, `abschluss.md` (vor dem Bauen lesen).

Werkzeuge in `.claude/gemeinsam/scripts/` (am Mac `python3`): `sync-vorlage.py` (Vorlagenblöcke und NILS-Schriften einsetzen), `seite-pruefen.py` (Prüfung plus Browser-Test), `medien-einsetzen.py` (eingebettete Bilder auflisten, ablegen, einsetzen), `pw-hash.py` (nur die Lehrkraft führt es aus).

Agenten: `skript-abgleicher` (je Seite einen Quelltext einarbeiten, parallel einsetzbar) und `seiten-pruefer` (fertige Seite prüfen, nur lesend).

**Technisches Zeichnen (NILS-Schriften, Festlegungen):** `.claude/gemeinsam/regeln/faecher.md`.

## Schritt 1 – Angaben klären (nur was fehlt)
Ablauf, Fragen, Listen und Ablageort: **`.claude/gemeinsam/regeln/dialog.md`** (vorher lesen). Kurz:
- Fehlen die Pfade zu Aufgaben-PDF und Musterlösung (oder zur HTML-Datei, zum NILS-Skript), im Chat fragen.
- Vorlage, Klasse, Beruf, Fach · Abschnitt (und Hilfsmittel) per AskUserQuestion, nur was fehlt, nie raten. Ausbildungsjahr folgt aus der Klasse.
- Allgemeinbildende Fächer: Kurzkopf `div.tb.kurz`, kein Beruf und keine Hilfsmittel.
- Nach dem Einlesen immer nach den Niveaus und den Sprachhilfen fragen (außer die Lehrkraft hat es gesagt).

## Schritt 2 – Einlesen
**PDFs:** mit dem Read-Werkzeug seitenweise lesen (`pages`, höchstens 20 Seiten pro Aufruf).
- Meldet Read, dass `pdftoppm` fehlt: Poppler (enthält `pdftoppm`) muss auf diesem Rechner installiert sein. Sag das der Lehrkraft und biete als Ausweg an, den Text des PDFs hier einzufügen.
- Liefert eine Seite keinen Text (Scan, Foto): Das kann ich nicht zuverlässig lesen. Sag es und bitte um die Textfassung.
- Namen oder andere personenbezogene Daten im PDF: nicht übernehmen, durch "Schülerin oder Schüler A" ersetzen und die Lehrkraft erinnern (Datenschutz laut CLAUDE.md).

**HTML (Arbeitsweise B):** Datei lesen (große Dateien in Teilen, Bilder als `data:`-Adressen nicht ausgeben; zum Ansehen auspacken, siehe Schritt 4d). Das Original wird nie verändert.

## Schritt 3 – Zusammenführen (Arbeitsweise A)
1. Aus dem Aufgabenblatt eine Liste bauen: Aufgabennummer, Titel, Aufgabentext, Punkte/Hinweise, Abbildungen, Antwortart.
2. Aus der Musterlösung zu jeder Aufgabe die Lösung, den Lösungsweg und die Bewertungshinweise.
3. Über die Aufgabennummer zuordnen. Melde der Lehrkraft am Ende: Aufgaben ohne Lösung, Lösungen ohne Aufgabe, abweichende Nummerierung. Nichts erfinden: Fehlt eine Lösung, gilt die Regel **Lösungsvorschläge** in Schritt 4 (nur Aussagen mit Quelle, bei Meinungsaufgaben nur Vergleichskriterien; für eine Fundstelle darfst du ohne Rückfrage im Web suchen). Lässt sich keine Quelle finden, keinen Vorschlag schreiben und darauf hinweisen.

## Schritt 4 – Umbau in Bausteine der Vorlage
- Bausteine, Lösungsvorschläge, Bewertung (`data-ok`, `data-keys`, `data-score`), Punkte (`data-gewicht`), Speicherschlüssel (`data-k`), Abbildungen, Formeln: **`bausteine.md`**.
- Lernschritte-Vorlage (Schritte, Phasen, Karten): **`bausteine.md`, Schritt 4c**.
- Interaktive Module übernehmen (4a), eigene Interaktivität bei neuen E-Learnings (4b), alte Grafiken neu zeichnen oder putzen (4d): **`module-grafiken.md`**.
- **Jede Aufgabe muss sich auf Papier lösen lassen** (leeres Arbeitsblatt): Interaktive Teile bekommen `screen-only` und eine Papierfassung `div.print-alt` nach dem Katalog in **`druckfassung.md`**, Textfelder genug Schreiblinien (`data-zeilen`).
- Neuerer Quelltext für vorhandene Abschnitte (z. B. NILS-Skript → Kugelsortiervorrichtung 1–6): **`skript-uebernahme.md`**.

## Schritt 5 – Bauen
Vorgehen nach `.claude/gemeinsam/regeln/seite.md`:
1. Vorlage kopieren und `sync-vorlage.py --datei <Seite> --schreiben` ausführen, genau nach `seite.md` (Abschnitt Vorlage).
2. `<title>`, Schriftfeld (Titel, Untertitel, Beruf, Ausbildungsjahr, Lernfeld · Blockwoche, Hilfsmittel) füllen. Der `<title>` ergibt auch den Namen der PDF-Datei ("Als PDF speichern"): Bei Kapiteln `<Kapitel> – <Thema> – <Titel im Schriftfeld>`, z. B. `Kugelsortiervorrichtung 4 – Formelemente, Bemaßung und Oberflächen – Technisches Zeichnen 1`; der Titel aus dem Schriftfeld am Ende entfällt im Dateinamen. Die Name-Zelle bleibt unverändert (der Name kommt aus der Lernplattform), das `<span class="ver">` im Benennungsfeld bleibt leer (die Version trägt Baue-Lernpaket beim Bauen ein). Bei `Allgemeinbildung.html` zusätzlich die Zeile über dem Titel füllen (z. B. `Ethik · 10. Klasse · B2 Nürnberg`); das Logo bleibt.
3. Lösungssperre: `<meta name="loesung-hash">` nach `seite.md` füllen (ein Hash für alles, nie ein Passwort im Klartext oder im Chat). Übernommene Module mit eigener Passwortabfrage prüfen ebenfalls gegen diesen Hash.
4. `<main>` mit den Bausteinen aus Schritt 4 füllen.
5. Speichern als **`Unterricht/<Klasse>/<Fach>/<Abschnitt>/<Thema>/index.html`** (z. B. `Unterricht/MGF10/LF1/BW4/Pythagoras-1-Grundlagen/index.html`, siehe Schritt 1). Der Ordner ist direkt als Quelle für Baue-Lernpaket geeignet. Bilder sind eingebettet (Schritt 4). Nur große Medien (Video, 3D-Modell) liegen als Datei im selben Ordner.

## Schritt 6 – Prüfen (Pflicht)
1. `python .claude/gemeinsam/scripts/seite-pruefen.py <Seite> --arbeitsordner <Scratchpad>\pruefen` (Prüfung aus `.claude/gemeinsam/regeln/abschluss.md` plus Browser-Test). Screenshot und Leerdruck ansehen (PDF-Seiten im Scratchpad mit pypdfium2 in Bilder umwandeln). Hinweise beheben oder im Bericht nennen.
2. **Vollständigkeit:** Anzahl der Aufgaben im HTML = Anzahl im Original. Jede zugeordnete Lösung steht in einer Aufgabe oder in `section.answers`.
3. **Lösungen verborgen:** Mit Grep prüfen, dass in `<main>` keine Lösungstexte außerhalb von `details.sol`, `section.answers`, `.sol-only` stehen (Stichproben mit markanten Lösungswörtern).
4. **Eingabefelder:** Jede Aufgabe mit Antwort hat ein Feld, jedes `<select>` beginnt mit leerer Option, kein Feld hat einen Vorgabewert, jedes Feld hat einen eigenen `data-k` (kein Schlüssel doppelt).
5. **Niveaus:** Jede Aufgabe liegt in einem `level`-Block (außer die Lehrkraft hat "Ohne Niveaus" gewählt).
6. **Nur Allgemeinbildung.html:** Schrittnummern in den Überschriften lückenlos, letzter Schritt ist `section.step.result` mit `#stepResult`, jede `phasebar` hat ein gültiges `data-form`, kein `<h3>` in `.teacher`/`.sol-only`. Im Headless-Browser einmal durch alle Schritte klicken (Leiste und Weiter).
7. **Abbildungen:** Jede neue Fassung neben dem Original ansehen (Vergleich aus Schritt 4d). Jedes Maß, Symbol und jede Beschriftung des Originals einzeln abhaken. Nichts ist abgeschnitten oder überdeckt, keine Lösung steht im Bild oder im `alt`, kein Scan steht ungeputzt in der Seite.
8. **Leerdruck:** Jede Aufgabe ist auf Papier lösbar (`druckfassung.md`, Abschnitt 6).
Fehler beheben, erneut prüfen, dann in einer Zeile sagen, welche Prüfungen bestanden sind.

## Schritt 7 – Abschluss
Kurz und konkret:
- Öffnen, Standardsatz und Commit-Frage nach `.claude/gemeinsam/regeln/abschluss.md`.
- Welche Vorlage (Schriftfeld oder Lernschritte) und was übernommen wurde (Anzahl Aufgaben, Niveaus, Lösungen verknüpft; bei Lernschritte Anzahl Schritte und Minuten je Stunde).
- **Lösungsvorschläge:** bei welchen Aufgaben ein Vorschlag mit Quelle steht, bei welchen nur Vergleichskriterien und welche keinen haben (Organisationsaufgaben, keine Quelle gefunden).
- **Abbildungen:** welche neu gezeichnet, welche nur geputzt (mit Grund), welche unverändert geblieben sind, und jede inhaltliche Korrektur (z. B. ergänztes Ø).
- **Offene Punkte:** fehlende Abbildungen, Aufgaben ohne Lösung, nicht übernommene Interaktivität, gemachte Annahmen (z. B. Niveau-Einteilung, "Schülerlösung" = Aufgabenblatt).
- Nächster Schritt anbieten: "Soll ich daraus mit Baue-Lernpaket ein SCORM-Paket für die ByCS Lernplattform bauen?"

## Grenzen (offen sagen)
- Abgabe, Punkte (40/40/20, bestanden ab 70 %), Bewertung und was Lernende nach der Abgabe sehen: `.claude/skills/Baue-Lernpaket/punkte.md`. Kurz: Nach der Abgabe sehen sie alle Lösungsvorschläge in `details.sol` (auch im PDF); was sie nie sehen sollen (Bewertungsraster, Hinweise für die Lehrkraft), gehört in `section.answers` oder `.sol-only`. Aufgaben ohne hinterlegte Lösung zählen als "bearbeitet = volle Punkte".
- Eigene interaktive Module (Schritt 4a/4b) werden nach der Abgabe nicht automatisch gesperrt; ihr Ergebnisfeld schon, und es wird nichts mehr gemeldet.
- Die Lösungssperre hält nur ab, wer nicht in den Quelltext schaut. Für Prüfungen sind die Lösungen in einer getrennten Datei besser aufgehoben.
- Neu zeichnen und putzen geht nur, wo das Original lesbar ist: Unlesbare Scans und sehr komplexe Zeichnungen lassen sich ohne bessere Vorlage nicht vollständig übernehmen.
- Beide Vorlagen speichern Eingaben nur in der Lernplattform (SCORM). Per Doppelklick geöffnet, gehen Eingaben beim Neuladen verloren; `Allgemeinbildung.html` merkt sich dort nur den zuletzt geöffneten Schritt.

## Datenschutz
- Keine Namen oder Noten von Lernenden anfordern, speichern oder übernehmen (Felder für Gruppenmitglieder siehe Schritt 4).
- Nichts auf externe Dienste hochladen (Ausnahmen: CLAUDE.md, Datenschutz).
