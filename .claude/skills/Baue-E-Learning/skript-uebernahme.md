# Baue-E-Learning – Skript übernehmen: neueren Quelltext in E-Learnings einarbeiten

Teil des Skills Baue-E-Learning (Ablauf in `SKILL.md`). Gilt, wenn ein fachlich neuerer Quelltext (z. B. ein NILS-Skript) in bestehende E-Learnings kommt oder daraus neue E-Learnings in der Aufteilung dieses Repos entstehen. Für viele Seiten auf einmal den Agenten **skript-abgleicher** nutzen, je Seite einen, parallel (`.claude/agents/skript-abgleicher.md`).

## Quellen
- **NILS-Skripte:** GitHub `Ho-Koh/nils-skripte`, lokal `C:\git\NILS-Skripte`. Vor der Arbeit `git -C C:\git\NILS-Skripte pull --ff-only`.
  - In `ausgabe/` liegen je Skript drei Dateien mit gleicher Nummer: `NILS_<TZn>_SuS_<VV-BBB>.html` (Schülerfassung), `NILS_<TZn>_Lös_<VV-BBB>.html` (Lehrkraft, mit Lösungen und Kapitel `#lk` „Hinweise für Lehrkräfte“) und `NILS_<TZn>_PDF_<VV-BBB>.pdf` (Druckfassung).
  - Immer die höchste Nummer nehmen und im Bericht nennen.
- **Vorrang:** `Ressourcen/NILS/Festlegungen.md` (Lehrkraft) geht vor `Ressourcen/Tabellenbuch/TAB_Referenz_01-002.md` (Entscheidungen A1–A6), und beide gehen vor dem NILS-Text. Widerspricht der NILS-Text einer Festlegung, gilt die Festlegung. Die Abweichung kommt in die Rückmeldung (unten).

## Zuordnung Kapitel → Seiten
Zuerst eine Tabelle *NILS-Kapitel (`section.ch#kN`, `data-t`) → Zielseite* aufstellen und der Lehrkraft zeigen, wenn sie noch nicht festgelegt ist. Die Abschnitte dieses Repos bleiben, z. B. Kugelsortiervorrichtung 1–6 aus TZ1 k1–k12.

| Zielseite | TZ1-Kapitel |
|---|---|
| Kugelsortiervorrichtung 1 – Aufbau, Funktion, Montage | k1 Die KSV, k3 Bewegungen, k4 Montage |
| Kugelsortiervorrichtung 2 – Stückliste, Zeichnungen lesen | k2 Stückliste (+ Fertigungszeichnungen aus der Lös) |
| Kugelsortiervorrichtung 3 – Blattformate, Schriftfeld, Maßstäbe, Linienarten | k5, k6, k7 |
| Kugelsortiervorrichtung 4 – Formelemente, Bemaßung, Oberflächen | k8, k9 |
| Kugelsortiervorrichtung 5 – Fertigungszeichnungen erstellen | k10 |
| Kugelsortiervorrichtung 6 – Zeichnungen prüfen, Abschlusstest | k11, k12 |

Neue Seiten aus einem Skript, zum Beispiel TZ2 oder TZ3:
- Nach Thema und Arbeitszeit teilen, höchstens so viele Pakete, wie die Lehrkraft vorgibt.
- Richtwert: 45–90 Minuten Bearbeitungszeit je Seite.
- Grundlage sind Aufgabenzahl, Zeichenaufträge und Test.

## Umbau
Die Seite wird frei neu aufgebaut. Der Speicherstand der Schülerinnen und Schüler muss nur erhalten bleiben, wenn die Lehrkraft es sagt. Vorhandene `data-k` ohne Auftrag nicht wiederverwenden.

