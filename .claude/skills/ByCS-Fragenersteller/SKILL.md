---
name: ByCS-Fragenersteller
description: Schreibt Fragen für die ByCS Lernplattform (BayernCloud Schule, Moodle-basiert, früher mebis) als Moodle-XML-Datei mit Rückmeldung zu jeder Antwort. Es gibt keine Quizze mehr: Die Fragen sind immer für einen bewerteten Test (ohne Niveaus), danach baut der Skill ByCS-Test daraus die fertige Test-Aktivität. Verwenden, wenn die Lehrkraft ein ByCS-, mebis- oder Moodle-Quiz, Testfragen, eine Fragensammlung, eine Moodle-XML-Datei oder einen personalisierten Lernpfad möchte.
---

# ByCS-Fragenersteller: Fragen für den Test

Ziel: eine `.xml`-Datei im **Moodle-XML-Format**, die die Lehrkraft in die **ByCS Lernplattform**
(BayernCloud Schule) importiert. Sie ist die Grundlage für den Test (Skill ByCS-Test).
GIFT wird nicht verwendet.

## Schritt 1 – Angaben klären (nur was fehlt)
**Es gibt keine Quizze mehr, nur Tests.** Egal ob die Lehrkraft "Quiz", "Fragen", "Test" oder "Lernpfad" sagt: Die Fragen werden immer für einen bewerteten Test geschrieben, ohne Niveaus, ohne Check-in, ohne Lernpfad (nicht danach fragen, Header "Niveaus" entfällt). Danach baut der Skill **ByCS-Test** gleich die fertige Test-Aktivität.
Thema und (optional) eine Quelle: ein Arbeitsblatt in `Unterricht/`, eine Buchseite oder Notizen.
Klasse, Fach und Abschnitt für den Ablageort per Auswahldialog nach `.claude/gemeinsam/regeln/dialog.md` (nur was fehlt; nach Beruf, Hilfsmitteln, Niveaus und Sprachhilfen nicht fragen). Fragen und Rückmeldungen nach `.claude/gemeinsam/regeln/sprache.md` schreiben (Pflicht in BVJ und BIK, sonst Richtschnur).
Gibt es zu diesem Thema schon ein Arbeitsblatt, die Fragen darauf aufbauen, damit Unterrichtsmaterial und Test zusammenpassen.

Regeln für die Fragen des Tests, Namensmuster **Test - Thema**:
- Ordner `Unterricht/<Klasse>/<Fach>/<Abschnitt>/Test-<Thema>/`, Fragen `Fragen-<Thema>.xml` (Schreibweise nach `.claude/gemeinsam/regeln/ablage.md`, z. B. `Test-Praxismodul-3D-Druck/Fragen-Praxismodul-3D-Druck.xml`),
- Kategorie `$course$/top/Standard für Test - <Thema>` (die Standardkategorie des Tests), nur diese eine,
- gemischte Schwierigkeit, in der Regel etwa 12 bis 24 Fragen, Punkte je Frage nach Aufwand (`<defaultgrade>`), die Höchstpunktzahl des Tests ist ihre Summe,
- nur die Fragetypen, die ByCS-Test kennt (kein `essay`, kein `aitext`), keine Bilder.
Nach dem Review (Lehrkraft hat die Vorschau geprüft und die Fragen ausgewählt) baut der Skill **ByCS-Test** daraus die `.mbz` und schreibt die Anleitung `index.html`. (Schritt 4).

## Schritt 2 – Bauen (Fragen in Moodle-XML)
Vor dem Schreiben `reference/moodle-xml-cheatsheet.md` im Ordner dieses Skills lesen. Sie enthält die genauen
Tags für jeden Fragetyp.

In der Datei genau eine Kategorie, ein `<question type="category">`-Block: `$course$/top/Standard für Test - [Thema]`, darunter die Fragen (gemischte Schwierigkeit, kein Check-in, keine Niveaus).

Regeln:
- Typen mischen: Multiple Choice (`multichoice`), Wahr/Falsch (`truefalse`), Kurzantwort (`shortanswer`),
  Zuordnung (`matching`), numerisch (`numerical`), Lückentext (`multianswer`), Lücken auswählen (`gapselect`)
  und Drag and Drop in Lücken (`ddwtos`), wo es passt.
- Freitext-Fragen nur auf Wunsch der Lehrkraft und nur auf Prüfungs- oder Profiniveau:
  - `aitext` ("Freitext (KI-Feedback)"): die KI gibt Rückmeldung und einen Punktevorschlag nach `aiprompt` und `markscheme`.
    Das ist ein Zusatz-Plugin, das nicht in jedem Moodle vorhanden ist. Vor dem Schreiben fragen, ob es in der ByCS (Testkurs) verfügbar ist, und
    auf den Datenschutz hinweisen (die Antworten gehen an den KI-Dienst der Plattform). Das Feld `model` leer lassen.
  - `essay`: wird von Hand bewertet. Beide Freitext-Typen nicht in Tests verwenden, weil das Ergebnis nicht sofort feststeht.
