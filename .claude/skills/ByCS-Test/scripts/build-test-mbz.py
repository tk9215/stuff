#!/usr/bin/env python3
"""Baut aus einer geprüften Moodle-XML-Quizdatei eine fertige Test-Aktivität (.mbz) für die ByCS.

  python .claude/skills/ByCS-Test/scripts/build-test-mbz.py <Test-Thema>/Fragen-<Thema>.xml --thema "<Thema>" --zeit <Minuten>
         [--abschnitt <Nummer>] [--out <datei.mbz>] [--vorlage <Vorlage.mbz>] [--keine-anleitung]
  --thema ist der Titel mit Umlauten. Der Ordner heißt dazu Test-<Thema als Ordnername> (Namensregel in
  .claude/gemeinsam/scripts/unterrichtsmaterial.py). Beim erneuten Bau kann --thema entfallen: Es steht in der Anleitung index.html.
  python .claude/skills/ByCS-Test/scripts/build-test-mbz.py --pruefen <datei.mbz>

Legt Test-<Thema>.mbz und die Anleitung index.html (Vorlage ../templates/test-anleitung.html) in den Ordner der XML.
Die Lehrkraft stellt die .mbz im Kurs per "Wiederherstellen" her: Es entsteht der Test "Test - <Thema>"
mit allen Fragen in seiner eigenen Fragensammlung.

Alle Einstellungen (Versuche, Bewertung, Überprüfungsoptionen, Kennwort, Safe Exam Browser, Fragen pro Seite,
Notenstufen) stammen aus der Vorlage ../templates/Test-Vorlage.mbz, einer Aktivitätssicherung aus der ByCS.
Ersetzt werden nur Name, Arbeitszeit, Fragen, Höchstpunktzahl und die Grenzen der Notenstufen (gleiche
Prozentsätze wie in der Vorlage, bezogen auf die neue Höchstpunktzahl). Eine neue Vorlage: Datei austauschen.

Unterstützte Fragetypen: multichoice, truefalse, shortanswer, matching, numerical, multianswer (Lückentext),
gapselect, ddwtos. Nur Standardbibliothek.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import io
import random
import re
import string
import sys
import tarfile
import time
import xml.etree.ElementTree as ET
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from xml.sax.saxutils import escape

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "gemeinsam" / "scripts"))
import unterrichtsmaterial  # noqa: E402  (.claude/gemeinsam/scripts: Namensregel)
from mbz import Archiv, IdGen  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")

SKILL = Path(__file__).resolve().parent.parent
VORLAGE_STANDARD = SKILL / "templates" / "Test-Vorlage.mbz"
ANLEITUNG = SKILL / "templates" / "test-anleitung.html"

NULL = "$@NULL@$"
XML_KOPF = '<?xml version="1.0" encoding="UTF-8"?>\n'
FORMATE = {"moodle_auto_format": 0, "html": 1, "plain_text": 2, "markdown": 4}


class Fehler(Exception):
    pass


def t(wert) -> str:
    """Wert für XML-Text: None wird zu NULL, sonst maskiert (&, <, >)."""
    return NULL if wert is None else escape(str(wert))


def zahl(x, stellen: int = 7) -> str:
    return f"{Decimal(str(x)).quantize(Decimal(1).scaleb(-stellen), rounding=ROUND_HALF_UP):f}"


# ---------------------------------------------------------------------------
# Vorlage lesen


class Vorlage:
    def __init__(self, pfad: Path):
        if not pfad.exists():
            raise Fehler(f"Vorlage fehlt: {pfad}")
        with tarfile.open(pfad, "r:gz") as tar:
            self.dateien = {m.name: tar.extractfile(m).read().decode("utf-8") for m in tar.getmembers() if m.isfile()}
        quiz = [n for n in self.dateien if re.fullmatch(r"activities/quiz_\d+/quiz\.xml", n)]
        if len(quiz) != 1:
            raise Fehler("Die Vorlage muss genau eine Test-Aktivität (quiz) enthalten.")
        self.ordner = quiz[0].rsplit("/", 1)[0]
        self.quiz = self.dateien[quiz[0]]
        self.modul = self.dateien[f"{self.ordner}/module.xml"]
        self.noten = self.dateien[f"{self.ordner}/grades.xml"]
        self.manifest = self.dateien["moodle_backup.xml"]
        q = ET.fromstring(self.quiz)
        self.einst = {k.tag: (k.text or "") for k in q.find("quiz") if len(k) == 0}
        seb = q.find("quiz/subplugin_quizaccess_seb_quiz/quizaccess_seb_quizsettings")
        self.seb = {k.tag: (k.text or "") for k in seb} if seb is not None else {}
        self.quiz_id = q.get("id")
        self.modul_id = q.get("moduleid")
        self.ctx_id = q.get("contextid")
        self.summe = Decimal(q.findtext("quiz/sumgrades"))
        self.pro_seite = int(q.findtext("quiz/questionsperpage") or 0)
        self.stufen = []  # (Text, Format, min-Anteil, max-Anteil)
        for fb in q.findall("quiz/feedbacks/feedback"):
            self.stufen.append((fb.findtext("feedbacktext"), fb.findtext("feedbacktextformat"),
                                Decimal(fb.findtext("mingrade")) / self.summe,
                                Decimal(fb.findtext("maxgrade")) / self.summe))
        m = ET.fromstring(self.manifest)
        self.wwwroot = m.findtext("information/original_wwwroot")
        self.sektion_id = ET.fromstring(self.modul).findtext("sectionid")
        self.abschnitt = ET.fromstring(self.modul).findtext("sectionnumber")
        fragen = self.dateien.get("questions.xml", "")
        owner = re.search(r"<ownerid>(\d+)</ownerid>", fragen)
        self.besitzer = owner.group(1) if owner else "2"

# ---------------------------------------------------------------------------
# Moodle-XML lesen


def text(el, pfad: str = "text", standard: str = "") -> str:
    if el is None:
        return standard
    x = el.find(pfad)
    return standard if x is None or x.text is None else x.text


def fmt(el, standard: str = "html") -> int:
    if el is None:
        return FORMATE[standard]
    return FORMATE.get(el.get("format", standard), 1)


def wahr(wert, standard: bool = False) -> bool:
    if wert is None:
        return standard
    return wert.strip().lower() in ("1", "true", "yes")


def kat_pfad(roh: str) -> list[str]:
    teile = [p for p in roh.split("/") if p]
    while teile and teile[0].startswith("$") and teile[0].endswith("$"):
        teile.pop(0)
    if teile and teile[0] == "top":
        teile.pop(0)
    return teile


def lies_quiz(pfad: Path):
    try:
        wurzel = ET.parse(pfad).getroot()
    except ET.ParseError as e:
        raise Fehler(f"{pfad}: kein gültiges XML ({e}).")
    if wurzel.tag != "quiz":
        raise Fehler(f"{pfad}: Wurzelelement <{wurzel.tag}> statt <quiz>.")
    fragen, kategorien, aktuell = [], [], []
    for q in wurzel.findall("question"):
        typ = q.get("type")
        if typ == "category":
            aktuell = kat_pfad(text(q.find("category")))
            if aktuell and aktuell not in [k for k, _ in kategorien]:
                kategorien.append((aktuell, text(q.find("info"))))
            continue
        if q.find(".//file") is not None:
            raise Fehler(f"Frage \"{text(q.find('name'))}\": eingebettete Dateien/Bilder werden nicht unterstützt.")
        fragen.append((q, list(aktuell)))
    if not fragen:
        raise Fehler(f"{pfad}: keine Fragen gefunden.")
    return fragen, kategorien

# ---------------------------------------------------------------------------
# Lückentext (Cloze) zerlegen

CLOZE = re.compile(r"\{(\d*):([A-Z_]+):((?:\\.|[^}\\])*)\}")
CLOZE_TYPEN = {
    "MULTICHOICE": ("multichoice", 0, 1, 0), "MC": ("multichoice", 0, 1, 0),
    "MULTICHOICE_V": ("multichoice", 1, 1, 0), "MCV": ("multichoice", 1, 1, 0),
    "MULTICHOICE_H": ("multichoice", 2, 1, 0), "MCH": ("multichoice", 2, 1, 0),
    "MULTICHOICE_S": ("multichoice", 0, 1, 1), "MCS": ("multichoice", 0, 1, 1),
    "MULTICHOICE_VS": ("multichoice", 1, 1, 1), "MCVS": ("multichoice", 1, 1, 1),
    "MULTICHOICE_HS": ("multichoice", 2, 1, 1), "MCHS": ("multichoice", 2, 1, 1),
    "MULTIRESPONSE": ("multichoice", 1, 0, 0), "MR": ("multichoice", 1, 0, 0),
    "MULTIRESPONSE_H": ("multichoice", 2, 0, 0), "MRH": ("multichoice", 2, 0, 0),
    "MULTIRESPONSE_S": ("multichoice", 1, 0, 1), "MRS": ("multichoice", 1, 0, 1),
    "MULTIRESPONSE_HS": ("multichoice", 2, 0, 1), "MRHS": ("multichoice", 2, 0, 1),
    "SHORTANSWER": ("shortanswer", 0), "SA": ("shortanswer", 0), "MW": ("shortanswer", 0),
    "SHORTANSWER_C": ("shortanswer", 1), "SAC": ("shortanswer", 1), "MWC": ("shortanswer", 1),
    "NUMERICAL": ("numerical",), "NM": ("numerical",),
}


def teile_unmaskiert(s: str, zeichen: str) -> list[str]:
    teile, akt, i = [], "", 0
    while i < len(s):
        if s[i] == "\\" and i + 1 < len(s):
            akt += s[i:i + 2]
            i += 2
            continue
        if s[i] == zeichen:
            teile.append(akt)
            akt = ""
        else:
            akt += s[i]
        i += 1
    teile.append(akt)
    return teile


def entmaske(s: str) -> str:
    return re.sub(r"\\(.)", r"\1", s).strip()


def zerlege_cloze(quelltext: str, name: str):
    luecken = []

    def ersetze(m):
        gewicht = int(m.group(1) or 1)
        art = m.group(2)
        if art not in CLOZE_TYPEN:
            raise Fehler(f"Frage \"{name}\": Lückentyp {art} wird nicht unterstützt.")
        antworten = []
        for teil in teile_unmaskiert(m.group(3), "~"):
            if not teil.strip():
                continue
            antwort, *fb = teile_unmaskiert(teil, "#")
            antwort = antwort.strip()
            anteil = 0.0
            if antwort.startswith("="):
                anteil, antwort = 1.0, antwort[1:]
            else:
                p = re.match(r"%(-?[\d.]+)%(.*)", antwort, re.S)
                if p:
                    anteil, antwort = float(p.group(1)) / 100, p.group(2)
            antworten.append((entmaske(antwort), anteil, entmaske("#".join(fb))))
        if not antworten:
            raise Fehler(f"Frage \"{name}\": leere Lücke {m.group(0)}.")
        luecken.append({"quelle": m.group(0), "gewicht": gewicht, "art": CLOZE_TYPEN[art], "antworten": antworten})
        return "{#%d}" % len(luecken)

    text_neu = CLOZE.sub(ersetze, quelltext)
    if not luecken:
        raise Fehler(f"Frage \"{name}\": Lückentext ohne Lücke.")
    return text_neu, luecken

# ---------------------------------------------------------------------------
# questions.xml schreiben


class Fragensammlung:
    def __init__(self, vorlage: Vorlage, ids: IdGen, jetzt: int, ctx: int, modul: int, name: str):
        self.v, self.ids, self.jetzt, self.ctx, self.modul = vorlage, ids, jetzt, ctx, modul
        self.host = re.sub(r"^https?://", "", vorlage.wwwroot or "lernplattform.bycs.de").strip("/")
        self.kats: list[dict] = []
        top = self.kategorie("top", None, sortorder=0)
        self.top = top
        self.standard = self.kategorie(f"Standard für {name}", top,
                                       info=f"Standardkategorie für Fragen, die im Kontext '{name}' freigegeben sind.")

    def stamp(self) -> str:
        zeit = time.strftime("%y%m%d%H%M%S", time.localtime(self.jetzt))
        zufall = "".join(random.choice(string.ascii_letters + string.digits) for _ in range(6))
        return f"{self.host}+{zeit}+{zufall}"

    def kategorie(self, name, eltern, info="", sortorder=999):
        k = {"id": self.ids.neu(), "name": name, "eltern": eltern["id"] if eltern else 0, "info": info,
             "sortorder": sortorder, "stamp": self.stamp(), "eintraege": []}
        self.kats.append(k)
        return k

    # -- Bausteine ----------------------------------------------------------
    def antwort(self, aid, textwert, textformat, anteil, fb, fbformat) -> str:
        return (f'                    <answer id="{aid}">\n'
                f"                      <answertext>{t(textwert)}</answertext>\n"
                f"                      <answerformat>{textformat}</answerformat>\n"
                f"                      <fraction>{zahl(anteil)}</fraction>\n"
                f"                      <feedback>{t(fb)}</feedback>\n"
                f"                      <feedbackformat>{fbformat}</feedbackformat>\n"
                f"                    </answer>\n")

    def antworten(self, liste) -> str:
        return "                  <answers>\n" + "".join(liste) + "                  </answers>\n"

    def rueckmeldungen(self, q) -> str:
        teile = []
        for tag in ("correctfeedback", "partiallycorrectfeedback", "incorrectfeedback"):
            el = q.find(tag)
            teile.append(f"                    <{tag}>{t(text(el))}</{tag}>\n"
                         f"                    <{tag}format>{fmt(el)}</{tag}format>\n")
        return "".join(teile)

    def frage(self, qid, eltern, name, qtext, qformat, gf, gfformat, punkte, strafe, qtype, plugin, hinweise="") -> str:
        return (f'              <question id="{qid}">\n'
                f"                <parent>{eltern}</parent>\n"
                f"                <name>{t(name)}</name>\n"
                f"                <questiontext>{t(qtext)}</questiontext>\n"
                f"                <questiontextformat>{qformat}</questiontextformat>\n"
                f"                <generalfeedback>{t(gf)}</generalfeedback>\n"
                f"                <generalfeedbackformat>{gfformat}</generalfeedbackformat>\n"
                f"                <defaultmark>{zahl(punkte)}</defaultmark>\n"
                f"                <penalty>{zahl(strafe)}</penalty>\n"
                f"                <qtype>{qtype}</qtype>\n"
                f"                <length>1</length>\n"
                f"                <stamp>{self.stamp()}</stamp>\n"
                f"                <timecreated>{self.jetzt}</timecreated>\n"
                f"                <timemodified>{self.jetzt}</timemodified>\n"
                f"                <createdby>{self.v.besitzer}</createdby>\n"
                f"                <modifiedby>{self.v.besitzer}</modifiedby>\n"
                f"{plugin}"
                f"                <plugin_qbank_comment_question>\n                  <comments>\n                  </comments>\n"
                f"                </plugin_qbank_comment_question>\n"
                f"                <plugin_qbank_customfields_question>\n                  <customfields>\n"
                f"                  </customfields>\n                </plugin_qbank_customfields_question>\n"
                f"                <question_hints>\n{hinweise}                </question_hints>\n"
                f"                <tags>\n                </tags>\n"
                f"              </question>\n")

    def eintrag(self, kat, frage_xml, qid, idnumber=None, status="ready", naechste="2"):
        kat["eintraege"].append(
            f'      <question_bank_entry id="{self.ids.neu()}">\n'
            f"        <questioncategoryid>{kat['id']}</questioncategoryid>\n"
            f"        <idnumber>{t(idnumber)}</idnumber>\n"
            f"        <ownerid>{self.v.besitzer}</ownerid>\n"
            f"        <nextversion>{naechste}</nextversion>\n"
            f"        <question_version>\n"
            f'          <question_versions id="{self.ids.neu()}">\n'
            f"            <version>1</version>\n"
            f"            <status>{status}</status>\n"
            f"            <questions>\n{frage_xml}            </questions>\n"
            f"          </question_versions>\n"
            f"        </question_version>\n"
            f"      </question_bank_entry>\n")
        return kat["eintraege"][-1]

    def hinweise(self, q) -> str:
        teile = []
        for h in q.findall("hint"):
            nc = "1" if h.find("shownumcorrect") is not None else NULL
            cw = "1" if h.find("clearwrong") is not None else NULL
            opt = h.findtext("options")
            teile.append(f'                  <question_hint id="{self.ids.neu()}">\n'
                         f"                    <hint>{t(text(h))}</hint>\n"
                         f"                    <hintformat>{fmt(h)}</hintformat>\n"
                         f"                    <shownumcorrect>{nc}</shownumcorrect>\n"
                         f"                    <clearwrong>{cw}</clearwrong>\n"
                         f"                    <options>{t(opt) if opt is not None else NULL}</options>\n"
                         f"                  </question_hint>\n")
        return "".join(teile)

    # -- Fragetypen ---------------------------------------------------------
    def plugin_multichoice(self, antworten, single, mischen, nummerierung, layout, q=None, nc=0, std=1):
        rm = self.rueckmeldungen(q) if q is not None else "".join(
            f"                    <{tag}></{tag}>\n                    <{tag}format>1</{tag}format>\n"
            for tag in ("correctfeedback", "partiallycorrectfeedback", "incorrectfeedback"))
        return ("                <plugin_qtype_multichoice_question>\n" + self.antworten(antworten) +
                f'                  <multichoice id="{self.ids.neu()}">\n'
                f"                    <layout>{layout}</layout>\n"
                f"                    <single>{single}</single>\n"
                f"                    <shuffleanswers>{mischen}</shuffleanswers>\n"
                f"{rm}"
                f"                    <answernumbering>{t(nummerierung)}</answernumbering>\n"
                f"                    <shownumcorrect>{nc}</shownumcorrect>\n"
                f"                    <showstandardinstruction>{std}</showstandardinstruction>\n"
                f"                  </multichoice>\n"
                "                </plugin_qtype_multichoice_question>\n")

    def plugin_numerical(self, werte, q=None):
        """werte: Liste (Antworttext, Anteil, Feedback, Feedbackformat, Toleranz)."""
        antw, saetze = [], []
        for wert, anteil, fb, fbf, tol in werte:
            aid = self.ids.neu()
            antw.append(self.antwort(aid, wert, 0, anteil, fb, fbf))
            saetze.append(f'                    <numerical_record id="{self.ids.neu()}">\n'
                          f"                      <answer>{aid}</answer>\n"
                          f"                      <tolerance>{t(tol)}</tolerance>\n"
                          f"                    </numerical_record>\n")
        einheiten = ""
        if q is not None:
            for u in q.findall("units/unit"):
                einheiten += (f'                    <numerical_unit id="{self.ids.neu()}">\n'
                              f"                      <multiplier>{t(u.findtext('multiplier', '1'))}</multiplier>\n"
                              f"                      <unit>{t(u.findtext('unit_name', ''))}</unit>\n"
                              f"                    </numerical_unit>\n")
        g = (lambda tag, std: (q.findtext(tag) if q is not None and q.findtext(tag) is not None else std))
        return ("                <plugin_qtype_numerical_question>\n" + self.antworten(antw) +
                f"                  <numerical_units>\n{einheiten}                  </numerical_units>\n"
                f"                  <numerical_options>\n"
                f'                    <numerical_option id="{self.ids.neu()}">\n'
                f"                      <showunits>{t(g('showunits', '3'))}</showunits>\n"
                f"                      <unitsleft>{t(g('unitsleft', '0'))}</unitsleft>\n"
                f"                      <unitgradingtype>{t(g('unitgradingtype', '0'))}</unitgradingtype>\n"
                f"                      <unitpenalty>{zahl(g('unitpenalty', '0.1'))}</unitpenalty>\n"
                f"                    </numerical_option>\n"
                f"                  </numerical_options>\n"
                f"                  <numerical_records>\n{''.join(saetze)}                  </numerical_records>\n"
                "                </plugin_qtype_numerical_question>\n")

    def plugin_shortanswer(self, werte, gross):
        antw = [self.antwort(self.ids.neu(), w, 0, a, fb, fbf) for w, a, fb, fbf in werte]
        return ("                <plugin_qtype_shortanswer_question>\n" + self.antworten(antw) +
                f'                  <shortanswer id="{self.ids.neu()}">\n'
                f"                    <usecase>{gross}</usecase>\n"
                f"                  </shortanswer>\n"
                "                </plugin_qtype_shortanswer_question>\n")

    def xml_antworten(self, q):
        return [(text(a), float(a.get("fraction", "0")) / 100, text(a.find("feedback")), fmt(a.find("feedback")),
                 fmt(a, "moodle_auto_format"), a) for a in q.findall("answer")]

    def neue_frage(self, q, pfad, infos) -> tuple[int, Decimal]:
        """Legt eine Frage an. Gibt (Eintrags-ID, Punkte) zurück."""
        typ = q.get("type")
        name = text(q.find("name")).strip()
        qt_el = q.find("questiontext")
        qtext, qformat = text(qt_el), fmt(qt_el)
        gf_el = q.find("generalfeedback")
        gf, gfformat = text(gf_el), fmt(gf_el)
        punkte = Decimal(q.findtext("defaultgrade") or "1")
        strafe = q.findtext("penalty") or "0.3333333"
        status = "hidden" if wahr(q.findtext("hidden")) else "ready"
        idnumber = q.findtext("idnumber") or None
        kat = self.standard  # alle Fragen in die Standardkategorie des Tests, Kategorien der XML zählen nicht
        qid = self.ids.neu()
        nc = 1 if q.find("shownumcorrect") is not None else 0
        hinw = self.hinweise(q)

        if typ == "multichoice":
            antw = [self.antwort(self.ids.neu(), w, af, a, fb, fbf) for w, a, fb, fbf, af, _ in self.xml_antworten(q)]
            plugin = self.plugin_multichoice(antw, 1 if wahr(q.findtext("single"), True) else 0,
                                             1 if wahr(q.findtext("shuffleanswers"), True) else 0,
                                             q.findtext("answernumbering") or "abc", 0, q, nc,
                                             1 if wahr(q.findtext("showstandardinstruction"), True) else 0)
            qtype = "multichoice"
        elif typ == "truefalse":
            werte = {}
            for w, a, fb, fbf, _, _ in self.xml_antworten(q):
                werte[w.strip().lower()] = (a, fb, fbf)
            if set(werte) != {"true", "false"}:
                raise Fehler(f"Frage \"{name}\": Wahr/Falsch braucht die Antworten true und false.")
            ja, nein = self.ids.neu(), self.ids.neu()
            antw = [self.antwort(ja, "Wahr", 0, *werte["true"]), self.antwort(nein, "Falsch", 0, *werte["false"])]
            plugin = ("                <plugin_qtype_truefalse_question>\n" + self.antworten(antw) +
                      f'                  <truefalse id="{self.ids.neu()}">\n'
                      f"                    <trueanswer>{ja}</trueanswer>\n"
                      f"                    <falseanswer>{nein}</falseanswer>\n"
                      f"                    <showstandardinstruction>"
                      f"{1 if wahr(q.findtext('showstandardinstruction')) else 0}</showstandardinstruction>\n"
                      f"                  </truefalse>\n"
                      "                </plugin_qtype_truefalse_question>\n")
            qtype = "truefalse"
        elif typ == "shortanswer":
            werte = [(w, a, fb, fbf) for w, a, fb, fbf, _, _ in self.xml_antworten(q)]
            plugin = self.plugin_shortanswer(werte, 1 if wahr(q.findtext("usecase")) else 0)
            qtype = "shortanswer"
        elif typ == "numerical":
            werte = [(w, a, fb, fbf, el.findtext("tolerance") or "0") for w, a, fb, fbf, _, el in self.xml_antworten(q)]
            plugin = self.plugin_numerical(werte, q)
            qtype = "numerical"
        elif typ == "matching":
            paare = q.findall("subquestion")
            if len(paare) < 2:
                raise Fehler(f"Frage \"{name}\": Zuordnung braucht mindestens zwei Paare.")
            matches = "".join(
                f'                    <match id="{self.ids.neu()}">\n'
                f"                      <questiontext>{t(text(s))}</questiontext>\n"
                f"                      <questiontextformat>{fmt(s)}</questiontextformat>\n"
                f"                      <answertext>{t(text(s, 'answer/text'))}</answertext>\n"
                f"                    </match>\n" for s in paare)
            plugin = ("                <plugin_qtype_match_question>\n"
                      f'                  <matchoptions id="{self.ids.neu()}">\n'
                      f"                    <shuffleanswers>{1 if wahr(q.findtext('shuffleanswers'), True) else 0}</shuffleanswers>\n"
                      f"{self.rueckmeldungen(q)}"
                      f"                    <shownumcorrect>{nc}</shownumcorrect>\n"
                      f"                  </matchoptions>\n"
                      f"                  <matches>\n{matches}                  </matches>\n"
                      "                </plugin_qtype_match_question>\n")
            qtype = "match"
        elif typ in ("ddwtos", "gapselect"):
            tag = "dragbox" if typ == "ddwtos" else "selectoption"
            optionen = q.findall(tag)
            if not optionen:
                raise Fehler(f"Frage \"{name}\": keine Auswahloptionen (<{tag}>).")
            for n in {int(x) for x in re.findall(r"\[\[(\d+)\]\]", qtext)}:
                if n < 1 or n > len(optionen):
                    raise Fehler(f"Frage \"{name}\": Lücke [[{n}]] hat keine passende Option.")
            antw = []
            for o in optionen:
                gruppe = (o.findtext("group") or "1").strip()
                if typ == "ddwtos":
                    unendlich = "b:1" if o.find("infinite") is not None else "b:0"
                    fb = f'O:8:"stdClass":2:{{s:9:"draggroup";s:{len(gruppe)}:"{gruppe}";s:8:"infinite";{unendlich};}}'
                else:
                    fb = gruppe
                antw.append(self.antwort(self.ids.neu(), text(o), 1, 0, fb, 0))
            plugin = (f"                <plugin_qtype_{typ}_question>\n" + self.antworten(antw) +
                      f'                  <{typ} id="{self.ids.neu()}">\n'
                      f"                    <shuffleanswers>{1 if wahr(q.findtext('shuffleanswers'), True) else 0}</shuffleanswers>\n"
                      f"{self.rueckmeldungen(q)}"
                      f"                    <shownumcorrect>{nc}</shownumcorrect>\n"
                      f"                  </{typ}>\n"
                      f"                </plugin_qtype_{typ}_question>\n")
            qtype = typ
        elif typ == "multianswer":
            qtext_neu, luecken = zerlege_cloze(qtext, name)
            punkte = Decimal(sum(l["gewicht"] for l in luecken))
            unter_ids, unter_xml = [], []
            for l in luecken:
                uid = self.ids.neu()
                unter_ids.append(uid)
                art = l["art"]
                if art[0] == "multichoice":
                    antw = [self.antwort(self.ids.neu(), w, 1, a, fb, 1) for w, a, fb in l["antworten"]]
                    plugin_u = self.plugin_multichoice(antw, art[2], art[3], "0", art[1], None, 0, 0)
                elif art[0] == "shortanswer":
                    plugin_u = self.plugin_shortanswer([(w, a, fb, 1) for w, a, fb in l["antworten"]], art[1])
                else:
                    werte = []
                    for w, a, fb in l["antworten"]:
                        wert, _, tol = w.partition(":")
                        werte.append((wert.strip(), a, fb, 1, tol.strip() or "0"))
                    plugin_u = self.plugin_numerical(werte)
                unter_xml.append((uid, self.frage(uid, qid, name, l["quelle"], qformat, "", 1, l["gewicht"], strafe,
                                                  art[0], plugin_u)))
            plugin = ("                <plugin_qtype_multianswer_question>\n"
                      "                  <answers>\n                  </answers>\n"
                      f'                  <multianswer id="{self.ids.neu()}">\n'
                      f"                    <question>{qid}</question>\n"
                      f"                    <sequence>{','.join(map(str, unter_ids))}</sequence>\n"
                      f"                  </multianswer>\n"
                      "                </plugin_qtype_multianswer_question>\n")
            haupt = self.eintrag(kat, self.frage(qid, 0, name, qtext_neu, qformat, gf, gfformat, punkte, strafe,
                                                 "multianswer", plugin, hinw), qid, idnumber, status)
            for uid, x in unter_xml:
                self.eintrag(kat, x, uid, None, status, NULL)
            return int(re.search(r'id="(\d+)"', haupt).group(1)), punkte
        else:
            raise Fehler(f"Frage \"{name}\": Fragetyp \"{typ}\" wird im Test nicht unterstützt "
                         "(nur multichoice, truefalse, shortanswer, matching, numerical, multianswer, gapselect, ddwtos).")

        e = self.eintrag(kat, self.frage(qid, 0, name, qtext, qformat, gf, gfformat, punkte, strafe, qtype, plugin, hinw),
                         qid, idnumber, status)
        return int(re.search(r'id="(\d+)"', e).group(1)), punkte

    def xml(self) -> str:
        teile = [XML_KOPF, "<question_categories>\n"]
        for k in self.kats:
            teile.append(f'  <question_category id="{k["id"]}">\n'
                         f"    <name>{t(k['name'])}</name>\n"
                         f"    <contextid>{self.ctx}</contextid>\n"
                         f"    <contextlevel>70</contextlevel>\n"
                         f"    <contextinstanceid>{self.modul}</contextinstanceid>\n"
                         f"    <info>{t(k['info'])}</info>\n"
                         f"    <infoformat>0</infoformat>\n"
                         f"    <stamp>{k['stamp']}</stamp>\n"
                         f"    <parent>{k['eltern']}</parent>\n"
                         f"    <sortorder>{k['sortorder']}</sortorder>\n"
                         f"    <idnumber>{NULL}</idnumber>\n"
                         f"    <question_bank_entries>\n{''.join(k['eintraege'])}    </question_bank_entries>\n"
                         f"  </question_category>\n")
        teile.append("</question_categories>")
        return "".join(teile)

# ---------------------------------------------------------------------------
# Sicherung bauen


def setze(xml: str, tag: str, wert: str) -> str:
    neu, n = re.subn(rf"<{tag}>[^<]*</{tag}>", f"<{tag}>{wert}</{tag}>", xml, count=1)
    if n != 1:
        raise Fehler(f"Vorlage: <{tag}> nicht gefunden.")
    return neu


def ersetze_block(xml: str, tag: str, inhalt: str) -> str:
    neu, n = re.subn(rf"(\n?[ ]*)<{tag}>.*?</{tag}>", lambda m: f"{m.group(1)}<{tag}>\n{inhalt}    </{tag}>",
                     xml, count=1, flags=re.S)
    if n != 1:
        raise Fehler(f"Vorlage: <{tag}> nicht gefunden.")
    return neu


def ids_tauschen(xml: str, alt_neu: dict[str, str]) -> str:
    """Ersetzt die IDs der Vorlage (Test, Modul, Kontext, Abschnitt) überall durch neue."""
    for alt, neu in alt_neu.items():
        xml = re.sub(rf"(?<![\d]){alt}(?![\d])", neu, xml)
    return xml


def baue(xml_pfad: Path, thema: str, minuten: int, ziel: Path, vorlage_pfad: Path, abschnitt: int | None) -> dict:
    v = Vorlage(vorlage_pfad)
    name = f"Test - {thema.strip()}"
    jetzt = int(time.time())
    ids = IdGen()
    quiz_id, modul_id, ctx_id, sektion_id = (str(ids.neu()) for _ in range(4))
    alt_neu = {v.quiz_id: quiz_id, v.modul_id: modul_id, v.ctx_id: ctx_id, v.sektion_id: sektion_id}

    fragen, kategorien = lies_quiz(xml_pfad)
    infos = {tuple(p): i for p, i in kategorien}
    fs = Fragensammlung(v, ids, jetzt, int(ctx_id), int(modul_id), name)
    slots = []
    for q, pfad in fragen:
        eintrag, punkte = fs.neue_frage(q, pfad, infos)
        slots.append((eintrag, punkte, text(q.find("name")).strip(), q.get("type")))
    summe = sum((p for _, p, _, _ in slots), Decimal(0))

    # quiz.xml aus der Vorlage
    quiz = ids_tauschen(v.quiz, alt_neu)
    quiz = setze(quiz, "name", t(name))
    quiz = setze(quiz, "timelimit", str(minuten * 60))
    quiz = setze(quiz, "sumgrades", zahl(summe, 5))
    quiz = setze(quiz, "grade", zahl(summe, 5))
    quiz = setze(quiz, "timecreated", str(jetzt))
    quiz = setze(quiz, "timemodified", str(jetzt))
    quiz = re.sub(r"(<quizaccess_seb_quizsettings>.*?<timecreated>)\d+(</timecreated>)",
                  rf"\g<1>{jetzt}\g<2>", quiz, flags=re.S)
    inst = []
    for nr, (eintrag, punkte, _, _) in enumerate(slots, 1):
        seite = (nr - 1) // v.pro_seite + 1 if v.pro_seite else 1
        inst.append(f'      <question_instance id="{ids.neu()}">\n'
                    f"        <quizid>{quiz_id}</quizid>\n"
                    f"        <slot>{nr}</slot>\n"
                    f"        <page>{seite}</page>\n"
                    f"        <displaynumber>{NULL}</displaynumber>\n"
                    f"        <requireprevious>0</requireprevious>\n"
                    f"        <maxmark>{zahl(punkte)}</maxmark>\n"
                    f"        <quizgradeitemid>{NULL}</quizgradeitemid>\n"
                    f'        <question_reference id="{ids.neu()}">\n'
                    f"          <usingcontextid>{ctx_id}</usingcontextid>\n"
                    f"          <component>mod_quiz</component>\n"
                    f"          <questionarea>slot</questionarea>\n"
                    f"          <questionbankentryid>{eintrag}</questionbankentryid>\n"
                    f"          <version>{NULL}</version>\n"
                    f"        </question_reference>\n"
                    f"      </question_instance>\n")
    quiz = ersetze_block(quiz, "question_instances", "".join(inst))
    abschnitt_alt = re.search(r"<sections>.*?<section id=\"\d+\">(.*?)</section>", v.quiz, re.S)
    quiz = ersetze_block(quiz, "sections", f'      <section id="{ids.neu()}">{abschnitt_alt.group(1) if abschnitt_alt else chr(10)}</section>\n')
    stufen = []
    noten_liste = [(txt, lo * summe, hi * summe, lo) for txt, _, lo, hi in v.stufen]
    for txt, tf, lo, hi in v.stufen:
        stufen.append(f'      <feedback id="{ids.neu()}">\n'
                      f"        <feedbacktext>{t(txt)}</feedbacktext>\n"
                      f"        <feedbacktextformat>{tf}</feedbacktextformat>\n"
                      f"        <mingrade>{zahl(lo * summe, 5)}</mingrade>\n"
                      f"        <maxgrade>{zahl(hi * summe, 5)}</maxgrade>\n"
                      f"      </feedback>\n")
    quiz = ersetze_block(quiz, "feedbacks", "".join(stufen))

    # Bewertung, Modul, Verweise, Manifest
    note_id = str(ids.neu())
    noten = ids_tauschen(v.noten, alt_neu)
    noten = re.sub(r'<grade_item id="\d+">', f'<grade_item id="{note_id}">', noten, count=1)
    noten = setze(noten, "itemname", t(name))
    noten = setze(noten, "grademax", zahl(summe, 5))
    noten = setze(noten, "timecreated", str(jetzt))
    noten = setze(noten, "timemodified", str(jetzt))

    modul = ids_tauschen(v.modul, alt_neu)
    modul = setze(modul, "added", str(jetzt))
    if abschnitt is not None:
        modul = setze(modul, "sectionnumber", str(abschnitt))

    kat_refs = "".join(f"    <question_category>\n      <id>{k['id']}</id>\n    </question_category>\n" for k in fs.kats)
    inforef = (XML_KOPF + "<inforef>\n  <grade_itemref>\n    <grade_item>\n"
               f"      <id>{note_id}</id>\n    </grade_item>\n  </grade_itemref>\n"
               f"  <question_categoryref>\n{kat_refs}  </question_categoryref>\n</inforef>")

    dateiname = ziel.name
    manifest = ids_tauschen(v.manifest, alt_neu)
    manifest = re.sub(r"<name>[^<]*</name>", f"<name>{t(dateiname)}</name>", manifest, count=1)
    manifest = re.sub(r"(<name>filename</name>\s*<value>)[^<]*(</value>)", rf"\g<1>{t(dateiname)}\g<2>", manifest)
    manifest = setze(manifest, "backup_date", str(jetzt))
    manifest = setze(manifest, "title", t(name))
    manifest = re.sub(r'backup_id="[0-9a-f]+"', f'backup_id="{hashlib.md5(f"{jetzt}{name}".encode()).hexdigest()}"',
                      manifest)

    ordner = f"activities/quiz_{modul_id}"
    arch = Archiv(jetzt)
    for pfad, inhalt in v.dateien.items():
        if pfad in (".ARCHIVE_INDEX",):
            continue
        if pfad.startswith(v.ordner + "/"):
            arch.datei(ordner + pfad[len(v.ordner):], inhalt)
        else:
            arch.datei(pfad, inhalt)
    arch.datei(f"{ordner}/quiz.xml", quiz)
    arch.datei(f"{ordner}/grades.xml", noten)
    arch.datei(f"{ordner}/module.xml", modul)
    arch.datei(f"{ordner}/inforef.xml", inforef)
    arch.datei("moodle_backup.xml", manifest)
    arch.datei("questions.xml", fs.xml())
    arch.datei("moodle_backup.log", "")
    arch.schreibe(ziel)
    return {"name": name, "summe": summe, "slots": slots, "minuten": minuten, "pro_seite": v.pro_seite,
            "abschnitt": abschnitt if abschnitt is not None else v.abschnitt, "noten": noten_liste,
            "vorlage": v, "mbz": ziel.name, "xml": xml_pfad.name, "jetzt": jetzt}

# ---------------------------------------------------------------------------
# Anleitung (index.html)

TYPNAMEN = {"multichoice": "Multiple-Choice", "truefalse": "Wahr/Falsch", "shortanswer": "Kurzantwort",
            "matching": "Zuordnung", "numerical": "Numerisch", "multianswer": "Lückentext (Cloze)",
            "gapselect": "Lückentextauswahl", "ddwtos": "Drag-and-Drop auf Text"}
VERHALTEN = {"deferredfeedback": "Spätere Auswertung", "immediatefeedback": "Direkte Auswertung",
             "interactive": "Mehrfachbeantwortung", "adaptive": "Adaptiver Modus",
             "adaptivenopenalty": "Adaptiver Modus (ohne Abzüge)", "deferredcbm": "Spätere Auswertung mit Sicherheit"}
BEWERTUNG = {"1": "Bester Versuch", "2": "Durchschnittliche Bewertung", "3": "Erster Versuch", "4": "Letzter Versuch"}
NACH_ABGABE = 0x1000  # Überprüfungsoption "Direkt nach dem Versuch"


def de(x, stellen: int = 2) -> str:
    return f"{Decimal(str(x)):.{stellen}f}".replace(".", ",")


def schreibe_anleitung(ziel: Path, info: dict):
    v: Vorlage = info["vorlage"]
    e, seb = v.einst, v.seb
    h = lambda x: html.escape(str(x), quote=False)
    zeile = lambda lab, val: f'      <div class="row"><span class="lab">{h(lab)}</span><span class="val">{val}</span></div>\n'
    versuche = e.get("attempts_number", "0")
    versuche_txt = "unbegrenzt" if versuche == "0" else versuche
    seb_an = seb.get("requiresafeexambrowser", "0") not in ("", "0")
    kennwort = e.get("password", "")

    infos = [f"Erlaubte Versuche: {h(versuche_txt)}", f"Zeitbegrenzung: {info['minuten']} Minuten",
             f"Bewertungsmethode: {h(BEWERTUNG.get(e.get('grademethod', '1'), 'Bester Versuch'))}"]
    if kennwort:
        infos.append("Für diesen Test ist ein Kennwort nötig.")
    if seb_an:
        infos.append("Dieser Test muss mit dem Safe Exam Browser durchgeführt werden.")
    infozeilen = "".join(f"      <p>{x}</p>\n" for x in infos)

    danach = ['Den Test öffnen und "Einstellungen" wählen.']
    if kennwort:
        danach.append(f'Unter "Weitere Zugriffsbeschränkungen" das Kennwort neu vergeben. In der Datei steht nur der '
                      f'Platzhalter "{h(kennwort)}".')
    danach.append('Unter "Zeit" den Zeitraum ("Test öffnen" und "Test schließen") für den Termin eintragen.')
    if seb_an:
        danach.append('Unter "Safe Exam Browser" prüfen, ob die Einstellung zur Klasse passt. Der Test verlangt den Safe Exam Browser.')
    danach.append('Speichern und den Test einmal mit "Vorschau" selbst durchklicken.')
    danach_html = "".join(f"      <li>{x}</li>\n" for x in danach)

    def sichtbar(feld):
        try:
            return int(e.get(feld, "0") or 0) & NACH_ABGABE
        except ValueError:
            return False
    zu_sehen = [n for f, n in (("reviewmarks", "Punkte"), ("reviewcorrectness", "richtig oder falsch"),
                               ("reviewspecificfeedback", "Rückmeldungen zu den Antworten"),
                               ("reviewgeneralfeedback", "allgemeines Feedback"),
                               ("reviewrightanswer", "richtige Antworten"), ("reviewoverallfeedback", "Gesamtfeedback (Note)"))
                if sichtbar(f)]
    ueberpruefung = ("sehen " + ", ".join(zu_sehen)) if zu_sehen else "sehen nichts"

    abschnitte = [
        ("Allgemeines", [("Name", h(info["name"]))]),
        ("Zeit", [("Zeitbegrenzung", f"{info['minuten']} Minuten"),
                  ("Wenn die Zeit abgelaufen ist", "Versuch wird automatisch abgegeben" if e.get("overduehandling") == "autosubmit"
                   else h(e.get("overduehandling", ""))),
                  ("Test öffnen / schließen", "nicht gesetzt (trägst du ein)")]),
        ("Bewertung", [("Erlaubte Versuche", h(versuche_txt)),
                       ("Bewertungsmethode", h(BEWERTUNG.get(e.get("grademethod", "1"), ""))),
                       ("Maximale Bewertung", f"{de(info['summe'])} (Summe der Fragenpunkte)")]),
        ("Fragenanordnung", [("Seitenumbruch", f"nach je {info['pro_seite']} Fragen" if info["pro_seite"] else "alle auf einer Seite"),
                             ("Navigation", "frei" if e.get("navmethod") == "free" else "nacheinander (ohne Zurück)")]),
        ("Frageverhalten", [("Antworten mischen", "ja" if e.get("shuffleanswers") == "1" else "nein"),
                            ("Frageverhalten", h(VERHALTEN.get(e.get("preferredbehaviour", ""), e.get("preferredbehaviour", ""))))]),
        ("Überprüfungsoptionen", [("Direkt nach der Abgabe", f"Lernende {ueberpruefung}")]),
        ("Weitere Zugriffsbeschränkungen", [("Kennwort", f'Platzhalter "{h(kennwort)}", neu vergeben' if kennwort else "keins")]),
        ("Safe Exam Browser", [("Safe Exam Browser erforderlich", "ja" if seb_an else "nein")]),
    ]
    einst = "".join(f'    <details class="fs" open><summary>{h(t_)}</summary>\n' + "".join(zeile(a, b) for a, b in z) +
                    "    </details>\n" for t_, z in abschnitte)

    fragen, seite = [], 0
    for nr, (_, punkte, name, typ) in enumerate(info["slots"], 1):
        s = (nr - 1) // info["pro_seite"] + 1 if info["pro_seite"] else 1
        if s != seite:
            seite = s
            fragen.append(f'    <div class="page">Seite {s}</div>\n')
        fragen.append(f'    <div class="slot"><span class="nr">{nr}</span><span class="typ">{h(TYPNAMEN.get(typ, typ))}</span>'
                      f'<span class="name">{h(name)}</span><span class="pkt">{de(punkte)}</span></div>\n')

    # Oberste Stufe: Moodle setzt die Obergrenze über die Höchstpunktzahl (Vorlage 110 %), angezeigt wird "bis Höchstpunktzahl".
    noten = "".join(f'      <tr><td>{h(html.unescape(re.sub(r"<[^>]+>", "", t_ or "")).strip())}</td><td class="z">{de(lo)}</td>'
                    f'<td class="z">{"bis " + de(info["summe"]) if i == 0 else de(hi)}</td>'
                    f'<td class="z">{de(p * 100, 0)} %</td></tr>\n'
                    for i, (t_, lo, hi, p) in enumerate(info["noten"]))
    noten_txt = ("Die Schülerinnen und Schüler sehen die Note direkt nach der Abgabe." if sichtbar("reviewoverallfeedback") else
                 "Die Schülerinnen und Schüler sehen die Note mit diesen Überprüfungsoptionen nicht, du siehst sie in den Ergebnissen beim Versuch.")

    werte = {"NAME": h(info["name"]), "MBZ": h(info["mbz"]), "XML": h(info["xml"]), "ABSCHNITT": h(info["abschnitt"]),
             "INFOZEILEN": infozeilen.rstrip("\n"), "DANACH": danach_html.rstrip("\n"), "EINSTELLUNGEN": einst.rstrip("\n"),
             "ANZAHL": str(len(info["slots"])), "SUMME": de(info["summe"]), "PROSEITE": str(info["pro_seite"] or "alle"),
             "FRAGEN": "".join(fragen).rstrip("\n"), "NOTEN": noten.rstrip("\n"), "NOTEN_SICHTBAR": noten_txt,
             "DATUM": time.strftime("%d.%m.%Y", time.localtime(info["jetzt"]))}
    seite_html = ANLEITUNG.read_text(encoding="utf-8")
    for k, w in werte.items():
        seite_html = seite_html.replace("{{" + k + "}}", w)
    rest = re.findall(r"\{\{[A-Z_]+\}\}", seite_html)
    if rest:
        raise Fehler(f"Anleitung: Platzhalter nicht gefüllt: {sorted(set(rest))}")
    ziel.write_text(seite_html, encoding="utf-8", newline="\n")


def standard_ziel(xml: Path) -> Path:
    """Test-<Thema>/Fragen-<Thema>.xml ergibt Test-<Thema>/Test-<Thema>.mbz."""
    if xml.parent.name.startswith("Test-"):
        return xml.parent / f"{xml.parent.name}.mbz"
    stamm = xml.stem
    if stamm.startswith("Fragen-"):
        stamm = "Test-" + stamm[len("Fragen-"):]
    return xml.with_name(stamm + ".mbz")

def thema_aus_anleitung(ordner: Path) -> str | None:
    """Thema aus der Anleitung eines früheren Baus (<title>Test - Thema – Anleitung</title>)."""
    seite = ordner / "index.html"
    if seite.is_file():
        m = re.search(r"<title>Test - (.*?) – Anleitung</title>", seite.read_text(encoding="utf-8"))
        if m:
            return html.unescape(m.group(1))
    return None


def pruefe_ordner(xml: Path, thema: str):
    """Der Ordner heißt Test-<Thema als Ordnername>. Im Ordnerschema Pflicht, außerhalb nur ein Hinweis."""
    soll = "Test-" + unterrichtsmaterial.namensteil(thema)
    ordner = xml.resolve().parent
    if ordner.name == soll:
        return
    text = f'Der Ordner heißt "{ordner.name}", zum Thema "{thema}" gehört "{soll}".'
    try:
        unterrichtsmaterial.aus_pfad(str(ordner))
    except unterrichtsmaterial.UnterrichtsmaterialFehler:
        print("Hinweis: " + text)
        return
    raise Fehler(text + " Ordner umbenennen oder --thema anpassen.")


# ---------------------------------------------------------------------------
# Prüfen


def pruefen(pfad: Path) -> list[str]:
    probleme = []
    with tarfile.open(pfad, "r:gz") as tar:
        dateien = {m.name: tar.extractfile(m).read() for m in tar.getmembers() if m.isfile()}
    index = dateien.get(".ARCHIVE_INDEX", b"").decode("utf-8").splitlines()
    eintraege = {z.split("\t")[0].rstrip("/") for z in index[1:] if z}
    with tarfile.open(pfad, "r:gz") as tar:
        alle = {m.name.rstrip("/") for m in tar.getmembers()} - {".ARCHIVE_INDEX"}
    if eintraege != alle:
        probleme.append(f".ARCHIVE_INDEX passt nicht zum Inhalt: {sorted(eintraege ^ alle)}")
    if not index or not index[0].endswith(f"Count: {len(alle)}"):
        probleme.append(".ARCHIVE_INDEX: falsche Anzahl")
    baeume = {}
    for name, inhalt in dateien.items():
        if name.endswith(".xml"):
            try:
                baeume[name] = ET.fromstring(inhalt)
            except ET.ParseError as e:
                probleme.append(f"{name}: kein gültiges XML ({e})")
    if probleme:
        return probleme
    quizdatei = [n for n in baeume if re.fullmatch(r"activities/quiz_\d+/quiz\.xml", n)]
    if len(quizdatei) != 1:
        return ["keine oder mehrere quiz.xml"]
    ordner = quizdatei[0].rsplit("/", 1)[0]
    quiz = baeume[quizdatei[0]].find("quiz")
    fragen = baeume["questions.xml"]
    eintraege = {e.get("id"): e for e in fragen.iter("question_bank_entry")}
    frage_ids = {q.get("id"): q for q in fragen.iter("question")}
    kat_ids = {k.get("id") for k in fragen.findall("question_category")}
    for k in fragen.findall("question_category"):
        if k.findtext("parent") not in kat_ids | {"0"}:
            probleme.append(f"Kategorie {k.findtext('name')}: unbekannte Elternkategorie")
    summe = Decimal(0)
    for qi in quiz.findall("question_instances/question_instance"):
        e = qi.findtext("question_reference/questionbankentryid")
        if e not in eintraege:
            probleme.append(f"Slot {qi.findtext('slot')}: Fragensammlungs-Eintrag {e} fehlt")
        summe += Decimal(qi.findtext("maxmark"))
    for ma in fragen.iter("multianswer"):
        for uid in ma.findtext("sequence").split(","):
            u = frage_ids.get(uid)
            if u is None or u.findtext("parent") != ma.findtext("question"):
                probleme.append(f"Lückentext {ma.findtext('question')}: Teilfrage {uid} fehlt oder falsch verknüpft")
    for tf in fragen.iter("truefalse"):
        aids = {a.get("id") for a in fragen.iter("answer")}
        if tf.findtext("trueanswer") not in aids or tf.findtext("falseanswer") not in aids:
            probleme.append("Wahr/Falsch: Antwort-Verweis fehlt")
    sg, gr = Decimal(quiz.findtext("sumgrades")), Decimal(quiz.findtext("grade"))
    noten = baeume[f"{ordner}/grades.xml"]
    gm = Decimal(noten.findtext("grade_items/grade_item/grademax"))
    if not (sg == summe == gr == gm):
        probleme.append(f"Punkte uneinheitlich: Summe Slots {summe}, sumgrades {sg}, grade {gr}, grademax {gm}")
    stufen = sorted((Decimal(f.findtext("mingrade")), Decimal(f.findtext("maxgrade")))
                    for f in quiz.findall("feedbacks/feedback"))
    for (lo1, hi1), (lo2, _) in zip(stufen, stufen[1:]):
        if hi1 != lo2:
            probleme.append(f"Notenstufen nicht lückenlos bei {hi1}/{lo2}")
    if stufen and (stufen[0][0] != 0 or stufen[-1][1] < sg):
        probleme.append("Notenstufen decken nicht 0 bis Höchstpunktzahl ab")
    inforef = baeume[f"{ordner}/inforef.xml"]
    if {i.text for i in inforef.iter("id") if i.text} != kat_ids | {noten.find("grade_items/grade_item").get("id")}:
        probleme.append("inforef.xml passt nicht zu Kategorien und Bewertung")
    m = baeume["moodle_backup.xml"]
    if m.findtext("information/contents/activities/activity/title") != quiz.findtext("name"):
        probleme.append("moodle_backup.xml: Titel passt nicht zum Testnamen")
    if m.findtext("information/contents/activities/activity/directory") != ordner:
        probleme.append("moodle_backup.xml: Ordner der Aktivität passt nicht")
    return probleme


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("xml", nargs="?", type=Path, help="geprüfte Moodle-XML-Datei (Test-<Thema>/Fragen-<Thema>.xml)")
    ap.add_argument("--thema", help='Thema, ergibt den Testnamen "Test - <Thema>" (beim erneuten Bau aus der Anleitung)')
    ap.add_argument("--zeit", type=int, help="Arbeitszeit in Minuten")
    ap.add_argument("--abschnitt", type=int, help="Kursabschnitt (Nummer), in den der Test kommt (sonst wie in der Vorlage)")
    ap.add_argument("--out", type=Path, help="Zieldatei (Standard: Test-<Thema>.mbz neben der XML)")
    ap.add_argument("--keine-anleitung", action="store_true", help="index.html nicht schreiben")
    ap.add_argument("--vorlage", type=Path, default=VORLAGE_STANDARD)
    ap.add_argument("--pruefen", type=Path, metavar="MBZ", help="nur eine fertige Sicherung prüfen")
    a = ap.parse_args()
    try:
        if a.pruefen:
            probleme = pruefen(a.pruefen)
            for p in probleme:
                print("FEHLER:", p)
            print("Prüfung bestanden." if not probleme else f"{len(probleme)} Problem(e).")
            sys.exit(1 if probleme else 0)
        thema = a.thema or (thema_aus_anleitung(a.xml.parent) if a.xml else None)
        if not a.xml or not thema or not a.zeit:
            ap.error("XML-Datei, --thema und --zeit sind nötig.")
        if a.zeit <= 0:
            ap.error("--zeit muss größer als 0 sein.")
        pruefe_ordner(a.xml, thema)
        ziel = a.out or standard_ziel(a.xml)
        info = baue(a.xml, thema, a.zeit, ziel, a.vorlage, a.abschnitt)
        if not a.keine_anleitung:
            schreibe_anleitung(ziel.parent / "index.html", info)
    except Fehler as e:
        print(f"Fehler: {e}")
        sys.exit(2)
    print(f"Gebaut: {ziel}")
    if not a.keine_anleitung:
        print(f"Anleitung: {ziel.parent / 'index.html'}")
    print(f'Test "{info["name"]}": {len(info["slots"])} Fragen, {info["summe"].normalize():f} Punkte, '
          f'{info["minuten"]} Minuten, {info["pro_seite"]} Fragen pro Seite, Kursabschnitt {info["abschnitt"]}')
    for nr, (_, p, n, typ) in enumerate(info["slots"], 1):
        print(f"  {nr:2}. {n} ({typ}, {p.normalize():f} P.)")
    probleme = pruefen(ziel)
    for p in probleme:
        print("FEHLER:", p)
    print("Prüfung bestanden." if not probleme else f"{len(probleme)} Problem(e).")
    sys.exit(1 if probleme else 0)


if __name__ == "__main__":
    main()
