# Einrichtung: neuer Rechner, Teamordner, GitHub, Passwort, im Browser arbeiten

Nur lesen, wenn etwas fehlt oder ein Rechner neu eingerichtet wird (auch bei Kolleg/innen).

## Teamordner BYCS-SYNC
In den Teamordner `B2-BS-Kollegium - Dokumente/BYCS-SYNC` (OneDrive/SharePoint) stellt nur GitHub zu, nach jedem Push:
Lernpakete (`Pakete/<Klasse>/<Fach>/`), Kurse (`Kurse/<Klasse>[/<Fach>]/`), Tests (`Tests/…`) und das Handbuch. Dafür braucht ein
Rechner den Teamordner nicht. Am Rechner wird er nur gelesen: Download-Links für den Kursbau (`linkseite.py`), die
Prüfung `kette-pruefen.py --zugestellt` und das Hochladen von Kursen und Tests in die ByCS.

**Prüfen und einrichten:** `python .claude/gemeinsam/scripts/linkseite.py --teamordner` (am Mac `python3`) zeigt, wo
der Teamordner liegt, oder gibt die Anleitung aus (Link zum Ordner im Web, "…" → "Synchronisieren", am Mac
Festplattenvollzugriff für VS Code, sonst "Operation not permitted"; Claude kann das Fenster öffnen:
`open "x-apple.systempreferences:com.apple.preference.security?Privacy_AllFiles"`). Die Anleitung der Lehrkraft ganz
weitergeben, nach ihrem "fertig" erneut prüfen. Liegt der Ordner an einer ungewöhnlichen Stelle:
`git config bycs.ziel "<Pfad zum Ordner BYCS-SYNC>"`. Nachzuholen ist nichts: GitHub stellt auch ohne Teamordner zu.

Im Teamordner wird nie gelöscht: Umbenannte oder entfernte Pakete, Kurse und Tests bleiben dort liegen, bis die
Lehrkraft sie löscht.

## GitHub: prüfen, bauen, zustellen ("Bauen und zustellen")
- Workflow `.github/workflows/paket-zustellen.yml` nach jedem Push auf `main`:
  1. vergleicht mit dem letzten grünen Lauf (was ein roter Lauf nicht zugestellt hat, holt der nächste grüne nach),
  2. prüft mit `pruefen.py --seit … --erneuern` (Ablage, Steckbrief, Version, Kursplan, Test-XML, Handbuch;
     Mitdokumentieren nur als Warnung) und erneuert Handbuch und Test-Vorschau,
  3. committet Erneuertes als `github-actions[bot]` ("Automatisch: Handbuch und Vorschau erneuert [intern]"),
  4. baut die geänderten Lernpakete und Kurse und stellt sie mit geänderten Test-Ordnern und dem Handbuch zu
     (`.claude/skills/Baue-Lernpaket/scripts/paket-zustellen.py`).
  Ist die Prüfung rot, wird nichts zugestellt. Ausnahme: Ein Fehler im Abteilungs- oder Notizschutz hält nur seinen
  Bereich an (siehe "Zurückhalten").
- Von Hand (nur Werkzeug-Verantwortliche): GitHub → Actions → "Bauen und zustellen" → Run workflow: Themenordner,
  Test-Ordner, Kurs (Name wie `Kurs-ALLE10-PuG`), `Kurse`, `Handbuch` oder `alle`, mit Haken "Probe" nach
  `<Bereich>/_Pilot/`. Ein Lauf von Hand prüft nicht und stellt zu, was auf `main` liegt, auch was ein roter Lauf
  angehalten hat. Deshalb prüft er zuerst, wer ihn gestartet hat (`pruefen.py --von-hand`): Wer nicht im Team
  `werkzeug-verantwortliche` ist, bekommt einen roten Lauf, und nichts wird zugestellt.
- Secrets (Settings → Environments → `zustellung`, nur `main` darf es nutzen; keine Repository-Secrets): `FLOW_URL`, `FLOW_SCHLUESSEL` (Flow), `BYCS_LINKSEITE`
  (Adresse der Linkseite für den Kursbau), `TEAM_APP_ID`, `TEAM_APP_KEY` (Teams lesen, siehe Abteilungsschutz).
  Nie ins Repo, nie in den Chat.
