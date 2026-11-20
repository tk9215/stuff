# Mein Unterrichtsprojekt

Claude liest diese Datei in jeder Sitzung. Hier steht nur, was immer gilt. Alles Weitere steht genau einmal in
`.claude/gemeinsam/regeln/` und wird gelesen, bevor die Arbeit beginnt (Wegweiser).

## Über mich
- Ich unterrichte an einer Berufsschule in Bayern, Deutschland.
- Klasse, Beruf, Fach und Abschnitt (Blockwoche, Lernsituation, Modul) wechseln: Sie kommen jedes Mal aus dem Auswahldialog, nie raten.
- Lehrplan: Bayerischer LehrplanPLUS (https://www.lehrplanplus.bayern.de).
- Unsere Lernplattform: ByCS Lernplattform (BayernCloud Schule, läuft auf Moodle, früher mebis).

## Wegweiser: erst lesen, dann arbeiten
Alle Dateien liegen in `.claude/gemeinsam/regeln/`. Die Skills nennen, welche sie brauchen. Ohne Skill gilt:

| Wenn du … | lies zuerst |
|---|---|
| Unterrichtsmaterial anlegst, ablegst, umbenennst oder etwas in `Ressourcen/` speicherst | `ablage.md` |
| Klasse, Beruf, Fach, Abschnitt, Vorlage oder Niveaus brauchst | `dialog.md` |
| eine Seite (`.html`) baust oder änderst | `seite.md` |
| Unterrichtsmaterial für ein bestimmtes Fach baust (z. B. PuG, Lernfelder mit Technischem Zeichnen) | `faecher.md` (nennt die Fachregel, falls es eine gibt) |
| Text schreibst, den Schülerinnen und Schüler lesen (Aufgaben, Infotexte, Rückmeldungen, Testfragen) | `sprache.md` (Pflicht in BVJ und BIK, sonst Richtschnur) |
| eine Seite fertig meldest, ein Paket baust oder committen willst | `abschluss.md` |
| Skills, Vorlagen, Skripte, Hooks, Regeln, Einstellungen, diese Datei oder das Handbuch änderst | `handbuch.md` |
| mit `BYCS-SYNC/`, Teamordner, Download-Links oder Zustellung zu tun hast | `zustellung.md` |
| "Teamordner … nicht gefunden" siehst, die Passwortdatei fehlt, ein Rechner neu ist oder du im Browser arbeitest (Claude Code im Web) | `einrichtung.md` |

## Wie ich Unterrichtsmaterialien möchte
- Sprache der Schülermaterialien: Deutsch. Kurze, klare Anweisungen, schülergerechte Formulierungen.
- **Immer "Schülerinnen und Schüler"** (richtig gebeugt), wo die lange Form stört "Lernende". Nie "Schüler" allein und nie "Schüler/innen", im ganzen Projekt und in deinen Antworten. Zusammensetzungen wie "Schülersicht" oder "Schülerarbeiten" bleiben. Ausnahme: wörtliche Zitate aus Leitbild und Qualitätszielen der B2 bleiben im Original ("Schüler*innen", passend zu "Bürger*innen").
- Standard sind drei Niveaus: **Einsteigerniveau** blau, **Prüfungsniveau** rot, **Profiniveau** schwarz. Unterrichtsmaterial ohne Niveaus ist in jedem Fach erlaubt, aber nie von selbst: bei neuem Unterrichtsmaterial und beim Umbau immer im Auswahldialog fragen, außer ich habe es schon gesagt.
- Bewertete Pakete: Einsteigerniveau 40 %, Prüfungsniveau 40 %, Profiniveau 20 % der Punkte. Bestehensgrenze 70 %, auch ohne Niveaus. Einsteigerniveau + Prüfungsniveau (80 %) sind die Mindestanforderung.
- Am Ende eine Lösung für die Lehrkraft, deutlich abgetrennt.
- Fragen für die ByCS werden immer gleich als Test gebaut, es gibt keine Quizze mehr.

## Was immer gilt
- **Unterrichtsmaterial ist immer EINE Webseite (`.html`)** aus der Vorlage `.claude/gemeinsam/templates/Fachunterricht.html` oder `Allgemeinbildung.html`, die ich per Doppelklick öffne. Nie Markdown. Ausnahmen zum Importieren: `.xml`, `.ics`, `.zip`, `.mbz`. Interne Arbeitsdateien (Notizen, Regeln, Wegweiser) sind `.md`.
- **Ablage:** `Unterricht/<Klasse>/<Fach>/<Abschnitt>/<Thema>/index.html`, Lernpakete und Kurssicherungen entstehen **nur über GitHub** im Teamordner (SharePoint `BYCS-SYNC`), nie im Projektordner: kein Ordner `BYCS-SYNC/` im Repo, lokal Gebautes landet im Temp-Ordner. In Git liegen nur die Quellen (Seiten, Kurspläne, Test-Ordner). GitHub prüft nach jedem Push, baut Lernpakete und Kurse, erneuert das Handbuch und stellt alles in den Teamordner zu. Git-Hooks gibt es nicht mehr. Namen nie abtippen: `python .claude/gemeinsam/scripts/unterrichtsmaterial.py "<Ordner>"` zeigt sie.
- **Vorlagenblöcke nie anfassen:** `<style>` und `<script>` der Vorlage bleiben unverändert. Beim bloßen Umbau einer bestehenden Datei nie von dir aus neuen interaktiven Code schreiben.
- **Keine externen Ressourcen:** Bilder, Skripte, Stylesheets und Schriften kommen nie von außen. Klickbare Links nach außen sind erlaubt.
- **Lösungen bleiben gesperrt:** nur in `<details class="sol">` oder `<section class="answers">`, mit dem einen Passwort-Hash aus `.claude/gemeinsam/data/solution-password.txt`. Nie ein Passwort im Klartext in eine Seite, nie im Chat, nie im Handbuch.
- **Der Schülername wird nie eingetippt.** Er kommt aus der ByCS, wenn die Seite im SCORM-Paket läuft.
- **Fertig heißt geprüft:** `python .claude/gemeinsam/scripts/seite-pruefen.py <Seite>` besteht, danach zur Kontrolle öffnen und berichten nach `abschluss.md`. Vor jedem Commit: `python .claude/gemeinsam/scripts/pruefen.py --erneuern` besteht (dieselbe Prüfung macht GitHub nach dem Push).
- **Mitdokumentieren:** Änderungen am Werkzeug brauchen im selben Commit eine Zeile in `.claude/handbuch/neuigkeiten.txt` (`pruefen.py` stoppt sonst; nur intern: `--intern` und "[intern]" in der Commit-Nachricht).
- **Werkzeug ändern nur Werkzeug-Verantwortliche:** Was Werkzeug ist (Skills, Vorlagen, Skripte, Regeln, Einstellungen, Workflow, von Hand Geschriebenes im Handbuch, diese Datei), steht in `.claude/gemeinsam/data/schutz.txt`. Nur ändern, wenn `python .claude/gemeinsam/scripts/pruefen.py --rechte` "Werkzeug-Verantwortliche: ja" meldet. `bycs.werkzeug` setzt nie Claude, nur die Lehrkraft selbst. Sonst den Wunsch an die Werkzeug-Verantwortlichen weitergeben, eigene Skills in `~/.claude/skills/<Name>/` anlegen, nie im Projekt. Alles Weitere (auch Abteilungsschutz): `einrichtung.md`, "Werkzeugschutz und Abteilungsschutz".
- **Kein PowerShell** (in `.claude/settings.json` gesperrt): keine `.ps1`-Dateien, keine PowerShell-Befehle in Skills oder Anleitungen. Skripte sind Python 3 (am Mac `python3`) oder `sh`.

## Git: direkt auf `main` arbeiten
- Wir arbeiten zu mehreren an diesem Repo: Kolleg/innen pflegen Korrekturen selbst ein. Änderungen direkt auf `main` committen und pushen, keinen eigenen Branch anlegen.
- Vor der ersten Änderung einer Sitzung und vor jedem Commit die neueste Fassung holen: `git pull --rebase` (nach jedem Push committet GitHub das erneuerte Handbuch, es gibt also fast immer etwas Neues). Bei einem Konflikt anhalten und fragen, nie raten und nie fremde Änderungen überschreiben.
- **Wann fragen, wann selbst committen:**
  - Ändert der Commit ein **Lernpaket** (Themenordner, dessen `index.html` eine Version trägt; `pruefen.py` meldet "Lernpaket betroffen: ja"): immer fragen: "Committen und pushen? Nach dem Push ist die Änderung sofort bei den Schülerinnen und Schülern (über den Download-Link im Kurs)." Erst nach meinem Ja.
  - **Alles andere** (Werkzeug, Regeln, Notizen, Kurse, Tests, Handbuch, Ressourcen): nach bestandener Prüfung selbst committen und pushen und danach kurz sagen, was gepusht ist. Kurse und Tests erreichen die Schülerinnen und Schüler erst, wenn ich sie in der ByCS wiederherstelle.
- GitHub weist Pushes ab, die Werkzeug oder Unterricht eines fremden Teams ändern ("repository rule violations"). Dann nie erzwingen und keinen anderen Weg suchen: `abschluss.md`.
- Keinen Pull Request erstellen, außer ich bitte darum.
- Lässt die Cloud-Sitzung den Push auf `main` nicht zu, mir das sagen und den Branch der Sitzung nutzen. Am Ende der Sitzung erinnern, dass der Branch zusammengeführt oder gelöscht werden muss.

## Datenschutz (immer)
- Nie nach Namen, Noten oder anderen personenbezogenen Daten von Schülerinnen und Schülern fragen oder sie speichern.
- Wenn ich Schülerarbeiten einfüge, davon ausgehen, dass sie anonymisiert sind. Steht doch ein Name darin, ihn durch "Schülerin oder Schüler A" ersetzen und mich daran erinnern.
- Nichts auf externe Dienste hochladen. Ausnahmen:
  - Websuchen, um die ich bitte, und Suchen nach Belegen für Lösungsvorschläge (nur Fachbegriffe, keine Schülerdaten),
  - `git push` auf `main`,
  - die Zustellung der Lernpakete, Kurse, Test-Ordner und des Handbuchs durch GitHub an den Teamordner (OneDrive/SharePoint) nach jedem Push (Workflow "Bauen und zustellen", Power Automate).

## Hilfreiche Kontextdateien
- `Ressourcen/Inhalt.md`: was in `Ressourcen/` liegt.
- `#Handbuch.html`: Startseite für Kolleg/innen.
- `ToDo/NOTIZEN.md`: mein Notizzettel (Skill `Notizen`; ohne Werkzeugrecht nur neue Einträge, eigene Einträge und eigene Themenordner: `einrichtung.md`, "Notizschutz"), je Thema, das Unterrichtsmaterial dazu liegt in `ToDo/<Thema>/`. Lesen, wenn ich frage, was noch offen ist, oder ein Thema daraus nenne. Neue Stichworte unter "Eingang (unsortiert)", Fertiges mit Datum nach "Erledigt". **Jeder Eintrag bekommt den Ersteller** (Name und GitHub-Login, wie `pruefen.py --rechte` sie zeigt), z. B. "(Ersteller: Vorname Nachname, @login)".
