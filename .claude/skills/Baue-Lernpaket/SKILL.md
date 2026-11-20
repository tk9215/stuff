---
name: Baue-Lernpaket
description: Baut aus einem Ordner mit einem E-Learning (HTML, Bilder, Medien) ein SCORM-Paket als ZIP für die ByCS Lernplattform (BayernCloud Schule, Moodle). Das Paket meldet je Aufgabe, ob sie bearbeitet wurde und wie gut (Punkte 0 bis 100 %, Teilpunkte, Antworten im Moodle-Bericht, Punkte je Niveau und je Aufgabe im Bericht "Ziele") zur Lernstandsüberwachung zurück. Bestehensgrenze immer 70 %. Use when the teacher says "Erstelle ein Lernpaket", "SCORM", "ZIP für die Lernplattform" or wants a folder turned into an importable learning package.
---

# E-Learning-Ordner in SCORM-Paket (ZIP) umwandeln

Du machst aus einem fertigen E-Learning-Ordner ein SCORM-2004-Paket für die ByCS Lernplattform (Moodle). Moodle zeigt Punkte (0–100 %), Teilpunkte je Aufgabe, Punkte je Niveau (Bericht "Ziele") und "bestanden" ab 70 %.

**Du schreibst weder ZIP-Code noch SCORM-Code selbst.** Getestet und fertig sind `scripts/build-scorm.py` (baut und prüft), `templates/scorm-api.js` (meldet Punkte, Bestehensgrenze 70 fest) und `templates/imsmanifest.xml`, alle in `.claude/skills/Baue-Lernpaket/`.

Nebendateien in diesem Ordner, **nur bei Bedarf lesen**:
- `punkte.md`: `ScormReport`-Aufrufe für Seiten ohne Vorlage, was die Vorlagen melden (Abgabe, Bewertung, Gewichtung), Moodle-Berichte "Interaktionen" und "Ziele". Lesen bei Seiten ohne Vorlage und bei Fragen zu Punkten oder Berichten.
- `versionierung.md`: wie Version, Änderungsliste und Commit zusammenhängen. Lesen, wenn die Version überrascht oder eine alte Fassung zurückgeholt werden soll.
- `speichern.md`: wie Eingaben in der ByCS gespeichert und gesichert werden. Lesen bei verlorenen Eingaben oder "Nicht gespeichert".

## Schritt 1 – Angaben klären (nur was fehlt)
Nötig ist nur der **Quellordner** (Startdatei meist `index.html`). Alles andere wird nie gefragt oder eingetippt:
- Klasse, Fach, Abschnitt und Thema stehen im Ablageort `Unterricht/<Klasse>/<Fach>/<Abschnitt>/<Thema>/` (`.claude/gemeinsam/regeln/ablage.md`), der Titel in Moodle ist der `<title>` der Startdatei.
- `python .claude/gemeinsam/scripts/unterrichtsmaterial.py "<Quellordner>"` zeigt Steckbrief und Paketname und meldet, wenn der Ort nicht zur Regel passt.

## Schritt 2 – Prüfen (Quellordner)
- Startdatei vorhanden, alle verlinkten Dateien im Ordner, keine `http(s)://`-Verweise in `src=` oder `<link`, keine personenbezogenen Daten.
- **Passwortschutz:** `<meta name="loesung-hash">` mit genau dem Hash aus `.claude/gemeinsam/data/solution-password.txt`, kein Klartext-Passwort. Sonst erst umstellen (`.claude/gemeinsam/regeln/seite.md`), dann bauen.
- Den Quellordner nie verändern (das Skript arbeitet auf einer Kopie und pflegt in der Quelle nur Steckbrief, Version und Änderungsliste).

## Schritt 3 – Punkte-Anbindung sicherstellen
- **Seite aus `Fachunterricht.html`, `Allgemeinbildung.html` oder der Übungs-App:** meldet selbst, nichts tun. Warnt `build-scorm.py` vor einer alten Fassung (`partial: true`, `scoring: false`), den Script-Block aus der aktuellen Vorlage übernehmen.
- **Andere Seite:** Sie muss `ScormReport` aufrufen, sonst zeigt Moodle 0 Punkte (Moodle rechnet nichts selbst). `punkte.md` lesen. Fehlen die Aufrufe: der Lehrkraft melden und fragen, ob du sie einbauen sollst (dort einhängen, wo richtig/falsch schon entschieden wird, Punktelogik nicht neu erfinden).
- Der Lehrkraft einmal sagen: Hinterlegte Lösungen stehen im Quelltext, Schlüsselbegriffe sind für Freitext nur ein grober Maßstab. Für bewertete Prüfungen den Skill ByCS-Test nehmen.