- Einstellung: Settings → Actions → General → Workflow permissions: **Read and write** (für den Commit des Handbuchs).
- Der Flow (Power Automate, Konto `B2_flow`, Schreibrecht auf den ganzen Ordner `BYCS-SYNC`) nimmt in `Pakete/`,
  `Kurse/` und `Tests/` samt Unterordnern nur `.html`, `.mbz`, `.xml` und `_scorm.zip` an, ganz oben nur das Handbuch.
  Er ersetzt eine vorhandene Datei an Ort und Stelle (der Download-Link bleibt) und legt fehlende Unterordner an.
- **Roter Lauf** (GitHub schickt eine Mail): Im Protokoll stehen die Fehler (`::error::` bzw. `FEHLER:`). Meist stimmt
  der Steckbrief oder die Version nicht (am Rechner beheben, pushen), ein Kurs wartet noch auf den Download-Link eines
  neuen Pakets (Lauf nach 10 Minuten mit "Re-run jobs" wiederholen) oder der Flow antwortet nicht (Ausführungsverlauf
  des Flows in Power Automate ansehen, dann "Re-run jobs").
- Nach jedem Push liegt auf `main` meist ein Commit von GitHub (Handbuch): vor der nächsten Änderung `git pull --rebase`.

**Linkseite:** Die Download-Links der Lernpakete holt `python .claude/gemeinsam/scripts/linkseite.py`. Die Adresse
liest es aus der Umgebung `BYCS_LINKSEITE`, aus `git config bycs.linkseite` oder aus der Verknüpfung `# ByCS-Links`
im Teamordner (sie enthält einen Schlüssel: nie ins Repo, nie in den Chat). Die Linkseite verlangt ein Passwort: Auf
GitHub steht es in der Adresse im Secret (`…&pw=…`). Am Rechner fragt `linkseite.py` beim ersten Mal in einem kleinen
Fenster danach und merkt es in `.git/config` (`git config bycs.linkpasswort`), auch wenn Claude das Skript startet.
Nie im Chat nach dem Passwort fragen und es nie ausgeben. Meldet es "ohne Link", liegt das Paket
noch nicht im Teamordner oder OneDrive ist noch nicht fertig.

## Werkzeugschutz und Abteilungsschutz: Wer was ändern darf
Die einzige vollständige Beschreibung des Schutzes (CLAUDE.md, `pruefen.py`, Workflow und Skill `Notizen` verweisen
hierher). Wer was ändern darf, steuern allein die Teams der Organisation B2-NBG auf GitHub, im Repo stehen keine Namen.
Das Werkzeug ändern nur Werkzeug-Verantwortliche (Team `werkzeug-verantwortliche`). Alle anderen schreiben über das
Team `material-autor-innen` und seine Unterteams (je Abteilung und Fachbereich eines, sie erben das Schreibrecht):
`Unterricht/`, `ToDo/`, `Ressourcen/`, Kurse und Tests.
Drei Stufen: Der Rechner warnt vor dem Commit (`pruefen.py`), GitHub weist verbotene Pushes ab (Rulesets), und nach
dem Push prüft `pruefen.py` auf GitHub noch einmal und dazu alles, was ein Ruleset nicht kann (Notizen, Handbuch).

### Die Regeln: `schutz.txt`
- **Die eine Liste:** `.claude/gemeinsam/data/schutz.txt` (selbst Werkzeug). Zeilen `Werkzeug | <Muster>`,
  `Frei | <Muster>` (geht vor), `Klasse | <Kürzel> | <Team>`, `Fach | <Kürzel> | <Team>`. Muster mit `/` am Ende meinen
  einen Ordner samt Inhalt, `*` steht für beliebige Zeichen (für die Rulesets nur als ganzer Ordnername). Die
  Rulesets folgen der Liste im letzten Commit, sobald `schutz-github.py --anwenden` gelaufen ist (siehe „Einrichten“).
  In der Prüfung nach dem Push gilt die Liste in der Fassung des **letzten grünen Laufs**, am Rechner die Fassung im
  letzten Commit. Fehlt die Liste, schützt `pruefen.py` wenigstens das Werkzeug (`NOTFALL_WERKZEUG`).
