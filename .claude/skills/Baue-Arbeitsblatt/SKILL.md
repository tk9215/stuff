---
name: Baue-Arbeitsblatt
description: Erstellt ein Arbeitsblatt zu einem beliebigen Thema in drei Schwierigkeitsstufen (Einsteigerniveau, Prüfungsniveau, Profiniveau) mit Lösung für die Lehrkraft. Verwenden, wenn die Lehrkraft ein Arbeitsblatt, Übungsblatt, Übungsaufgaben oder differenziertes Unterrichtsmaterial möchte.
---

# Differenziertes Arbeitsblatt

Du hilfst einer Lehrkraft, ein Arbeitsblatt in drei Niveaus für eine Klasse mit gemischter Leistungsstärke zu erstellen. Das Arbeitsblatt nutzt dieselben Bausteine wie ein E-Learning: Es lässt sich am Bildschirm ausfüllen, wird bewertet, kann mit Baue-Lernpaket zum SCORM-Paket werden und im Lehrkraft-Modus leer gedruckt werden.

## Schritt 1 – Angaben klären (nur was fehlt)
- **Thema:** fehlt es, im Chat fragen.
- **Klasse, Beruf, Fach und Abschnitt:** per Auswahldialog nach `.claude/gemeinsam/regeln/dialog.md` (nur was fehlt, nie raten).
- **Niveaus:** im selben Auswahldialog (`dialog.md`, Niveaus, Fall A).
- **Sprachhilfen:** nach `dialog.md` (Sprachhilfen). Geschrieben wird nach `.claude/gemeinsam/regeln/sprache.md` (Pflicht in BVJ und BIK, sonst Richtschnur).
Sonst nicht fragen, sondern starten.

## Schritt 2 – Planen (der Lehrkraft in 3–5 Zeilen zeigen)
- Lernziel in einem Satz ("Die Schülerinnen und Schüler können ...").
- Bei drei Niveaus: Was sich zwischen den Niveaus ändert: Unterstützung, Komplexität, Selbstständigkeit (nicht nur "mehr Aufgaben").

## Schritt 3 – Bauen
`.claude/gemeinsam/templates/Fachunterricht.html` kopieren, `sync-vorlage.py --datei <Seite> --schreiben` ausführen, Kopf und Passwort-Hash nach `.claude/gemeinsam/regeln/seite.md` füllen und `<main>` mit dieser Struktur füllen:

```html
<section class="ch"><span class="chnum">Arbeitsblatt</span><h2>[Thema]</h2>
  <p class="goal">Du kannst ...</p>

  <section class="level foundation"><h2>Einsteigerniveau ★</h2>
    <div class="box">Wortspeicher / Satzanfänge / Lösungsbeispiel</div>
    <div class="task"><span class="tt">Aufgabe 1 - Titel</span>
      <p>Anweisung ...</p>
      <textarea data-k="a1-1" data-keys="Begriff; Begriff|Synonym"></textarea>
      <details class="sol"><summary>Lösungsvorschlag</summary>...</details>
    </div>
    ... 4–5 Aufgaben
  </section>
  <section class="level core"><h2>Prüfungsniveau ★★</h2> ... 4–5 Aufgaben ...</section>
  <section class="level challenge"><h2>Profiniveau ★★★</h2> ... 3–4 Aufgaben ...</section>
</section>

<section class="answers"><h2>Lösung für die Lehrkraft</h2> ... Bewertungshinweise, Lösungen nach Niveau gruppiert ...</section>
```

Regeln:
- Auf jedem Niveau dasselbe Thema und Ziel, damit die Klasse die Ergebnisse gemeinsam besprechen kann.
- Jede Aufgabe nummerieren. Pro Aufgabe eine Anweisung. Operatoren verwenden (nennen, erklären, vergleichen, beurteilen).
- Eingabefelder, Speicherschlüssel `data-k` und Bewertungsangaben (`data-ok`, `data-tol`, `data-keys`) wie im Skill Baue-E-Learning, Schritt 4. Felder immer leer lassen, jedes `<select>` beginnt mit einer leeren Option.
- Aufgaben nur auf Papier (Skizze): `<div class="lines"></div>` ohne Eingabefeld.
- **Lösungsvorschläge** nach `seite.md`: Jede inhaltliche Aufgabe bekommt ein kurzes `details.sol`, nur mit Aussagen mit Quelle. Die Schülerinnen und Schüler sehen es nach der Abgabe. Was nur die Lehrkraft sehen soll, gehört in `section.answers`.
- Kein Namensfeld: Der Name kommt aus der Name-Zelle im Kopf.
- Bei "Ohne Niveaus" gibt es keine Niveau-Blöcke, die Aufgaben stehen direkt in `section.ch`.
- Die Sprache der Unterrichtsmaterialien aus `CLAUDE.md` verwenden.

## Schritt 4 – Prüfen (Pflicht) und Abschluss
- Speichern als `Unterricht/<Klasse>/<Fach>/<Abschnitt>/<Thema>-Arbeitsblatt/index.html` (`.claude/gemeinsam/regeln/ablage.md`).
- Prüfen mit `python .claude/gemeinsam/scripts/seite-pruefen.py <Seite>`, öffnen und berichten nach `.claude/gemeinsam/regeln/abschluss.md`.
- Die Datei einmal erneut lesen: Jede Aufgabe hat ein Feld (oder Schreiblinien), einen eigenen `data-k` und ein `details.sol`; die Niveaus (falls gewählt) unterscheiden sich deutlich.
- Nach dem Standardsatz eine Verbesserung anbieten (z. B. "Soll ich daraus ein Lernpaket (/Baue-Lernpaket) oder einen Test (/ByCS-Fragenersteller) machen?").