## Schritt 4 – Bauen
Im Projektordner (am Mac `python3`):
```
python .claude/skills/Baue-Lernpaket/scripts/build-scorm.py --source "<Themenordner>" --aenderung "<was sich geändert hat>"
```
- `--aenderung`: ein Satz für die Änderungsliste, verständlich fürs Kollegium (erscheint im Handbuch), beim ersten Bau `"Erste Fassung"`. Pflicht, sobald sich das E-Learning seit der letzten committeten Version geändert hat.
- Optional: `--major` (Hauptversion erzwingen), `--start <datei>` (Startdatei heißt nicht `index.html`), `--nur-packen` (schreibt nichts in die Quelle).
- Name und Titel sind keine Angaben: Paket `<Klasse>_<Fach>_<Abschnitt>_<Thema>_scorm.zip` nach dem Ablageort. Anderer Name = Themenordner umbenennen (vorher fragen: Der Download-Link ändert sich; erst bauen und committen, dann umbenennen).
- Das ZIP landet im Temp-Ordner (Pfad gibt das Skript aus), nur zum Ansehen und Testen, nie ins Repo, nie nach `Unterricht/`, nie von Hand in den Teamordner. Pakete entstehen nur über GitHub.
- Warnungen des Skripts (kein `ScormReport`, externe Verweise) an die Lehrkraft weitergeben.
- **Version:** Das Skript zählt selbst. Nebennummer (V1.3) für Korrekturen, **Hauptnummer** (V2.0) bei Änderungen an Aufgaben, Punkten oder Struktur. Eine Hauptversion meldet es als Warnung: Laufende Versuche können durcheinanderkommen, also nicht mitten in einer Bearbeitungsphase committen und das der Lehrkraft vor dem Commit sagen.

**Zustellen macht GitHub:** Nach dem Push baut GitHub jedes geänderte Lernpaket neu und legt es in den Teamordner (etwa eine Minute, Download-Link bleibt gleich; ein neues Paket bekommt von selbst einen Link: `python .claude/gemeinsam/scripts/linkseite.py "<Paketname>"`). Der Bau am Rechner ist trotzdem Pflicht: Ohne Steckbrief, Version und Änderungsliste in der Seite stellt GitHub nichts zu. Meldet `pruefen.py` „geändert, aber nicht neu gebaut“: Paket neu bauen, dann committen. Alle Pakete von Hand zustellen (z. B. nach einer Änderung an `scorm-api.js`, nur Werkzeug-Verantwortliche): GitHub → Actions → "Bauen und zustellen" → Run workflow. Angekommen? `python .claude/gemeinsam/scripts/kette-pruefen.py --zugestellt "<Themenordner>"`. Roter Lauf: `.claude/gemeinsam/regeln/einrichtung.md`.

## Schritt 5 – Abschluss
- Pfad der ZIP-Datei, Version (bei Hauptversion mit Warnung) und die bestandenen Prüfungen in einer Zeile nennen.
- Fragen: "Committen und pushen? Nach dem Push ist die Änderung sofort bei den Schülerinnen und Schülern (über den Download-Link im Kurs)." Erst nach dem Ja committen (`.claude/gemeinsam/regeln/abschluss.md`).
- Nur bei einem **neuen** Paket die Einrichtung in der ByCS nennen: Aktivität **SCORM-Paket**, ZIP hochladen oder als Paket-URL den Download-Link von der Linkseite "ByCS-Links" eintragen. Einstellungen:
  - Anzahl der Versuche **1**, Neuen Versuch erzwingen **Nein**, Nach dem letzten Versuch sperren **Nein** (sonst sehen die Schülerinnen und Schüler ihre Lösungen nach der Abgabe nicht mehr)
  - Bewertungsmethode "Höchstnote", Maximale Bewertung 100, Note zum Bestehen 70
  - Abschlussbedingungen: "abgeschlossen" (= abgegeben) und/oder "bestanden" (= mindestens 70 %)
  - Danach einmal mit einem Testzugang durchspielen (Abgabe, Berichte "Interaktionen" und "Ziele", erneutes Öffnen).
- Versehentlich abgegeben: Die Lehrkraft klickt in der Seite auf "Abgabe zurücknehmen" und gibt ihr Passwort ein, die Eingaben bleiben. Notlösung: den Versuch unter Berichte löschen (leere Seite).

## Datenschutz
- Keine Namen oder Noten von Lernenden anfordern oder speichern.
- Nichts auf externe Dienste hochladen. Den Upload in die ByCS macht die Lehrkraft selbst (Ausnahmen: CLAUDE.md, Datenschutz).