- **Werkzeugschutz:** Werkzeug sind `CLAUDE.md`, `.gitignore`, alles unter `.claude/` und `.github/` und das von Hand
  Geschriebene im Handbuch `#Handbuch.html`. **Frei bleiben** die Listen, die bei der normalen Arbeit fortgeschrieben
  werden (`berufe.txt`, `faecher.txt`, `neuigkeiten.txt`, `fragen.txt`), und die automatischen Teile des Handbuchs
  (z. B. "Was ist neu" nach einem geänderten Lernpaket, die Häufigen Fragen, `pruefen.py --erneuern`). Eine neue Frage
  darf also jede und jeder aufnehmen, wenn ein vorhandener Abschnitt sie schon beantwortet; muss ein Abschnitt ergänzt
  werden, geht der Wunsch an die Werkzeug-Verantwortlichen.
- **Abteilungsschutz:** Unterricht ändern nur Mitglieder des zuständigen Teams oder Werkzeug-Verantwortliche. Für
  `Unterricht/<Klasse>/<Fach>/…` gewinnt der Fachbereich, wenn das Fach einen hat, sonst gilt die Abteilung der Klasse
  (Lernfelder gehören der Abteilung). Ohne Zuordnung ist ein Ordner für alle frei, GitHub gibt einen Hinweis. Frei sind
  auch `Unterricht/Offen/` und jede `Vorschau.html` (schreibt GitHub).
- **Notizschutz (`ToDo/`):** Ein Skill verleiht keine Rechte: Er arbeitet mit den Rechten der Person, und Git sieht
  nicht, ob ein Skill geschrieben hat. Deshalb prüft `pruefen.py` für alle außer Werkzeug-Verantwortlichen, **was**
  sich in `ToDo/` geändert hat. Erlaubt: neuer Eintrag unter „Eingang (unsortiert)“ mit Datum und
  „Ersteller: Vorname Nachname, @login“; eigene Einträge ändern, abhaken und nach „Erledigt“ verschieben (nicht
  löschen); ein neuer Themenordner `ToDo/<Thema>/` mit `Uebergabe.md` („Ersteller: Vorname Nachname, @login“), den
  diese Person danach weiter pflegt. Alles andere (fremde Einträge, Sortieren, Überschriften, fremde Ordner, Dateien
  direkt in `ToDo/`) ist ein Fehler. Der Skill `Notizen` schreibt genau in dieser Form, schützt aber selbst nichts.
- **Wem ein Eintrag gehört:** Steht ein GitHub-Login dabei, zählt nur er. Auf GitHub sind die eigenen Logins die der
  Personen, die in `ToDo/` gepusht haben (das bestätigt GitHub, den Login kann niemand fälschen). Am Rechner fragt
  `pruefen.py` den eigenen Login mit der gespeicherten Git-Anmeldung ab (`--rechte` zeigt ihn). Ältere Einträge ohne
  Login gehören dem Namen (Autorenname der Commits, `git config user.name`); der Login darf dort nachgetragen werden.
  Neue Einträge und Themenordner brauchen den Login (am Rechner ohne Verbindung genügt vorerst der Name).

### Am Rechner (vor dem Commit)
- **Nachsehen, was man darf:** `python .claude/gemeinsam/scripts/pruefen.py --rechte` zeigt
  „Werkzeug-Verantwortliche: ja/nein“ (und woher das stammt), die eigenen Teams und den eigenen Namen. Claude und die
  Skills fragen so, bevor sie Werkzeug oder fremde Notizen ändern, und lesen `bycs.werkzeug` nie selbst.
- **Wer man ist,** fragt `pruefen.py` GitHub mit der gespeicherten Git-Anmeldung (dieselbe wie beim Push,
  `git credential fill`, ohne Rückfrage; `/user/teams`, nur lesen; die Anmeldung wird nie angezeigt oder gespeichert).
  GitHub geht vor: Steht `bycs.werkzeug ja` auf einem Rechner, obwohl man nicht im Team ist, gilt der Schutz trotzdem
  (mit Warnung). Nur wenn GitHub nicht erreichbar ist, entscheidet `git config bycs.werkzeug ja`. Claude setzt das nie,
  auch nicht auf Bitte "damit die Prüfung durchgeht" (in `.claude/settings.json` gesperrt: `git config … bycs.werkzeug`
  und Bearbeiten von `.git/config`).
