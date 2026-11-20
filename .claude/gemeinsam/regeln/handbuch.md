# Handbuch für Kolleg/innen und Mitdokumentieren

`#Handbuch.html` (ganz oben im Repo) ist die Startseite für das Kollegium. Der Einstieg fragt "Was willst du tun?"
und zeigt nur den gewählten Weg: Lernpaket nutzen, Fehler korrigieren oder selbst erstellen. GitHub stellt es nach jedem Push, der es ändert, in den Teamordner zu (ganz oben, neben den Ordnern). Es hat ein
eigenes Layout mit eigenem CSS und JavaScript in der Datei (nicht `Fachunterricht.html`), ist kein E-Learning und
wird nicht als Paket gebaut. Bausteine: Kommentar am Anfang der Datei.

## Mitdokumentieren ist Pflicht
- Wer Skills, Vorlagen, Skripte, Helfer, Regeln, Einstellungen, den Workflow oder `CLAUDE.md` ändert, trägt im selben
  Commit oben in `.claude/handbuch/neuigkeiten.txt` eine Zeile ein:
  `TT.MM.JJJJ | ein Satz ohne Technik, aus Sicht der Kolleg/innen`.
- Ändert sich die Bedienung, auch den passenden Abschnitt im Handbuch anpassen.
- `pruefen.py` (vor dem Commit) meldet einen Fehler, wenn das fehlt, und sagt, was zu tun ist. Nur bei rein internen
  Änderungen ohne Bedeutung fürs Kollegium: `pruefen.py --intern` und "[intern]" in der Commit-Nachricht. Auf GitHub
  ist es nur eine Warnung im Lauf (Commits von Claude, erkennbar an "Co-Authored-By: Claude").
- Neue Skills in `.claude/handbuch/skills.txt` eintragen (`Skill | Wofür | Beispiel`).
- Neue Fragen von Kolleg/innen in `.claude/handbuch/fragen.txt` aufnehmen (`Frage | id des Abschnitts`) und den
  Abschnitt so ergänzen, dass er sie beantwortet.

## Automatisch, nie von Hand ändern
"Was ist neu" und die Zahl der Lernpakete (aus den Themenordnern in `Unterricht/`, deren `index.html` eine Version trägt), Skill-Liste (ohne Helfer), Häufige Fragen, Seitenleiste,
Kennzahlen und Stand. Das macht `python .claude/handbuch/handbuch.py` (auch über `pruefen.py --erneuern` vor dem Commit
und auf GitHub nach jedem Push, das dann selbst committet). Es prüft Fragen, Links und Pakete und liest die Seiten im
Arbeitsstand (in Git oder neu, nicht ignoriert).

## Stil: so wenig wie möglich
Geschrieben für Kolleg/innen ohne Technikkenntnis, nach Aufgaben gegliedert, kurze Schritte. Das Lehrkraft-Passwort
steht nie im Handbuch.
- **Sichtbar stehen nur Schritte** und das, was alle brauchen. Hintergründe, Sonderfälle und Formeln kommen in einen
  Kasten `<details class="mehr">` ("Zusatzinfos", Aufbau im Kommentar am Anfang der Datei).
- **Nicht ins Handbuch gehört, was Claude selbst weiß oder tut:** Ablageschema, Dateinamen, Agenten, Git-Abläufe,
  Aufbau von `.claude/`. Wer es braucht, fragt Claude.
- Jedes Kapitel trägt `data-weg` (`nutzen`, `korrigieren`, `erstellen` oder `immer`). Neues zuerst einem Weg zuordnen,
  kein neues Kapitel für alle anlegen.
- **Im Handbuch heißt es "die KI", nie "Claude"** (auch in `neuigkeiten.txt` und `fragen.txt`, `handbuch.py` prüft das).
  Einzige Ausnahme: der Name der Erweiterung „Claude Code“ im Schritt zur Einrichtung. Der Hinweis, dass ein
  bezahltes Abo (Pro, bei OpenAI Plus) unbedingt nötig ist, bleibt dort stehen, ebenso der Hinweis, dass das Projekt
  für ein anderes Werkzeug erst eingerichtet werden muss.
- **Keine Paketliste im Handbuch.** Die Kolleg/innen brauchen die Linkseite: Die Links mit `data-linkseite` führen
  direkt dorthin. Die Adresse enthält einen Schlüssel und steht nur im Handbuch (Entscheidung der Lehrkraft vom
  12.11.2026, das Repo ist privat), sonst nirgends im Repo, nie im Chat und nie in einer Ausgabe. Wird das Repo
  öffentlich, muss sie vorher raus.
- Das Kapitel "Warum wir so arbeiten" (eine Fassung für alle, keine parallelen Versionen) und der Kasten "Warum mit
  Link" unter "Paket per Link einbinden" bleiben sichtbar, nicht in einen Aufklappkasten verschieben.
- Die Häufigen Fragen stehen unsichtbar in der Seite und sind nur über die Suche zu finden. "Was ist neu" zeigt
  nur die neuesten Lernpaket-Änderungen, die Zeilen aus `neuigkeiten.txt` stehen eingeklappt darunter.

## Prüfen
`python .claude/handbuch/handbuch.test.py`, danach die HTML-Prüfung wie für jede Seite (`abschluss.md`).
