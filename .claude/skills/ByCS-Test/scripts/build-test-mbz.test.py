#!/usr/bin/env python3
"""Rundlauf-Test für build-test-mbz.py.

Baut aus der Quiz-XML des Praxismoduls 3D-Druck eine Test-Sicherung und vergleicht sie inhaltlich mit
templates/Test-Vorlage.mbz (die ByCS hat diesen Test aus genau diesen Fragen erzeugt): Fragetyp, Texte,
Antworten, Punkte, Rückmeldungen, Optionen, Slots, Seiten, Notenstufen und alle Testeinstellungen.
Ein Feld gilt als gleich, wenn es mit einer der Fassungen in der Vorlage übereinstimmt (Version 1 = Import,
Version 2 = in der ByCS nachbearbeitet). IDs, Zeitstempel und <p>-Hüllen zählen nicht.

  python .claude/skills/ByCS-Test/scripts/build-test-mbz.test.py
"""

from __future__ import annotations

import re
import subprocess
import sys
import tarfile
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

SKILL = Path(__file__).resolve().parent.parent
REPO = SKILL.parent.parent.parent
VORLAGE = SKILL / "templates" / "Test-Vorlage.mbz"
QUIZ = REPO / "Unterricht/ALLE/BerHan/M-3D-Druck/Test-Praxismodul-3D-Druck/Fragen-Praxismodul-3D-Druck.xml"
SKRIPT = SKILL / "scripts" / "build-test-mbz.py"

UNWICHTIG = {"stamp", "timecreated", "timemodified", "createdby", "modifiedby", "parent", "question", "sequence"}
VERWEISE = {"trueanswer", "falseanswer", "answer"}  # zeigen per ID auf eine Antwort


def lade(pfad: Path) -> dict[str, ET.Element]:
    with tarfile.open(pfad, "r:gz") as tar:
        return {m.name: ET.fromstring(tar.extractfile(m).read()) for m in tar.getmembers()
                if m.isfile() and m.name.endswith(".xml")}


def norm(s: str | None) -> str:
    s = (s or "").strip()
    s = re.sub(r"^<p>(.*)</p>$", r"\1", s, flags=re.S)
    return s.strip()


def flach(el: ET.Element, antworten: dict[str, str], pfad: str = "", aus: dict | None = None) -> dict:
    aus = {} if aus is None else aus
    zaehler: dict[str, int] = {}
    for k in el:
        if k.tag in UNWICHTIG:
            continue
        i = zaehler.get(k.tag, 0)
        zaehler[k.tag] = i + 1
        p = f"{pfad}/{k.tag}[{i}]"
        if len(k):
            flach(k, antworten, p, aus)
        else:
            wert = norm(k.text)
            if k.tag in VERWEISE and wert in antworten:
                wert = "→" + antworten[wert]
            aus[p] = wert
    return aus


def frage_flach(q: ET.Element, alle: dict[str, ET.Element]) -> dict:
    antworten = {a.get("id"): norm(a.findtext("answertext")) for a in q.iter("answer") if a.get("id")}
    d = flach(q, antworten)
    for ma in q.iter("multianswer"):
        for i, uid in enumerate(ma.findtext("sequence").split(",")):
            u = alle[uid]
            ua = {a.get("id"): norm(a.findtext("answertext")) for a in u.iter("answer") if a.get("id")}
            for k, v in flach(u, ua).items():
                d[f"/teilfrage[{i}]{k}"] = v
    return d


def fassungen(fragen_xml: ET.Element) -> list[list[dict]]:
    """Je Hauptfrage (parent 0) eine Liste der Fassungen, flach gemacht, in Reihenfolge der Einträge."""
    alle = {q.get("id"): q for q in fragen_xml.iter("question")}
    liste = []
    for e in fragen_xml.iter("question_bank_entry"):
        versionen = e.findall("question_version/question_versions")
        erste = versionen[0].find("questions/question")
        if erste.findtext("parent") != "0":
            continue
        versionen.sort(key=lambda v: -int(v.findtext("version")))
        liste.append((e.get("id"), [frage_flach(v.find("questions/question"), alle) for v in versionen]))
    return liste


def vergleiche(name: str, neu: dict, alt: list[dict]) -> list[str]:
    fehler = []
    for k in sorted(set(neu) | set().union(*alt)):
        if not any(neu.get(k) == a.get(k) for a in alt):
            fehler.append(f"{name}{k}: neu {neu.get(k)!r}, Vorlage {[a.get(k) for a in alt]!r}")
    return fehler


