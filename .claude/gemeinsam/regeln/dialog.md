# Auswahldialog: Angaben klären (nur was fehlt)

Ein Ablauf für alle Skills. Jeder Skill fragt nur, was er braucht:

| Skill | Vorlage | Klasse · Fach · Abschnitt | Beruf, Hilfsmittel | Niveaus |
|---|---|---|---|---|
| Baue-E-Learning | ja | ja | ja | nach dem Einlesen (Fall B unten) |
| Baue-Arbeitsblatt, Uebungs-App | nein | ja | ja | im ersten Dialog (Fall A) |
| Baue-Testvorbereitung | nein | ja | ja | im ersten Dialog, "Ohne Niveaus" empfohlen |
| Einheit-planen | nein | ja | nein (Kurzkopf) | im ersten Dialog (Fall A) |
| Raster-Feedback | nein | ja | nein (Kurzkopf) | nein |
| ByCS-Fragenersteller, ByCS-Test | nein | ja | nein | nein, immer "Ohne Niveaus" |

Bei allgemeinbildenden Fächern entfallen Beruf und Hilfsmittel in jedem Skill.

## Ablauf
**Dateien:** Fehlen die Pfade zu Aufgaben-PDF und Musterlösungs-PDF (oder zur HTML-Datei), frage im Chat danach. Sonst sofort weiter.

**Auswahldialog:** Vorlage, Klasse, Beruf, Fach und Abschnitt fragst du mit dem Werkzeug **AskUserQuestion** ab (EIN Aufruf, Auswahl per Klick, unter "Other" kann die Lehrkraft frei eintippen). Was die Lehrkraft in ihrer Nachricht schon genannt hat, wird nicht gefragt. Nie raten. Ein Aufruf hat höchstens vier Fragen: Wären es fünf, kommt "Hilfsmittel" in den zweiten Dialog (zusammen mit der Niveau-Bestätigung, siehe unten).

**Nur allgemeinbildende Fächer:** Bei Ethik, Politik und Gesellschaft, Deutsch, Englisch, Religion und Sport gibt es im Kopf keine Felder Beruf, Ausbildungsjahr, Lernfeld · Blockwoche und Hilfsmittel. Dann Beruf und Hilfsmittel nicht fragen (Klasse, Fach und Abschnitt schon, für den Ablageort `Unterricht/<Klasse>/<Fach>/<Abschnitt>/`, z. B. `Unterricht/ALLE10/Eth/BW1/`). Im Kopf `<div class="tb kurz">` setzen und diese vier Zellen löschen, es bleiben Benennung und Name (bei `Allgemeinbildung.html` mit Logo und Zeile über dem Titel). Alle anderen Fächer behalten die Felder.

**Nach dem Dialog:** Steht das Fach fest, in `faecher.md` nachsehen, ob es eine Fachregel gibt. Steht die Klasse fest, gilt `sprache.md` (Pflicht in BVJ und BIK, sonst Richtschnur).

Vor dem Dialog lesen:
- `.claude/gemeinsam/data/berufe.txt` (Berufe, zuletzt verwendeter oben)
- die Ausgabe von `python .claude/gemeinsam/scripts/unterrichtsmaterial.py --liste` (am Mac `python3`): Fächer mit Kürzel aus `.claude/gemeinsam/data/faecher.txt` (zuletzt verwendetes oben), bekannte Klassen und die vorhandenen Abschnitte je Klasse und Fach.