| Im NILS-Skript | In der Seite |
|---|---|
| `section.ch#kN` mit `data-t`, `.chnum`, `h2`, `p.goal` | Abschnitt der Seite (`section.ch`, Titel „Abschnitt 1.1“ usw. wie bisher), Lernziel als `p.goal` |
| `div.task` mit `span.tt` „Aufgabe 8.3 …“ | `div.task`, Titel mit der Nummer dieser Seite (`Aufgabe 4.3 – …`), in den passenden Niveau-Block |
| `<select data-o="a\|b\|c" data-a="b">` | `<select data-k="…"><option value="">-</option><option>a</option><option data-ok>b</option><option>c</option></select>` (Optionen in der NILS-Reihenfolge) |
| `<input type="text" data-a="5,5" data-alt="…">` | `<input type="text" data-k="…" data-ok="5,5\|…">`, bei Zahlen mit `data-tol` |
| Quiz `buildQuiz(el, [{q,o,a,e}])` | je Frage Radio-Gruppe mit `data-ok`; die Erklärung `e` in `details.sol` |
| `.merke`, `.warn`, `.hint` | `.merke`, `.warn`, `p.hint`; digitale Hinweise („Tippe …“) mit `screen-only` |
| `details.sol` der SuS, Lösungen und Musterzeichnungen der Lös | `details.sol` in der Aufgabe (die Schülerinnen und Schüler sehen sie nach der Abgabe) |
| Nur in der Lös: Kapitel `#lk`, Fertigungszeichnungen mit Zoom, „nur Lehrkraftfassung“ | `section.answers` bzw. `.sol-only` |
| Freischaltung `gate.js` (Lösung erst nach Prüfen) | entfällt, die Vorlage sperrt über das Lehrkraft-Passwort und gibt nach der Abgabe frei |
| Eingebettete Bilder | über `.claude/gemeinsam/scripts/medien-einsetzen.py` (`--liste`, Platzhalter `nils-medium:<Nr>`, `--einsetzen`), nie base64 abtippen |
| Interaktive Module (3D, Zeichenschritte, Raster, Sortieren) | unverändert nach Schritt 4a (`module-grafiken.md`), dazu immer die Papierfassung aus `druckfassung.md` |
| Zeichnungen per JS (`draw.js`, `parts.js`) | als Modul übernehmen (4a) oder einmal als SVG erzeugen und einbetten, Text in NILS Normschrift |

Regeln:
- **Wortlaut:** Der Text bleibt wörtlich, außer eine Festlegung verlangt eine Änderung oder ein Fehler ist offensichtlich. Beides kommt in den Bericht. Teilaufgaben (a, b, c) bekommen je ein eigenes Feld.
- **Durchmesser** immer `⌀`.
- **Allgemeintoleranz** wie in `Ressourcen/Normen/Schriftfeld-Allgemeintoleranzen-ISO-22081.jpg`.
- **NILS-Schrift:** Die Seite bekommt `<meta name="schrift" content="nils">` vor `<title>`, danach `sync-vorlage.py --datei <Seite> --schreiben`.
- **Niveaus:** Die Aufgaben des Skripts auf Einsteiger-, Prüfungs- und Profiniveau verteilen, nach Schritt 1 Niveaus (Vorschau zeigen, außer die Lehrkraft hat schon entschieden).
- **Version:** Neuer Inhalt ist beim Paketbau eine Hauptversion. In der Frage zum Commit vor laufenden Bearbeitungen warnen.

## Bericht und Rückmeldung
- **Je Seite:**
  - übernommene, neue und entfallene Aufgaben
  - verknüpfte Lösungen
  - Aufgaben ohne Quelle für einen Lösungsvorschlag
  - gebaute Papierfassungen
  - Abweichungen vom NILS-Text mit Grund
  - offene Punkte
- **Rückmeldung an den Ersteller:** Alle Verbesserungen der ByCS-Fassung und alle Abweichungen kommen nach `Ressourcen/NILS/Rueckmeldung-an-NILS_<JJJJ-MM-TT>.md`, je Punkt *Skript, Kapitel, was, warum*. Ins NILS-Repo wird nichts geschrieben.