- Jede Frage bekommt als `<name>` nur ein kurzes Thema, z. B. `Lichtenergie`: ohne laufende Nummer, ohne Niveau-Kürzel und ohne Termin-Kürzel (nicht `E03 Lichtenergie`, nicht `F02 T1 …`). Das Niveau steht schon in der Kategorie. Eine Übersichtstabelle in der Anleitung nennt die Fragen mit diesem Namen.
- **Jede Antwort bekommt eine Rückmeldung** in einem eigenen `<feedback>`. Die Rückmeldung bei falschen Antworten erklärt
  die Fehlvorstellung und gibt einen Hinweis, sie sagt nicht nur "falsch".
- Bei Fragen auf Einsteigerniveau ein `<generalfeedback>` ergänzen, das den Kerngedanken noch einmal erklärt.
- **Sonderzeichen im Text maskieren**: `&` wird zu `&amp;`, `<` wird zu `&lt;`, `>` wird zu `&gt;`.
  Sonst ist das XML kaputt und der Import schlägt fehl. Umlaute und ß sind in Ordnung (die Datei ist UTF-8).
- Keine Bilder, keine eingebetteten HTML-Tags im Text (hält den Import einfach). `format="html"` nur mit reinem Text verwenden.
- **Nur einfache Zeichen.** Gerade Anführungszeichen, keine geschwungenen, keine Pfeile oder Sonderzeichen
  ("ergibt" statt eines Pfeils schreiben). Die ByCS warnt, dass Sonderzeichen Importfehler verursachen können.
- Jeder Fragenblock ist vollständig: `<question>` öffnet und `</question>` schließt ihn, mit allen
  darin geöffneten Tags geschlossen.

## Schritt 3 – Prüfen (Pflicht)
Vor dem Speichern bestätigen:
- die erste Zeile ist `<?xml version="1.0" encoding="UTF-8"?>` und das Wurzelelement ist `<quiz>` ... `</quiz>`;
- die Anzahl der `<question `-Tags entspricht der Anzahl der `</question>`-Tags (Grep-Werkzeug im Zählmodus);
- die Anzahl der `<answer`-Tags (Suchmuster `<answer[ >]`, damit `<answernumbering>` nicht mitzählt; es zählen auch die `<answer>` in Zuordnungsfragen) entspricht der Anzahl der `</answer>`-Tags (`aitext`, `essay`, `multianswer`, `gapselect` und `ddwtos` haben keine);
- in Lückentexten (`multianswer`) schließt jede `{` mit `}`; bei `gapselect`/`ddwtos` gibt es zu jedem `[[n]]` eine passende Option;
- Multiple Choice hat genau eine Antwort mit `fraction="100"` (oder absichtlich mehrere Teilpunkte);
- Zuordnungsfragen haben mindestens 3 `<subquestion>`-Paare;
- jedes `&`, `<` und `>` im Text ist maskiert (die Datei nach `&` und `<` durchsuchen und jeden Treffer prüfen);
- keine geschwungenen Anführungszeichen, Pfeile oder anderen Sonderzeichen (Umlaute sind in Ordnung).

Speichern als `<Ablageort>/Fragen-<Thema>.xml`.

Dann die **Vorschau** erzeugen (am Mac `python3`):
`python .claude/skills/ByCS-Fragenersteller/scripts/quiz-vorschau.py <Ablageort>/Fragen-<Thema>.xml`
Das legt `<Ablageort>/Vorschau.html` an: das Quiz im ByCS-Look, offline, ohne Upload. Schülersicht (beantworten, "Prüfen", Rückmeldung und Punkte) und Review-Sicht (alle Lösungen, Rückmeldungen, Punkte und Hinweise). Meldet das Skript einen XML-Fehler, die Datei korrigieren und neu starten.
- Die Vorschau einmal headless öffnen (Edge/Chrome wie in `seite-pruefen.py`) und prüfen: kein roter Fehlerkasten, in der Review-Sicht unter "Überblick" keine Hinweise. Jeden Hinweis beheben (z. B. fehlende Rückmeldung, Teilpunkte ergeben nicht 100 %, Sonderzeichen, Lücke ohne Option) oder ihn der Lehrkraft nennen, wenn er Absicht ist.
- Danach die Vorschau zur Kontrolle im integrierten Browser öffnen: `code -r "<Ablageort>/Vorschau.html"`.
- `Vorschau.html` nie von Hand ändern. Vor dem Commit erneuert `pruefen.py --erneuern` sie zu jeder geänderten Quiz-XML (bei geänderter Vorlage alle), nach dem Push macht GitHub dasselbe. Alle von Hand neu: `quiz-vorschau.py --alle`; prüfen, ob alle aktuell sind: `quiz-vorschau.py --pruefen`.
- Allgemeiner Viewer für jede andere Moodle-XML: `.claude/skills/ByCS-Fragenersteller/templates/quiz-vorschau.html` per Doppelklick öffnen und die Datei hineinziehen.

## Schritt 4 – Abschluss (Test bauen)
Nicht von Hand anlegen und keine eigene Anleitung schreiben: nach dem Review gleich den Skill **ByCS-Test** aufrufen (Arbeitszeit abfragen). Er baut `Test-<Thema>.mbz` und die Anleitung `index.html`. GitHub archiviert den Ordner nach dem Push im Teamordner unter `BYCS-SYNC/Tests/`.
