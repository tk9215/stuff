---
name: Uebungs-App
description: Baut eine kleine interaktive Übungs-App für Schülerinnen und Schüler als eine Offline-HTML-Datei (Quiz mit Hinweisen, Lernkarten, Sortierspiel oder Zuordnungsspiel). Verwenden, wenn die Lehrkraft eine interaktive Übung, ein Lernspiel, ein Übungswerkzeug oder einen Selbsttest für Schülerinnen und Schüler möchte.
---

# Interaktive Übungs-App (eine HTML-Datei)

Du baust eine kleine Lern-App, die Schülerinnen und Schüler in jedem Browser öffnen. Ohne Anmeldung, ohne Internet, ohne Datenerfassung.
**Du schreibst den Code der App nie selbst.** Die getestete App steht in `.claude/skills/Uebungs-App/templates/uebungs-app.html`.
Du trägst nur Titel, Passwort-Hash und die Fragen ein. So bleibt die App heil.

## Schritt 1 – Angaben klären (nur was fehlt)
**Klasse, Beruf, Fach und Abschnitt, Niveaus** per Auswahldialog nach `.claude/gemeinsam/regeln/dialog.md` (nie raten; Niveaus im ersten Dialog, Fall A). Fragen, Hinweise und Rückmeldungen nach `.claude/gemeinsam/regeln/sprache.md` schreiben (Pflicht in BVJ und BIK, sonst Richtschnur; nach Sprachhilfen nicht fragen). Bei allgemeinbildenden Fächern bleiben die JSON-Felder `beruf`, `jahr`, `lernfeld` und `hilfsmittel` leer.
**Thema und Art** in einer Nachricht im Chat:
1. **Quiz mit Hinweisen** (`"type": "quiz"`): Hinweis nach dem ersten Fehlversuch, Erklärung nach der Antwort
2. **Lernkarten** (`"type": "flashcards"`): umdrehen, "Wusste ich" / "Nochmal üben"
3. **Sortieren** (`"type": "sort"`): Begriffe in 2–3 Gruppen einordnen
4. **Zuordnen** (`"type": "match"`): Paare, Begriff und Definition
Hat die Lehrkraft keine Vorliebe, das Quiz mit Hinweisen wählen.

## Schritt 2 – Bauen
1. `.claude/skills/Uebungs-App/templates/uebungs-app.html` nach `Unterricht/<Klasse>/<Fach>/<Abschnitt>/<Thema>-Uebung/index.html` kopieren (`.claude/gemeinsam/regeln/ablage.md`; nicht `Fachunterricht.html`: die ist für Dokumente). Der Ordner ist direkt die Quelle für Baue-Lernpaket.
2. Den Titel-Tag auf das Thema ändern. `"lang"` im JSON auf `"de"` (Standard) oder `"en"` setzen.
   Die App hat dasselbe Aussehen wie `Fachunterricht.html` (Schriftfeld, standardmäßig hell). Das Schriftfeld über die JSON-Felder `title`, `subtitle`, `beruf`, `jahr` (Ausbildungsjahr aus der Klasse), `lernfeld` (`<voller Name des Fachs> · Blockwoche <n>`), `hilfsmittel` füllen. Der Schülername wird aus der ByCS Lernplattform gelesen und nie eingetippt.
   **Passwort-Hash:** `content` von `<meta name="loesung-hash">` auf den Wert `hash=` aus `.claude/gemeinsam/data/solution-password.txt` setzen (`.claude/gemeinsam/regeln/seite.md`, Lösungssperre). Im Lehrkraft-Modus zeigt die App dann eine Lösungsübersicht aller Einträge.
3. NUR das JSON zwischen `<script id="app-data" type="application/json">` und dem zugehörigen `</script>` ersetzen.
   Die Formate der Einträge stehen im Kommentar am Anfang der Vorlage. 8–12 Einträge erstellen.
4. CSS und die anderen `<script>`-Blöcke nicht anfassen.
5. **Punkte für die Lernplattform:** Quiz, Sortieren und Zuordnen melden im SCORM-Paket (Skill Baue-Lernpaket) jede Aufgabe: richtig beim ersten Versuch = Punkt. Jeder Eintrag darf `"level": "foundation"`, `"core"` oder `"challenge"` haben (Standard `core`; Gewichtung 40 / 40 / 20 %, Bestehen ab 70 %). Mische die Niveaus nach CLAUDE.md; bei "Ohne Niveaus" das Feld `level` weglassen. Lernkarten melden "abgeschlossen" (100 Punkte, bestanden), wenn alle Karten gewusst sind. Ohne Lernplattform (Doppelklick) passiert nichts.

JSON-Regeln (ein Fehler = kaputte App):
- Jeder Text in doppelten Anführungszeichen `"..."`. Apostrophe wie in `Gerd's` sind in Ordnung.
- Ein doppeltes Anführungszeichen im Text muss als `\"` geschrieben werden. Besser: doppelte Anführungszeichen im Text vermeiden.
- Kommas zwischen Einträgen, aber **kein Komma nach dem letzten Eintrag** einer Liste.
- `"answer"` und `"group"` sind Zahlen, ab 0 gezählt (erste Option = 0).
- Jeder Quiz-Eintrag hat `question`, `options`, `answer`, `hint`, `explanation`.

## Schritt 3 – Prüfen (Pflicht)
1. Den geschriebenen JSON-Block noch einmal Zeile für Zeile gegen die obigen Regeln lesen.
2. Die Prüfung nach `.claude/gemeinsam/regeln/abschluss.md` durchführen (die Datei muss weiterhin mit `</html>` enden, kein roter Fehlerkasten).
3. Prüfen, dass jede `"answer"`-Zahl auf die richtige Option zeigt.
4. Prüfen, dass `<meta name="loesung-hash">` genau den Wert aus `solution-password.txt` enthält.
Alles Falsche korrigieren und erneut prüfen.

## Schritt 4 – Abschluss
- "Doppelklick auf `Unterricht/.../index.html` zum Öffnen. Siehst du statt der App einen roten Kasten, kopiere seine Meldung zu mir. Mit 'Lehrkraft-Modus' und deinem Passwort siehst du alle Lösungen."
- Teilen: als SCORM-Paket mit dem Skill Baue-Lernpaket (dann kommen die Punkte in die ByCS), oder als **Datei**-Ressource in die ByCS Lernplattform bzw. aufs Schullaufwerk (dann ohne Punkte).
- Anbieten: "Soll ich weitere Fragen oder eine andere Art ergänzen?"
