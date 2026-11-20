# Ablage und Namen

Gilt für alles in `Unterricht/`, `BYCS-SYNC/` (Teamordner), `ToDo/` und `Ressourcen/`. Die Regel steht als Code in
`.claude/gemeinsam/scripts/unterrichtsmaterial.py`, `kette-pruefen.py` prüft sie bei jedem Commit.

## Ordnerschema
`Unterricht/<Klasse>/<Fach>/<Abschnitt>/<Thema>/index.html`, z. B. `Unterricht/MGF10/LF1/BW2/Toleranzen-1-Pruefen-Messen-Lehren/`.

| Ebene | Regel | Beispiele |
|---|---|---|
| Klasse | Klassenkürzel in Großbuchstaben oder Sammelname | `MGF10`, `BFS11`, `ALLE10`, `ALLE11`, `ALLE` |
| Fach | Kürzel aus `.claude/gemeinsam/data/faecher.txt`. Der volle Name steht nur im Schriftfeld und im Handbuch. | `LF1`, `Eth`, `PuG` |
| Abschnitt | `BW<n>` Blockwoche, `LS<n>` Lernsituation, `M-<Name>` Modul, `R-<Name>` Themenreihe | `BW2`, `LS3`, `M-3D-Druck` |
| Thema | sprechend, nie gekürzt, nie mit `_` | `Toleranzen-1-Pruefen-Messen-Lehren` |

- **Blockwoche immer `BW<n>`** (nie `B1`), in Ordnernamen, Dateinamen und Paketen. Lernsituationen `LS<n>`.
- `_` trennt im Paketnamen die vier Felder, innerhalb eines Feldes kommt es nie vor.
- **Namen nie abtippen:** Paketname, Titel und Steckbrief der Seite (`<meta name="klasse|fach|abschnitt|thema">`)
  entstehen aus dem Ablageort und aus `<title>`. `python .claude/gemeinsam/scripts/unterrichtsmaterial.py "<Ordner>"`
  (am Mac `python3`) zeigt sie und sagt, ob der Ort zur Regel passt.
- Bleibt eine Angabe offen: unter `Unterricht/Offen/<Thema>/` speichern und die offene Angabe als Erstes im Bericht nennen.

## Art des Unterrichtsmaterials im Ordnernamen
| Unterrichtsmaterial | Ordner | Skill |
|---|---|---|
| E-Learning | `<Thema>/` | Baue-E-Learning |
| Arbeitsblatt | `<Thema>-Arbeitsblatt/` | Baue-Arbeitsblatt |
| Übungs-App | `<Thema>-Uebung/` | Uebungs-App |
| Testvorbereitung | `<Thema>-Testvorbereitung/` | Baue-Testvorbereitung |
| Test | `Test-<Thema>/` mit `Fragen-<Thema>.xml`, `Test-<Thema>.mbz`, `index.html` (Anleitung), `Vorschau.html` | ByCS-Fragenersteller, ByCS-Test |
| Unterrichtsplan | `<Thema>-Unterrichtsplan/` (mit `.ics`) | Einheit-planen |
| Feedback | `<JJJJ-MM-TT>-<Aufgabe>-Feedback/` (bleibt lokal, `.gitignore`) | Raster-Feedback |
| Kursplan | eine Datei, kein Ordner: `Unterricht/<Klasse>/<Fach>/Kurs-<Klasse>-<Fach>.json` (Kurs zu einem Fach) oder `Unterricht/<Klasse>/Kurs-<Klasse>.json` (mehrere Fächer). Mehrere Kurse am selben Ort: Zusatz anhängen (`Kurs-ALLE-BerHan-3D-Druck.json`). Nie eine Jahreszahl im Dateinamen: Das Schuljahr steht im Plan (`vollname` "… SJ 2026/2027", `kurzname` "… 26/27") | Baue-Kurs |

**Keine Quizze mehr, immer Tests:** Wünscht die Lehrkraft Fragen für die ByCS (auch "Quiz"), entsteht ein Test
"Ohne Niveaus". Kein `-Quiz`-Ordner, kein Lernpfad mit Niveaus. In der ByCS heißt der Test "Test - <Thema>".

## Gebautes: `BYCS-SYNC/` im Teamordner (nur über GitHub, nie im Projektordner, nie in `Unterricht/`)
- Lernpaket: `BYCS-SYNC/Pakete/<Klasse>/<Fach>/<Klasse>_<Fach>_<Abschnitt>_<Thema>_scorm.zip`.
- Kurssicherung: `BYCS-SYNC/Kurse/<Klasse>[/<Fach>]/<Name des Kursplans>.mbz` (z. B. `Kurse/ALLE10/PuG/Kurs-ALLE10-PuG.mbz`),
  ohne Datum, im selben Unterordner wie der Kursplan unter `Unterricht/`.
