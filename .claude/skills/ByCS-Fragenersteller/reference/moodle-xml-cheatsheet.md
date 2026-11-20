# Moodle-XML-Spickzettel (ByCS Lernplattform)

Diese Datei ist die Formatreferenz. Eine Datei enthält alle Fragen.

## Dateigerüst
```xml
<?xml version="1.0" encoding="UTF-8"?>
<quiz>
  <question type="category">
    <category>
      <text>$course$/top/[Thema]/1 Check-in</text>
    </category>
  </question>
  <!-- hier folgen die Fragen dieser Kategorie -->
</quiz>
```
Den Kategorie-Block vor jeder Gruppe wiederholen (`2 Einsteigerniveau`, `3 Prüfungsniveau`, `4 Profiniveau`).

## Gemeinsame Felder (jede Frage)
```xml
<question type="multichoice">
  <name><text>E01 Kurztitel</text></name>
  <questiontext format="html"><text>Der Fragetext.</text></questiontext>
  <generalfeedback format="html"><text>Text zur erneuten Erklärung, oder leer.</text></generalfeedback>
  <defaultgrade>1</defaultgrade>
  <penalty>0.3333333</penalty>
  <hidden>0</hidden>
  ... typspezifische Felder und Antworten ...
</question>
```

## Multiple Choice (eine richtige Antwort)
```xml
<single>true</single>
<shuffleanswers>true</shuffleanswers>
<answernumbering>abc</answernumbering>
<answer fraction="100" format="html">
  <text>Richtige Option</text>
  <feedback format="html"><text>Richtig, weil ...</text></feedback>
</answer>
<answer fraction="0" format="html">
  <text>Falsche Option</text>
  <feedback format="html"><text>Nicht ganz. Die Fehlvorstellung und ein Hinweis.</text></feedback>
</answer>
```
Für mehrere richtige Antworten `<single>false</single>` und mehrere Anteile (z. B. 50 und 50) verwenden.

## Wahr/Falsch
```xml
<answer fraction="100" format="moodle_auto_format">
  <text>true</text>
  <feedback format="html"><text>Ja, weil ...</text></feedback>
</answer>
<answer fraction="0" format="moodle_auto_format">
  <text>false</text>
  <feedback format="html"><text>Denk noch einmal nach: ...</text></feedback>
</answer>
```
Der Fragetyp ist `truefalse`. Die erste Antwort ist immer die Antwort "true" (wahr).

## Kurzantwort
```xml
<usecase>0</usecase>
<answer fraction="100" format="moodle_auto_format">
  <text>Kohlendioxid</text>
  <feedback format="html"><text>Richtig!</text></feedback>
</answer>
<answer fraction="100" format="moodle_auto_format">
  <text>CO2</text>
  <feedback format="html"><text>Richtig!</text></feedback>
</answer>
```
Der Fragetyp ist `shortanswer`. `usecase` 0 bedeutet: Groß-/Kleinschreibung wird nicht beachtet. Pro akzeptierter Schreibweise eine Antwort ergänzen.

## Zuordnung (mindestens 3 Paare)
```xml
<shuffleanswers>true</shuffleanswers>
<subquestion format="html">
  <text>Pflanzenteil</text>
  <answer><text>Blatt</text></answer>
</subquestion>
<subquestion format="html">
  <text>Wurzel</text>
  <answer><text>Wasseraufnahme</text></answer>
</subquestion>
<subquestion format="html">
  <text>Stängel</text>
  <answer><text>Transport</text></answer>
</subquestion>
```
Der Fragetyp ist `matching`. Jede `<subquestion>` ist ein Paar: Text links, Antwort rechts.

## Numerisch
```xml
<answer fraction="100" format="moodle_auto_format">
  <text>0.5</text>
  <tolerance>0.01</tolerance>
  <feedback format="html"><text>Richtig!</text></feedback>
</answer>
```
Der Fragetyp ist `numerical`. Einen Dezimalpunkt verwenden, kein Komma.

