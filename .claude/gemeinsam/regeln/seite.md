# Eine Seite bauen oder ändern

Gilt für jede `.html`-Seite in `Unterricht/`: E-Learning, Arbeitsblatt, Unterrichtsplan, Feedback, Testvorbereitung.
Übungs-Apps und Test-Anleitungen haben eine eigene Vorlage (siehe unten), der Rest gilt auch für sie.

## Vorlage
- Jede Seite ist EINE `.html`-Datei, die per Doppelklick aufgeht. Sie beginnt mit
  `.claude/gemeinsam/templates/Fachunterricht.html` (Schriftfeld-Seite). E-Learnings können stattdessen mit
  `.claude/gemeinsam/templates/Allgemeinbildung.html` beginnen (Layout "Lernschritte": Schritt-Leiste, Phasen mit
  Timer). Welche Vorlage, klärt der Auswahldialog (`dialog.md`). Alles hier gilt für beide.
- Die ganze Datei kopieren, den TEMPLATE-Kommentar am Anfang löschen, die `<style>`- und `<script>`-Blöcke der
  Vorlage unverändert lassen. Die Bausteine stehen im Kommentar am Anfang der Vorlage.
- Danach `python .claude/gemeinsam/scripts/sync-vorlage.py --datei <neue Seite> --schreiben` (am Mac `python3`):
  setzt die Markierungen und, bei `<meta name="schrift" content="nils">` (Technisches Zeichnen), die NILS-Schriften.
- Ändert sich eine Vorlage: `sync-vorlage.py --vorlagen`, dann `sync-vorlage.py` (Probelauf) und
  `sync-vorlage.py --schreiben` (alle Seiten), danach die Pakete neu bauen. Markierte Bereiche nie von Hand ändern.
- **Übungs-Apps** beginnen mit `.claude/skills/Uebungs-App/templates/uebungs-app.html`, die **Anleitung zu einem
  Test** erzeugt `build-test-mbz.py` aus `.claude/skills/ByCS-Test/templates/test-anleitung.html` (Look der
  ByCS-Testseite, ohne Namensfeld und Lehrkraft-Modus).

## Schriftfeld in `<header>`
Titel, Untertitel, Beruf, Ausbildungsjahr, Lernfeld · Blockwoche, Hilfsmittel.
- Klasse, Beruf, Fach und Abschnitt kommen aus dem Auswahldialog (`dialog.md`), nie raten.
- Das **Ausbildungsjahr** wird nie gefragt: Es folgt aus den Ziffern am Ende der Klasse (10 = 1. Jahr, 11 = 2. Jahr,
  12 = 3. Jahr, 13 = 4. Jahr, `ALLE` ohne Ziffern = alle Jahrgänge).
- Zelle "Lernfeld · Blockwoche": der volle Name des Fachs aus `faecher.txt`, nie das Kürzel.
- Eine zusätzliche Zelle aus dem Original (z. B. Allgemeintoleranz) kommt als eigene Zeile `<div class="wide">` nach
  der Name-Zelle.
- **Kurzkopf** `<div class="tb kurz">` (nur Benennung und Name, ohne Beruf, Ausbildungsjahr, Lernfeld · Blockwoche
  und Hilfsmittel) bei:
  - allgemeinbildenden Fächern (Ethik, Politik und Gesellschaft, Deutsch, Englisch, Religion, Sport),
  - Dokumenten nur für die Lehrkraft (Feedback zu Schülerarbeiten, Unterrichtsplan, Anleitung zum Lernpfad).
- Die **Name-Zelle** bleibt unverändert: Der Schülername wird nie eingetippt, er kommt aus der ByCS, wenn die Seite im
  SCORM-Paket läuft.
- **Version:** Das `<span class="ver">` im Benennungsfeld bleibt leer. Die Version (sichtbar nur `V1.3`, ganz klein
  oben rechts) und die unsichtbare Änderungsliste (Kommentar `VERSIONEN` nach `<title>`) trägt der Skill
  Baue-Lernpaket beim Bauen ein.
- **Farbschema:** Hell ist der Standard, die Seite hat einen Hell/Dunkel-Schalter.
- Die Seite muss gut druckbar sein (die Vorlage regelt A4 und legt die Lösung auf eine eigene Seite).

## Lösungssperre und Passwort
- `content` von `<meta name="loesung-hash">` auf den Wert `hash=` aus `.claude/gemeinsam/data/solution-password.txt`
  setzen. Fehlt die Datei: `einrichtung.md`.
