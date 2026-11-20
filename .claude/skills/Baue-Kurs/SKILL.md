---
name: Baue-Kurs
description: Baut aus fertigen Unterrichtsmaterialien (Ordner mit Blockwochen, PDFs, E-Learning-HTML, SCORM-Pakete aus dem Skill Baue-Lernpaket) eine Moodle-Kurssicherung (.mbz) für die ByCS Lernplattform (BayernCloud Schule, Moodle). Abschnitte je Blockwoche, Dateien und SCORM-Pakete als Aktivitäten, gestaltete Abschnittstexte, Abschluss und Voraussetzungen, Aufbau wie die Beispielsicherung "MGF10 Eth 26/27". Die Lehrkraft stellt den Kurs danach in ByCS per Wiederherstellung her. Use when the teacher says "Erstelle einen Kurs", "Kurs für die ByCS", "mbz", "Moodle-Sicherung", "Kurs wiederherstellen", "SCORM-Pakete in einen Kurs" or wants material placed in a course.
---

# Moodle-Kurs (.mbz) aus Unterrichtsmaterial bauen

Du machst aus einem Ordner mit Unterrichtsmaterial eine Kurssicherung (`.mbz`), die die Lehrkraft in der ByCS Lernplattform als Kurs wiederherstellt. Blockwochen werden Abschnitte, Dateien, SCORM-Pakete und Tests werden Aktivitäten. Vorbild für Stil und Einstellungen sind die ByCS-Kurse "MGF10 Eth 26/27" und "Modul 3D-Druck BVJ/BIK" (Werte in `VORLAGE` im Skript).

**Du schreibst das Moodle-Format nicht selbst.** `.claude/skills/Baue-Kurs/scripts/build-mbz.py` baut die Sicherung und prüft sie (nur Standardbibliothek). Die `.mbz` ist zum Hochladen gedacht, darum keine Webseite.

Nebendateien in diesem Ordner, **nur bei Bedarf lesen**:
- `kursplan.md`: Layout aus dem Ordnerbaum, Download-Links, Gestaltung der Abschnittstexte, Felder im Kursplan. Lesen, wenn ein Kursplan neu entsteht oder geändert wird.
- `umfang.md`: was die Sicherung enthält und nicht enthält (Kurseinstellungen, Notenskala), Grenzen, Hilfe bei gescheiterter Wiederherstellung.
- `templates/kursplan-beispiel.json`: Vorlage für den Plan.

## Schritt 1 – Angaben klären (nur was fehlt)
Gibt es den Kursplan schon (`Unterricht/<Klasse>/<Fach>/Kurs-….json` oder `Unterricht/<Klasse>/Kurs-….json`), nichts fragen und bei Schritt 3 weitermachen. Sonst:
1. **Inhalt** (Pflicht): welcher Ordner bzw. welche Dateien. Frage nach, rate nicht. Typisch: `Unterricht/<Klasse>/<Fach>/` mit den Ordnern der Abschnitte (`.claude/gemeinsam/regeln/ablage.md`).
2. **Vollname** und **Kurzname** für die ByCS, immer mit Schuljahr: Vollname "… SJ 20XX/20XX", Kurzname "… XX/XX" (z. B. "MGF10 Ethik SJ 2026/2027" und "MGF10 Eth 26/27"). Der Kurzname muss in ByCS noch frei sein.
3. **Startdatum** (JJJJ-MM-TT).
4. **Banner:** immer mit dem Skill **ByCS-Kursbanner**. Titel, Stufe und Untertitel aus dem Kurs ableiten, nur fragen, was sich nicht ableiten lässt. PNG nach `Ressourcen/Bilder/<Thema>/<Titel>-Banner-ByCS.png`, in `Ressourcen/Inhalt.md` eintragen. Ein anderes Bild nur auf ausdrücklichen Wunsch.