## Lückentext (Cloze, Fragetyp `multianswer`)
```xml
<question type="multianswer">
  <name><text>P04 Lückentext</text></name>
  <questiontext format="html">
    <text>Pflanzen nehmen {1:SHORTANSWER:=Kohlendioxid#Richtig!~=CO2#Richtig!} auf und geben {1:MULTICHOICE:Stickstoff#Nein~=Sauerstoff#Ja!~Wasserstoff#Nein} ab.</text>
  </questiontext>
  <generalfeedback format="html"><text></text></generalfeedback>
  <penalty>0.3333333</penalty>
  <hidden>0</hidden>
</question>
```
Die Lücken stehen direkt im Fragetext: `{Punkte:TYP:=richtig#Rückmeldung~falsch#Rückmeldung}`.
Typen: `SHORTANSWER` (Eingabe), `MULTICHOICE` (Auswahlmenü), `MULTICHOICE_S` (Auswahlmenü, ohne Groß-/Kleinschreibung), `NUMERICAL` (Zahl, z. B. `{1:NUMERICAL:=3.14:0.01}`).
Das Zeichen `=` markiert die richtige Antwort, `~` trennt die Optionen, `#` leitet die Rückmeldung ein.
Kommen `}`, `~`, `#` oder `\` im Text selbst vor, steht davor ein Rückwärtsschrägstrich. Besser: diese Zeichen im Text vermeiden.
Ein `<defaultgrade>` wird NICHT angegeben, die Punkte ergeben sich aus den Lücken.

## Lücken auswählen (`gapselect`)
```xml
<question type="gapselect">
  <name><text>E05 Lücken</text></name>
  <questiontext format="html"><text>Die Pflanze nimmt [[1]] auf und bildet [[2]].</text></questiontext>
  <generalfeedback format="html"><text></text></generalfeedback>
  <defaultgrade>1</defaultgrade>
  <penalty>0.3333333</penalty>
  <hidden>0</hidden>
  <shuffleanswers>1</shuffleanswers>
  <correctfeedback format="html"><text>Richtig!</text></correctfeedback>
  <partiallycorrectfeedback format="html"><text>Teilweise richtig. Prüfe die falschen Lücken.</text></partiallycorrectfeedback>
  <incorrectfeedback format="html"><text>Noch nicht. Lies den Merksatz noch einmal.</text></incorrectfeedback>
  <shownumcorrect/>
  <selectoption><text>Kohlendioxid</text><group>1</group></selectoption>
  <selectoption><text>Traubenzucker</text><group>1</group></selectoption>
  <selectoption><text>Sauerstoff</text><group>1</group></selectoption>
</question>
```
Die Platzhalter `[[1]]`, `[[2]]` verweisen auf die Reihenfolge der `<selectoption>`-Einträge. Die richtige Option für Lücke 1 ist der erste Eintrag, für Lücke 2 der zweite usw. `<group>` gleich lassen, wenn die Optionen für alle Lücken zur Auswahl stehen.

## Lücken per Drag and Drop (`ddwtos`)
Gleicher Aufbau wie `gapselect`, aber statt `<selectoption>` heißt jedes Element `<dragbox>`:
```xml
<dragbox><text>Kohlendioxid</text><group>1</group></dragbox>
```
Auch hier `[[1]]`, `[[2]]` im Fragetext, die Reihenfolge der `<dragbox>`-Einträge bestimmt die richtige Lösung.

## Freitext (`essay`, wird von Hand bewertet)
```xml
<question type="essay">
  <name><text>Pf05 Begründung</text></name>
  <questiontext format="html"><text>Begründe in 2 bis 3 Sätzen ...</text></questiontext>
  <generalfeedback format="html"><text>Lösungsvorschlag für die Lernenden (nach der Bewertung sichtbar).</text></generalfeedback>
  <defaultgrade>2</defaultgrade>
  <penalty>0</penalty>
  <hidden>0</hidden>
  <responseformat>plain</responseformat>
  <responserequired>1</responserequired>
  <responsefieldlines>8</responsefieldlines>
  <attachments>0</attachments>
  <graderinfo format="html"><text>Hinweise für die Lehrkraft: worauf achten?</text></graderinfo>
  <responsetemplate format="html"><text></text></responsetemplate>