Fragen im Dialog:
1. **Vorlage** (Header "Vorlage"): nur Baue-E-Learning und nur, wenn die Lehrkraft sie nicht genannt hat ("Lernschritte", "wie das Ethik-E-Learning", "Schriftfeld", "wie immer" = Schriftfeld). Optionen, Skizzen und Empfehlung: `dialog-vorlage.md`.
2. **Klasse** (Header "Klasse"): das Klassenkürzel in Großbuchstaben (`MGF10`, `BFS10`, `BFS11`) oder ein Sammelname für Unterrichtsmaterial, das mehrere Klassen nutzen (`ALLE10` = alle 10. Klassen, `ALLE11`, `ALLE` = alle Jahrgänge, z. B. Schulleitbild). Optionen: die bekannten Klassen aus `--liste`, die zum Material passen, dazu der passende Sammelname, höchstens vier; alles andere tippt die Lehrkraft unter "Other" ein. Das **Ausbildungsjahr wird nicht gefragt**, es folgt aus den Ziffern am Ende der Klasse: Ausbildungsjahr = Jahrgang − 9 (`MGF10` = "1. Jahr", `BFS11` = "2. Jahr", 12 = "3. Jahr", 13 = "4. Jahr", ohne Ziffern = "alle Jahrgänge"). Nennt das Material eine Klasse, steht diese Option als erste mit "(empfohlen)".
3. **Beruf** (Header "Beruf"): die ersten vier Einträge aus `berufe.txt`, der oberste mit "(zuletzt verwendet)".
4. **Fach · Abschnitt** (Header "Fach"): je Fach aus `faecher.txt` (zuletzt verwendete zuerst, nur die zur Klasse passenden) der **nächste freie Abschnitt** (höchste vorhandene `BW<n>` + 1) und der **letzte vorhandene Abschnitt** (für weitere Kapitel in derselben Woche), insgesamt höchstens vier Optionen. Label z. B. `LF1 Fertigen von Bauelementen mit handgeführten Werkzeugen · Blockwoche 3`, Beschreibung z. B. `MGF10, neue Blockwoche (BW1 und BW2 vorhanden)`. Die erste Option bekommt "(empfohlen)". Unter "Other" tippt die Lehrkraft `Fach · Abschnitt` ein. **Vier Arten von Abschnitt:** `BW<n>` Blockwoche (Blockunterricht), `LS<n>` Lernsituation (Tagesunterricht), `M-<Name>` Modul (z. B. `M-3D-Druck`), `R-<Name>` Themenreihe über mehrere Wochen (z. B. `R-Toleranzen`). Sagt das Material nicht, welche Art es ist, und gibt es für Klasse und Fach noch keinen Abschnitt, frag danach.
5. **Hilfsmittel** (Header "Hilfsmittel"), nur wenn das Material keine nennt: Optionen `Tabellenbuch Metall`, `Tabellenbuch Metall, Taschenrechner`, `Keine`.

Nach der Antwort:
- **Vorlage** für Schritt 4 und 5 merken und im Bericht nennen.
- **Listen fortschreiben:** Den gewählten oder neu eingetippten Beruf in `berufe.txt` ganz oben eintragen (steht er weiter unten, dort entfernen). Ebenso das Fach in `faecher.txt` (`Kürzel | voller Name | Klassen`): ein gewähltes wandert nach oben, ein neues bekommt ein Kürzel (Lernfelder `LF<Nummer>` mit der Klasse dahinter, weil dieselbe Nummer in jedem Beruf etwas anderes bedeutet; Fächer ein kurzes Kürzel wie `Eth`, `PuG`, `D`, `E`, nur Buchstaben und Ziffern). Das Kürzel für ein neues Fach nennst du der Lehrkraft im Bericht.
- **Schriftfeld:** Beruf wie gewählt; Ausbildungsjahr aus der Klasse (z. B. "1. Jahr"); Zelle "Lernfeld · Blockwoche" mit dem vollen Namen des Fachs, nie dem Kürzel: `<voller Name> · Blockwoche <n>` (bei `LS<n>`: `· Lernsituation <n>`, bei `M-`/`R-`: `· <Name>`).
- **Ablageort:** `Unterricht/<Klasse>/<Fach>/<Abschnitt>/<Thema>/index.html` (`<Fach>` ist das Kürzel, `<Thema>` sprechend aus dem Titel). Regeln, Art des Unterrichtsmaterials im Ordnernamen und Schreibweise: `ablage.md`. Ob der Ort passt, zeigt `python .claude/gemeinsam/scripts/unterrichtsmaterial.py "<Ordner>"`. Namen von Ordnern und Paketen nie von Hand zusammensetzen.
- Bricht die Lehrkraft den Dialog ab oder bleibt eine Angabe offen: alles andere fertig bauen, in der Zelle "offen" eintragen, unter `Unterricht/Offen/<Thema>/` speichern und die offenen Angaben als Erstes im Bericht nennen.

