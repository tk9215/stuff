#!/usr/bin/env python3
"""Baut aus einem Kursplan eine Moodle-Kurssicherung (.mbz) und prüft sie danach.

  python .claude/skills/Baue-Kurs/scripts/build-mbz.py --plan <Kursname oder Pfad zum Kursplan> [--out <datei.mbz>]
  python .claude/skills/Baue-Kurs/scripts/build-mbz.py --pruefen <datei.mbz>
  python .claude/skills/Baue-Kurs/scripts/build-mbz.py --links <ByCS-Sicherung.mbz>

Aufbau wie die Beispielsicherung (ByCS, Moodle 5.2.4): Abschnitt 0 für Allgemeines,
danach je ein Abschnitt pro Blockwoche. Aktivitäten: Datei (Ressource), SCORM-Paket (mitgeliefert
oder über einen Download-Link, in Moodle "localsync"; "link": "linkseite" im Plan holt ihn von der Linkseite) und Test (Test-Aktivität aus dem Skill ByCS-Test).
Der Kursplan liegt unter Unterricht/<Klasse>[/<Fach>]/Kurs-<Klasse>[-<Fach>][-<Zusatz>].json (die Quelle, in Git), die Sicherung
entsteht als BYCS-SYNC/Kurse/<Klasse>[/<Fach>]/<gleicher Name>.mbz (ohne Datum, nicht in Git: GitHub baut sie nach dem Push und stellt sie in den
Teamordner zu; lokal gebaut nur zum Ansehen, im Temp-Ordner statt im Repo, unterrichtsmaterial.gebaut). Pfade im Plan gelten ab dem Projektordner (BYCS-SYNC/..., Unterricht/...).
Tests behalten das Kennwort aus ihrer Test-.mbz (Platzhalter "Bitte_neu_vergeben"): Das echte Kennwort vergibt die
Lehrkraft nach dem Wiederherstellen in der ByCS. Ein Kennwort im Plan gibt es nicht.
Nur Standardbibliothek. Benutzerdaten, Einschreibungen und Kurspasswörter werden nie übernommen.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import io
import json
import mimetypes
import posixpath
import random
import re
import sys
import tarfile
import time
import urllib.parse
import uuid
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "gemeinsam" / "scripts"))
import unterrichtsmaterial  # noqa: E402  (.claude/gemeinsam/scripts: Namensregel)
import linkseite  # noqa: E402  (Download-Links der Lernpakete von der Linkseite)
from mbz import Archiv, IdGen  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(unterrichtsmaterial.ROOT)
mimetypes.add_type("text/html", ".html")
mimetypes.add_type("application/pdf", ".pdf")
mimetypes.add_type("application/javascript", ".js")
mimetypes.add_type("application/zip", ".zip")

NULL = "$@NULL@$"
XML_KOPF = '<?xml version="1.0" encoding="UTF-8"?>\n'
# SHA-1 eines leeren Inhalts: Moodle nutzt ihn für Verzeichniseinträge in files.xml.
LEERER_HASH = "da39a3ee5e6b4b0d3255bfef95601890afd80709"
DISPLAYOPTIONS = 'a:2:{s:10:"printintro";i:1;s:8:"showtype";i:1;}'

# Werte aus der Beispielsicherung (ByCS, Moodle 5.2.4). Bei einer neuen Moodle-Version
# mit einer frischen Sicherung vergleichen.
VORLAGE = {
    "wwwroot": "https://lernplattform.bycs.de",
    "site_hash": "6aa9a12f353641854c7eaa8a0fcd932f",
    "moodle_version": "2026042004",
    "moodle_release": "5.2.4 (Build: 20261005)",
    "backup_version": "2026042000",
    "backup_release": "5.2",
    "kategorie_id": 43224,
    "kategorie": "Städt. Berufsschule 2 Nürnberg",
    "besitzer_id": 946991,  # Lehrkraft-Konto als Eigentümer der Dateien
    "rolle_lehrkraft": 3,
    "rolle_schueler": 5,
    "bloecke": [("ai_control", "2025120400"), ("ai_chat", "2026102300")],
    # Kurseinstellungen der Lehrkraft (Sicherung "Modul 3D-Druck BVJ/BIK" vom 08.11.2026, 23:58):
    "gruppenmodus": 1,             # getrennte Gruppen
    "gruppenmodus_erzwingen": 1,
    "abschlussbedingungen_zeigen": 0,
    # Notenskala im Kurs: Note ab Prozent der Höchstpunktzahl, Anzeige "Note (Prozent)", Punkte und Bereich ohne Nachkommastellen.
    "notenstufen": [(92, "1"), (81, "2"), (67, "3"), (50, "4"), (30, "5"), (0, "6")],
    "notenanzeige": 32,
    "bereich_nachkommastellen": 0,
    "nachkommastellen": 0,         # Bewertungen im ganzen Kurs ohne Komma (Kurssumme ist ein Mittelwert)
    "scorm_noten_verborgen": 1,    # Lernpakete zählen nicht sichtbar in den Bewertungen, nur Tests
}

# SCORM-Einstellungen wie im Skill Baue-Lernpaket verlangt: 1 Versuch, kein neuer Versuch erzwungen, nicht sperren,
# Höchstnote, maximal 100, bestanden ab 70, Anzeige in neuem Fenster. Abschluss: 4 = abgeschlossen, 2 = bestanden.
# Anzeige und Navigation wie im Ethikkurs der Lehrkraft (ByCS-Sicherung "MGF10 Eth 26/27").
# Mit Link: Moodle lädt das Paket bei jedem Start neu vom Link (updatefreq 3). Korrekturen kommen so ohne
# neue Wiederherstellung im Kurs an.
SCORM_ABSCHLUSS = {"abgeschlossen": 4, "bestanden": 2}
SCORM_BESTEHEN = 70

ROOT_EINSTELLUNGEN = [
    ("users", "0"), ("anonymize", "0"), ("role_assignments", "0"), ("activities", "1"),
    ("blocks", "1"), ("files", "1"), ("filters", "1"), ("comments", "0"), ("badges", "1"),
    ("calendarevents", "1"), ("userscompletion", "0"), ("logs", "0"), ("grade_histories", "0"),
    ("groups", "1"), ("competencies", "0"), ("customfield", "1"), ("contentbankcontent", "1"),
    ("xapistate", "0"), ("legacyfiles", "1"),
]

# Leere Standarddateien, wie sie Moodle in jeder Sicherung ablegt.
INFOREF_LEER = XML_KOPF + "<inforef>\n</inforef>\n"
ROLLEN_LEER = XML_KOPF + "<roles>\n  <role_overrides>\n  </role_overrides>\n  <role_assignments>\n  </role_assignments>\n</roles>\n"
FILTER_LEER = XML_KOPF + "<filters>\n  <filter_actives>\n  </filter_actives>\n  <filter_configs>\n  </filter_configs>\n</filters>\n"
KALENDER_LEER = XML_KOPF + "<events>\n</events>\n"
NOTEN_LEER = XML_KOPF + "<grade_history>\n  <grade_grades>\n  </grade_grades>\n</grade_history>\n"
AKTIVITAET_NOTEN_LEER = XML_KOPF + "<activity_gradebook>\n  <grade_items>\n  </grade_items>\n  <grade_letters>\n  </grade_letters>\n</activity_gradebook>\n"
ROLLEN_DEFINITION = XML_KOPF + """<roles_definition>
  <role id="3">
    <name>Lehrer</name>
    <shortname>editingteacher</shortname>
    <nameincourse>$@NULL@$</nameincourse>
    <description>&lt;p&gt;Teachers can do anything within a course, including changing the activities and grading students.&lt;/p&gt;</description>
    <sortorder>7</sortorder>
    <archetype>editingteacher</archetype>
  </role>
  <role id="5">
    <name>Schüler</name>
    <shortname>student</shortname>
    <nameincourse>$@NULL@$</nameincourse>
    <description>&lt;p&gt;Students generally have fewer privileges within a course.&lt;/p&gt;</description>
    <sortorder>11</sortorder>
    <archetype>student</archetype>
  </role>
