# Abschluss: prüfen, öffnen, berichten, Paket, Commit

Die Reihenfolge gilt für jede Seite, egal aus welchem Skill: erst prüfen, dann der Lehrkraft zeigen, dann committen
(bei Lernpaketen erst nach ihrem Ja). So kommt nichts Ungeprüftes zu den Schülerinnen und Schülern.

## 1. Prüfen (vor "Seite ist fertig", immer)
`python .claude/gemeinsam/scripts/seite-pruefen.py <Seite> --arbeitsordner <Scratchpad>/pruefen` (am Mac `python3`)
erledigt die Punkte 1 bis 6 in einem Lauf und legt Screenshot, Leerdruck und PDF-Export als Datei ab: ansehen.

1. **Nicht abgeschnitten:** Die Datei endet mit `</html>`. Wenn nicht: neu schreiben (wenn nötig kürzer).
2. **Richtiger Anfang:** Die erste Zeile ist `<!doctype html>`.
3. **Tags geschlossen:** `<section`, `<div`, `<table`, `<ol`, `<ul` kommen so oft vor wie ihr schließendes Tag.
4. **Nichts übrig geblieben:** keine Platzhalter (`[Titel]`, `[Untertitel]`, `[Beruf]`, `[Thema]`, `TODO`), kein
   TEMPLATE-Kommentar, keine Markdown-Zeichen (`**`, `##`) im Text.
5. **Funktioniert offline:** kein `http://` oder `https://` in `src=` oder `<link`.
6. **Keine Skriptfehler:** Die Seite öffnet im Headless-Browser ohne roten Fehlerkasten. Das Skript der Vorlage ist
   unverändert.

- Seiten ohne die Vorlagen (Übungs-App, Handbuch): die Punkte von Hand prüfen (letzte 10 Zeilen lesen, Grep im
  Zählmodus) und einmal im Headless-Browser öffnen.
- Besteht eine Prüfung nicht: korrigieren und wiederholen. Dann in einer kurzen Zeile sagen, welche Prüfungen
  bestanden sind.
- **Mehrere Seiten auf einmal** (Vorlage geändert, Skript in mehrere Kapitel eingearbeitet): je Seite einen Agenten
  `seiten-pruefer` parallel starten. Er prüft und berichtet nur, behoben wird danach.
- Meldet die Lehrkraft eine leere Seite oder einen roten Fehlerkasten: um die kopierte rote Meldung bitten, die
  Ursache beheben, erneut prüfen.

## 2. Zur Kontrolle öffnen (nach inhaltlichen Änderungen)
- Wurde ein E-Learning inhaltlich geändert (Texte, Aufgaben, Lösungen, Bilder, interaktive Module), die Seite nach
  bestandener Prüfung im integrierten Browser von VS Code öffnen: `code -r "Unterricht/<…>/index.html"`
  (`.vscode/settings.json` ordnet `.html` dem integrierten Browser zu; den Quelltext öffnet Rechtsklick → "Öffnen
  mit…" → "Text-Editor").
- Sind mehrere E-Learnings betroffen, vorher per AskUserQuestion fragen: **Alle öffnen**, **Eine exemplarisch** oder
  **Keine öffnen**. Bei "Eine exemplarisch" eine typische Seite wählen und sagen, welche.

## 3. Berichten
Standardsatz (ein Skill kann einen eigenen, kürzeren vorgeben): "Doppelklick auf `Unterricht/<…>/index.html` zum
Öffnen. Mit dem Button 'Als PDF speichern' lädst du ein PDF herunter. Im Lehrkraft-Modus druckt 'Leeres
Arbeitsblatt drucken' eine unausgefüllte Fassung für die Bearbeitung auf Papier (im Druckdialog auch als PDF
speicherbar)." Dazu offene Punkte und gemachte Annahmen nennen.

## 4. Paket, Prüfung vor dem Commit, Commit
- Ein Lernpaket baut der Skill Baue-Lernpaket (`build-scorm.py --source <Themenordner> --aenderung "…"`). Der Text
  bei `--aenderung` erscheint im Handbuch: verständlich fürs Kollegium formulieren.
- Vor jedem Commit: `git pull --rebase`, dann `python .claude/gemeinsam/scripts/pruefen.py --erneuern` (am Mac
  `python3`). Es prüft Ablage, Steckbrief, Version, Kursplan, Test-XML, Handbuch und Mitdokumentieren und erneuert
  Handbuch und Test-Vorschau. Fehler beheben, erneuerte Dateien mit committen. Rein interne Änderung ohne Bedeutung fürs
  Kollegium: `--intern` und "[intern]" in der Commit-Nachricht.
- Die letzte Zeile von `pruefen.py` entscheidet:
  - **"Lernpaket betroffen: ja"**: fragen: "Committen und pushen? Nach dem Push ist die Änderung sofort bei den
    Schülerinnen und Schülern (über den Download-Link im Kurs)." Erst nach dem Ja committen und pushen.
  - **"nein"**: selbst committen und pushen, danach in einem Satz sagen, was gepusht ist.
- Nach dem Push prüft GitHub dasselbe noch einmal, baut Lernpakete und Kurse und stellt alles in den Teamordner zu
  (etwa eine Minute, Workflow "Bauen und zustellen", `einrichtung.md`). Lernpakete und Kurssicherungen werden nie
  committet. Der Lehrkraft sagen: Schlägt der Lauf fehl, kommt eine Mail von GitHub, und es wird nichts zugestellt.
  Kontrolle bei Bedarf: `python .claude/gemeinsam/scripts/kette-pruefen.py --zugestellt`.
- **GitHub weist den Push ab** („GH013: Repository rule violations“, „File path is restricted“, darunter die
  gesperrten Dateien): Der Push enthält Werkzeug oder Unterricht eines Teams, in dem die Lehrkraft nicht ist. Der
  ganze Push ist abgewiesen, auch das Erlaubte darin. Nie erzwingen, nie einen anderen Branch oder Weg suchen, keine
  Rulesets ändern. Anhalten, `git log origin/main..HEAD --stat` zeigen, die gesperrten Dateien nennen und fragen,
  wie es weitergeht (meist: die gesperrte Änderung aus den Commits nehmen und den Wunsch an das zuständige Team
  bzw. die Werkzeug-Verantwortlichen weitergeben). Hintergrund: `einrichtung.md`, „Werkzeugschutz und
  Abteilungsschutz“.
- Bei einer neuen Hauptversion (z. B. V2.0) dazusagen: "Achtung, Hauptversion: Laufende Versuche können
  durcheinanderkommen, besser nicht mitten in einer Bearbeitungsphase."
- Änderungen an Skills, Vorlagen, Skripten, Workflow, Regeln oder `CLAUDE.md` brauchen im selben Commit eine Zeile in
  `.claude/handbuch/neuigkeiten.txt` (`handbuch.md`).
- Meldung "Teamordner … nicht gefunden": `einrichtung.md`.