</question>
```
Die Lehrkraft muss jede Antwort selbst bewerten. Deshalb NICHT im Check-in verwenden, denn dessen Ergebnis steuert die Zugriffsbeschränkung.

## Freitext mit KI-Rückmeldung (`aitext`, Zusatz-Plugin "AI Text")
Der Fragetyp heißt in der Oberfläche "Freitext (KI-Feedback)". Er ist ein Zusatz-Plugin (qtype_aitext) und nicht in jeder Moodle-Installation vorhanden. In der ByCS vorher in einem Testkurs prüfen.
```xml
<question type="aitext">
  <name><text>Pf06 Erklärung mit KI</text></name>
  <questiontext format="html"><text>Erkläre in 2 bis 3 Sätzen, warum ...</text></questiontext>
  <generalfeedback format="html"><text></text></generalfeedback>
  <defaultgrade>2</defaultgrade>
  <penalty>0</penalty>
  <hidden>0</hidden>
  <idnumber></idnumber>
  <responseformat>plain</responseformat>
  <responsefieldlines>10</responsefieldlines>
  <minwordlimit></minwordlimit>
  <maxwordlimit></maxwordlimit>
  <graderinfo format="html"><text>Hinweise für die Lehrkraft.</text></graderinfo>
  <responsetemplate format="html"><text></text></responsetemplate>
  <aiprompt>Prüfe, ob die Antwort nennt, dass ... Gib freundliche Rückmeldung auf Deutsch in einfacher Sprache und einen Hinweis zur Verbesserung. Verrate den Lösungsvorschlag nicht.</aiprompt>
  <markscheme>Ein Punkt, wenn ... genannt wird. Ein Punkt, wenn ... begründet wird.</markscheme>
  <model></model>
  <spellcheck>0</spellcheck>
</question>
```
- `aiprompt`: Auftrag an die KI (was prüfen, wie rückmelden, welche Sprache). `markscheme`: Bewertungsschema (wofür gibt es wie viele Punkte).
- `responseformat`: `editor`, `plain` oder `monospaced`. `responsefieldlines`: Zeilen des Eingabefelds (2, 3, 5, 10, 15, 20, 25, 30, 35 oder 40).
- `model` leer lassen: dann gilt das in der Plattform eingestellte KI-Modell. Einen Modellnamen nur eintragen, wenn die Lehrkraft ihn nennt.
- Optionale Beispielantworten (zum Testen) mit `<sampleresponse><question>0</question><response>Text</response></sampleresponse>` weglassen.
- Die KI-Bewertung ist ein Vorschlag und kann falsch liegen. Für bewertete Pakete die Lehrkraft darauf hinweisen und nur kurze Antworten mit klaren Kriterien verwenden.
- Datenschutz: Die Antworten gehen an den KI-Dienst der Plattform. Die Lehrkraft klärt vorher, welcher Dienst eingestellt ist.

## Maskierung
| Im Text gewünscht | In der Datei schreiben |
|---|---|
| & | &amp; |
| < | &lt; |
| > | &gt; |

Einfache gerade Anführungszeichen verwenden. Umlaute und ß sind in Ordnung.

## Prüfungen vor dem Speichern
- Jedes `<question` hat ein `</question>`, jedes `<answer[ >]` (auch in Zuordnungsfragen) hat ein `</answer>`.
- Nur ein Wurzelelement `<quiz>`, und es schließt mit `</quiz>`.
- Kein nicht maskiertes `&`, `<` oder `>` im Text.
- Multiple Choice hat eine Antwort mit `fraction="100"`.
- Lückentext: jede `{` hat eine `}`. Lücken auswählen / Drag and Drop: zu jedem `[[n]]` im Text gibt es genug `<selectoption>` bzw. `<dragbox>`.
- `aitext` und `essay` haben keine `<answer>`-Tags (das ist richtig so).
