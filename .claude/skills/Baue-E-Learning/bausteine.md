# Baue-E-Learning – Schritt 4: Bausteine der Vorlage

Teil des Skills Baue-E-Learning (Ablauf in `SKILL.md`). Papierfassungen für den Leerdruck: `druckfassung.md`. Module und Grafiken: `module-grafiken.md`.

## Schritt 4 – Umbau in Bausteine der Vorlage
| Im Material | In der Vorlage |
|---|---|
| Kapitel / Themenblock | `<section class="ch">` mit `chnum`, `h2`, Lernziel als `p.goal` |
| Unterrichtsphase (Methode, Sozialform, Zeit); bei Lernschritte siehe Schritt 4c | `<section class="phase">` mit `div.phasehead` (`phnum`, `h2`, `div.phmeta` mit `span.chip s-einzel\|s-partner\|s-gruppe\|s-plenum`, `chip m`, `chip z`, `p.phauftrag`). Enthält die Niveau-Blöcke und Aufgaben. Aufeinanderfolgende Phasen wechseln Methode oder Sozialform. Lehrkraft-Hinweis: `<div class="box sol-only">`. Aufbau im Kommentar der Vorlage. |
| Niveau | `<section class="level foundation\|core\|challenge">` mit `h2` |
| Aufgabe | `<div class="task"><span class="tt">Aufgabe 1.1 - Titel</span> ...</div>` |
| Freitext, Begründung, Rechenweg | `<textarea>` in der Aufgabe. Schreiblinien im leeren Arbeitsblatt: `data-zeilen="4"` (sonst `rows`, mindestens 3, ohne Angabe 5). So viele Linien setzen, wie die Antwort auf Papier braucht. |
| Interaktive Aufgabe (Sortieren, Zuordnen per Klick, 3D, Spiel, Regler) | Bildschirmteil mit `class="screen-only"`, dazu eine Papierfassung `<div class="print-alt">` nach `druckfassung.md` |
| Kurzantwort, Zahl, Einheit | `<input type="text">` bzw. `type="number"` |
| Lückentext | Satz mit `<input type="text">` oder `<select>` an der Lücke |
| Auswahl (Multiple Choice) | `<label><input type="radio" name="...">` (Mehrfachauswahl: `checkbox`) |
| Zuordnen | je Zeile ein `<select>` |
| Tabelle zum Ausfüllen | `<table>` mit Eingabefeldern in den Zellen |
| Merksatz, Info | `<div class="merke">`, Warnung `<div class="warn">`, Wortspeicher `<div class="box">` |
| Aufgabe nur auf Papier (Skizze zeichnen) | `<div class="lines"></div>` ohne Eingabefeld |
| Aufgabe braucht Papier/Material (Arbeitsblatt, Ausdruck, Zeichenblatt) | direkt nach dem Aufgabentitel `<div class="paper"><b>Auf Papier:</b> Du brauchst [Material]. Melde dich bei deiner Lehrkraft und hol es dir ab.</div>`. Nicht bei mündlichen Aufgaben oder Aufgaben am Computer. |
| Ergebnis eines Spiels/Zusatzmoduls ("6 von 8") | `<input type="text" readonly data-score>` (oder `data-score="richtig"`, wenn der Text "x von y richtig" lautet): zählt als Punkte, nicht nur als bearbeitet |
| Lösungsvorschlag zu einer Aufgabe | `<details class="sol"><summary>Lösungsvorschlag</summary>...</details>` **innerhalb** der Aufgabe |
| Richtige Antwort für die automatische Bewertung (aus der Musterlösung) | `data-ok` an der richtigen Radio-/Checkbox-Option oder `<option>`; `data-ok="A\|B"` am Textfeld; `data-ok="12,5" data-tol="0,1"` bei Zahlen; `data-keys="Begriff; Begriff\|Synonym"` an der `<textarea>` (Schlüsselbegriffe aus der Musterlösung, 3 bis 6) |
| Punkte einer Aufgabe im Original (z. B. "4 P.") oder Wunsch der Lehrkraft, eine Aufgabe stärker zu gewichten | `data-gewicht="4"` an `<div class="task">` (Komma erlaubt). Es ist das Gewicht innerhalb des Niveaus: Die Seite rechnet die Punkte auf 100 um (Niveau 40/40/20) und zeigt sie an der Aufgabe. Ohne Angabe zählen alle Aufgaben eines Niveaus gleich. |
| Gesamtlösung, Bewertungsraster | `<section class="answers">` am Ende |