- **Jedes E-Learning, überall derselbe Hash:** auch übernommene eigene Dateien, Zusatzmodule und Übungs-Apps.
- Nie ein Passwort im Klartext in eine Seite schreiben. Hat eine übernommene Seite ein eigenes Passwort, die Prüfung
  auf den Hash umstellen (Salt `bs-lernpaket|`, SHA-256, Eingabe getrimmt und in Großbuchstaben, Funktion `sha256` aus
  `Fachunterricht.html`; Beispiel: `Ressourcen/Quellen/Ethik/Ethik10_Ethische_Brille_eLearning.html`).
- Ändert die Lehrkraft das Passwort: den neuen Hash in alle E-Learnings in `Unterricht/` eintragen und ihre Pakete neu
  bauen.

## Aufgaben und Lösungen
- Kurze, klare Anweisungen. Bei neuem Unterrichtsmaterial eine Aufgabe pro nummeriertem Schritt. Beim Umbau bleibt der
  Originaltext wörtlich, Teilaufgaben (a, b, c) bekommen je ein eigenes Eingabefeld.
- **Schreibfelder** (`<textarea>`, Textfeld, Radio/Checkbox, `<select>` mit leerer erster Option) gehören INNERHALB
  von `<div class="task"><span class="tt">...</span>`. Beim Drucken werden Aufgaben ohne Eintrag durch "Hier fehlt
  noch etwas" ersetzt.
- **Lösungen** gehören in `<details class="sol">` (Lösungsvorschlag je Aufgabe) oder `<section class="answers">`
  (nur für Lehrkräfte, z. B. Bewertungsraster). Beide bleiben gesperrt, bis das Lehrkraft-Passwort eingegeben wird.
- Nach "Abgeben" (ein Versuch) sehen die Schülerinnen und Schüler ihre Bewertung und die Lösungsvorschläge aus `details.sol`,
  auch im PDF-Export. `section.answers` und `.sol-only` erscheinen nie für Schülerinnen und Schüler und nie im PDF.
- Bei versehentlicher Abgabe nimmt die Lehrkraft sie mit "Abgabe zurücknehmen" und ihrem Passwort zurück.
- **Lösungsvorschläge:** Jede inhaltliche Aufgabe bekommt einen kurzen Lösungsvorschlag in `details.sol`, nur mit
  Aussagen mit Quelle (Musterlösung, Material der Lehrkraft oder belegte Fundstelle mit Angabe). Für eine Fundstelle
  darf ohne Rückfrage im Web gesucht werden (nur Fachbegriffe, keine Schülerdaten). Findet sich keine Quelle, gibt es
  keinen Vorschlag, und die Aufgabe wird im Bericht genannt. Bei eigener Meinung oder eigenen Beispielen nur
  Vergleichskriterien ("Eigene Meinung, keine Musterlösung. Vergleiche: …"). Organisationsaufgaben (Gruppe finden,
  Rollen) brauchen keinen. Einzelheiten: Skill Baue-E-Learning, `bausteine.md`.

## Ressourcen und eigener Code
- **Keine externen Ressourcen:** Bilder, Skripte, Stylesheets und Schriften kommen nie von außen. Klickbare Links
  (`<a href>`) nach außen sind erlaubt.
- **Bilder** als `data:`-Adresse einbetten. Nur große Medien (Video, 3D-Modell) kommen als Datei in denselben Ordner;
  die Seite funktioniert dann nur als SCORM-Paket.
- **Module aus einer bestehenden Datei der Lehrkraft** (3D-Ansicht, Simulationen, Spiele) werden übernommen: CSS und
  JS unverändert in ein zusätzliches `<style>` und `<script>` NACH den Blöcken der Vorlage. Erlaubt sind nur diese
  Anpassungen: Reste der alten Seitenhülle entfernen (Navigation, Namensabfrage, Abgabe, Speichern), die
  Passwortprüfung auf den Hash umstellen und ein kleines Script, das das Ergebnis ins Feld der Aufgabe schreibt
  (Skill Baue-E-Learning, `module-grafiken.md`).
- **Beim bloßen Umbau** einer bestehenden Datei nie von sich aus neuen interaktiven Code schreiben.
- **Neues E-Learning aus PDFs** (Baue-E-Learning, Arbeitsweise A) und **Testvorbereitung:** zusätzliches CSS und
  reines JavaScript für interaktive Aufgaben ist erlaubt (Sortieren, Zuordnen, Anklicken, Simulationen), in
  zusätzlichen Blöcken nach den Vorlagenblöcken, offline, ohne Bibliotheken. Die Vorlagenblöcke werden nie angefasst.
