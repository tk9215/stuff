---
name: Einheit-planen
description: Plant eine vollständige Unterrichtseinheit (Unterrichtsreihe) mit einem Team von Agenten – Lehrplanprüfung, Stundenplan mit Aufbau, Termine unter Beachtung des Schulkalenders, eine Kalenderdatei und eine abschließende Qualitätsprüfung. Verwenden, wenn die Lehrkraft eine Einheit, Unterrichtsreihe oder eine Abfolge von Stunden ab einem Startdatum planen möchte.
---

# Eine Einheit mit dem Agententeam planen

Du bist der **Orchestrator**. Du erledigst die Detailarbeit nicht selbst.
Du gibst jeden Schritt an einen Fachagenten, reichst die Ergebnisse weiter und fügst alles zusammen.

## Schritt 0 – Angaben klären (nur was fehlt)
**Klasse, Fach und Abschnitt** (für den Ablageort) per Auswahldialog nach `.claude/gemeinsam/regeln/dialog.md`. Der Unterrichtsplan ist ein Dokument nur für die Lehrkraft: kurzer Kopf, nach Beruf und Hilfsmittel nicht fragen (`.claude/gemeinsam/regeln/seite.md`). Abschnitt = die Blockwoche oder Lernsituation, in der die Einheit beginnt.

**Niveaus** im selben Auswahldialog (`dialog.md`, Niveaus, Fall A).

Der Rest in EINER Nachricht im Chat:
- Thema
- Startdatum
- Unterrichtstage und -zeiten (z. B. "Mo 08:00 und Do 09:45, 45 Minuten")
- Anzahl der Stunden (Standard: 8)

Ablageort: `Unterricht/<Klasse>/<Fach>/<Abschnitt>/<Thema>-Unterrichtsplan/` (`.claude/gemeinsam/regeln/ablage.md`).

Gib den Auftrag in 3 Zeilen wieder, dann starte.

## Schritt 1 – Lehrplan → `lehrplan-agent`
Bitte ihn um die passenden LehrplanPLUS-Kompetenzen und 3–5 Lernziele zu diesem Thema und dieser Jahrgangsstufe.

## Schritt 2 – Stunden → `unterrichts-planer`
Gib ihm den Auftrag (mit der Wahl bei den Niveaus) und das Lehrplanergebnis. Er liefert den Stundenplan mit Aufbau.

## Schritt 3 – Termine → `kalender-agent`
Gib ihm das Startdatum, die Unterrichtstage/-zeiten, die Anzahl der Stunden, die Stundentitel aus Schritt 2 und den Pfad für die `.ics`-Datei: `<Ablageort>/<Thema>-Stunden.ics`.
Er überspringt Ferien, schreibt die `.ics`-Datei und liefert die Terminliste.
(Schritt 1 und 3 hängen nicht voneinander ab. Du kannst sie gleichzeitig starten,
aber der Kalenderagent braucht die Stundentitel, deshalb ist es am einfachsten, ihn nach Schritt 2 zu starten.)

## Schritt 4 – Bauen (zusammenfügen)
`<Ablageort>/index.html` als EINE Webseite schreiben: `.claude/gemeinsam/templates/Fachunterricht.html` kopieren, `sync-vorlage.py --datei <Seite> --schreiben` ausführen, kurzen Kopf setzen (`<div class="tb kurz">`, `seite.md`) und `<main>` füllen:
```html
<h1>Einheit: [Thema]</h1>
<p class="lead">[Fach], [Jahrgangsstufe] · [erstes Datum] bis [letztes Datum] · [n] Stunden</p>
<h2>Lehrplanbezüge und Lernziele</h2> ... (alles Ungeprüfte in einer .box kennzeichnen)
<h2>Übersicht</h2> <table> Nr. | Datum | Stundentitel | Ziel | Hauptaktivität </table>
<h2>Stunden</h2> je Stunde ein <h3>, mit dem Plan des Agenten unterrichts-planer und dem echten Datum
<h2>Übersprungene Termine</h2> Ferien und Grund
```

Dann den Plan mit `python .claude/gemeinsam/scripts/seite-pruefen.py <Seite>` prüfen (`.claude/gemeinsam/regeln/abschluss.md`).

## Schritt 5 – Prüfen (Pflicht) → `qualitaets-pruefer`
Gib ihm den Pfad des Unterrichtsplans und der `.ics`-Datei und die Wahl bei den Niveaus. Behebe jeden Punkt unter **Muss korrigiert werden**.
Nenne der Lehrkraft die **Wünschenswert**-Vorschläge, setze sie aber nicht ungefragt um.

## Schritt 6 – Abschluss
Sage der Lehrkraft in höchstens 8 Zeilen: die beiden Dateinamen ("Doppelklick auf die .html-Datei öffnet den Plan; die .ics-Datei öffnen, um die Stunden in den Kalender zu übernehmen"), das erste und letzte Stundendatum,
welche Ferien übersprungen wurden, und einen Vorschlag
(z. B. "Das Arbeitsblatt für Stunde 3 mit /Baue-Arbeitsblatt erstellen").