Regeln:
- **Jedes `<select>` hat als erste Option eine leere** (`<option value="">-</option>`), sonst zählt die Aufgabe immer als bearbeitet.
- **Lösungen stehen ausschließlich** in `details.sol`, `section.answers` oder Elementen mit Klasse `sol-only`. Nirgends sonst (nicht im Aufgabentext, nicht als Vorgabewert, nicht in `placeholder` oder `title`). Einzige Ausnahme: die Bewertungsangaben `data-ok`, `data-tol`, `data-keys` an den Feldern (nicht sichtbar, nur für die Punkte).
- **Lösungsvorschläge:** Jede inhaltliche Aufgabe bekommt einen `<details class="sol">` (`<summary>Lösungsvorschlag</summary>`, unabhängig davon, ob er aus einer Musterlösung stammt oder recherchiert ist). Die Schülerinnen und Schüler sehen ihn nach der Abgabe, auch im PDF. Ausgenommen sind reine Organisationsaufgaben (Gruppe finden, Rollen verteilen, Checkliste zur Präsentation).
  - **Kurz:** nur der Kern, keine Ausschmückung, keine Wiederholung des Aufgabentexts.
  - **Technisches Zeichnen:** Fachquellen sind die NILS-Skripte (Lös-Fassung), `Ressourcen/Tabellenbuch/TAB_Referenz_01-002.md` (Entscheidungen A1–A6) und `Ressourcen/NILS/Festlegungen.md` (hat Vorrang). Tabellenbuchseiten nie kopieren, Seitenzahlen offen lassen ("(Tabellenbuch Metall, Bemaßung)").
  - **Nur Aussagen mit Quelle:** aus der Musterlösung, dem Material oder Original der Lehrkraft (z. B. ihre Lehrkraft-Hinweise, Lösungstabellen, Vorschläge im Script) oder einer belegten Fundstelle mit Angabe in Klammern (Werk, Stelle, Jahr). Websuche danach ist ohne Rückfrage erlaubt (nur Fachbegriffe, keine Schülerdaten). Nichts Eigenes ohne Beleg.
  - **Eigene Meinung, eigenes Beispiel, eigene Entscheidung:** keine Musterlösung, nur Vergleichskriterien aus dem Arbeitsauftrag, z. B. "Eigene Meinung, keine Musterlösung. Vergleiche: Nennst du …? Begründest du …?"
  - Was die Schülerinnen und Schüler auch nach der Abgabe nicht sehen sollen (Beobachtungstipps, Ablauf), gehört in `.teacher.sol-only` bzw. `.sol-only` oder `section.answers`.
- **Bewertung hinterlegen:** Wo die Musterlösung eindeutig ist (Auswahl, Zuordnung, Zahl, Fachbegriff), immer `data-ok` setzen. Bei Freitext `data-keys` mit den tragenden Fachbegriffen der Musterlösung. Bei offenen Aufgaben ohne eindeutige Lösung (Meinung, Skizze) nichts setzen: Sie zählen dann nur als bearbeitet. Im Bericht nennen, welche Aufgaben automatisch bewertet werden und welche nicht.
- **Punkte:** Nennt das Original Punkte je Aufgabe, als `data-gewicht` übernehmen (nur wenn sie sich innerhalb eines Niveaus unterscheiden). Im Bericht an die Lehrkraft die Punkte je Aufgabe auflisten, wie die Seite sie anzeigt.
- **Aufgabentitel** beginnen mit der Nummer bis zum Gedankenstrich (`Aufgabe 1.1 - Titel`, `Lerntheke 3 - Titel`): Daraus entsteht die Kennung der Aufgabe in den Moodle-Berichten (`Aufgabe-1.1_Einsteiger_10P`).
- Die Antwortfelder immer **leer** lassen.
- Eingabefelder nur **innerhalb** von `.task` (sonst werden sie weder gezählt noch gespeichert).
- **Speicherschlüssel:** Jedes Eingabefeld bekommt `data-k="<Aufgabe>-<Nr.>"`, fortlaufend je Aufgabe (z. B. `a3-1`, `a3-2`; jede Radio-/Checkbox-Option einen eigenen). Unter diesem Schlüssel speichert das SCORM-Paket die Eingabe, so bleibt der Fortschritt der Lernenden auch nach einer Änderung der Seite erhalten. Beim Ändern einer bestehenden Seite vergebene Schlüssel nie ändern oder wiederverwenden, neue Felder bekommen neue Schlüssel. Felder ohne `data-k` bekommen ihren Schlüssel zur Laufzeit aus Aufgabe und Reihenfolge.
- Aufgabennummern und Reihenfolge des Originals beibehalten. Texte nicht umformulieren, außer offensichtliche Tippfehler (dann melden). Kürzen nur, wenn die Lehrkraft es will. Teilaufgaben (a, b, c) bekommen je ein eigenes Eingabefeld, der Text bleibt wörtlich ("eine Aufgabe pro Schritt" aus `seite.md` gilt für neues Unterrichtsmaterial).
- **Abbildungen:** Grafiken und Zeichnungen aus altem Material kommen neu gezeichnet oder geputzt in die Seite (Schritt 4d in `module-grafiken.md`). Eigene neue Skizzen ohne alte Vorlage dürfen Inline-SVG sein (mit `currentColor`, dann passen sie sich dem Dunkelmodus an). Fehlt die Vorlage einer Abbildung: Platzhalter `<div class="box">Abbildung fehlt: ...</div>` mit Beschreibung und die fehlenden Bilder am Ende der Lehrkraft auflisten. Bilder immer als `data:`-Adresse einbetten (kein Link nach außen). Nur große Medien (Video, 3D-Modell) kommen als Datei in denselben Ordner. Dann funktioniert die Seite nur als SCORM-Paket, das im Bericht sagen.
- **Formeln:** als lesbarer Text mit Unicode (z. B. `v = s / t`, `m²`, `·`), keine Bibliotheken.
- Bei Arbeitsweise B: Interaktive Module des Originals (3D-Ansicht, Animationen, Simulationen, Spiele) bleiben **erhalten**, siehe Schritt 4a. Nur Teile, die zur alten Seitenhülle gehören (eigene Navigation, Namensabfrage, Passwortfenster, Abgabe-/PDF-Bereich, Hell/Dunkel-Schalter), entfallen, weil die Vorlage sie ersetzt. Nenne diese Teile im Bericht. Felder für Mitschüler/innen (z. B. "Meine Gruppenmitglieder") bleiben erhalten: Die Schülerinnen und Schüler tragen die Namen selbst ein, gespeichert wird in der ByCS (mit der Lehrkraft so abgesprochen). Nur das eigene Namensfeld entfällt.


