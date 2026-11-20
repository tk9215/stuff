---
name: Notizen
description: Pflegt den gemeinsamen Notizzettel (ToDo/NOTIZEN.md) und die Themenordner in ToDo/. Stichwort eintragen, Offenes zeigen, ein Thema nachschlagen, eigene Einträge abhaken, Themenordner anlegen. Schreibt nur so, wie es der Notizschutz erlaubt. Verwenden, wenn die Lehrkraft "notier", "merk dir", "Notizzettel", "was ist noch offen", "ToDo" oder ein Thema aus den Notizen nennt.
---

# Notizzettel pflegen

## Zuerst
- `git pull --rebase`. Dann `python .claude/gemeinsam/scripts/pruefen.py --rechte` (am Mac `python3`): Die Zeile
  „Werkzeug-Verantwortliche“ sagt, ob alles erlaubt ist (fragt GitHub, wie die Prüfung), die Zeile „Ersteller in
  Notizen“ steht so in jedem neuen Eintrag (eigener Name und GitHub-Login). Meldet sie „Login: unbekannt“ (GitHub
  nicht erreichbar), keinen neuen Eintrag schreiben, sondern sagen, dass es geht, sobald GitHub erreichbar ist.
  `git config bycs.werkzeug` nie selbst lesen oder setzen.
- Der Schutz steckt nicht in diesem Skill, sondern in `pruefen.py` (am Rechner und auf GitHub, „Notizschutz“ in
  `.claude/gemeinsam/regeln/einrichtung.md`). Dieser Skill schreibt nur so, dass die Prüfung besteht.
- `ToDo/NOTIZEN.md` und `ToDo/` nie löschen.

## Was alle dürfen (ohne Werkzeugrecht)
- **Lesen:** Offenes zeigen, ein Thema nachschlagen. Das geht immer.
- **Eintragen** („notier …“): eine neue Zeile unter „## Eingang (unsortiert)“, unter den vorhandenen Einträgen:
  `- [ ] **Kurztitel (JJJJ-MM-TT, Ersteller: <Name>, @<Login>):** Text.` Eingerückte Unterpunkte (`  - …`) sind erlaubt.
  Die Lehrkraft nicht mit Rückfragen bremsen, der Eingang darf unsortiert sein.
- **Eigene Einträge** (bei „Ersteller:“ steht der eigene Login, bei älteren Einträgen ohne Login der eigene Name):
  den Text ändern, auf `[>]` setzen oder abhaken. Älteren eigenen Einträgen darf der eigene Login nachgetragen werden. Abhaken
  heißt: `[x]`, Datum davor, den Eintrag nach „## Erledigt“ verschieben (oben unter die Überschrift). Eigene Einträge
  nicht löschen, sondern abhaken.
- **Themenordner anlegen:** `ToDo/<Thema>/` (Ordnername: erstes Wort groß, danach deutsche Rechtschreibung, mit
  Bindestrichen) mit einer `Uebergabe.md`, darin oben `Ersteller: <Name>, @<Login>`, Stand und nächste Schritte. Im
  Eintrag auf den Ordner verweisen. Wer in der `Uebergabe.md` steht, darf den Ordner später weiter pflegen.

## Was nur Werkzeug-Verantwortliche dürfen
Fremde Einträge ändern, abhaken oder löschen, Einträge in Themenabschnitte sortieren, Überschriften und Text außerhalb
der Einträge ändern, fremde Themenordner ändern, Dateien direkt in `ToDo/` ablegen, Ordner löschen. Meldet
`--rechte` „Werkzeug-Verantwortliche: nein“: nichts davon tun, sondern den Wunsch als kurzen Text formulieren, den
die Lehrkraft an die Werkzeug-Verantwortlichen weitergibt, oder als eigenen Eintrag im Eingang notieren („Bitte an die
Werkzeug-Verantwortlichen: …“).

Mit „Werkzeug-Verantwortliche: ja“ ist alles erlaubt. Dann zusätzlich: **Sortieren** (nur auf Wunsch, Wortlaut nicht ändern) und
beim Abhaken fragen, ob ein verarbeiteter Themenordner gelöscht oder nach `Ressourcen/` verschoben werden soll, nie von
selbst löschen.

## Aufbau von NOTIZEN.md
Markierungen `[ ]` offen, `[>]` in Arbeit, `[x]` erledigt. Reihenfolge = Priorität. Abschnitte: „Eingang
(unsortiert)“, Themenabschnitte, „Erledigt“ (unten, mit Datum, neueste oben).

## Datenschutz
Keine Namen, Noten oder anderen personenbezogenen Daten von Schülerinnen und Schülern in die Notizen. Werden welche
eingefügt: durch „Schülerin oder Schüler A“ ersetzen und daran erinnern.

## Abschluss
`python .claude/gemeinsam/scripts/pruefen.py --erneuern` muss bestehen. Meldet sie „Notizschutz“, die Änderung so
zurücknehmen, dass nur Erlaubtes übrig bleibt. Notizen sind kein Lernpaket: danach nach `CLAUDE.md` selbst committen
und pushen und kurz sagen, was gepusht ist. Bei reinen Notiz-Einträgen entfällt die Zeile in `neuigkeiten.txt`.