def main() -> int:
    fehler: list[str] = []
    with tempfile.TemporaryDirectory() as tmp:
        ziel = Path(tmp) / "Test.mbz"
        r = subprocess.run([sys.executable, str(SKRIPT), str(QUIZ), "--thema", "Praxismodul 3D-Druck", "--zeit", "20",
                            "--out", str(ziel), "--keine-anleitung"], capture_output=True, text=True, encoding="utf-8")
        if r.returncode != 0:
            print(r.stdout, r.stderr)
            print("FEHLER: Bau oder Eigenprüfung gescheitert.")
            return 1
        neu, alt = lade(ziel), lade(VORLAGE)

    # Fragen
    f_neu, f_alt = fassungen(neu["questions.xml"]), fassungen(alt["questions.xml"])
    if len(f_neu) != len(f_alt):
        fehler.append(f"Anzahl Fragen: neu {len(f_neu)}, Vorlage {len(f_alt)}")
    for (_, [n]), (_, a) in zip(f_neu, f_alt):
        titel = n.get("/name[0]", "?")
        fehler += vergleiche(f"[{titel}]", {k: v for k, v in n.items() if k != "/name[0]"},
                             [{k: v for k, v in x.items() if k != "/name[0]"} for x in a])
        if titel not in [x.get("/name[0]") for x in a]:
            fehler.append(f"[{titel}] Name kommt in der Vorlage nicht vor")

    # Testeinstellungen
    qn = next(v for k, v in neu.items() if k.endswith("/quiz.xml")).find("quiz")
    qa = next(v for k, v in alt.items() if k.endswith("/quiz.xml")).find("quiz")
    ohne = {"name", "timecreated", "timemodified", "question_instances", "sections", "feedbacks", "quiz_grade_items",
            "overrides", "grades", "attempts", "subplugin_quizaccess_seb_quiz"}
    for k in qa:
        if k.tag not in ohne and norm(k.text) != norm(qn.findtext(k.tag)):
            fehler.append(f"Einstellung {k.tag}: neu {qn.findtext(k.tag)!r}, Vorlage {k.text!r}")
    seb_n = qn.find("subplugin_quizaccess_seb_quiz/quizaccess_seb_quizsettings")
    for k in qa.find("subplugin_quizaccess_seb_quiz/quizaccess_seb_quizsettings"):
        if k.tag not in {"quizid", "cmid", "timecreated"} and norm(k.text) != norm(seb_n.findtext(k.tag)):
            fehler.append(f"SEB {k.tag}: neu {seb_n.findtext(k.tag)!r}, Vorlage {k.text!r}")
    slots = lambda q: [(i.findtext("slot"), i.findtext("page"), i.findtext("maxmark"))
                       for i in q.findall("question_instances/question_instance")]
    if slots(qn) != slots(qa):
        fehler.append(f"Slots/Seiten/Punkte: neu {slots(qn)}, Vorlage {slots(qa)}")
    stufen = lambda q: [(f.findtext("feedbacktext"), f.findtext("mingrade"), f.findtext("maxgrade"))
                        for f in q.findall("feedbacks/feedback")]
    if stufen(qn) != stufen(qa):
        fehler.append(f"Notenstufen: neu {stufen(qn)}, Vorlage {stufen(qa)}")
    if qn.findtext("name") != "Test - Praxismodul 3D-Druck":
        fehler.append(f"Testname: {qn.findtext('name')!r}")

    # Bewertung
    gn = next(v for k, v in neu.items() if k.endswith("/grades.xml")).find("grade_items/grade_item")
    ga = next(v for k, v in alt.items() if k.endswith("/grades.xml")).find("grade_items/grade_item")
    for tag in ("grademax", "gradepass", "gradetype", "itemmodule"):
        if gn.findtext(tag) != ga.findtext(tag):
            fehler.append(f"Bewertung {tag}: neu {gn.findtext(tag)!r}, Vorlage {ga.findtext(tag)!r}")

    for f in fehler:
        print("FEHLER:", f)
    print(f"{len(f_neu)} Fragen, Einstellungen, Slots, Notenstufen verglichen: "
          + ("alles gleich." if not fehler else f"{len(fehler)} Abweichung(en)."))
    return 1 if fehler else 0


if __name__ == "__main__":
    sys.exit(main())