## Schritt 4c – Nur bei der Vorlage Lernschritte (Allgemeinbildung.html)
Zusätzlich zu Schritt 4 (Aufgaben, Niveaus, Lösungen, Bewertung bleiben gleich):

| Im Material | In Allgemeinbildung.html |
|---|---|
| Zeitplan, Arbeitsformen, Gesprächsregeln | erster Schritt "Überblick" (steht in der Vorlage: Zeitplan-Tabelle und Legende `div.lg` mit `span.pf pfx-einzel\|partner\|gruppe\|plenum\|wahl`) |
| Abschnitt einer Stunde, der auf eine Bildschirmseite passt (eine bis drei zusammengehörige Phasen) | `<section class="step" data-lesson="Stunde 1 von 3">` mit `<h2>2 · Titel</h2>` und `<p class="lead">` |
| Phase (Sozialform, Zeit) | `<div class="phasebar" data-form="einzel\|partner\|gruppe\|plenum\|wahl" data-min="12">Titel der Phase</div>`, Methode optional als `data-label` (statt `section.phase` aus Fachunterricht.html) |
| Arbeitsauftrag, Fallbeispiel, Material | `<div class="card"><span class="tag">Einzelarbeit · Freitext</span> ... </div>`, die Aufgaben (`div.task`) stehen in der Karte |
| Hinweise für die Lehrkraft | `<div class="teacher sol-only"><b>Lehrkraft: ...</b> ... </div>`, Überschrift nie als `<h3>` (stünde sonst im PDF) |
| Wahlaufgaben, Hausaufgabe | eigener Schritt mit `data-form="wahl"` |
| Ergebnis, Abgabe am Ende | letzter Schritt `section.step.result` aus der Vorlage; nur Nummer und `data-lesson` anpassen |
| Eigenes Namensfeld, Lehrkraft-Knopf, Ergebnisanzeige, Speichern/Sicherung, Druckknopf des Originals | entfallen: Name aus der Lernplattform, Lehrkraft-Modus, Ergebnis-Seite, Speichern über SCORM, PDF-Export der Vorlage. Im Bericht nennen. Felder für Gruppenmitglieder bleiben (Schritt 4). |

Regeln:
- Niveau-Blöcke (`section.level`) stehen innerhalb eines Schritts.
- Schritte fortlaufend nummerieren (`1 · Überblick`, `2 · ...`); die Leiste oben zählt selbst, die Überschrift muss dazu passen.
- Die Minuten der Phasen einer Stunde ergeben höchstens 45. Passt das Original nicht dazu, nichts ändern, sondern im Bericht melden.
