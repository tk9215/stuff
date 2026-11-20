# Was die Kurssicherung enthält, was nicht, und ihre Grenzen

Teil des Skills Baue-Kurs (Ablauf in `SKILL.md`). Lesen bei Fragen zum Umfang, zu Kurseinstellungen und Notenskala, oder wenn die Wiederherstellung scheitert.

## Enthält und enthält nicht
**Enthält:**
- Kursname, Kurzname, Startdatum, Kursbeschreibung, Kursbild (Banner aus dem Skill ByCS-Kursbanner)
- Abschnitt 0 für Allgemeines, danach je Blockwoche oder Lernpfad-Schritt ein Abschnitt, jeweils mit gestaltetem Abschnittstext (HTML)
- Aktivitäten:
  - **Datei** (Ressource), z. B. PDF oder E-Learning-HTML, auf Wunsch für Schülerinnen und Schüler verborgen und mit Beschreibung
  - **SCORM-Paket** aus dem Skill Baue-Lernpaket (ein Lernobjekt je Paket). Einstellungen wie im Skill Baue-Lernpaket verlangt und wie im Ethikkurs: 1 Versuch, kein neuer Versuch erzwungen, nicht gesperrt, Höchstnote, maximal 100, bestanden ab 70, Anzeige in neuem Fenster.
    - **Mit Download-Link (Standard, wie im Ethikkurs):** Moodle holt das Paket bei jedem Start neu vom geteilten Link im Teamordner (Automatisch aktualisieren: jedes Mal). Eine Korrektur, die GitHub nach dem Push in den Teamordner zustellt, kommt so ohne neue Wiederherstellung bei den Schülerinnen und Schülern an. Das ZIP kommt trotzdem in die Sicherung (Startdatei, Lernobjekt, Prüfsumme): Lernpakete liegen nicht in Git, `build-mbz.py` baut jedes im Plan genannte Paket vor dem Kursbau frisch aus seinem Themenordner (der Pfad im Plan bleibt `BYCS-SYNC/Pakete/…`).
    - **Ohne Link:** Das ZIP wird mitgeliefert, spätere Korrekturen müssen von Hand in die ByCS.
  - **Test** (Moodle-Quiz) aus dem Skill ByCS-Test: Die fertige `Test-<Thema>.mbz` wird mit Fragen, Einstellungen und Notenstufen in den Kurs übernommen (Kennwort: Platzhalter, siehe `SKILL.md`).
- Abschluss bei SCORM: „abgeschlossen“ (= abgegeben) oder „bestanden“
- Voraussetzung: Eine Aktivität öffnet sich erst, wenn eine andere abgeschlossen ist
- die Blöcke KI-Chat und KI-Steuerung und die Kategorie der Beispielsicherung (Werte in `VORLAGE` im Skript)
- Kurseinstellungen der Lehrkraft: Gruppenmodus „Getrennte Gruppen“ (erzwungen), Abschlussbedingungen auf der Kursseite nicht anzeigen
- Notenskala im Kurs: Note 1 ab 92 %, 2 ab 81 %, 3 ab 67 %, 4 ab 50 %, 5 ab 30 %, 6 darunter; Anzeige „Note (Prozent)“, Bereich ohne Nachkommastellen. Die Bewertungen der Lernpakete sind in den Bewertungen verborgen, Tests bleiben sichtbar. Tests aus dem Skill ByCS-Test haben dieselben Grenzen als Notenstufen.
- Ändert die Lehrkraft solche Einstellungen in der ByCS, ihre neue Kurssicherung geben lassen, im Scratchpad entpacken, mit der gebauten Sicherung vergleichen und die Werte in `VORLAGE` übernehmen. Die Sicherung danach nicht im Projekt aufbewahren.

**Enthält nicht** (bewusst):
- Benutzerdaten, Abgaben, Noten und Einschreibungen
- Kurspasswörter: die Einschreibung legt die Lehrkraft in ByCS selbst fest
- Aufgaben mit Abgabe, Seiten, Foren, Datumsbedingungen, Tests, die nicht aus dem Skill ByCS-Test stammen
- Die Lernplattform-Erweiterung "Lizenzinfo" aus dem Beispiel

## Grenzen (offen sagen)
- **Nicht in der echten ByCS getestet.** Die Sicherung besteht die eigene Prüfung. Dateien, Abschnitte und Bewertungselemente folgen der Beispielsicherung.
- **SCORM:** Lernpakete mit Link folgen den ByCS-Sicherungen (Ethikkurs, Modul 3D-Druck), die Prüfung des Skripts hat beide Sicherungen bestanden (`--pruefen`), und der gebaute Kurs stimmt mit der Sicherung nach der Wiederherstellung in der ByCS überein. Mitgelieferte ZIPs ohne Link folgen nur dem Sicherungsformat von Moodle und sind in der ByCS nicht erprobt. Notlösung: die ZIPs von Hand als SCORM-Aktivität hochladen (Einstellungen siehe Baue-Lernpaket).
- **Tests:** Die Test-Aktivität kommt unverändert aus der Test-`.mbz` (angepasst werden nur Abschnitt, Name, Beschreibung, Kennwort und Bewertungskategorie). Ihre Einstellungen entsprechen dem Test im ByCS-Kurs "Modul 3D-Druck BVJ/BIK". Die oberste Notengrenze (z. B. 25,3 statt 24 bei 23 Punkten) setzt Moodle beim nächsten Speichern selbst neu, sie wirkt gleich.
- Die ByCS kann beim Anzeigen einzelne Inline-Stile entfernen (z. B. runde Ecken). Farben und Schrift bleiben in der Regel erhalten.
- Schlägt die Wiederherstellung fehl: Die Fehlermeldung der Lehrkraft Wort für Wort anfordern und die Ursache beheben. Häufig eine andere Moodle-Version. Dann die Werte in `VORLAGE` (Skript) mit einer frischen Sicherung der ByCS vergleichen.
- `VORLAGE` (Version, Kategorie, Eigentümer-Kennung, Blöcke) stammt aus der Beispielsicherung. Für eine andere Schule dort anpassen.