</roles_definition>
"""
STATISCH_MODUL = {
    "calendar.xml": KALENDER_LEER,
    "filters.xml": FILTER_LEER,
    "grade_history.xml": NOTEN_LEER,
    "roles.xml": ROLLEN_LEER,
}


def t(wert) -> str:
    """Wert für XML-Text: None wird zu NULL, sonst maskiert (&, <, >)."""
    return NULL if wert is None else escape(str(wert))


def fehler(text: str):
    raise SystemExit(f"Fehler: {text}")


def finde(text: str) -> Path:
    """Pfad aus dem Kursplan: ab dem Projektordner (BYCS-SYNC/..., Unterricht/...), sonst wie angegeben."""
    text = re.sub(r"^/([a-zA-Z])/", r"\1:/", text)  # Git-Bash-Schreibweise /c/Ordner in C:/Ordner umwandeln
    pfad = Path(text)
    if not pfad.is_absolute() and text.replace("\\", "/").startswith("BYCS-SYNC/"):
        return Path(unterrichtsmaterial.gebaut(text))   # Gebautes liegt nur auf GitHub im Projektordner, sonst im Temp-Ordner
    if not pfad.is_absolute() and (ROOT / pfad).exists():
        return ROOT / pfad
    return pfad


def berlin_mitternacht(datum_text: str) -> int:
    """Unix-Zeit für Mitternacht des Datums in Berlin (MEZ/MESZ, EU-Umstellung)."""
    tag = dt.date.fromisoformat(datum_text)
    sommer = letzter_sonntag(tag.year, 3) < tag <= letzter_sonntag(tag.year, 10)
    versatz = 2 if sommer else 1
    utc = dt.datetime(tag.year, tag.month, tag.day, tzinfo=dt.timezone.utc) - dt.timedelta(hours=versatz)
    return int(utc.timestamp())


def letzter_sonntag(jahr: int, monat: int) -> dt.date:
    naechster = dt.date(jahr + (monat == 12), monat % 12 + 1, 1)
    letzter = naechster - dt.timedelta(days=1)
    return letzter - dt.timedelta(days=(letzter.weekday() - 6) % 7)


_BAU = None


def baue_lernpaket(text: str) -> None:
    """Lernpakete liegen nicht in Git: vor dem Kursbau frisch aus dem Themenordner bauen (ohne etwas in die Quelle zu schreiben)."""
    global _BAU
    rel = text.replace("\\", "/")
    quelle = unterrichtsmaterial.paket_quelle(rel) if rel.startswith("BYCS-SYNC/Pakete/") else None
    if not quelle or not (ROOT / quelle / "index.html").is_file():
        return
    if _BAU is None:
        import contextlib
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "build_scorm", Path(__file__).resolve().parents[2] / "Baue-Lernpaket" / "scripts" / "build-scorm.py")
        _BAU = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_BAU)
        _BAU.contextlib = contextlib
    aus = io.StringIO()
    try:
        with _BAU.contextlib.redirect_stdout(aus):
            _BAU.bauen(str(ROOT / quelle), nur_packen=True)
    except _BAU.BauFehler as f:
        fehler(f"Lernpaket {quelle}: {f}")


def lade_datei(text: str, name: str | None = None) -> dict:
    baue_lernpaket(text)
    pfad = finde(text)
    if not pfad.is_file():
        fehler(f"Datei nicht gefunden: {text}")
    daten = pfad.read_bytes()
    if not daten:
        fehler(f"Datei ist leer: {text}")
    name = name or pfad.name
    mime = mimetypes.guess_type(name)[0] or "application/octet-stream"
    return {"name": name, "daten": daten, "mime": mime}


def lokal(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def kinder(el: ET.Element, name: str) -> list[ET.Element]:
    return [c for c in el if lokal(c.tag) == name]


def attr(el: ET.Element, name: str, standard=None):
    for k, v in el.attrib.items():
        if lokal(k).lower() == name.lower():
            return v
    return standard


def lies_scorm(daten: bytes, quelle: str) -> dict:
    """Liest ein SCORM-Paket mit genau einem Lernobjekt (wie es der Skill Baue-Lernpaket baut)."""
    try:
        paket = zipfile.ZipFile(io.BytesIO(daten))
    except zipfile.BadZipFile:
        fehler(f"{quelle}: kein ZIP-Archiv")
    namen = [n for n in paket.namelist() if not n.endswith("/")]
    if "imsmanifest.xml" not in namen:
        fehler(f"{quelle}: imsmanifest.xml fehlt ganz oben im Paket")
    wurzel = ET.fromstring(paket.read("imsmanifest.xml"))
    schema = " ".join((e.text or "") for e in wurzel.iter() if lokal(e.tag) == "schemaversion")
    version = "SCORM_13" if "2004" in schema or "CAM 1.3" in schema else "SCORM_1.2"
    orgs = [e for e in wurzel.iter() if lokal(e.tag) == "organizations"][0]
    alle_orgs = kinder(orgs, "organization")
    org = next((o for o in alle_orgs if o.get("identifier") == orgs.get("default")), alle_orgs[0])
    items = kinder(org, "item")
    if len(items) != 1 or kinder(items[0], "item"):
        fehler(f"{quelle}: nur Pakete mit genau einem Lernobjekt werden unterstützt")
    item = items[0]
    ressourcen = {r.get("identifier"): r for r in wurzel.iter() if lokal(r.tag) == "resource"}
    ressource = ressourcen.get(item.get("identifierref"))
    if ressource is None or (attr(ressource, "scormType", "") or "").lower() != "sco":
        fehler(f"{quelle}: das Lernobjekt verweist auf keine SCO-Ressource")
    start = urllib.parse.unquote(ressource.get("href", ""))
    if start not in namen:
        fehler(f"{quelle}: Startdatei {start} fehlt im Paket")
    ziel = next((e for e in item.iter() if lokal(e.tag) == "primaryObjective"), None)
    mindest = next((e.text for e in item.iter() if lokal(e.tag) == "minNormalizedMeasure"), None)
    return {
        "manifest": wurzel.get("identifier"),
        "version": version,
        "org_id": org.get("identifier"),
        "org_titel": (kinder(org, "title")[0].text if kinder(org, "title") else "") or "",
        "item_id": item.get("identifier"),
        "item_titel": (kinder(item, "title")[0].text if kinder(item, "title") else "") or "",
        "sichtbar": (item.get("isvisible") or "true"),
        "start": start,
        "ziel": None if ziel is None else {
            "id": ziel.get("objectiveID", ""),
            "durch_mass": 1 if (attr(ziel, "satisfiedByMeasure", "false") or "").lower() == "true" else 0,
            "mindest": float(mindest) if mindest else 0.0,
        },
        "inhalt": [(n, paket.read(n)) for n in namen],
    }


def paket_name(link: str) -> str:
    """Dateiname, unter dem Moodle ein Paket von einem Link ablegt (wie in der ByCS-Sicherung)."""
    name = link.split("://", 1)[-1].rsplit("/", 1)[-1]
    return re.sub(r"[\x00-\x1f&<>\"`|':\\/]", "", name) or "paket.zip"


def lies_test(text: str) -> dict:
    """Liest eine Test-Aktivität (.mbz aus dem Skill ByCS-Test oder eine Aktivitätssicherung der ByCS)."""
    pfad = finde(text)
    if not pfad.is_file():
        fehler(f"Test nicht gefunden: {text}")
    dateien: dict[str, bytes] = {}
    try:
        with tarfile.open(pfad, "r:gz") as tar:
            for m in tar.getmembers():
                if m.isfile():
                    dateien[m.name] = tar.extractfile(m).read()
    except tarfile.TarError:
        fehler(f"{text}: keine Moodle-Sicherung (.mbz)")
    if "moodle_backup.xml" not in dateien or "questions.xml" not in dateien:
        fehler(f"{text}: moodle_backup.xml oder questions.xml fehlt")
    mb = ET.fromstring(dateien["moodle_backup.xml"])
    akts = list(mb.iterfind("information/contents/activities/activity"))
    if mb.findtext("information/details/detail/type") != "activity" or len(akts) != 1 \
            or akts[0].findtext("modulename") != "quiz":
        fehler(f"{text}: keine Sicherung genau einer Test-Aktivität (Skill ByCS-Test)")
    if mb.findtext("information/moodle_version") != VORLAGE["moodle_version"]:
        print(f"Hinweis: {pfad.name} stammt aus Moodle {mb.findtext('information/moodle_release')}, "
              f"der Kurs aus {VORLAGE['moodle_release']}.")
    verz = akts[0].findtext("directory")
    akt = {n[len(verz) + 1:]: d for n, d in dateien.items() if n.startswith(verz + "/")}
    for pflicht in ("module.xml", "quiz.xml", "grades.xml", "inforef.xml"):
        if pflicht not in akt:
            fehler(f"{text}: {verz}/{pflicht} fehlt")
    fragen = dateien["questions.xml"].decode("utf-8")
    m = re.search(r"<question_categories>\n?(.*)</question_categories>", fragen, re.S)
    liste = dateien.get("files.xml", b"").decode("utf-8")
    saetze = re.findall(r"[ \t]*<file id=\"\d+\">.*?</file>\n?", liste, re.S)
    blobs = {n: d for n, d in dateien.items() if n.startswith("files/")}
    reserviert = {int(z) for n, d in dateien.items() if n.endswith(".xml")
                  for z in re.findall(r"\b\d{5,10}\b", d.decode("utf-8"))}
    quiz = ET.fromstring(akt["quiz.xml"]).find("quiz")
    return {
        "modul_id": int(akts[0].findtext("moduleid")),
        "name": quiz.findtext("name"),
        "dateien": akt,
        "kategorien": m.group(1) if m else "",
        "datei_saetze": saetze,
        "blobs": blobs,
        "reserviert": reserviert,
    }


def lade_plan(pfad: Path) -> dict:
    plan = json.loads(pfad.read_text(encoding="utf-8"))
    kurs = plan.get("kurs") or {}
    for feld in ("vollname", "kurzname", "startdatum"):
        if not kurs.get(feld):
            fehler(f"Kursplan: 'kurs.{feld}' fehlt.")
    if len(kurs["kurzname"]) > 100 or len(kurs["vollname"]) > 254:
        fehler("Kursplan: Kurzname höchstens 100, Vollname höchstens 254 Zeichen.")
    berlin_mitternacht(kurs["startdatum"])  # prüft das Datumsformat JJJJ-MM-TT

    seitenlinks: dict = {}

    def eintrag(e: dict) -> dict:
        typ = e.get("typ", "datei")
        if typ not in ("datei", "scorm", "test"):
            fehler(f"Kursplan: unbekannter typ '{typ}' (erlaubt: datei, scorm, test)")
        abschluss = e.get("abschluss")
        if abschluss is not None and (typ != "scorm" or abschluss not in SCORM_ABSCHLUSS):
            fehler(f"Kursplan: 'abschluss' gibt es nur bei SCORM ({', '.join(SCORM_ABSCHLUSS)}): {e.get('titel')}")
        if e.get("link") and typ != "scorm":
            fehler(f"Kursplan: 'link' gibt es nur bei SCORM: {e.get('titel')}")
        if e.get("passwort") is not None:
            fehler(f"Kursplan: 'passwort' gibt es nicht mehr ({e.get('titel')}). Der Test behält den Platzhalter "
                   "\"Bitte_neu_vergeben\", das echte Kennwort nach dem Wiederherstellen in der ByCS vergeben.")
        if typ == "test":
            test = lies_test(e["datei"])
            return {
                "typ": "test",
                "titel": e.get("titel") or test["name"],
                "beschreibung": e.get("beschreibung", ""),
                "versteckt": bool(e.get("versteckt")),
                "abschluss": None,
                "voraussetzung": e.get("voraussetzung"),
                "test": test,
            }
        link = e.get("link")
        if link == "linkseite":  # Link nicht im Plan: von der Linkseite holen (einmal je Bau)
            try:
                if not seitenlinks:
                    seitenlinks.update(linkseite.holen())
                link = linkseite.link(e["datei"], seitenlinks)
            except linkseite.LinkFehler as f:
                fehler(f"Kursplan: {e.get('titel') or e['datei']}: {f}")
        if link and not re.fullmatch(r"https://\S+", link):
            fehler(f"Kursplan: 'link' muss eine https-Adresse sein: {e.get('titel')}")
        d = {
            "typ": typ,
            "titel": e.get("titel") or Path(e["datei"]).stem,
            "beschreibung": e.get("beschreibung", ""),
            "versteckt": bool(e.get("versteckt")),
            "abschluss": abschluss,
            "voraussetzung": e.get("voraussetzung"),
            "link": link,
            **lade_datei(e["datei"], e.get("dateiname")),
        }
        if typ == "scorm":
            d["scorm"] = lies_scorm(d["daten"], e["datei"])
            if not e.get("titel") and d["scorm"]["org_titel"]:
                d["titel"] = d["scorm"]["org_titel"]  # Titel aus dem Paket (<title> der Seite), nicht abtippen
        return d

    abschnitte = []
    for a in plan.get("abschnitte", []):
        if not a.get("name"):
            fehler("Kursplan: jeder Abschnitt braucht ein 'name'.")
        abschnitte.append({"name": a["name"], "zusammenfassung": a.get("zusammenfassung", ""),
                           "dateien": [eintrag(e) for e in a.get("dateien", [])]})
    allgemein = [eintrag(e) for e in plan.get("allgemein", [])]
    titel = [e["titel"] for e in allgemein] + [e["titel"] for a in abschnitte for e in a["dateien"]]
    if len(set(titel)) != len(titel):
        fehler("Kursplan: zwei Aktivitäten haben denselben Titel (Voraussetzungen wären nicht eindeutig)")
    links = [e["link"] for e in allgemein + [e for a in abschnitte for e in a["dateien"]] if e.get("link")]
    if len(set(links)) != len(links):
        fehler("Kursplan: zwei Lernpakete haben denselben Link (jedes Paket braucht seinen eigenen Download-Link)")
    for e in allgemein + [e for a in abschnitte for e in a["dateien"]]:
        if e["voraussetzung"] and e["voraussetzung"] not in titel:
            fehler(f"Kursplan: Voraussetzung '{e['voraussetzung']}' ist keine Aktivität im Plan")
    return {
        "kurs": kurs,
        "allgemein": allgemein,
        "allgemein_zusammenfassung": plan.get("allgemein_zusammenfassung", ""),
        "abschnitte": abschnitte,
    }


def datei_xml(d: dict) -> str:
    return f'''  <file id="{d["id"]}">
    <contenthash>{d["hash"]}</contenthash>
    <contextid>{d["ctx"]}</contextid>
    <component>{d["component"]}</component>
    <filearea>{d["filearea"]}</filearea>
    <itemid>0</itemid>
    <filepath>{t(d.get("pfad", "/"))}</filepath>
    <filename>{t(d["name"])}</filename>
    <userid>{d["userid"]}</userid>
    <filesize>{d["size"]}</filesize>
    <mimetype>{t(d["mime"])}</mimetype>
    <status>0</status>
    <timecreated>{d["jetzt"]}</timecreated>
    <timemodified>{d["jetzt"]}</timemodified>
    <source>{t(d["quelle"])}</source>
    <author>{NULL}</author>
    <license>{d["lizenz"]}</license>
    <sortorder>{d["sort"]}</sortorder>
    <repositorytype>{NULL}</repositorytype>
    <repositoryid>{NULL}</repositoryid>
    <reference>{NULL}</reference>
  </file>
'''


def verzeichnis_xml(ids: IdGen, saetze: list[str], ctx: int, component: str, filearea: str, pfad: str,
                    besitzer: int, jetzt: int) -> int:
    verz_id = ids.neu()
    saetze.append(datei_xml(dict(id=verz_id, hash=LEERER_HASH, ctx=ctx, component=component, filearea=filearea,
                                 pfad=pfad, name=".", userid=besitzer, size=0, mime=None, jetzt=jetzt, quelle=None,
                                 sort=0, lizenz=NULL)))
    return verz_id


def lege_datei_an(arch: Archiv, ids: IdGen, saetze: list[str], datei: dict, ctx: int, component: str,
                  filearea: str, sort: int, besitzer: int, jetzt: int, pfad: str = "/",
                  verzeichnis: bool = True, quelle: str | None = None) -> list[int]:
    """Legt Inhalt und files.xml-Eintrag an, auf Wunsch mit Verzeichniseintrag "." (gibt alle IDs zurück)."""
    h = hashlib.sha1(datei["daten"]).hexdigest()
    arch.datei(f"files/{h[:2]}/{h}", datei["daten"])
    datei_id = ids.neu()
    saetze.append(datei_xml(dict(id=datei_id, hash=h, ctx=ctx, component=component, filearea=filearea, pfad=pfad,
                                 name=datei["name"], userid=besitzer, size=len(datei["daten"]),
                                 mime=datei["mime"], jetzt=jetzt, quelle=quelle or datei["name"], sort=sort, lizenz="U")))
    if not verzeichnis:
        return [datei_id]
    return [datei_id, verzeichnis_xml(ids, saetze, ctx, component, filearea, pfad, besitzer, jetzt)]


def modul_xml(modul_id: int, modname: str, sektion_id: int, nummer: int, jetzt: int, sichtbar: bool = True,
              completion: int = 0, availability: str | None = None, showdescription: int = 0) -> str:
    v = 1 if sichtbar else 0
    return XML_KOPF + f'''<module id="{modul_id}" version="{VORLAGE["backup_version"]}">
  <modulename>{modname}</modulename>
  <sectionid>{sektion_id}</sectionid>
  <sectionnumber>{nummer}</sectionnumber>
  <idnumber>{NULL}</idnumber>
  <added>{jetzt}</added>
  <score>0</score>
  <indent>0</indent>
  <visible>{v}</visible>
  <visibleoncoursepage>1</visibleoncoursepage>
  <visibleold>{v}</visibleold>
  <groupmode>0</groupmode>
  <groupingid>0</groupingid>
  <completion>{completion}</completion>
  <completiongradeitemnumber>{NULL}</completiongradeitemnumber>
  <completionpassgrade>0</completionpassgrade>
  <completionview>0</completionview>
  <completionexpected>0</completionexpected>
  <availability>{t(availability)}</availability>
  <showdescription>{showdescription}</showdescription>
  <downloadcontent>1</downloadcontent>
  <lang>{NULL}</lang>
  <enableaitools>{NULL}</enableaitools>
  <enabledaiactions>{NULL}</enabledaiactions>
  <tags>
  </tags>
</module>
'''


def ressource_xml(inst_id: int, modul_id: int, ctx: int, name: str, intro: str, jetzt: int) -> str:
    return XML_KOPF + f'''<activity id="{inst_id}" moduleid="{modul_id}" modulename="resource" contextid="{ctx}">
  <resource id="{inst_id}">
    <name>{t(name)}</name>
    <intro>{t(intro)}</intro>
    <introformat>1</introformat>
    <tobemigrated>0</tobemigrated>
    <legacyfiles>0</legacyfiles>
    <legacyfileslast>{NULL}</legacyfileslast>
    <display>0</display>
    <displayoptions>{escape(DISPLAYOPTIONS)}</displayoptions>
    <filterfiles>0</filterfiles>
    <revision>0</revision>
    <timemodified>{jetzt}</timemodified>
  </resource>
</activity>
'''


def scorm_xml(inst_id: int, modul_id: int, ctx: int, e: dict, sha1: str, org_sco: int, item_sco: int,
              ids: IdGen, jetzt: int) -> str:
    s = e["scorm"]
    sco_daten = f'''          <sco_data id="{ids.neu()}">
            <name>isvisible</name>
            <value>{t(s["sichtbar"])}</value>
          </sco_data>
'''
    ziel = ""
    if s["ziel"]:
        ziel = f'''          <seq_objective id="{ids.neu()}">
            <primaryobj>1</primaryobj>
            <objectiveid>{t(s["ziel"]["id"])}</objectiveid>
            <satisfiedbymeasure>{s["ziel"]["durch_mass"]}</satisfiedbymeasure>
            <minnormalizedmeasure>{s["ziel"]["mindest"]:.4f}</minnormalizedmeasure>
            <seq_mapinfos>
            </seq_mapinfos>
          </seq_objective>
'''
    abschluss = SCORM_ABSCHLUSS.get(e["abschluss"]) if e["abschluss"] else None
    return XML_KOPF + f'''<activity id="{inst_id}" moduleid="{modul_id}" modulename="scorm" contextid="{ctx}">
  <scorm id="{inst_id}">
    <name>{t(e["titel"])}</name>
    <scormtype>{"localsync" if e.get("link") else "local"}</scormtype>
    <reference>{t(e.get("link") or e["name"])}</reference>
    <intro>{t(e["beschreibung"])}</intro>
    <introformat>1</introformat>
    <version>{s["version"]}</version>
    <maxgrade>100</maxgrade>
    <grademethod>1</grademethod>
    <whatgrade>0</whatgrade>
    <maxattempt>1</maxattempt>
    <forcecompleted>0</forcecompleted>
    <forcenewattempt>0</forcenewattempt>
    <lastattemptlock>0</lastattemptlock>
    <masteryoverride>1</masteryoverride>
    <displayattemptstatus>1</displayattemptstatus>
    <displaycoursestructure>0</displaycoursestructure>
    <updatefreq>{3 if e.get("link") else 0}</updatefreq>
    <sha1hash>{sha1}</sha1hash>
    <md5hash></md5hash>
    <revision>1</revision>
    <launch>{item_sco}</launch>
    <skipview>0</skipview>
    <hidebrowse>1</hidebrowse>
    <hidetoc>3</hidetoc>
    <nav>0</nav>
    <navpositionleft>-100</navpositionleft>
    <navpositiontop>-100</navpositiontop>
    <auto>0</auto>
    <popup>1</popup>
    <options>scrollbars=1,directories=0,location=0,menubar=0,toolbar=0,status=0</options>
    <width>100</width>
    <height>100</height>
    <timeopen>0</timeopen>
    <timeclose>0</timeclose>
    <timemodified>{jetzt}</timemodified>
    <completionstatusrequired>{t(abschluss)}</completionstatusrequired>
    <completionscorerequired>{NULL}</completionscorerequired>
    <completionstatusallscos>0</completionstatusallscos>
    <autocommit>0</autocommit>
    <scoes>
      <sco id="{org_sco}">
        <manifest>{t(s["manifest"])}</manifest>
        <organization></organization>
        <parent>/</parent>
        <identifier>{t(s["org_id"])}</identifier>
        <launch></launch>
        <scormtype></scormtype>
        <title>{t(s["org_titel"])}</title>
        <sortorder>1</sortorder>
        <sco_datas>
        </sco_datas>
        <seq_ruleconds>
        </seq_ruleconds>
        <seq_rolluprules>
        </seq_rolluprules>
        <seq_objectives>
        </seq_objectives>
      </sco>
      <sco id="{item_sco}">
        <manifest>{t(s["manifest"])}</manifest>
        <organization>{t(s["org_id"])}</organization>
        <parent>{t(s["org_id"])}</parent>
        <identifier>{t(s["item_id"])}</identifier>
        <launch>{t(s["start"])}</launch>
        <scormtype>sco</scormtype>
        <title>{t(s["item_titel"])}</title>
        <sortorder>2</sortorder>
        <sco_datas>
{sco_daten}        </sco_datas>
        <seq_ruleconds>
        </seq_ruleconds>
        <seq_rolluprules>
        </seq_rolluprules>
        <seq_objectives>
{ziel}        </seq_objectives>
      </sco>
    </scoes>
  </scorm>
</activity>
'''


def aktivitaet_noten_xml(item_id: int, kat_id: int, name: str, modname: str, inst_id: int, sort: int,
                         bestehen: int, jetzt: int, verborgen: int = 0) -> str:
    return XML_KOPF + f'''<activity_gradebook>
  <grade_items>
    <grade_item id="{item_id}">
      <categoryid>{kat_id}</categoryid>
      <itemname>{t(name)}</itemname>
      <itemtype>mod</itemtype>
      <itemmodule>{modname}</itemmodule>
      <iteminstance>{inst_id}</iteminstance>
      <itemnumber>0</itemnumber>
      <iteminfo>{NULL}</iteminfo>
      <idnumber></idnumber>
      <calculation>{NULL}</calculation>
      <gradetype>1</gradetype>
      <grademax>100.00000</grademax>
      <grademin>0.00000</grademin>
      <scaleid>{NULL}</scaleid>
      <outcomeid>{NULL}</outcomeid>
      <gradepass>{bestehen:.5f}</gradepass>
      <multfactor>1.00000</multfactor>
      <plusfactor>0.00000</plusfactor>
      <aggregationcoef>0.00000</aggregationcoef>
      <aggregationcoef2>0.00000</aggregationcoef2>
      <weightoverride>0</weightoverride>
      <sortorder>{sort}</sortorder>
      <display>0</display>
      <decimals>{NULL}</decimals>
      <hidden>{verborgen}</hidden>
      <locked>0</locked>
      <locktime>0</locktime>
      <needsupdate>0</needsupdate>
      <timecreated>{jetzt}</timecreated>
      <timemodified>{jetzt}</timemodified>
      <grade_grades>
      </grade_grades>
    </grade_item>
  </grade_items>
  <grade_letters>
  </grade_letters>
</activity_gradebook>
'''


def inforef_xml(datei_refs: list[int], noten_refs: list[int] | None = None) -> str:
    text = XML_KOPF + "<inforef>\n"
    if datei_refs:
        text += "  <fileref>\n" + "".join(f"    <file>\n      <id>{r}</id>\n    </file>\n" for r in datei_refs) + "  </fileref>\n"
    if noten_refs:
        text += "  <grade_itemref>\n" + "".join(f"    <grade_item>\n      <id>{r}</id>\n    </grade_item>\n" for r in noten_refs) + "  </grade_itemref>\n"
    return text + "</inforef>\n"


def section_xml(sektion_id: int, nummer: int, name: str | None, zusammenfassung: str, seq: list[int], jetzt: int) -> str:
    folge = ",".join(str(s) for s in seq)
    return XML_KOPF + f'''<section id="{sektion_id}">
  <number>{nummer}</number>
  <name>{t(name)}</name>
  <summary>{t(zusammenfassung)}</summary>
  <summaryformat>1</summaryformat>
  <sequence>{folge}</sequence>
  <visible>1</visible>
  <availabilityjson>{NULL}</availabilityjson>
  <component>{NULL}</component>
  <itemid>{NULL}</itemid>
  <timemodified>{jetzt}</timemodified>
</section>
'''


def kurs_xml(kurs: dict, kurs_id: int, kurs_ctx: int, startdatum: int, jetzt: int, ids: IdGen) -> str:
    cf_schule, cf_teilnehmer = ids.neu(), ids.neu()
    return XML_KOPF + f'''<course id="{kurs_id}" contextid="{kurs_ctx}">
  <shortname>{t(kurs["kurzname"])}</shortname>
  <fullname>{t(kurs["vollname"])}</fullname>
  <idnumber></idnumber>
  <summary>{t(kurs.get("zusammenfassung", ""))}</summary>
  <summaryformat>1</summaryformat>
  <format>topics</format>
  <showgrades>1</showgrades>
  <newsitems>0</newsitems>
  <startdate>{startdatum}</startdate>
  <enddate>0</enddate>
  <marker>0</marker>
  <maxbytes>524288000</maxbytes>
  <legacyfiles>0</legacyfiles>
  <showreports>0</showreports>
  <visible>1</visible>
  <groupmode>{VORLAGE["gruppenmodus"]}</groupmode>
  <groupmodeforce>{VORLAGE["gruppenmodus_erzwingen"]}</groupmodeforce>
  <defaultgroupingid>0</defaultgroupingid>
  <lang></lang>
  <theme></theme>
  <timecreated>{jetzt}</timecreated>
  <timemodified>{jetzt}</timemodified>
  <requested>0</requested>
  <showactivitydates>0</showactivitydates>
  <showcompletionconditions>{VORLAGE["abschlussbedingungen_zeigen"]}</showcompletionconditions>
  <pdfexportfont>{NULL}</pdfexportfont>
  <enablecompletion>1</enablecompletion>
  <completionnotify>0</completionnotify>
  <enableaitools>{NULL}</enableaitools>
  <category id="{VORLAGE["kategorie_id"]}">
    <name>{t(VORLAGE["kategorie"])}</name>
    <description></description>
  </category>
  <tags>
  </tags>
  <customfields>
    <customfield id="{cf_schule}">
      <shortname>schule</shortname>
      <type>text</type>
      <value>{t(VORLAGE["kategorie"])}</value>
      <valueformat>0</valueformat>
      <valuetrust></valuetrust>
    </customfield>
    <customfield id="{cf_teilnehmer}">
      <shortname>participants</shortname>
      <type>checkbox</type>
      <value>0</value>
      <valueformat>0</valueformat>
      <valuetrust></valuetrust>
    </customfield>
  </customfields>
  <courseformatoptions>
    <courseformatoption>
      <format>topics</format>
      <sectionid>0</sectionid>
      <name>coursedisplay</name>
      <value>0</value>
    </courseformatoption>
    <courseformatoption>
      <format>topics</format>
      <sectionid>0</sectionid>
      <name>hiddensections</name>
      <value>1</value>
    </courseformatoption>
  </courseformatoptions>
</course>
'''


def kurs_inforef(refs: list[int]) -> str:
    rollen = "".join(f"    <role>\n      <id>{r}</id>\n    </role>\n"
                     for r in (VORLAGE["rolle_lehrkraft"], VORLAGE["rolle_schueler"]))
    text = XML_KOPF + f"<inforef>\n  <roleref>\n{rollen}  </roleref>\n"
    if refs:
        text += "  <fileref>\n" + "".join(f"    <file>\n      <id>{r}</id>\n    </file>\n" for r in refs) + "  </fileref>\n"
    return text + "</inforef>\n"


def einschreibung_xml(enrol_id: int, jetzt: int) -> str:
    # Nur die manuelle Einschreibung. Kurspasswörter der Vorlage werden NICHT übernommen.
    return XML_KOPF + f'''<enrolments>
  <enrols>
    <enrol id="{enrol_id}">
      <enrol>manual</enrol>
      <status>0</status>
      <name>{NULL}</name>
      <enrolperiod>0</enrolperiod>
      <enrolstartdate>0</enrolstartdate>
      <enrolenddate>0</enrolenddate>
      <expirynotify>0</expirynotify>
      <expirythreshold>86400</expirythreshold>
      <notifyall>0</notifyall>
      <password>{NULL}</password>
      <cost>{NULL}</cost>
      <currency>{NULL}</currency>
      <roleid>{VORLAGE["rolle_schueler"]}</roleid>
      <customint1>0</customint1>
      <customint2>{NULL}</customint2>
      <customint3>{NULL}</customint3>
      <customint4>{NULL}</customint4>
      <customint5>{NULL}</customint5>
      <customint6>{NULL}</customint6>
      <customint7>{NULL}</customint7>
      <customint8>{NULL}</customint8>
      <customchar1>{NULL}</customchar1>
      <customchar2>{NULL}</customchar2>
      <customchar3>{NULL}</customchar3>
      <customdec1>{NULL}</customdec1>
      <customdec2>{NULL}</customdec2>
      <customtext1>{NULL}</customtext1>
      <customtext2>{NULL}</customtext2>
      <customtext3>{NULL}</customtext3>
      <customtext4>{NULL}</customtext4>
      <timecreated>{jetzt}</timecreated>
      <timemodified>{jetzt}</timemodified>
      <user_enrolments>
      </user_enrolments>
    </enrol>
  </enrols>
</enrolments>
'''


def noten_xml(kat_id: int, item_id: int, jetzt: int, ids: IdGen) -> str:
    buchstaben = "".join(f'''    <grade_letter id="{ids.neu()}">
      <lowerboundary>{grenze:.5f}</lowerboundary>
      <letter>{t(note)}</letter>
    </grade_letter>
''' for grenze, note in sorted(VORLAGE["notenstufen"]))
    return XML_KOPF + f'''<gradebook>
  <attributes>
  </attributes>
  <grade_categories>
    <grade_category id="{kat_id}">
      <parent>{NULL}</parent>
      <depth>1</depth>
      <path>/{kat_id}/</path>
      <fullname>?</fullname>
      <aggregation>11</aggregation>
      <keephigh>0</keephigh>
      <droplow>0</droplow>
      <aggregateonlygraded>1</aggregateonlygraded>
      <aggregateoutcomes>0</aggregateoutcomes>
      <timecreated>{jetzt}</timecreated>
      <timemodified>{jetzt}</timemodified>
      <hidden>0</hidden>
    </grade_category>
  </grade_categories>
  <grade_items>
    <grade_item id="{item_id}">
      <categoryid>{NULL}</categoryid>
      <itemname>{NULL}</itemname>
      <itemtype>course</itemtype>
      <itemmodule>{NULL}</itemmodule>
      <iteminstance>{kat_id}</iteminstance>
      <itemnumber>{NULL}</itemnumber>
      <iteminfo>{NULL}</iteminfo>
      <idnumber>{NULL}</idnumber>
      <calculation>{NULL}</calculation>
      <gradetype>1</gradetype>
      <grademax>100.00000</grademax>
      <grademin>0.00000</grademin>
      <scaleid>{NULL}</scaleid>
      <outcomeid>{NULL}</outcomeid>
      <gradepass>0.00000</gradepass>
      <multfactor>1.00000</multfactor>
      <plusfactor>0.00000</plusfactor>
      <aggregationcoef>0.00000</aggregationcoef>
      <aggregationcoef2>0.00000</aggregationcoef2>
      <weightoverride>0</weightoverride>
      <sortorder>1</sortorder>
      <display>0</display>
      <decimals>{NULL}</decimals>
      <hidden>0</hidden>
      <locked>0</locked>
      <locktime>0</locktime>
      <needsupdate>0</needsupdate>
      <timecreated>{jetzt}</timecreated>
      <timemodified>{jetzt}</timemodified>
      <grade_grades>
      </grade_grades>
    </grade_item>
  </grade_items>
  <grade_letters>
{buchstaben}  </grade_letters>
  <grade_settings>
    <grade_setting id="{ids.neu()}">
      <name>displaytype</name>
      <value>{VORLAGE["notenanzeige"]}</value>
    </grade_setting>
    <grade_setting id="{ids.neu()}">
      <name>decimalpoints</name>
      <value>{VORLAGE["nachkommastellen"]}</value>
    </grade_setting>
    <grade_setting id="{ids.neu()}">
      <name>minmaxtouse</name>
      <value>1</value>
    </grade_setting>
    <grade_setting id="{ids.neu()}">
      <name>report_user_rangedecimals</name>
      <value>{VORLAGE["bereich_nachkommastellen"]}</value>
    </grade_setting>
  </grade_settings>
</gradebook>
'''


def block_xml(bid: int, name: str, version: str, bctx: int, kurs_ctx: int, jetzt: int) -> str:
    return XML_KOPF + f'''<block id="{bid}" contextid="{bctx}" version="{version}">
  <blockname>{name}</blockname>
  <parentcontextid>{kurs_ctx}</parentcontextid>
  <showinsubcontexts>1</showinsubcontexts>
  <pagetypepattern>*</pagetypepattern>
  <subpagepattern>{NULL}</subpagepattern>
  <defaultregion>side-pre</defaultregion>
  <defaultweight>1</defaultweight>
  <configdata></configdata>
  <timecreated>{jetzt}</timecreated>
  <timemodified>{jetzt}</timemodified>
  <block_positions>
  </block_positions>
</block>
'''


def manifest_xml(backup_name: str, jetzt: int, kurs: dict, kurs_id: int, kurs_ctx: int,
                 abschnitte: list[dict], aktivitaeten: list[dict]) -> str:
    akt = "".join(f'''        <activity>
          <moduleid>{a["id"]}</moduleid>
          <sectionid>{a["sec"]}</sectionid>
          <modulename>{a["modname"]}</modulename>
          <title>{t(a["titel"])}</title>
          <directory>{a["verz"]}</directory>
          <insubsection></insubsection>
        </activity>
''' for a in aktivitaeten)
    sek = "".join(f'''        <section>
          <sectionid>{s["id"]}</sectionid>
          <title>{t("0" if s["nummer"] == 0 else s["name"])}</title>
          <directory>sections/section_{s["id"]}</directory>
          <parentcmid></parentcmid>
          <modname></modname>
        </section>
''' for s in abschnitte)

    einst = [f'''      <setting>
        <level>root</level>
        <name>filename</name>
        <value>{t(backup_name)}</value>
      </setting>
''']
    einst += [f'''      <setting>
        <level>root</level>
        <name>{n}</name>
        <value>{v}</value>
      </setting>
''' for n, v in ROOT_EINSTELLUNGEN]
    for s in abschnitte:
        for n, v in ((f"section_{s['id']}_included", "1"), (f"section_{s['id']}_userinfo", "0")):
            einst.append(f'''      <setting>
        <level>section</level>
        <section>section_{s["id"]}</section>
        <name>{n}</name>
        <value>{v}</value>
      </setting>
''')
    for a in aktivitaeten:
        schluessel = f"{a['modname']}_{a['id']}"
        for n, v in ((f"{schluessel}_included", "1"), (f"{schluessel}_userinfo", "0")):
            einst.append(f'''      <setting>
        <level>activity</level>
        <activity>{schluessel}</activity>
        <name>{n}</name>
        <value>{v}</value>
      </setting>
''')

    return XML_KOPF + f'''<moodle_backup>
  <information>
    <name>{t(backup_name)}</name>
    <moodle_version>{VORLAGE["moodle_version"]}</moodle_version>
    <moodle_release>{t(VORLAGE["moodle_release"])}</moodle_release>
    <backup_version>{VORLAGE["backup_version"]}</backup_version>
    <backup_release>{VORLAGE["backup_release"]}</backup_release>
    <backup_date>{jetzt}</backup_date>
    <mnet_remoteusers>0</mnet_remoteusers>
    <include_files>1</include_files>
    <include_file_references_to_external_content>0</include_file_references_to_external_content>
    <original_wwwroot>{VORLAGE["wwwroot"]}</original_wwwroot>
    <original_site_identifier_hash>{VORLAGE["site_hash"]}</original_site_identifier_hash>
    <original_course_id>{kurs_id}</original_course_id>
    <original_course_format>topics</original_course_format>
    <original_course_fullname>{t(kurs["vollname"])}</original_course_fullname>
    <original_course_shortname>{t(kurs["kurzname"])}</original_course_shortname>
    <original_course_startdate>{berlin_mitternacht(kurs["startdatum"])}</original_course_startdate>
    <original_course_enddate>0</original_course_enddate>
    <original_course_contextid>{kurs_ctx}</original_course_contextid>
    <original_system_contextid>1</original_system_contextid>
    <details>
      <detail backup_id="{uuid.uuid4().hex}">
        <type>course</type>
        <format>moodle2</format>
        <interactive>1</interactive>
        <mode>70</mode>
        <execution>2</execution>
        <executiontime>0</executiontime>
      </detail>
    </details>
    <contents>
      <activities>
{akt}      </activities>
      <sections>
{sek}      </sections>
      <course>
        <courseid>{kurs_id}</courseid>
        <title>{t(kurs["kurzname"])}</title>
        <directory>course</directory>
      </course>
    </contents>
    <settings>
{"".join(einst)}    </settings>
  </information>
</moodle_backup>
'''


def baue_ressource(arch, ids, saetze, e, modul_id, sektion_id, nummer, jetzt, besitzer, availability) -> str:
    inst_id, ctx = ids.neu(), ids.neu()
    refs = lege_datei_an(arch, ids, saetze, e, ctx, "mod_resource", "content", 1, besitzer, jetzt)
    verz = f"activities/resource_{modul_id}"
    arch.datei(f"{verz}/module.xml", modul_xml(modul_id, "resource", sektion_id, nummer, jetzt, not e["versteckt"],
                                               availability=availability, showdescription=1 if e["beschreibung"] else 0))
    arch.datei(f"{verz}/resource.xml", ressource_xml(inst_id, modul_id, ctx, e["titel"], e["beschreibung"], jetzt))
    arch.datei(f"{verz}/inforef.xml", inforef_xml(refs))
    arch.datei(f"{verz}/grades.xml", AKTIVITAET_NOTEN_LEER)
    for dateiname, inhalt in STATISCH_MODUL.items():
        arch.datei(f"{verz}/{dateiname}", inhalt)
    return verz


def baue_scorm(arch, ids, saetze, e, modul_id, sektion_id, nummer, jetzt, besitzer, availability,
               kat_id, noten_sort) -> str:
    inst_id, ctx = ids.neu(), ids.neu()
    s = e["scorm"]
    # Paket (ZIP) und entpackter Inhalt: Moodle spielt das Paket aus dem Bereich "content" ab.
    # Mit Link legt Moodle das Paket unter einem Namen aus dem Link ab, Quelle ist der Link (wie in der ByCS).
    paket = dict(e, name=paket_name(e["link"])) if e.get("link") else e
    refs = lege_datei_an(arch, ids, saetze, paket, ctx, "mod_scorm", "package", 0, besitzer, jetzt,
                         quelle=e.get("link"))
    ordner_im_paket = {"/"}
    for pfad, daten in s["inhalt"]:
        ordner, name = posixpath.split(pfad)
        filepath = "/" + (ordner + "/" if ordner else "")
        teile = ordner.split("/") if ordner else []
        for i in range(1, len(teile) + 1):
            ordner_im_paket.add("/" + "/".join(teile[:i]) + "/")
        datei = {"name": name, "daten": daten, "mime": mimetypes.guess_type(name)[0] or "application/octet-stream"}
        refs += lege_datei_an(arch, ids, saetze, datei, ctx, "mod_scorm", "content", 0, besitzer, jetzt,
                              pfad=filepath, verzeichnis=False)
    for filepath in sorted(ordner_im_paket):
        refs.append(verzeichnis_xml(ids, saetze, ctx, "mod_scorm", "content", filepath, besitzer, jetzt))
    org_sco, item_sco, noten_id = ids.neu(), ids.neu(), ids.neu()
    verz = f"activities/scorm_{modul_id}"
    completion = 2 if e["abschluss"] else 0
    arch.datei(f"{verz}/module.xml", modul_xml(modul_id, "scorm", sektion_id, nummer, jetzt, not e["versteckt"],
                                               completion=completion, availability=availability,
                                               showdescription=1 if e["beschreibung"] else 0))
    arch.datei(f"{verz}/scorm.xml", scorm_xml(inst_id, modul_id, ctx, e, hashlib.sha1(e["daten"]).hexdigest(),
                                              org_sco, item_sco, ids, jetzt))
    arch.datei(f"{verz}/inforef.xml", inforef_xml(refs, [noten_id]))
    arch.datei(f"{verz}/grades.xml", aktivitaet_noten_xml(noten_id, kat_id, e["titel"], "scorm", inst_id,
                                                           noten_sort, SCORM_BESTEHEN, jetzt,
                                                           VORLAGE["scorm_noten_verborgen"]))
    for dateiname, inhalt in STATISCH_MODUL.items():
        arch.datei(f"{verz}/{dateiname}", inhalt)
    return verz


def ersetze_erstes(text: str, tag: str, wert: str) -> str:
    neu, n = re.subn(rf"<{tag}>.*?</{tag}>", lambda _m: f"<{tag}>{wert}</{tag}>", text, count=1, flags=re.S)
    if not n:
        fehler(f"Test: <{tag}> nicht gefunden")
    return neu


def baue_test(arch, saetze, fragen, e, sektion_id, nummer, availability, kat_id, noten_sort) -> str:
    """Bindet die Test-Aktivität aus der Test-Sicherung ein. IDs bleiben, Abschnitt und Bewertung werden angepasst."""
    test = e["test"]
    verz = f"activities/quiz_{test['modul_id']}"
    for name, daten in test["dateien"].items():
        text = daten.decode("utf-8")
        if name == "module.xml":
            v = "0" if e["versteckt"] else "1"
            text = ersetze_erstes(text, "sectionid", str(sektion_id))
            text = ersetze_erstes(text, "sectionnumber", str(nummer))
            text = ersetze_erstes(text, "visible", v)
            text = ersetze_erstes(text, "visibleold", v)
            text = ersetze_erstes(text, "availability", t(availability))
            text = ersetze_erstes(text, "showdescription", "1" if e["beschreibung"] else "0")
        elif name == "quiz.xml":
            text = ersetze_erstes(text, "name", t(e["titel"]))
            if e["beschreibung"]:
                text = ersetze_erstes(text, "intro", t(e["beschreibung"]))
        elif name == "grades.xml":
            text = ersetze_erstes(text, "categoryid", str(kat_id))
            text = ersetze_erstes(text, "itemname", t(e["titel"]))
            text = ersetze_erstes(text, "sortorder", str(noten_sort))
        arch.datei(f"{verz}/{name}", text)
    for pfad, daten in test["blobs"].items():
        arch.datei(pfad, daten)
    saetze.extend(z if z.endswith("\n") else z + "\n" for z in test["datei_saetze"])
    fragen.append(test["kategorien"])
    return verz


def baue(plan: dict, ziel: Path) -> dict:
    kurs = plan["kurs"]
    jetzt = int(time.time())
    tests = [e for e in plan["allgemein"] + [e for a in plan["abschnitte"] for e in a["dateien"]] if e["typ"] == "test"]
    if len({e["test"]["modul_id"] for e in tests}) != len(tests):
        fehler("Kursplan: derselbe Test ist zweimal eingetragen")
    ids = IdGen(set().union(*(e["test"]["reserviert"] for e in tests)))
    fragen: list[str] = []  # Fragenkategorien der Tests für questions.xml
    arch = Archiv(jetzt)
    besitzer = VORLAGE["besitzer_id"]
    saetze: list[str] = []  # Einträge für files.xml

    kurs_id, kurs_ctx = ids.neu(), ids.neu()
    kat_id, kurs_noten_id = ids.neu(), ids.neu()
    startdatum = berlin_mitternacht(kurs["startdatum"])

    kurs_refs: list[int] = []
    if kurs.get("banner"):
        banner = lade_datei(kurs["banner"])
        kurs_refs += lege_datei_an(arch, ids, saetze, banner, kurs_ctx, "course", "overviewfiles", 0, besitzer, jetzt)

    # Gliederung: Abschnitt 0 für Allgemeines, danach je Blockwoche ein Abschnitt.
    gliederung = [(0, None, plan["allgemein_zusammenfassung"], plan["allgemein"])]
    gliederung += [(n, a["name"], a["zusammenfassung"], a["dateien"]) for n, a in enumerate(plan["abschnitte"], start=1)]

    # Erst alle Modul-IDs vergeben, damit Voraussetzungen auch auf spätere Aktivitäten zeigen können.
    modul_von_titel = {}
    for _, _, _, eintraege in gliederung:
        for e in eintraege:
            e["_modul"] = e["test"]["modul_id"] if e["typ"] == "test" else ids.neu()
            modul_von_titel[e["titel"]] = e["_modul"]

    abschnitte: list[dict] = []
    aktivitaeten: list[dict] = []
    noten_sort = 1
    for nummer, name, zusammenfassung, eintraege in gliederung:
        sektion_id = ids.neu()
        seq: list[int] = []
        for e in eintraege:
            availability = None
            if e["voraussetzung"]:
                availability = json.dumps({"op": "&", "c": [{"type": "completion", "cm": modul_von_titel[e["voraussetzung"]], "e": 1}],
                                           "showc": [True]}, separators=(",", ":"))
            if e["typ"] == "scorm":
                noten_sort += 1
                verz = baue_scorm(arch, ids, saetze, e, e["_modul"], sektion_id, nummer, jetzt, besitzer,
                                  availability, kat_id, noten_sort)
            elif e["typ"] == "test":
                noten_sort += 1
                verz = baue_test(arch, saetze, fragen, e, sektion_id, nummer, availability, kat_id, noten_sort)
            else:
                verz = baue_ressource(arch, ids, saetze, e, e["_modul"], sektion_id, nummer, jetzt, besitzer, availability)
            seq.append(e["_modul"])
            aktivitaeten.append(dict(id=e["_modul"], sec=sektion_id, titel=e["titel"], verz=verz,
                                     modname={"scorm": "scorm", "test": "quiz"}.get(e["typ"], "resource")))
        arch.datei(f"sections/section_{sektion_id}/section.xml", section_xml(sektion_id, nummer, name, zusammenfassung, seq, jetzt))
        arch.datei(f"sections/section_{sektion_id}/inforef.xml", INFOREF_LEER)
        abschnitte.append(dict(id=sektion_id, nummer=nummer, name=name, seq=seq))

    arch.datei("course/course.xml", kurs_xml(kurs, kurs_id, kurs_ctx, startdatum, jetzt, ids))
    arch.datei("course/inforef.xml", kurs_inforef(kurs_refs))
    arch.datei("course/enrolments.xml", einschreibung_xml(ids.neu(), jetzt))
    for dateiname, inhalt in {"calendar.xml": KALENDER_LEER, "filters.xml": FILTER_LEER,
                              "roles.xml": ROLLEN_LEER, "contentbank.xml": XML_KOPF + "<contents>\n</contents>\n",
                              "completiondefaults.xml": XML_KOPF + "<course_completion_defaults>\n</course_completion_defaults>\n"}.items():
        arch.datei(f"course/{dateiname}", inhalt)
    for blockname, version in VORLAGE["bloecke"]:
        bid, bctx = ids.neu(), ids.neu()
        ordner = f"course/blocks/{blockname}_{bid}"
        arch.datei(f"{ordner}/block.xml", block_xml(bid, blockname, version, bctx, kurs_ctx, jetzt))
        arch.datei(f"{ordner}/inforef.xml", INFOREF_LEER)
        arch.datei(f"{ordner}/roles.xml", ROLLEN_LEER)
        if blockname == "ai_chat":
            arch.datei(f"{ordner}/aichat.xml", XML_KOPF + f'''<block id="{bid}" blockname="ai_chat" contextid="{bctx}">
  <aichat id="">
    <personas>
    </personas>
    <personas_selected>
    </personas_selected>
    <chat_options>
    </chat_options>
  </aichat>
</block>
''')

    arch.datei("gradebook.xml", noten_xml(kat_id, kurs_noten_id, jetzt, ids))
    arch.datei("grade_history.xml", NOTEN_LEER)
    arch.datei("groups.xml", XML_KOPF + "<groups>\n  <groupcustomfields>\n  </groupcustomfields>\n  <groupings>\n    <groupingcustomfields>\n    </groupingcustomfields>\n  </groupings>\n</groups>\n")
    arch.datei("badges.xml", XML_KOPF + "<badges>\n</badges>\n")
    arch.datei("completion.xml", XML_KOPF + "<course_completion>\n</course_completion>\n")
    arch.datei("outcomes.xml", XML_KOPF + "<outcomes_definition>\n</outcomes_definition>\n")
    arch.datei("scales.xml", XML_KOPF + "<scales_definition>\n</scales_definition>\n")
    arch.datei("questions.xml", XML_KOPF + "<question_categories>\n" + "".join(fragen) + "</question_categories>\n")
    arch.datei("roles.xml", ROLLEN_DEFINITION)
    arch.datei("files.xml", XML_KOPF + "<files>\n" + "".join(saetze) + "</files>\n")
    arch.datei("moodle_backup.xml", manifest_xml(ziel.name, jetzt, kurs, kurs_id, kurs_ctx, abschnitte, aktivitaeten))
    arch.datei("moodle_backup.log", b"")
    arch.schreibe(ziel)
    return {"abschnitte": len(abschnitte), "aktivitaeten": len(aktivitaeten),
            "scorm": sum(1 for a in aktivitaeten if a["modname"] == "scorm"),
            "tests": sum(1 for a in aktivitaeten if a["modname"] == "quiz")}


def pruefen(pfad: Path) -> int:
    """Prüft eine .mbz: Archivindex, XML, Verweise, Dateiinhalte (SHA-1 und Größe), Abschnittsfolge, SCORM."""
    fehler_liste: list[str] = []
    ok: list[str] = []
    dateien: dict[str, bytes] = {}
    ordner: set[str] = set()
    with tarfile.open(pfad, "r:gz") as tar:
        for m in tar.getmembers():
            name = m.name.rstrip("/")
            if m.isdir():
                ordner.add(name)
            elif m.isfile():
                dateien[name] = tar.extractfile(m).read()
            else:
                fehler_liste.append(f"Unerwarteter Eintrag im Archiv: {m.name}")
    ok.append("Archiv lesbar (gzip-tar)")

    # 1. Archivindex
    zeilen = dateien.get(".ARCHIVE_INDEX", b"").decode("utf-8").splitlines()
    alle = (set(dateien) | ordner) - {".ARCHIVE_INDEX"}
    if not zeilen or not zeilen[0].startswith("Moodle archive file index. Count: "):
        fehler_liste.append(".ARCHIVE_INDEX fehlt oder hat keine Kopfzeile")
    else:
        index_namen = {z.split("\t")[0].rstrip("/") for z in zeilen[1:]}
        if int(zeilen[0].rsplit(" ", 1)[1]) != len(alle) or index_namen != alle:
            fehler_liste.append(".ARCHIVE_INDEX passt nicht zum Inhalt des Archivs")
        else:
            ok.append(f"Archivindex stimmt ({len(alle)} Einträge)")

    # 2. XML lesbar
    baeume: dict[str, ET.Element] = {}
    for name, daten in dateien.items():
        if name.endswith(".xml"):
            try:
                baeume[name] = ET.fromstring(daten)
            except ET.ParseError as err:
                fehler_liste.append(f"{name}: kein gültiges XML ({err})")
    if "moodle_backup.xml" not in baeume:
        fehler_liste.append("moodle_backup.xml fehlt")
        return _ausgabe(fehler_liste, ok)
    ok.append("Alle XML-Dateien sind lesbar")

    # 3. Manifest: Kurs, Abschnitte, Aktivitäten
    mb = baeume["moodle_backup.xml"]
    kurs_verz = mb.findtext("information/contents/course/directory")
    if f"{kurs_verz}/course.xml" not in baeume:
        fehler_liste.append("Kursdatei course/course.xml fehlt")
    sektionen: dict[str, str] = {}
    for s in mb.iterfind("information/contents/sections/section"):
        sid, verz = s.findtext("sectionid"), s.findtext("directory")
        if f"{verz}/section.xml" not in baeume:
            fehler_liste.append(f"Abschnitt {sid}: section.xml fehlt")
        elif baeume[f"{verz}/section.xml"].get("id") != sid:
            fehler_liste.append(f"Abschnitt {sid}: ID in section.xml stimmt nicht")
        else:
            sektionen[sid] = verz
    module: dict[str, tuple[str, str]] = {}
    for a in mb.iterfind("information/contents/activities/activity"):
        mid, sid, typ, verz = a.findtext("moduleid"), a.findtext("sectionid"), a.findtext("modulename"), a.findtext("directory")
        modul = baeume.get(f"{verz}/module.xml")
        if modul is None:
            fehler_liste.append(f"Aktivität {mid}: module.xml fehlt")
            continue
        if modul.findtext("sectionid") != sid or sid not in sektionen:
            fehler_liste.append(f"Aktivität {mid}: liegt in keinem gültigen Abschnitt")
        if modul.get("id") != mid or modul.findtext("modulename") != typ:
            fehler_liste.append(f"Aktivität {mid}: ID oder Typ stimmen nicht")
        if f"{verz}/{typ}.xml" not in baeume:
            fehler_liste.append(f"Aktivität {mid}: {typ}.xml fehlt")
        module[mid] = (verz, typ)
    if len(set(sektionen)) != len(sektionen) or len(set(module)) != len(module):
        fehler_liste.append("Abschnitts- oder Aktivitäts-IDs sind nicht eindeutig")
    ok.append(f"Manifest: {len(sektionen)} Abschnitte, {len(module)} Aktivitäten, alle Verzeichnisse vorhanden")

    # 4. Abschnittsfolge: jede Aktivität steht genau einmal in einer Folge
    folge: list[str] = []
    for verz in sektionen.values():
        seq = baeume[f"{verz}/section.xml"].findtext("sequence") or ""
        folge += [x for x in seq.split(",") if x]
    if sorted(folge) != sorted(module):
        fehler_liste.append("Abschnittsfolge passt nicht zu den Aktivitäten (fehlt eine oder steht doppelt)")
    else:
        ok.append("Jede Aktivität steht genau einmal in einem Abschnitt")

    # 5. Voraussetzungen zeigen auf Aktivitäten dieser Sicherung
    for mid, (verz, _) in module.items():
        avail = baeume[f"{verz}/module.xml"].findtext("availability")
        if avail and avail != NULL:
            try:
                bedingungen = json.loads(avail).get("c", [])
            except json.JSONDecodeError:
                fehler_liste.append(f"Aktivität {mid}: Voraussetzung ist kein gültiges JSON")
                continue
            for b in bedingungen:
                if b.get("type") == "completion" and str(b.get("cm")) not in module:
                    fehler_liste.append(f"Aktivität {mid}: Voraussetzung zeigt auf unbekannte Aktivität {b.get('cm')}")

    # 6. Dateien: Inhalt im Archiv, SHA-1 und Größe stimmen
    datei_ids: set[str] = set()
    referenziert: set[str] = set()
    datei_saetze: list[ET.Element] = []
    anzahl = 0
    liste = baeume.get("files.xml")
    if liste is None:
        fehler_liste.append("files.xml fehlt")
    else:
        for f in liste.iterfind("file"):
            fid = f.get("id")
            datei_ids.add(fid)
            datei_saetze.append(f)
            h = f.findtext("contenthash")
            if h == LEERER_HASH:
                continue  # Verzeichniseintrag "."
            anzahl += 1
            pfad_arch = f"files/{h[:2]}/{h}"
            referenziert.add(pfad_arch)
            if pfad_arch not in dateien:
                fehler_liste.append(f"Datei {fid} ({f.findtext('filename')}): Inhalt fehlt im Archiv")
            elif hashlib.sha1(dateien[pfad_arch]).hexdigest() != h or len(dateien[pfad_arch]) != int(f.findtext("filesize")):
                fehler_liste.append(f"Datei {fid} ({f.findtext('filename')}): SHA-1 oder Größe stimmt nicht")
        unbenutzt = {p for p in dateien if p.startswith("files/")} - referenziert
        if unbenutzt:
            fehler_liste.append(f"{len(unbenutzt)} Datei(en) im Archiv ohne Eintrag in files.xml")
        ok.append(f"{anzahl} Dateien: Inhalt, SHA-1 und Größe stimmen")

    # 7. Verweise aus inforef.xml zeigen auf vorhandene Dateien und Bewertungselemente
    noten_ids = set()
    for name, baum in baeume.items():
        if name.endswith("grades.xml") or name == "gradebook.xml":
            noten_ids |= {g.get("id") for g in baum.iter("grade_item")}
    for name, baum in baeume.items():
        if name.endswith("inforef.xml"):
            for fid in baum.findall("fileref/file/id"):
                if fid.text not in datei_ids:
                    fehler_liste.append(f"{name}: verweist auf unbekannte Datei {fid.text}")
            for gid in baum.findall("grade_itemref/grade_item/id"):
                if gid.text not in noten_ids:
                    fehler_liste.append(f"{name}: verweist auf unbekanntes Bewertungselement {gid.text}")
    ok.append("Verweise (inforef.xml) zeigen auf vorhandene Dateien und Bewertungselemente")

    # 8. SCORM: Startobjekt vorhanden, Paket und Startdatei im Bereich content
    scorm_ok = 0
    for mid, (verz, typ) in module.items():
        if typ != "scorm":
            continue
        akt = baeume[f"{verz}/scorm.xml"]
        ctx = akt.get("contextid")
        sc = akt.find("scorm")
        scoes = {s.get("id"): s for s in sc.iterfind("scoes/sco")}
        start = scoes.get(sc.findtext("launch"))
        if start is None or not start.findtext("launch"):
            fehler_liste.append(f"SCORM {mid}: Startobjekt (launch) fehlt oder hat keine Startdatei")
            continue
        start_datei = start.findtext("launch")
        inhalt = {(f.findtext("filepath") + f.findtext("filename")) for f in datei_saetze
                  if f.findtext("contextid") == ctx and f.findtext("component") == "mod_scorm" and f.findtext("filearea") == "content"}
        feld = "source" if sc.findtext("scormtype") == "localsync" else "filename"
        paket = [f for f in datei_saetze if f.findtext("contextid") == ctx and f.findtext("filearea") == "package"
                 and f.findtext(feld) == sc.findtext("reference")]
        if "/" + start_datei not in inhalt:
            fehler_liste.append(f"SCORM {mid}: Startdatei {start_datei} fehlt im Bereich content")
        elif not paket or paket[0].findtext("contenthash") != sc.findtext("sha1hash"):
            fehler_liste.append(f"SCORM {mid}: Paket fehlt oder SHA-1 im scorm.xml stimmt nicht")
        else:
            scorm_ok += 1
    if scorm_ok:
        ok.append(f"{scorm_ok} SCORM-Aktivität(en): Startobjekt, Startdatei und Paket vorhanden")
    links = [baeume[f"{v}/scorm.xml"].findtext("scorm/reference") for v, typ in module.values()
             if typ == "scorm" and baeume[f"{v}/scorm.xml"].findtext("scorm/scormtype") == "localsync"]
    if len(set(links)) != len(links):
        fehler_liste.append("Zwei SCORM-Aktivitäten laden ihr Paket über denselben Link")
    elif links:
        ok.append(f"{len(links)} SCORM-Link(s), jeder nur einmal vergeben")

    # 9. Tests: Fragenkategorien und Fragen der Test-Aktivitäten liegen in questions.xml
    fb = baeume.get("questions.xml")
    kategorien = {c.get("id"): c for c in fb.iterfind("question_category")} if fb is not None else {}
    eintraege = {q.get("id") for c in kategorien.values() for q in c.iterfind("question_bank_entries/question_bank_entry")}
    for mid, (verz, typ) in module.items():
        if typ != "quiz":
            continue
        refs = {r.text for r in baeume[f"{verz}/quiz.xml"].iter("questionbankentryid")}
        kats = {k.text for k in baeume[f"{verz}/inforef.xml"].findall("question_categoryref/question_category/id")}
        fehlend = (refs - eintraege) | (kats - set(kategorien))
        fremd = [k for k in kats & set(kategorien) if kategorien[k].findtext("contextinstanceid") != mid]
        if fehlend:
            fehler_liste.append(f"Test {mid}: {len(fehlend)} Frage(n) oder Kategorie(n) fehlen in questions.xml")
        elif fremd:
            fehler_liste.append(f"Test {mid}: Fragenkategorien gehören zu einer anderen Aktivität")
        elif not refs:
            fehler_liste.append(f"Test {mid}: enthält keine Fragen")
        else:
            ok.append(f"Test {mid}: {len(refs)} Fragen und {len(kats)} Fragenkategorien vorhanden")

    return _ausgabe(fehler_liste, ok)


def _ausgabe(fehler_liste: list[str], ok: list[str]) -> int:
    for zeile in ok:
        print(f"OK     {zeile}")
    for zeile in fehler_liste:
        print(f"FEHLER {zeile}")
    if fehler_liste:
        print(f"Prüfung NICHT bestanden ({len(fehler_liste)} Fehler).")
        return 1
    print("Prüfung bestanden.")
    return 0


def links_auslesen(pfad: Path, ordner: Path | None = None) -> int:
    """Listet die SCORM-Links einer ByCS-Sicherung und ordnet sie über den SHA-1 den ZIPs im Teamordner zu (dort liegen die zugestellten Pakete)."""
    ordner = ordner or Path(linkseite.teamordner() or unterrichtsmaterial.gebaut("BYCS-SYNC"))
    zips = {hashlib.sha1(z.read_bytes()).hexdigest(): z.relative_to(ordner).as_posix() for z in ordner.rglob("*_scorm.zip")}
    with tarfile.open(pfad, "r:gz") as tar:
        dateien = {m.name: tar.extractfile(m).read() for m in tar.getmembers() if m.isfile()}
    mb = ET.fromstring(dateien["moodle_backup.xml"])
    gesehen: dict[str, str] = {}
    probleme = 0
    for a in mb.iterfind("information/contents/activities/activity"):
        if a.findtext("modulename") != "scorm":
            continue
        sc = ET.fromstring(dateien[f"{a.findtext('directory')}/scorm.xml"]).find("scorm")
        link, h = sc.findtext("reference"), sc.findtext("sha1hash")
        print(f"{sc.findtext('name')}\n  Typ:   {sc.findtext('scormtype')}\n  Link:  {link}\n"
              f"  Paket: {zips.get(h, 'kein ZIP im Teamordner mit diesem Inhalt (veraltet oder fremd)')}")
        if link in gesehen:
            probleme += 1
            print(f"  ACHTUNG: derselbe Link wie bei '{gesehen[link]}'. Jedes Paket braucht seinen eigenen Link.")
        gesehen.setdefault(link, sc.findtext("name"))
        if h not in zips:
            probleme += 1
    return 1 if probleme else 0


def main():
    parser = argparse.ArgumentParser(description="Moodle-Kurssicherung (.mbz) bauen oder prüfen.")
    parser.add_argument("--plan", help="Kursplan: Name (z. B. Kurs-ALLE10-PuG) oder Pfad zur Datei")
    parser.add_argument("--out", help="Zieldatei (.mbz); Standard: BYCS-SYNC/Kurse/<Klasse>[/<Fach>]/<Name des Kursplans>.mbz, außer auf GitHub im Temp-Ordner")
    parser.add_argument("--pruefen", help="vorhandene .mbz nur prüfen")
    parser.add_argument("--links", help="SCORM-Links einer ByCS-Sicherung auflisten und den ZIPs in BYCS-SYNC zuordnen")
    args = parser.parse_args()

    if args.pruefen:
        sys.exit(pruefen(Path(args.pruefen)))
    if args.links:
        sys.exit(links_auslesen(Path(args.links)))
    if not args.plan:
        parser.error("--plan oder --pruefen angeben")

    ziel = bauen_aus_plan(args.plan, Path(args.out) if args.out else None)
    sys.exit(pruefen(ziel))


def bauen_aus_plan(plan: str, ziel: Path | None = None) -> Path:
    """Baut die Kurssicherung zu einem Kursplan (Name wie Kurs-ALLE10-PuG oder Pfad). Auch für paket-zustellen.py.
    Fehler: SystemExit mit Text (wie fehler())."""
    name = plan[:-5] if plan.endswith(".json") else plan
    plan_pfad = next((k for k in [Path(plan), ROOT / plan] + [ROOT / p for p in unterrichtsmaterial.kursplaene() if unterrichtsmaterial.kursname(p) == name]
                      if k.is_file()), None)
    if plan_pfad is None:
        fehler(f"Kursplan nicht gefunden: {plan} (erwartet: Unterricht/<Klasse>[/<Fach>]/Kurs-….json)")
    daten = lade_plan(plan_pfad)
    try:
        plan_rel = plan_pfad.resolve().relative_to(Path(ROOT).resolve()).as_posix()
    except ValueError:   # Kursplan außerhalb des Projektordners: direkt in Kurse/
        plan_rel = plan_pfad.name
    ziel = ziel or Path(unterrichtsmaterial.gebaut(unterrichtsmaterial.kursdatei(plan_rel)))
    zahlen = baue(daten, ziel)
    print(f"Gebaut: {ziel} ({zahlen['abschnitte']} Abschnitte inkl. Abschnitt 0, "
          f"{zahlen['aktivitaeten']} Aktivitäten, davon {zahlen['scorm']} SCORM und {zahlen['tests']} Test(s))")
    return ziel


if __name__ == "__main__":
    main()
