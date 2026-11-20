# Fächer: welche Fachregel gilt

Nach dem Auswahldialog steht das Fach fest. Steht es in der Tabelle, die genannte Datei lesen (zusätzlich zu
`seite.md`), sonst gibt es keine Fachregel. Nur die eine Datei zum Fach lesen, nie alle.

| Fach (Kürzel aus `faecher.txt`) | lies zuerst |
|---|---|
| Politik und Gesellschaft (`PuG`): E-Learning, Test, Testvorbereitung, Arbeitsblatt | `faecher/pug.md` (Aufbau, Bilder, Streitfragen, keine Wahr/Falsch-Fragen) |
| Lernfelder Metall (`LF…`), sobald technisch gezeichnet wird | `Ressourcen/Tabellenbuch/TAB_Referenz_01-002.md` (Entscheidungen A1–A6) und `Ressourcen/NILS/Festlegungen.md`. Die Seite bekommt `<meta name="schrift" content="nils">` vor `<title>` (NILS Text, Condensed für Überschriften und Tabellen, Normschrift in Zeichnungen; `sync-vorlage.py` setzt sie ein, auch fürs PDF). Allgemeinbildende Fächer nie |

Neue Fachregel: Datei `faecher/<kürzel klein>.md` anlegen und hier eine Zeile eintragen. Was für alle Fächer gilt,
gehört nicht hierher, sondern in `seite.md` oder eine eigene Regel.
