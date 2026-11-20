---
name: Raster-Feedback
description: Gibt freundliches, konkretes Feedback zu anonymisierten Schülerarbeiten anhand des Bewertungsrasters der Lehrkraft, mit nächsten Schritten für die Schülerinnen und Schüler. Verwenden, wenn die Lehrkraft Schülerarbeiten einfügt oder darauf verweist und um Feedback, Korrekturhilfe oder Kommentare bittet.
---

# Feedback mit Bewertungsraster

## Zuerst die Regeln
- Die Arbeit muss anonymisiert sein. Siehst du einen echten Namen, ersetze ihn durch "Schülerin oder Schüler A" und erinnere die Lehrkraft in einer Zeile daran.
- Claude schlägt vor; die **Lehrkraft entscheidet**. Nie eine endgültige Note als Tatsache darstellen. Sage "vorgeschlagenes Niveau".

## Schritt 1 – Angaben klären (Bewertungsraster)
- Hat die Lehrkraft ein Raster angegeben, verwende es genau so.
- Wenn nicht, schlage ein einfaches Raster mit 3–4 Kriterien für die Aufgabe vor und frage "Soll ich dieses Raster verwenden?", bevor du bewertest.

## Schritt 2 – Bauen (Feedback je Arbeit)
Für jedes Kriterium: vorgeschlagenes Niveau + ein Zitat oder Beispiel aus der Arbeit als Beleg.

Dann das Feedback **an die Schülerin bzw. den Schüler** schreiben (zweite Person, freundlich, auf ihrem Leseniveau, nach `.claude/gemeinsam/regeln/sprache.md`):
- ✅ Zwei Dinge, die gut gelungen sind (konkret).
- 🎯 Ein oder zwei nächste Schritte (konkret, in der nächsten Stunde machbar).
- ❓ Eine Frage, die zum Weiterdenken anregt.

Den Teil für die Schülerinnen und Schüler unter 120 Wörtern halten.

## Schritt 3 – Zusammenfassung, Prüfen und Abschluss
Bei mehreren Arbeiten mit einer kurzen Tabelle enden: Schülerin oder Schüler | vorgeschlagenes Niveau je Kriterium | häufigstes Problem.
Dann die 1–2 häufigsten Probleme in der Klasse nennen, damit die Lehrkraft eine kurze Förderstunde planen kann.

Als EINE Webseite speichern: `.claude/gemeinsam/templates/Fachunterricht.html` kopieren, `sync-vorlage.py --datei <Seite> --schreiben` ausführen, kurzen Kopf setzen (`<div class="tb kurz">`, Dokument nur für die Lehrkraft, `.claude/gemeinsam/regeln/seite.md`) und den Inhalt in `<main>` setzen
(je Schülerin oder Schüler ein `<section>` mit dem Feedback in einer `.box`, die Zusammenfassung als `<table>`).
Klasse, Fach und Abschnitt für den Ablageort per Auswahldialog nach `.claude/gemeinsam/regeln/dialog.md` (nur was fehlt; nach Beruf, Hilfsmitteln und Niveaus nicht fragen).
Datei: `Unterricht/<Klasse>/<Fach>/<Abschnitt>/<JJJJ-MM-TT>-<Aufgabe>-Feedback/index.html` (heutiges Datum, `.claude/gemeinsam/regeln/ablage.md`). Ordner mit der Endung `-Feedback` bleiben auf dem eigenen Rechner: `.gitignore` schließt sie aus, sie werden nie committet. Mit `python .claude/gemeinsam/scripts/seite-pruefen.py <Seite>` prüfen (`.claude/gemeinsam/regeln/abschluss.md`), dann der Lehrkraft sagen, dass sie per Doppelklick geöffnet wird.