- **Was geprüft wird:** Werkzeug geändert ohne Werkzeugrecht → Fehler. Unterricht eines fremden Teams → Fehler, Claude
  committet nicht; ist GitHub nicht erreichbar, nur eine Warnung, wenn man im Bereich dieses Teams noch keine Commits
  hat (Git-Geschichte, `user.email`). Notizschutz wie oben. Werkzeug-Verantwortliche prüft der Rechner nicht.
  Verbindlich ist die Prüfung auf GitHub.

### Auf GitHub: vor dem Push gesperrt (Rulesets)
- **Was gesperrt ist:** `schutz-github.py` macht aus `schutz.txt` die Rulesets des Repos (Settings → Rules →
  Rulesets), alle heißen „Schutz: …“:
  - „Schutz: Werkzeug“: die Werkzeug-Muster, ausgenommen die Frei-Muster. Vorbei darf `werkzeug-verantwortliche`.
    `#Handbuch.html` ist nicht gesperrt (automatische Teile, Commit von GitHub), das von Hand Geschriebene prüft
    `pruefen.py` nach dem Push.
  - „Schutz: <team>“ je Team: seine Klassen (`Unterricht/<Klasse>/`) und Fächer (`Unterricht/*/<Fach>/`),
    ausgenommen die Frei-Muster und in den eigenen Klassen die Fächer anderer Teams. Vorbei dürfen das Team und
    `werkzeug-verantwortliche`.
  - „Schutz: main“: kein Force-Push, kein Löschen von `main`, für alle.
- **Wie es wirkt** (geprobt am 15.11.2026): auf allen Branches, auch für Commits über die GitHub-Webseite und für
  den Commit von GitHub selbst (der ändert nur Handbuch und Vorschau, beides ist frei). Groß- und Kleinschreibung
  der Pfade spielt keine Rolle. Ein Push wird **als Ganzes** abgewiesen, auch das Erlaubte darin
  („GH013: Repository rule violations“, „File path is restricted“, darunter die Dateien): `abschluss.md`.
  Ein Merge-Commit nach `git pull` ohne Rebase, der fremde Werkzeugänderungen von `main` mitbringt, geht durch.
- **Owner der Organisation** kommen an den Push-Rulesets vorbei, Admins des Repos können Rulesets ändern.
- **Prüfen:** `python .claude/gemeinsam/scripts/schutz-github.py --pruefen` vergleicht GitHub mit `schutz.txt`.
  Der Workflow macht das in jedem Lauf (Schritt „Rulesets passen zu schutz.txt?“, liest mit dem `GITHUB_TOKEN`):
  Fehlt ein Ruleset, ist eines abgeschaltet oder weicht es ab, wird nichts zugestellt. Wer vorbei darf, zeigt
  GitHub nur Admins: Das vergleicht nur `--pruefen` am Rechner eines Admins.
- **Notfall:** Sperrt ein Ruleset alle oder GitHub selbst aus, stellt ein Admin es unter Settings → Rules →
  Rulesets auf „Disabled“. Der nächste Lauf ist dann rot (gewollt), bis `--anwenden` wieder gelaufen ist.

### Auf GitHub (nach dem Push)
- **Zweite Sicherung:** Werkzeug- und Abteilungsschutz greifen hier nur noch, wenn ein Ruleset fehlt oder jemand
  daran vorbei durfte. Notizschutz und das von Hand Geschriebene im Handbuch prüft weiter nur diese Stufe. Sie ist
  jetzt verlässlich, weil Workflow und `pruefen.py` selbst gesperrt sind.
- **Jeder Push zählt für sich:** GitHub prüft alles seit dem letzten grünen Lauf, aber jeden Push einzeln: Was er
  geändert hat, muss die Person dürfen, die ihn gepusht hat. Der Workflow liefert dafür Commit und Person jedes Laufs
  seit dem letzten grünen (`BYCS_PUSHES`). Es zählt nur, was sich wirklich geändert hat: Wurde eine Änderung
  zurückgenommen, ist sie erledigt. Ein späterer Push gibt nichts frei, auch nicht von Werkzeug-Verantwortlichen.