## Schritt 2 – Kursplan schreiben
Erst `kursplan.md` lesen. Dann:
- Plan als eine Datei ablegen, Name nach dem Ort (`.claude/gemeinsam/regeln/ablage.md`): Kurs zu einem Fach `Unterricht/<Klasse>/<Fach>/Kurs-<Klasse>-<Fach>.json`, über mehrere Fächer `Unterricht/<Klasse>/Kurs-<Klasse>.json`, bei mehreren Kursen am selben Ort mit Zusatz (`Kurs-ALLE-BerHan-3D-Druck.json`). Keine Jahreszahl im Dateinamen (das Schuljahr steht nur in Vollname und Kurzname). `pruefen.py` meldet einen falschen Namen. Der Plan ist die Quelle des Kurses und wird committet. Pfade immer ab dem Projektordner, keine Laufwerkspfade.
- Lernpakete immer mit `"link": "linkseite"`. Nie einen Link abtippen oder in den Plan schreiben. Vorher prüfen, ob jedes Paket einen Link hat: `python .claude/gemeinsam/scripts/linkseite.py`.
- **Nie sichtbar übernehmen:** Musterlösungen, Lösungsdateien, Bewertungsraster, Unterrichtspläne (`"versteckt": true`). **Nie übernehmen:** Ordner `…-Feedback/`, aus Test-Ordnern alles außer der `Test-<Thema>.mbz` (die Vorschau enthält alle Lösungen), `.xml`, `.ics`.
- Dateinamen und Inhalte auf Personenbezug prüfen. Gefundenes melden, nicht übernehmen.
- **Kein Kennwort im Kurs:** Ein Test behält den Platzhalter `Bitte_neu_vergeben` aus seiner Test-`.mbz`. Das echte Kennwort vergibt die Lehrkraft nach dem Wiederherstellen in der ByCS; das im Bericht sagen. Ein Feld `passwort` im Kursplan lehnt das Skript ab.
- Die Gliederung als kurze Liste zeigen (Abschnitt → Aktivitäten). Ist der Auftrag eindeutig („bau den Kurs“), direkt bauen und die Gliederung im Bericht zeigen; sonst erst nach der Zustimmung bauen.

## Schritt 3 – Bauen und Prüfen (Pflicht)
Im Projektordner (am Mac `python3`):
```
python .claude/skills/Baue-Kurs/scripts/build-mbz.py --plan "<Kursname>"
```
- `--plan` nimmt den Namen des Kursplans (z. B. `Kurs-ALLE10-PuG`) oder seinen Pfad. Ergebnis: `<gleicher Name>.mbz` ohne Datum im Temp-Ordner (Pfad gibt das Skript aus), nur zum Ansehen und Prüfen, **nie im Repo**, nie in `Unterricht/`, nie von Hand in den Teamordner (`--out` nur für Probeläufe). Jedes im Plan genannte Lernpaket baut das Skript vorher frisch aus seinem Themenordner.
- Das Skript prüft die Sicherung selbst (Archiv, XML, Verweise, Dateiinhalte, Abschnitte, Voraussetzungen, SCORM, Tests). Exitcode 0 = bestanden. Bei Fehlern Ursache beheben und neu bauen, nie ungeprüft ausliefern.
- Zusätzlich selbst prüfen: Abschnitte = Abschnitts-Ordner + 1 (Abschnitt 0), Aktivitäten = Einträge im Plan, Titel und Reihenfolge wie besprochen. Bei neuem oder umgestaltetem Kurs eine Vorschau der Kursseite aus den Abschnittstexten bauen und als Screenshot ansehen.
- In einer Zeile sagen, welche Prüfungen bestanden sind.

## Schritt 4 – Abschluss
- Pfad der lokal gebauten `.mbz` nennen. Den Kursplan nach `.claude/gemeinsam/regeln/abschluss.md` prüfen und selbst committen und pushen (ein Kurs erreicht die Schülerinnen und Schüler erst nach der Wiederherstellung; sind auch Lernpakete geändert, doch fragen). Etwa eine Minute nach dem Push baut GitHub den Kurs neu und stellt ihn im Teamordner unter `BYCS-SYNC/Kurse/<Klasse>[/<Fach>]/` zu (ersetzt die Sicherung gleichen Namens).
- In ByCS: die Datei direkt aus dem Teamordner hochladen (Kurse haben keinen Download-Link) und **als neuen Kurs** wiederherstellen.
- **Zuerst in einem Testkurs ausprobieren:** mit einem Testzugang jedes SCORM-Paket einmal öffnen, abgeben und unter „Berichte“ prüfen. Mit Test: als Lehrkraft die Vorschau starten (Safe Exam Browser, Fragen, Punkte), Kennwort und Zeitraum (Testöffnung) setzen.
- Danach die Lehrkraft selbst: Einschreibung und Kurspasswort, Sichtbarkeit und Startdatum, Datumsbedingungen, Aufgaben mit Abgabe. Diese baut der Skill nicht.

## Grenzen (offen sagen)
Lernpakete über Link und Tests sind in der ByCS erprobt (Ethikkurs, Modul 3D-Druck), mitgelieferte ZIPs ohne Link nicht. Die ByCS kann einzelne Inline-Stile entfernen. Schlägt die Wiederherstellung fehl: Fehlermeldung Wort für Wort anfordern, dann `umfang.md`.

## Datenschutz
- Keine Namen, Noten oder Abgaben von Lernenden. Das Skript übernimmt keine Benutzerdaten.
- Nichts auf externe Dienste hochladen. Die Wiederherstellung in ByCS macht die Lehrkraft selbst (Ausnahmen: CLAUDE.md, Datenschutz).
