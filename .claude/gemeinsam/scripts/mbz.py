"""
mbz.py - gemeinsame Bausteine für Moodle-Sicherungen (.mbz): eindeutige IDs und das Archiv mit .ARCHIVE_INDEX.
Genutzt von .claude/skills/Baue-Kurs/scripts/build-mbz.py und .claude/skills/ByCS-Test/scripts/build-test-mbz.py.
Nur Python-Standardbibliothek (Windows und Mac, ab Python 3.9).
"""
from __future__ import annotations

import io
import random
import tarfile
from pathlib import Path


class IdGen:
    """Eindeutige Ganzzahlen für die Sicherung. Moodle ordnet sie beim Wiederherstellen neu zu."""

    def __init__(self, reserviert: set[int] | None = None):
        self.wert = random.randint(10_000_000, 900_000_000)
        self.reserviert = reserviert or set()  # IDs aus eingebundenen Test-Sicherungen

    def neu(self) -> int:
        self.wert += random.randint(7, 90)
        while self.wert in self.reserviert:
            self.wert += 1
        return self.wert


class Archiv:
    """Sammelt alle Dateien im Speicher und schreibt sie wie Moodle (tar.gz mit .ARCHIVE_INDEX)."""

    def __init__(self, jetzt: int):
        self.jetzt = jetzt
        self.dateien: dict[str, bytes] = {}
        self.ordner: set[str] = set()

    def datei(self, pfad: str, inhalt: str | bytes):
        if isinstance(inhalt, str):
            inhalt = inhalt.encode("utf-8")
        teile = pfad.split("/")
        for i in range(1, len(teile)):
            self.ordner.add("/".join(teile[:i]))
        self.dateien[pfad] = inhalt

    def schreibe(self, ziel: Path):
        ziel.parent.mkdir(parents=True, exist_ok=True)
        zeilen: list[tuple[str, bytes | None]] = [(o, None) for o in sorted(self.ordner)]
        zeilen += [(p, self.dateien[p]) for p in sorted(self.dateien)]
        # .ARCHIVE_INDEX wie bei Moodle: Kopfzeile mit Anzahl, dann je Eintrag Pfad, Art, Größe, Zeit.
        index = [f"Moodle archive file index. Count: {len(zeilen)}"]
        for name, inhalt in zeilen:
            index.append(f"{name}/\td\t0\t?" if inhalt is None else f"{name}\tf\t{len(inhalt)}\t{self.jetzt}")
        index_bytes = ("\n".join(index) + "\n").encode("utf-8")
        with tarfile.open(ziel, "w:gz", format=tarfile.USTAR_FORMAT) as tar:
            info = tarfile.TarInfo(".ARCHIVE_INDEX")
            info.size = len(index_bytes)
            info.mtime = self.jetzt
            tar.addfile(info, io.BytesIO(index_bytes))
            for name, inhalt in zeilen:
                info = tarfile.TarInfo(name)
                info.mtime = self.jetzt
                if inhalt is None:
                    info.type = tarfile.DIRTYPE
                    info.mode = 0o755
                    tar.addfile(info)
                else:
                    info.size = len(inhalt)
                    info.mode = 0o644
                    tar.addfile(info, io.BytesIO(inhalt))