- **Was dann angehalten wird:** Werkzeug ohne Werkzeugrecht, unlesbare Teams und alle übrigen Fehler (Steckbrief,
  Version, Test-XML) halten **alles** an, auch das Unterrichtsmaterial aus demselben Lauf.
- **Zurückhalten:** Ein Fehler im Abteilungs- oder Notizschutz hält nur das Betroffene an: den Themen- oder
  Test-Ordner (er wird als Ganzes gebaut), dazu jeden Kurs, der etwas daraus mitliefert (`ToDo/` wird ohnehin nie
  zugestellt). Alles andere wird zugestellt, der Lauf endet trotzdem rot ("Zurückgehalten, nicht zugestellt: …").
  Bis zur Freigabe stellt jeder neue Lauf das Übrige noch einmal zu (der Download-Link bleibt gleich). Technik:
  `pruefen.py --zurueckhalten <Datei>` schreibt die Pfade, `paket-zustellen.py --ohne <Datei>` lässt sie aus.
- **Freigeben:** nur, wer den Lauf wiederholt (Actions → Lauf → Re-run jobs; zählt ab dem zweiten Versuch), nachdem
  er sich die Änderung angesehen hat: ein Mitglied des genannten Teams für den Bereich dieses Teams,
  Werkzeug-Verantwortliche für alles. Oder die Änderung wird zurückgenommen (`git revert`) und gepusht. Wiederholt
  jemand ohne Recht den Lauf (z. B. weil ein Kurs auf einen Download-Link wartet), schadet das nicht, gibt aber auch
  nichts frei.
- **Lauf von Hand:** nur Werkzeug-Verantwortliche (`pruefen.py --von-hand`, siehe "GitHub: prüfen, bauen, zustellen").
- **Zugang zu den Teams:** Die Mitglieder liest `pruefen.py` im Lauf über eine GitHub-App der Organisation (nur
  Leserecht „Members“, Secrets `TEAM_APP_ID` und `TEAM_APP_KEY`), einmal je Team, Unterteams eingeschlossen. Fehlt der
  Zugang oder ein Team, ist der Lauf rot („konnte die Mitglieder des Teams … nicht lesen“) und nichts wird zugestellt.
  Neu einrichten: Organisation → Settings → Developer settings → GitHub Apps → New GitHub App (Webhook aus,
  Organization permissions → Members: Read-only, nur für diese Organisation), „Generate a private key“, „Install App“
  für B2-NBG, dann App-ID und Inhalt der `.pem`-Datei als Secrets eintragen (`gh secret set TEAM_APP_KEY --env zustellung < Datei.pem`).
  Der Schlüssel kommt nie ins Repo und nie in den Chat.

### Einrichten
- **Neue Kolleg/innen:** auf GitHub in das Team ihrer Abteilung und ihrer Fachbereiche aufnehmen, mehr nicht.
- **Neues Team:** als Unterteam von `material-autor-innen` anlegen (sichtbar, nicht geheim) und in `schutz.txt`
  zuordnen. Neue Klasse oder neues Fach: Werkzeug-Verantwortliche tragen die Zeile in `schutz.txt` ein.
- **Nach jeder Änderung an `schutz.txt`:** committen, dann `python .claude/gemeinsam/scripts/schutz-github.py
  --anwenden`, dann pushen (so ist der Lauf gleich grün). `--anwenden` braucht Admin-Recht am Repo und zeigt, was es
  anlegt, ersetzt oder löscht; andere Rulesets fasst es nicht an. `--zeigen` gibt die Rulesets nur aus.
- **Neue Werkzeug-Verantwortliche:** ins Team `werkzeug-verantwortliche` aufnehmen. Jeden ihrer Rechner richten sie
  einmal selbst ein (`git config bycs.werkzeug ja`), damit sie auch ohne Verbindung zu GitHub arbeiten können.
- **Eigene Skills:** Jede und jeder darf sich Skills bauen, aber im eigenen Ordner `~/.claude/skills/<Name>/SKILL.md`
  (gilt dann in allen Projekten dieses Rechners), nie unter `.claude/skills/` im Projekt. Bewährt sich einer,
  übernehmen ihn Werkzeug-Verantwortliche ins Projekt. Eigene Vorlagen für Seiten gibt es noch nicht (Seiten werden
  gegen die beiden Vorlagen geprüft).