**Titel/Untertitel** übernimmst du aus dem Material (nur wenn keiner erkennbar ist, im Chat fragen).

## Niveaus (ein Ablauf für alle Skills)
Immer mit AskUserQuestion fragen (Header "Niveaus"), bei neuem Unterrichtsmaterial und beim Umbau, außer die Lehrkraft hat es schon gesagt. Unterrichtsmaterial ohne Niveaus ist in jedem Fach erlaubt, aber nie von selbst. Die empfohlene Option steht oben und trägt "(empfohlen)".

- **Fall A, neues Unterrichtsmaterial ohne Vorlage der Lehrkraft** (Arbeitsblatt, Übungs-App, Unterrichtsplan, Testvorbereitung): im ersten Auswahldialog, Optionen "Drei Niveaus" und "Ohne Niveaus".
- **Fall B, Material der Lehrkraft wird umgebaut** (E-Learning aus PDF oder HTML): nach dem Einlesen. Sind die Aufgaben noch nicht eingeteilt, schlage selbst eine Einteilung vor (leichte Wiedergabe = Einsteigerniveau blau, Anwenden = Prüfungsniveau rot, Transfer/Knobeln = Profiniveau schwarz) und zeige sie als Vorschau. Optionen: "Drei Niveaus, so übernehmen", "Drei Niveaus, ändern", "Ohne Niveaus".
- **Empfehlung:** "Drei Niveaus". Ausnahmen: Ethik, wenn das Material keine Niveaus vorgibt (dann "Ohne Niveaus" oben, keine Einteilung vorschlagen, in Fall B ohne die Option "ändern"), und die Testvorbereitung ("Ohne Niveaus": wie der Test, eine Prüfungssimulation für alle).
- **Nie fragen:** Fragen und Tests für die ByCS sind immer "Ohne Niveaus".
- Bei "Ohne Niveaus" stehen die Aufgaben direkt im Kapitel (`section.ch`) bzw. in der Phase, ohne `level`-Blöcke.
- Gewichtung in bewerteten Paketen und Bestehensgrenze: `CLAUDE.md`.

## Sprachhilfen (ein Ablauf für alle Skills)
Bei neuem Unterrichtsmaterial und beim Umbau mit AskUserQuestion fragen (Header "Sprachhilfen", Mehrfachauswahl),
zusammen mit der Frage nach den Niveaus, außer die Lehrkraft hat es schon gesagt. Die Sprachhilfen sind nicht an die
Niveaus gebunden. Was sie sind und wie sie gebaut werden: `sprache.md`.

- **Optionen:** `Wortliste vor dem Text`, `Satzanfänge für Antworten`, `Glossar zum Nachschlagen`, `Keine`.
- **Empfehlung:** Klassenkürzel beginnt mit `BVJ` oder `BIK`: "Wortliste vor dem Text" und "Satzanfänge für
  Antworten" tragen "(empfohlen)" und stehen oben. Alle anderen Klassen: "Keine (empfohlen)" steht oben.
- **Wer fragt:** Baue-E-Learning (nach dem Einlesen, mit den Niveaus) und Baue-Arbeitsblatt (im ersten Dialog; wären
  es fünf Fragen, im zweiten Dialog). Baue-Testvorbereitung fragt nicht eigens: Die Sprachhilfen stehen im Plan
  (Vorschau) und lassen sich dort mit "Ändern" wählen.
- **Nie fragen:** Uebungs-App, Fragen und Tests für die ByCS, Dokumente nur für die Lehrkraft. Die Schreibregeln aus
  `sprache.md` gelten dort trotzdem für alles, was Schülerinnen und Schüler lesen.