- Tests bleiben in `Unterricht/…/Test-<Thema>/` (in Git).
- `tmp/` im Projektordner ist der lokale Arbeitsordner für alle (Entwürfe, Zwischenstände, Auszüge). Er ist in Git
  ausgenommen (nur `tmp/.gitkeep` liegt drin, damit der Ordner überall da ist), nichts darin wird committet oder
  zugestellt. Bleibendes gehört nach `Ressourcen/` oder `ToDo/`.
- Lokal Gebautes landet im Temp-Ordner und ist nur zum Ansehen: Nach dem Push baut GitHub und stellt in den Teamordner zu.
  Im Projektordner gibt es kein `BYCS-SYNC/`. Einzelheiten,
  Download-Links und was der Flow annimmt: `zustellung.md`.
- **Paketnamen ändern:** nur die Groß-/Kleinschreibung ohne Rückfrage (die Datei im Teamordner wird an Ort
  und Stelle ersetzt, der Link bleibt). Jede andere Änderung am Namen oder am Ort (andere Klasse, anderes Fach)
  legt im Teamordner eine neue Datei mit neuem Link an: vorher fragen.
- **Themenordner umbenennen:** erst bauen und committen, dann umbenennen. Sonst findet `version.py` den Commit
  zu "Commit folgt" nicht und zählt die Version nicht hoch.

## Schreibweise von Ordner- und Dateinamen
Auch für E-Learnings, SCORM-Pakete und das PDF aus "Als PDF speichern".
- Das erste Wort beginnt immer groß, auch wenn es kein Nomen ist: `Ethische-Brille`, `Alle`, `Offen`.
- Danach gilt die deutsche Rechtschreibung: Nomen und Nominalisierungen groß, Verben, Adjektive, Artikel und
  Bindewörter klein (`Kugelsortiervorrichtung-2-Stueckliste-Zeichnungen-lesen`, `Unser-Leitbild-kennen-und-leben`).
  Abkürzungen wie üblich (`ISO`, `B2`, `BW1`). Gibt es einen Seitentitel, dessen Schreibweise übernehmen.
- Umlaute als ae/oe/ue/ss, Wörter mit `-` verbunden.
- Technische Namen bleiben, wie sie sind: `index.html`, die Endung `_scorm.zip`, `imsmanifest.xml`, `scorm-api.js`,
  Skripte und alles in `.claude/` und `.github/`, dazu übernommene Dateien aus fremden Paketen in `Ressourcen/`
  (Schriftpaket, NILS-Dateinamen).
- Vor dem Speichern prüfen. Ist ein vorhandener Name falsch geschrieben, ihn korrigieren und die Verweise darauf
  (CLAUDE.md, Regeln, Skills, `ToDo/NOTIZEN.md`) anpassen.
- Unter Windows über einen Zwischennamen umbenennen (`git mv name name.__tmp__`, dann `git mv name.__tmp__ Name`),
  sonst erkennt Git die Änderung nicht.

## Ressourcen
`Ressourcen/` (ganz oben im Repo) sammelt Quellen und Bausteine zum Wiederverwenden: Schriften, Tabellenbuch,
Normen, Logos, Zeichnungssätze, 3D-Modelle, Bilder. Wegweiser ist `Ressourcen/Inhalt.md`.
- Was später noch gebraucht werden könnte (Quell-PDFs, Zeichnungen, 3D-Modelle, Logos, Kursbanner, Standbilder und
  gereinigte Grafiken aus dem Bau von E-Learnings), ohne Rückfrage dort ablegen, nach Art und Thema geordnet
  (`Bilder/<Thema>/`), und in `Inhalt.md` eintragen.
- Nie dorthin: Schülerdaten und Schülerarbeiten, fertige Seiten (`Unterricht/`), SCORM-Pakete (`BYCS-SYNC/`).
- Tabellenbuchseiten sind nur zum Nachschlagen: nie in Seiten kopieren, Seitenzahlen in Seiten offen lassen.
- Fachunterricht Technisches Zeichnen: `Ressourcen/NILS/Festlegungen.md` hat Vorrang vor den NILS-Skripten
  (Quelle: GitHub `Ho-Koh/nils-skripte`, lokal `C:\git\NILS-Skripte`, vorher `git pull`).

## Dateiformate
- Unterrichtsmaterial ist immer eine `.html`-Seite (Regeln: `seite.md`).
- Zum Importieren, nicht zum Lesen: Fragen `.xml`, Kalender `.ics`, SCORM-Pakete `.zip`, Kurssicherungen und
  Test-Aktivitäten `.mbz`.
- Interne Arbeitsdateien (Notizen, Festlegungen, Wegweiser, Rückmeldungen, Regeln) sind `.md`, nie `.txt`
  (z. B. `ToDo/NOTIZEN.md`, `Ressourcen/Inhalt.md`). `README.md` ist nur der Wegweiser zum Handbuch (für GitHub).
- Technische Datendateien, die Skripte lesen, bleiben, wie sie sind (`faecher.txt`, `berufe.txt`, `neuigkeiten.txt`).