### Grenzen
- Rulesets sperren Pfade, keinen Inhalt: Notizschutz und das von Hand Geschriebene im Handbuch bleiben eine
  Nachkontrolle (erkennen und zurückhalten, die Änderung liegt trotzdem auf `main`).
- Rulesets ändern (`--anwenden`, Notfall) kann nur, wer Admin am Repo ist. Seit dem 15.11.2026 sind das zwei Personen, beide
  auch Owner der Organisation (Vertretung).
- Wer vorbei darf, bestimmen die Teams: Team-Maintainer können Mitglieder aufnehmen.
- Ein neuer Branch auf einem **alten Commit** bringt keine geänderte Datei mit und wird nicht abgewiesen. Von dort
  ließe sich ein älterer Stand des Workflows von Hand starten. Er bekommt aber keine Secrets und kann nichts
  zustellen: Seit dem 15.11.2026 liegen sie im Environment `zustellung`, das nur `main` nutzen darf.
- Die Team-Lizenz hat 8 Plätze, alle belegt: Neue Kolleginnen und Kollegen brauchen einen Platz.
- Kein `CODEOWNERS`: Ohne Pull Requests zeigt es nur an, wer zuständig ist. Das steht in `schutz.txt`.
- Bei älteren Notizen ohne Login zählt der Name (`user.name`), den jede und jeder frei einstellen kann. Wer
  gepusht hat, steht aber immer im Lauf; mit dem Login nachgetragen ist auch das sicher.

## Keine Git-Hooks mehr
Was früher die Hooks taten, macht GitHub nach dem Push (siehe oben) und Claude vor dem Commit (`pruefen.py --erneuern`,
`abschluss.md`). Auf älteren Rechnern zeigt `core.hooksPath` noch auf den gelöschten Ordner `.githooks`; das schadet
nicht. Aufräumen: `git config --unset core.hooksPath`.

## Lehrkraft-Passwort
- Der Hash steht in `.claude/gemeinsam/data/solution-password.txt` (Zeile `hash=`, nicht im Repo).
- Fehlt die Datei: die Lehrkraft bitten, `python .claude/gemeinsam/scripts/pw-hash.py` (am Mac `python3`) selbst
  auszuführen, ohne Argument (das Passwort wird verdeckt abgefragt; als Argument lehnt das Skript es ab). Das Passwort wird nie im Chat eingegeben und steht nie im Handbuch. Bis dahin bleibt die
  Meta-Angabe leer, die Lösungen bleiben gesperrt.

## Im Browser arbeiten (Claude Code im Web)
- **Dev Container / Codespaces:** gibt es in diesem Repo nicht und sind nie Voraussetzung. Keinen `.devcontainer/` anlegen.
- **Claude Code im Web** (claude.ai/code): Terminal und Python sind da; die Passwortdatei fehlt (Lösungen bekommen
  dann keinen Hash: vor dem Fertigmelden sagen). Lässt die Sitzung den Push auf `main` nicht zu: CLAUDE.md, Abschnitt Git.
  Der Push kommt bei GitHub unter dem eigenen Konto an (geprüft 15.11.2026), Rulesets und Teams gelten wie am
  Rechner. Die Prüfung vor dem Commit kennt dort aber weder Login noch Teams (keine gespeicherte Git-Anmeldung,
  Git-Name „Claude“): Werkzeug und neue Notizen gehen aus einer Cloud-Sitzung nicht.
- **Grenzen im Browser:** Seiten öffnet man über die Vorschau statt per Doppelklick; der Teamordner fehlt (Kurse und
  Tests zum Wiederherstellen in SharePoint im Browser herunterladen); ohne installierten Browser läuft nur die statische Prüfung.
- **vscode.dev / github.dev** (Taste `.` im Repo): nur Lesen und kleine Textkorrekturen, kein Terminal, kein Claude-Bau.
  Auch solche Korrekturen prüft GitHub nach dem Push.

## Skripte
Python 3, nur Standardbibliothek (am Mac `python3`), oder `sh`. Kein PowerShell. Für den Browser-Test braucht
`seite-pruefen.py` einen installierten Browser (Edge, Chrome oder Chromium); Read braucht für PDFs Poppler (`pdftoppm`).
