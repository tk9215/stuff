#!/usr/bin/env python3
"""Legt neben eine Moodle-XML-Quizdatei eine Vorschau.html (ByCS-Look, offline, per Doppelklick).

Die Vorschau zeigt das Quiz ohne Upload: Schülersicht (beantworten, "Prüfen", Rückmeldung, Punkte)
und Review-Sicht (alle Lösungen, Rückmeldungen, Hinweise auf typische Fehler).
Grundlage ist die Vorlage ../templates/quiz-vorschau.html; die XML wird darin eingebettet (Base64).
Vorschau.html nie von Hand ändern, sondern neu erzeugen.

Aufruf (am Mac python3):
  python .claude/skills/ByCS-Fragenersteller/scripts/quiz-vorschau.py <Quiz.xml> [...]   Vorschau.html daneben schreiben
  python .claude/skills/ByCS-Fragenersteller/scripts/quiz-vorschau.py <Quiz.xml> --ziel <Datei.html>   woanders hin schreiben
  python .claude/skills/ByCS-Fragenersteller/scripts/quiz-vorschau.py --alle      alle Unterricht/**/*-Quiz/*.xml und Unterricht/**/Test-*/*.xml
  python .claude/skills/ByCS-Fragenersteller/scripts/quiz-vorschau.py --pruefen   nur prüfen, ob jede Vorschau aktuell ist
  Nach jedem Push erneuert GitHub die Vorschau zu jeder geänderten Quiz-XML (bei geänderter Vorlage alle) und committet sie
  (.claude/gemeinsam/scripts/pruefen.py --erneuern, Workflow "Bauen und zustellen"). Vor dem Commit macht Claude dasselbe.

Die allgemeine Vorschau für jede beliebige XML: die Vorlage selbst per Doppelklick öffnen und die Datei hineinziehen.
"""
from __future__ import annotations
import base64
import html
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

HIER = Path(__file__).resolve().parent
REPO = HIER.parents[3]
VORLAGE = HIER.parent / "templates" / "quiz-vorschau.html"
VORLAGE_REL = VORLAGE.relative_to(REPO).as_posix()
NAME = "Vorschau.html"
sys.dont_write_bytecode = True
sys.path.insert(0, str(REPO / ".claude" / "gemeinsam" / "scripts"))
import unterrichtsmaterial  # noqa: E402  (Namensregel: welche Ordner Quiz oder Test sind)

DATEN = re.compile(r'<script type="text/plain" id="quizdaten" data-datei="[^"]*">.*?</script>', re.S)


class QuizFehler(Exception):
    pass


def ist_quiz(rel: str) -> bool:
    """Quiz-XML im Ordnerschema: Unterricht/.../<Thema>-Quiz/<Datei>.xml oder Test-Ordner Unterricht/.../Test-<Thema>/<Datei>.xml"""
    p = Path(rel)
    return rel.startswith("Unterricht/") and p.suffix.lower() == ".xml" and unterrichtsmaterial.art(p.parent.name) in ("Quiz", "Test")


def bauen(xml_datei: Path) -> str:
    daten = xml_datei.read_bytes().replace(b"\r\n", b"\n")  # gleiche Vorschau unter Windows und macOS
    try:
        wurzel = ET.fromstring(daten)
    except ET.ParseError as e:
        zeile = e.position[0] if hasattr(e, "position") else "?"
        raise QuizFehler(f"{xml_datei}: XML fehlerhaft (Zeile {zeile}): {e}. So scheitert auch der Import in die ByCS.")
    if wurzel.tag != "quiz":
        raise QuizFehler(f"{xml_datei}: keine Moodle-XML-Quizdatei (Wurzelelement <{wurzel.tag}> statt <quiz>).")
    vorlage = VORLAGE.read_text(encoding="utf-8")
    b64 = base64.b64encode(daten).decode("ascii")
    zeilen = "\n".join(b64[i:i + 120] for i in range(0, len(b64), 120))
    block = (f'<script type="text/plain" id="quizdaten" data-datei="{html.escape(xml_datei.name)}">\n'
             f'{zeilen}\n</script>')
    seite, n = DATEN.subn(lambda _m: block, vorlage, count=1)
    if n != 1:
        raise QuizFehler(f"{VORLAGE}: Platzhalter <script id=\"quizdaten\"> nicht gefunden.")
    titel = html.escape("Vorschau " + xml_datei.stem)
    return seite.replace("<title>Quiz-Vorschau</title>", f"<title>{titel}</title>", 1)


def schreiben(xml_datei: Path, ziel: Path | None = None) -> Path:
    ziel = ziel or xml_datei.with_name(NAME)
    neu = bauen(xml_datei)
    if not ziel.exists() or ziel.read_text(encoding="utf-8") != neu:
        with open(ziel, "w", encoding="utf-8", newline="") as f:   # write_text(newline=) gibt es erst ab Python 3.10 (Mac: 3.9)
            f.write(neu)
    return ziel


def alle_quizze() -> list[Path]:
    return sorted(p for p in (REPO / "Unterricht").rglob("*.xml") if ist_quiz(p.relative_to(REPO).as_posix()))


def git(*args: str) -> list[str]:
    r = subprocess.run(["git", "-c", "core.quotePath=false", *args], cwd=REPO, capture_output=True, text=True, encoding="utf-8")
    return [z for z in r.stdout.split("\0") if z] if "-z" in args else [z for z in r.stdout.splitlines() if z]


def main(argv: list[str]) -> int:
    ziel = None
    if "--ziel" in argv:
        i = argv.index("--ziel")
        if i + 1 >= len(argv):
            print("Nach --ziel fehlt der Dateiname.", file=sys.stderr)
            return 2
        ziel = Path(argv[i + 1])
        del argv[i:i + 2]
    pruefen = "--pruefen" in argv
    if "--alle" in argv or pruefen:
        dateien = alle_quizze()
    else:
        dateien = [Path(a) for a in argv if not a.startswith("--")]
    if not dateien:
        print(__doc__)
        return 2
    if ziel and len(dateien) != 1:
        print("--ziel geht nur mit genau einer XML-Datei.", file=sys.stderr)
        return 2
    fehler = 0
    for x in dateien:
        try:
            if pruefen:
                v = x.with_name(NAME)
                if not v.exists() or v.read_text(encoding="utf-8") != bauen(x):
                    print(f"VERALTET oder fehlt: {v}")
                    fehler += 1
                continue
            v = schreiben(x, ziel)
            print(f"Doppelklick auf {v} zum Öffnen.")
        except (QuizFehler, OSError) as e:
            print(f"FEHLER: {e}", file=sys.stderr)
            fehler += 1
    if pruefen and not fehler:
        print(f"Alle {len(dateien)} Vorschau-Dateien sind aktuell.")
    return 1 if fehler else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
